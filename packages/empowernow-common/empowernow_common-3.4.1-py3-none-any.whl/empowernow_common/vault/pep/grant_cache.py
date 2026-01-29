"""Grant cache for authorization decisions.

Per design §C - Cache Semantics:
    - Authorization decisions are cached (reduces PDP load)
    - Secret values are NEVER cached
    - Negative decisions (DENY) have short TTL (5s default)
    - JTI replay protection prevents token reuse attacks

This module caches DECISIONS ONLY, not secret values.
Secret values are fetched fresh from the provider each time.
"""
from __future__ import annotations

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Optional, Tuple


# Grant key: (subject, tenant_id, resource_uri, action, cnf_binding)
GrantKey = Tuple[str, str, str, str, Optional[str]]


@dataclass
class Grant:
    """Authorization grant from PDP.
    
    Represents a permission to access a secret with specified constraints.
    
    Attributes:
        grant_id: Unique identifier for this grant
        ttl_s: Time-to-live in seconds
        max_uses: Maximum number of times this grant can be used
        uses: Current use count
        decision_id: PDP decision identifier (for audit correlation)
        policy_version: Version of policy that issued this grant
        classification: Data classification level (if applicable)
        must_revalidate_on: When to revalidate ("node" = per-request)
        cnf_binding: Sender binding (DPoP jkt or mTLS thumbprint)
        wrap_ttl: Response wrapping TTL (for wrapped responses)
    """
    
    grant_id: str
    ttl_s: int
    max_uses: int
    uses: int
    decision_id: str
    policy_version: str
    classification: Optional[str] = None
    must_revalidate_on: Optional[str] = None
    cnf_binding: Optional[str] = None
    wrap_ttl: Optional[str] = None


class GrantCache:
    """Cache for authorization grants (decisions, not values).
    
    Thread-safe cache with:
    - Positive grant caching with TTL
    - Negative result caching with short TTL
    - JTI anti-replay protection
    - Use count tracking
    - Per-grant locking for concurrent access
    
    Per design: We cache DECISIONS, never secret VALUES.
    This reduces PDP load without holding sensitive data.
    
    Usage:
        cache = GrantCache()
        
        # Check negative cache first (quick deny)
        if cache.is_negative(key):
            raise AuthzDeniedError()
        
        # Try to get cached grant
        grant = cache.get(key)
        if grant is None:
            # Call PDP to get new grant
            grant = await pdp.authorize(...)
            cache.put(key, grant)
        
        # Track use count
        if not cache.increment_uses_atomically(key):
            raise AuthzDeniedError("Uses exhausted")
    """
    
    def __init__(
        self,
        negative_ttl_s: int = 5,
        anti_replay_ttl_s: int = 300,
        jitter_ms: int = 500,
        monotonic_fn: callable = time.monotonic,
    ) -> None:
        """Initialize grant cache.
        
        Args:
            negative_ttl_s: TTL for negative (DENY) results (default: 5s)
            anti_replay_ttl_s: TTL for JTI replay protection (default: 300s)
            jitter_ms: Random jitter for cache expiry (default: 500ms)
            monotonic_fn: Time function for testing (default: time.monotonic)
        """
        self._grants: Dict[GrantKey, Tuple[Grant, float]] = {}
        self._negatives: Dict[GrantKey, float] = {}
        self._replay: Dict[str, float] = {}
        self._locks: Dict[GrantKey, asyncio.Lock] = {}
        self._negative_ttl_s = negative_ttl_s
        self._anti_replay_ttl_s = anti_replay_ttl_s
        self._jitter_ms = jitter_ms
        self._now = monotonic_fn
    
    def _expired(self, expires_at: float) -> bool:
        """Check if a timestamp has expired."""
        return self._now() >= expires_at
    
    def _deadline(self, ttl_s: int, with_jitter: bool = False) -> float:
        """Calculate expiration deadline.
        
        Args:
            ttl_s: Time-to-live in seconds
            with_jitter: If True, add random jitter to prevent thundering herd
        
        Returns:
            Monotonic timestamp when entry expires
        """
        base = self._now() + float(ttl_s)
        if with_jitter and self._jitter_ms > 0:
            base += random.randint(0, self._jitter_ms) / 1000.0
        return base
    
    def get(self, key: GrantKey) -> Optional[Grant]:
        """Get a cached grant if valid.
        
        Args:
            key: Grant key tuple
        
        Returns:
            Grant if cached and not expired, None otherwise
        """
        entry = self._grants.get(key)
        if not entry:
            return None
        
        grant, exp = entry
        if self._expired(exp):
            self._grants.pop(key, None)
            return None
        
        return grant
    
    def put(self, key: GrantKey, grant: Grant) -> None:
        """Cache a grant.
        
        Args:
            key: Grant key tuple
            grant: Grant to cache
        
        Note:
            Clears any negative cache entry for this key.
        """
        exp = self._deadline(grant.ttl_s)
        self._grants[key] = (grant, exp)
        self._negatives.pop(key, None)
    
    def increment_uses_atomically(self, key: GrantKey) -> bool:
        """Atomically increment use count for a grant.
        
        Args:
            key: Grant key tuple
        
        Returns:
            True if increment succeeded, False if grant expired or uses exhausted
        """
        entry = self._grants.get(key)
        if not entry:
            return False
        
        grant, exp = entry
        if self._expired(exp):
            self._grants.pop(key, None)
            return False
        
        new_uses = grant.uses + 1
        if new_uses > max(1, grant.max_uses):
            return False
        
        grant.uses = new_uses
        self._grants[key] = (grant, exp)
        return True
    
    def set_negative(self, key: GrantKey, ttl_s: Optional[int] = None) -> None:
        """Cache a negative (DENY) result.
        
        Args:
            key: Grant key tuple
            ttl_s: Custom TTL (uses default if None)
        
        Note:
            Short TTL allows recovery from transient DENY.
        """
        ttl = ttl_s if ttl_s is not None else self._negative_ttl_s
        self._negatives[key] = self._deadline(ttl, with_jitter=True)
    
    def is_negative(self, key: GrantKey) -> bool:
        """Check if key has a cached negative result.
        
        Args:
            key: Grant key tuple
        
        Returns:
            True if negative result is cached and not expired
        """
        exp = self._negatives.get(key)
        if exp is None:
            return False
        
        if self._expired(exp):
            self._negatives.pop(key, None)
            return False
        
        return True
    
    def mark_jti(self, jti: str) -> bool:
        """Mark a JTI as used (anti-replay protection).
        
        Args:
            jti: JWT ID to mark
        
        Returns:
            True if JTI was not previously used (new)
            False if JTI was already used (replay attempt)
        """
        exp = self._replay.get(jti)
        if exp and not self._expired(exp):
            return False  # Replay detected
        
        self._replay[jti] = self._deadline(self._anti_replay_ttl_s)
        return True
    
    def invalidate(self, key: GrantKey) -> None:
        """Invalidate a specific grant.
        
        Args:
            key: Grant key tuple
        """
        self._grants.pop(key, None)
        self._negatives.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._grants.clear()
        self._negatives.clear()
        self._replay.clear()
        self._locks.clear()
    
    @asynccontextmanager
    async def lock(self, key: GrantKey) -> AsyncIterator[None]:
        """Async lock for a specific grant key.
        
        Use when multiple concurrent requests might check/update
        the same grant to avoid race conditions.
        
        Args:
            key: Grant key tuple
        
        Yields:
            None (context manager)
        """
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        
        async with lock:
            yield
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries.
        
        Call periodically to prevent memory growth.
        
        Returns:
            Number of entries removed
        """
        now = self._now()
        removed = 0
        
        # Clean grants
        expired_grants = [k for k, (_, exp) in self._grants.items() if now >= exp]
        for k in expired_grants:
            del self._grants[k]
            removed += 1
        
        # Clean negatives
        expired_negatives = [k for k, exp in self._negatives.items() if now >= exp]
        for k in expired_negatives:
            del self._negatives[k]
            removed += 1
        
        # Clean replay JTIs
        expired_jti = [k for k, exp in self._replay.items() if now >= exp]
        for k in expired_jti:
            del self._replay[k]
            removed += 1
        
        return removed
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "grants": len(self._grants),
            "negatives": len(self._negatives),
            "replay_jti": len(self._replay),
            "locks": len(self._locks),
        }
