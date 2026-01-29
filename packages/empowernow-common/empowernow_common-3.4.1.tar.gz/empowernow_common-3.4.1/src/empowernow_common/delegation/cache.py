"""Delegation caching with TTL and invalidation.

This module provides a two-tier caching system for delegations:

Cache Tiers:
    L1 (in-memory): Per-process, 3s TTL, no negative caching
    L2 (Redis): Shared across instances, 30s TTL, supports negative caching

Consistency Model:
    - Redis is shared across all instances
    - In-memory is per-process (not shared)
    - Kafka events trigger invalidation (see events.py)
    - TTL provides eventual consistency fallback

Usage:
    # L1 only (single process)
    l1 = InMemoryDelegationCache()
    await l1.set(delegator, delegate, delegation, ttl=3)
    d = await l1.get(delegator, delegate)

    # L2 with Redis
    l2 = RedisDelegationCache(redis_client)
    await l2.set(delegator, delegate, delegation, ttl=30)
    await l2.set_negative(delegator, delegate, ttl=10)  # Cache "not found"
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from .models import Delegation

if TYPE_CHECKING:
    pass  # For Redis type hints

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class DelegationCacheConfig:
    """Configuration for delegation cache.

    Attributes:
        ttl_seconds: Default TTL for positive cache entries (L2).
        negative_ttl_seconds: TTL for "not found" entries (L2 only).
        max_entries: Maximum entries in L1 cache (TTL-based eviction).
        l1_ttl_seconds: TTL for L1 in-memory cache.
    """

    ttl_seconds: int = 30
    """Default TTL for positive entries in L2."""

    negative_ttl_seconds: int = 10
    """TTL for negative (not found) entries in L2."""

    max_entries: int = 10000
    """Maximum entries in L1 cache (TTL-based eviction when exceeded)."""

    l1_ttl_seconds: int = 3
    """TTL for L1 in-memory cache."""


# =============================================================================
# Abstract Base
# =============================================================================


class DelegationCache(ABC):
    """Abstract base for delegation caches.

    All cache implementations must implement get, set, and invalidate.
    Additional methods like set_negative are optional.
    """

    @abstractmethod
    async def get(self, delegator_arn: str, delegate_arn: str) -> Optional[Delegation]:
        """Get delegation from cache.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.

        Returns:
            Delegation if found and not expired, None otherwise.
        """
        ...

    @abstractmethod
    async def set(
        self,
        delegator_arn: str,
        delegate_arn: str,
        delegation: Delegation,
        ttl: Optional[int] = None,
    ) -> None:
        """Store delegation in cache.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.
            delegation: The delegation to cache.
            ttl: TTL in seconds (uses default if not specified).
        """
        ...

    @abstractmethod
    async def invalidate(self, delegator_arn: str, delegate_arn: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.

        Returns:
            True if entry was found and removed.
        """
        ...

    async def get_ttl(self, delegator_arn: str, delegate_arn: str) -> Optional[float]:
        """Get remaining TTL for an entry.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.

        Returns:
            Remaining TTL in seconds, or None if not found/not supported.
        """
        return None

    async def set_negative(
        self,
        delegator_arn: str,
        delegate_arn: str,
        ttl: Optional[int] = None,
    ) -> None:
        """Store a negative (not found) cache entry.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.
            ttl: TTL in seconds (uses default if not specified).
        """
        pass  # Default: no-op, subclasses can override


# =============================================================================
# In-Memory Cache (L1)
# =============================================================================


class InMemoryDelegationCache(DelegationCache):
    """In-memory delegation cache (L1).

    Features:
    - Per-process (not shared across instances)
    - Very short TTL (default 3s)
    - No negative caching (to allow quick recovery)
    - TTL-based eviction when max_entries reached (evicts soonest-expiring)

    This cache is designed to reduce Redis/network calls for very
    hot paths. It should not be relied upon for consistency.

    Example:
        cache = InMemoryDelegationCache()
        await cache.set(delegator, delegate, delegation, ttl=3)
        d = await cache.get(delegator, delegate)
    """

    def __init__(self, config: Optional[DelegationCacheConfig] = None) -> None:
        """Initialize in-memory cache.

        Args:
            config: Cache configuration (uses defaults if not provided).
        """
        self._config = config or DelegationCacheConfig()
        # Store: key -> (expires_at, delegation)
        self._store: Dict[str, Tuple[float, Delegation]] = {}

    def _make_key(self, delegator_arn: str, delegate_arn: str) -> str:
        """Create cache key from ARNs."""
        return f"{delegator_arn}|{delegate_arn}"

    async def get(self, delegator_arn: str, delegate_arn: str) -> Optional[Delegation]:
        """Get delegation from cache."""
        key = self._make_key(delegator_arn, delegate_arn)
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, delegation = item
        now = time.time()

        if expires_at < now:
            # Expired - remove and return None
            self._store.pop(key, None)
            return None

        return delegation

    async def get_ttl(self, delegator_arn: str, delegate_arn: str) -> Optional[float]:
        """Get remaining TTL for an entry."""
        key = self._make_key(delegator_arn, delegate_arn)
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, _ = item
        remaining = expires_at - time.time()
        return max(0.0, remaining)

    async def set(
        self,
        delegator_arn: str,
        delegate_arn: str,
        delegation: Delegation,
        ttl: Optional[int] = None,
    ) -> None:
        """Store delegation in cache."""
        # Evict if at capacity
        if self._config.max_entries > 0 and len(self._store) >= self._config.max_entries:
            self._evict_oldest()

        key = self._make_key(delegator_arn, delegate_arn)
        effective_ttl = ttl if ttl is not None else self._config.l1_ttl_seconds
        self._store[key] = (time.time() + effective_ttl, delegation)

    async def invalidate(self, delegator_arn: str, delegate_arn: str) -> bool:
        """Invalidate a specific cache entry."""
        key = self._make_key(delegator_arn, delegate_arn)
        return self._store.pop(key, None) is not None

    async def invalidate_by_delegator(self, delegator_arn: str) -> int:
        """Invalidate all entries for a delegator.

        Args:
            delegator_arn: ARN of the delegating user.

        Returns:
            Number of entries invalidated.
        """
        prefix = f"{delegator_arn}|"
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    async def invalidate_by_delegate(self, delegate_arn: str) -> int:
        """Invalidate all entries for a delegate.

        Args:
            delegate_arn: ARN of the delegate agent.

        Returns:
            Number of entries invalidated.
        """
        suffix = f"|{delegate_arn}"
        keys = [k for k in self._store if k.endswith(suffix)]
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    async def clear(self) -> int:
        """Clear all entries.

        Returns:
            Number of entries cleared.
        """
        count = len(self._store)
        self._store.clear()
        return count

    def _evict_oldest(self) -> None:
        """Evict the oldest (soonest expiring) entry."""
        if not self._store:
            return
        # Find entry with earliest expiration
        oldest_key = min(self._store, key=lambda k: self._store[k][0])
        self._store.pop(oldest_key, None)

    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        return len(self._store)


# =============================================================================
# Redis Cache (L2)
# =============================================================================


class RedisDelegationCache(DelegationCache):
    """Redis-backed delegation cache (L2).

    Features:
    - Shared across all instances
    - Longer TTL (default 30s)
    - Supports negative caching (10s TTL for "not found")
    - Atomic operations via Redis commands

    Key Format:
        Positive: delegation:v23:{delegator}|{delegate}
        Negative: delegation:v23:neg:{delegator}|{delegate}

    Example:
        redis = await aioredis.from_url("redis://localhost")
        cache = RedisDelegationCache(redis)
        await cache.set(delegator, delegate, delegation, ttl=30)
        await cache.set_negative(delegator, delegate, ttl=10)
    """

    KEY_PREFIX = "delegation:v23:"
    """Key prefix for positive entries."""

    NEGATIVE_PREFIX = "delegation:v23:neg:"
    """Key prefix for negative entries."""

    def __init__(
        self,
        redis_client: Any,
        config: Optional[DelegationCacheConfig] = None,
    ) -> None:
        """Initialize Redis cache.

        Args:
            redis_client: Async Redis client (e.g., aioredis).
            config: Cache configuration (uses defaults if not provided).
        """
        self._redis = redis_client
        self._config = config or DelegationCacheConfig()

    def _make_key(self, delegator_arn: str, delegate_arn: str) -> str:
        """Create positive cache key."""
        return f"{self.KEY_PREFIX}{delegator_arn}|{delegate_arn}"

    def _make_negative_key(self, delegator_arn: str, delegate_arn: str) -> str:
        """Create negative cache key."""
        return f"{self.NEGATIVE_PREFIX}{delegator_arn}|{delegate_arn}"

    async def get(self, delegator_arn: str, delegate_arn: str) -> Optional[Delegation]:
        """Get delegation from cache."""
        key = self._make_key(delegator_arn, delegate_arn)

        try:
            data = await self._redis.get(key)
        except Exception as e:
            logger.warning("Redis get failed: %s", e)
            return None

        if data is None:
            # Check negative cache
            neg_key = self._make_negative_key(delegator_arn, delegate_arn)
            try:
                if await self._redis.exists(neg_key):
                    # Negative cache hit - we know it doesn't exist
                    logger.debug("Negative cache hit for %s->%s", delegator_arn, delegate_arn)
                    return None
            except Exception as e:
                logger.warning("Redis exists failed: %s", e)
            return None

        try:
            return Delegation.model_validate_json(data)
        except Exception as e:
            logger.warning("Failed to deserialize delegation: %s", e)
            # Delete corrupted entry
            try:
                await self._redis.delete(key)
            except Exception:
                pass
            return None

    async def get_ttl(self, delegator_arn: str, delegate_arn: str) -> Optional[float]:
        """Get remaining TTL for an entry."""
        key = self._make_key(delegator_arn, delegate_arn)
        try:
            ttl = await self._redis.ttl(key)
            if ttl < 0:
                return None
            return float(ttl)
        except Exception as e:
            logger.warning("Redis ttl failed: %s", e)
            return None

    async def set(
        self,
        delegator_arn: str,
        delegate_arn: str,
        delegation: Delegation,
        ttl: Optional[int] = None,
    ) -> None:
        """Store delegation in cache."""
        key = self._make_key(delegator_arn, delegate_arn)
        effective_ttl = ttl if ttl is not None else self._config.ttl_seconds

        try:
            # Clear negative cache entry if exists
            neg_key = self._make_negative_key(delegator_arn, delegate_arn)
            await self._redis.delete(neg_key)

            # Set positive entry
            await self._redis.set(key, delegation.model_dump_json(), ex=effective_ttl)
        except Exception as e:
            logger.warning("Redis set failed: %s", e)

    async def set_negative(
        self,
        delegator_arn: str,
        delegate_arn: str,
        ttl: Optional[int] = None,
    ) -> None:
        """Store negative cache entry (delegation not found)."""
        neg_key = self._make_negative_key(delegator_arn, delegate_arn)
        effective_ttl = ttl if ttl is not None else self._config.negative_ttl_seconds

        try:
            await self._redis.set(neg_key, "1", ex=effective_ttl)
        except Exception as e:
            logger.warning("Redis set_negative failed: %s", e)

    async def invalidate(self, delegator_arn: str, delegate_arn: str) -> bool:
        """Invalidate a specific cache entry."""
        key = self._make_key(delegator_arn, delegate_arn)
        neg_key = self._make_negative_key(delegator_arn, delegate_arn)

        try:
            results = await self._redis.delete(key, neg_key)
            return results > 0
        except Exception as e:
            logger.warning("Redis delete failed: %s", e)
            return False

    async def invalidate_by_delegator(self, delegator_arn: str) -> int:
        """Invalidate all entries for a delegator."""
        count = 0

        try:
            # Positive entries
            pattern = f"{self.KEY_PREFIX}{delegator_arn}|*"
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
                count += 1

            # Negative entries
            neg_pattern = f"{self.NEGATIVE_PREFIX}{delegator_arn}|*"
            async for key in self._redis.scan_iter(match=neg_pattern):
                await self._redis.delete(key)
                count += 1
        except Exception as e:
            logger.warning("Redis invalidate_by_delegator failed: %s", e)

        return count

    async def invalidate_by_delegate(self, delegate_arn: str) -> int:
        """Invalidate all entries for a delegate."""
        count = 0

        try:
            # Positive entries
            pattern = f"{self.KEY_PREFIX}*|{delegate_arn}"
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
                count += 1

            # Negative entries
            neg_pattern = f"{self.NEGATIVE_PREFIX}*|{delegate_arn}"
            async for key in self._redis.scan_iter(match=neg_pattern):
                await self._redis.delete(key)
                count += 1
        except Exception as e:
            logger.warning("Redis invalidate_by_delegate failed: %s", e)

        return count

    async def invalidate_by_delegation_id(self, delegation_id: str) -> int:
        """Invalidate by delegation ID.

        Note: This requires scanning all keys as we don't index by ID.
        Consider adding a secondary index if this is called frequently.

        Args:
            delegation_id: The delegation ID to invalidate.

        Returns:
            Number of entries invalidated.
        """
        # This is expensive - log a warning
        logger.warning("Invalidating by delegation_id requires full scan: %s", delegation_id)

        count = 0
        try:
            pattern = f"{self.KEY_PREFIX}*"
            async for key in self._redis.scan_iter(match=pattern):
                data = await self._redis.get(key)
                if data:
                    try:
                        delegation = Delegation.model_validate_json(data)
                        if delegation.id == delegation_id:
                            await self._redis.delete(key)
                            count += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Redis invalidate_by_delegation_id failed: %s", e)

        return count

    async def clear(self) -> int:
        """Clear all delegation cache entries."""
        count = 0

        try:
            # Clear positive entries
            pattern = f"{self.KEY_PREFIX}*"
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
                count += 1

            # Clear negative entries
            neg_pattern = f"{self.NEGATIVE_PREFIX}*"
            async for key in self._redis.scan_iter(match=neg_pattern):
                await self._redis.delete(key)
                count += 1
        except Exception as e:
            logger.warning("Redis clear failed: %s", e)

        return count


# Backwards compatibility alias
DelegationCache_InMemory = InMemoryDelegationCache


__all__ = [
    "DelegationCacheConfig",
    "DelegationCache",
    "InMemoryDelegationCache",
    "RedisDelegationCache",
    "DelegationCache_InMemory",
]
