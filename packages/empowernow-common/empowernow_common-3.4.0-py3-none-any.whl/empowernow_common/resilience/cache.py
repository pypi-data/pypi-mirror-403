"""Redis caching support for resilience patterns.

This module provides optional caching functionality that integrates
with the ResilientExecutor. Users must provide their own Redis client
or use the RedisClientFactory to create one from configuration.

Enterprise patterns:
- Configuration via environment variables or Pydantic settings
- Connection pooling with per-event-loop management
- Fail-safe operations (errors logged, not raised)
- Key validation and sanitization
- Cache statistics for monitoring

Usage:
    from empowernow_common.resilience import ResilientExecutor, ResilienceConfig
    from empowernow_common.resilience import RedisClientFactory

    # Option 1: Create client from environment variables
    redis_client = await RedisClientFactory.create()

    # Option 2: Create client from explicit config
    redis_client = await RedisClientFactory.create(
        url="redis://localhost:6379/0",
        max_connections=20,
    )

    # Option 3: Provide your own client
    import redis.asyncio as redis
    redis_client = redis.from_url(os.environ["REDIS_URL"])

    executor = ResilientExecutor(
        name="my-api",
        config=ResilienceConfig(cache_enabled=True, cache_ttl=300),
        redis_client=redis_client,
    )

    @executor.wrap(cache_ttl=300)
    async def get_data(item_id: str):
        return await fetch_from_api(item_id)
"""

import os
import re
import json
import hashlib
import logging
import asyncio
import weakref
from typing import Any, Optional, TypeVar, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Key validation regex - alphanumeric start, allows colons, dots, hyphens
_KEY_VALIDATOR_REGEX = re.compile(r"^[A-Za-z0-9][\w:.-]*$")


def validate_cache_key(key: str) -> str:
    """Validate and sanitize cache keys to prevent injection/issues.

    Args:
        key: The cache key to validate

    Returns:
        Validated (possibly sanitized) key

    Raises:
        ValueError: If key is empty or too long
    """
    if not key:
        raise ValueError("Cache key cannot be empty")

    if len(key) > 512:
        raise ValueError(f"Cache key too long: {len(key)} bytes (max 512)")

    if "\x00" in key:
        raise ValueError("Cache key cannot contain null bytes")

    if _KEY_VALIDATOR_REGEX.match(key):
        return key

    # Sanitize by replacing invalid chars with underscore
    safe_key = re.sub(r"[^\w:.-]", "_", key)
    logger.warning(
        "Sanitized cache key",
        extra={"original_key": key[:100], "sanitized_key": safe_key[:100]},
    )
    return safe_key


def generate_cache_key(
    prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
) -> str:
    """Generate cache key from function call signature.

    Creates a deterministic hash from the function name and arguments
    to use as a cache key.

    Args:
        prefix: Key prefix (e.g., "resilience:myservice:")
        func_name: Name of the function being cached
        args: Positional arguments passed to the function
        kwargs: Keyword arguments passed to the function

    Returns:
        Cache key string like "prefix:func_name:abc123def456"
    """
    key_data = {
        "func": func_name,
        "args": [_serialize_arg(a) for a in args],
        "kwargs": {k: _serialize_arg(v) for k, v in sorted(kwargs.items())},
    }
    key_hash = hashlib.sha256(
        json.dumps(key_data, sort_keys=True).encode()
    ).hexdigest()[:16]
    return validate_cache_key(f"{prefix}{func_name}:{key_hash}")


def _serialize_arg(arg: Any) -> str:
    """Serialize an argument for cache key generation."""
    if isinstance(arg, (str, int, float, bool, type(None))):
        return str(arg)
    elif isinstance(arg, (list, tuple)):
        return json.dumps([_serialize_arg(a) for a in arg])
    elif isinstance(arg, dict):
        return json.dumps({k: _serialize_arg(v) for k, v in sorted(arg.items())})
    elif hasattr(arg, "id"):
        # Handle objects with an id attribute (common pattern)
        return f"{type(arg).__name__}:{arg.id}"
    else:
        return str(arg)


class RedisClientFactory:
    """Factory for creating Redis clients from configuration.

    Follows enterprise patterns:
    - Environment variable configuration
    - Per-event-loop connection pooling
    - Connection health checking

    Environment Variables:
        REDIS_URL or REDIS__URL: Redis connection URL
        REDIS_MAX_CONNECTIONS: Max pool connections (default: 20)
        REDIS_SOCKET_TIMEOUT: Socket timeout in seconds (default: 10)
        REDIS_SOCKET_CONNECT_TIMEOUT: Connect timeout (default: 10)
        REDIS_CLIENT_NAME: Client name for identification

    Usage:
        # From environment
        client = await RedisClientFactory.create()

        # Explicit config
        client = await RedisClientFactory.create(
            url="redis://localhost:6379",
            max_connections=50,
        )
    """

    # Per-event-loop connection management (prevents cross-loop issues)
    _pools: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, Any]" = (
        weakref.WeakKeyDictionary()
    )
    _clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, Any]" = (
        weakref.WeakKeyDictionary()
    )
    _locks: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = (
        weakref.WeakKeyDictionary()
    )
    _init_lock: Optional[asyncio.Lock] = None

    @classmethod
    async def create(
        cls,
        url: Optional[str] = None,
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        client_name: Optional[str] = None,
        health_check_interval: int = 5,
        force_reconnect: bool = False,
    ) -> "Redis[str]":
        """Create or get a Redis client with connection pooling.

        Configuration priority:
        1. Explicit parameters
        2. Environment variables
        3. Default values

        Args:
            url: Redis URL (default: from REDIS_URL or REDIS__URL env)
            max_connections: Max pool connections (default: 20)
            socket_timeout: Socket timeout seconds (default: 10)
            socket_connect_timeout: Connect timeout seconds (default: 10)
            client_name: Client identifier name
            health_check_interval: Health check interval seconds
            force_reconnect: Force new connection even if exists

        Returns:
            redis.asyncio.Redis client instance

        Raises:
            ValueError: If no Redis URL configured
            ImportError: If redis package not installed
        """
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError(
                "redis package not installed. Install with: pip install redis"
            )

        loop = asyncio.get_running_loop()

        # Ensure per-loop lock
        init_lock = cls._init_lock
        if init_lock is None:
            init_lock = asyncio.Lock()
            cls._init_lock = init_lock

        async with init_lock:
            lock = cls._locks.get(loop)
            if lock is None:
                lock = asyncio.Lock()
                cls._locks[loop] = lock

        async with lock:
            # Return existing client unless force_reconnect
            if loop in cls._clients and not force_reconnect:
                return cls._clients[loop]

            # Close existing if force reconnect
            if force_reconnect and loop in cls._clients:
                try:
                    await cls._clients[loop].close()
                    if loop in cls._pools:
                        await cls._pools[loop].disconnect()
                except Exception as e:
                    logger.warning("Error closing existing Redis connection: %s", e)
                cls._pools.pop(loop, None)
                cls._clients.pop(loop, None)

            # Resolve configuration with priority: param > env > default
            redis_url = (
                url
                or os.environ.get("REDIS_URL")
                or os.environ.get("REDIS__URL")
                or os.environ.get("REDIS_CONNECTION_URL")
            )

            if not redis_url:
                raise ValueError(
                    "Redis URL not configured. Set REDIS_URL environment variable "
                    "or pass url parameter."
                )

            max_conns = max_connections or int(
                os.environ.get("REDIS_MAX_CONNECTIONS", "20")
            )
            sock_timeout = socket_timeout or float(
                os.environ.get("REDIS_SOCKET_TIMEOUT", "10")
            )
            sock_connect_timeout = socket_connect_timeout or float(
                os.environ.get("REDIS_SOCKET_CONNECT_TIMEOUT", "10")
            )
            name = client_name or os.environ.get("REDIS_CLIENT_NAME", "resilience")

            logger.info(
                "Creating Redis connection pool",
                extra={
                    "url": _redact_url(redis_url),
                    "max_connections": max_conns,
                    "client_name": name,
                },
            )

            try:
                cls._pools[loop] = redis.ConnectionPool.from_url(
                    redis_url,
                    max_connections=max_conns,
                    decode_responses=True,
                    health_check_interval=health_check_interval,
                    socket_connect_timeout=sock_connect_timeout,
                    socket_timeout=sock_timeout,
                    socket_keepalive=True,
                    retry_on_timeout=True,
                    client_name=name,
                )

                cls._clients[loop] = redis.Redis(connection_pool=cls._pools[loop])

                # Verify connection
                ping_timeout = float(os.environ.get("REDIS_PING_TIMEOUT", "5"))
                await asyncio.wait_for(
                    cls._clients[loop].ping(), timeout=ping_timeout
                )

                logger.info(
                    "Connected to Redis",
                    extra={"url": _redact_url(redis_url), "client_name": name},
                )

                return cls._clients[loop]

            except Exception as e:
                logger.error(
                    "Failed to connect to Redis: %s",
                    str(e),
                    extra={"url": _redact_url(redis_url), "error": str(e)},
                )
                # Cleanup on failure
                cls._pools.pop(loop, None)
                cls._clients.pop(loop, None)
                raise

    @classmethod
    async def close_all(cls) -> None:
        """Close all Redis connections across all event loops."""
        for loop, client in list(cls._clients.items()):
            try:
                await client.close()
            except Exception:
                pass
            cls._clients.pop(loop, None)

        for loop, pool in list(cls._pools.items()):
            try:
                await pool.disconnect()
            except Exception:
                pass
            cls._pools.pop(loop, None)

        logger.info("Closed all Redis connections")

    @classmethod
    async def health_check(cls, timeout: float = 1.0) -> Dict[str, Any]:
        """Check Redis connection health.

        Args:
            timeout: Health check timeout in seconds

        Returns:
            Dict with status, latency_ms, and error info
        """
        import time

        result = {
            "status": "unhealthy",
            "latency_ms": 0,
            "error": None,
        }

        try:
            loop = asyncio.get_running_loop()
            if loop not in cls._clients:
                result["error"] = "No Redis client initialized"
                return result

            client = cls._clients[loop]
            start = time.perf_counter()
            await asyncio.wait_for(client.ping(), timeout=timeout)
            latency = (time.perf_counter() - start) * 1000

            result.update({
                "status": "healthy",
                "latency_ms": round(latency, 2),
            })

        except asyncio.TimeoutError:
            result["error"] = "Connection timed out"
        except Exception as e:
            result["error"] = str(e)

        return result


def _redact_url(url: str) -> str:
    """Redact password from Redis URL for logging."""
    if "@" in url:
        try:
            parts = url.split("@")
            auth_part = parts[0].split("://")[1]
            if ":" in auth_part:
                user = auth_part.split(":")[0]
                return url.replace(auth_part, f"{user}:***")
        except Exception:
            return "redis://***@..."
    return url


class CacheWrapper:
    """Wrapper for async Redis caching operations.

    Provides a simple interface for get/set/delete operations with
    automatic JSON serialization and error handling.

    By default, operations are fail-safe - cache errors are logged but don't
    raise exceptions, allowing the main operation to continue.

    In security_mode, operations are fail-secure - cache errors raise exceptions
    to prevent fail-open patterns in security-critical operations.

    Args:
        redis_client: An async Redis client (e.g., redis.asyncio.Redis)
        key_prefix: Prefix for all cache keys
        default_ttl: Default TTL in seconds for cached values
        security_mode: If True, cache errors raise exceptions (fail-secure)
    """

    def __init__(
        self,
        redis_client: "Redis[str]",
        key_prefix: str = "resilience:",
        default_ttl: int = 300,
        security_mode: bool = False,
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.security_mode = security_mode
        self._hits = 0
        self._misses = 0

    def _prefixed_key(self, key: str) -> str:
        """Add key_prefix to key if not already present."""
        if self.key_prefix and not key.startswith(self.key_prefix):
            return f"{self.key_prefix}{key}"
        return key

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key (prefix will be auto-added)

        Returns:
            Cached value if found, None otherwise (cache miss)

        Raises:
            Exception: In security_mode, cache errors raise exceptions (fail-secure)
        """
        try:
            full_key = self._prefixed_key(key)
            validated_key = validate_cache_key(full_key)
            value = await self.redis.get(validated_key)
            if value:
                self._hits += 1
                # Handle both bytes and string responses
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                return json.loads(value)
            self._misses += 1
            return None
        except Exception as e:
            # SECURITY: In security mode, cache errors must raise exceptions
            # Fail-secure: do not allow operations to proceed on cache failure
            if self.security_mode:
                logger.error(
                    "Cache get failed in security mode for %s: %s",
                    key,
                    str(e)[:100],
                    extra={"cache_key": key, "error": str(e)},
                )
                raise RuntimeError(
                    f"Cache operation failed in security mode for key '{key}': {str(e)}. "
                    "Security-critical operations cannot proceed with unreliable cache."
                ) from e
            
            # Non-security mode: fail-safe (log and return None)
            logger.warning(
                "Cache get failed for %s: %s",
                key,
                str(e)[:100],
                extra={"cache_key": key, "error": str(e)},
            )
            self._misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key (prefix will be auto-added)
            value: Value to cache (must be JSON-serializable)
            ttl: TTL in seconds (uses default if not specified)

        Returns:
            True if cached successfully, False otherwise

        Raises:
            Exception: In security_mode, cache errors raise exceptions (fail-secure)
        """
        try:
            full_key = self._prefixed_key(key)
            validated_key = validate_cache_key(full_key)
            serialized = json.dumps(value, default=str)
            await self.redis.set(validated_key, serialized, ex=ttl or self.default_ttl)
            logger.debug(
                "Cached value for %s (ttl=%ds)",
                key,
                ttl or self.default_ttl,
                extra={"cache_key": key, "ttl": ttl or self.default_ttl},
            )
            return True
        except Exception as e:
            # SECURITY: In security mode, cache errors must raise exceptions
            # Fail-secure: do not allow operations to proceed on cache failure
            if self.security_mode:
                logger.error(
                    "Cache set failed in security mode for %s: %s",
                    key,
                    str(e)[:100],
                    extra={"cache_key": key, "error": str(e)},
                )
                raise RuntimeError(
                    f"Cache operation failed in security mode for key '{key}': {str(e)}. "
                    "Security-critical operations cannot proceed with unreliable cache."
                ) from e
            
            # Non-security mode: fail-safe (log and return False)
            logger.warning(
                "Cache set failed for %s: %s",
                key,
                str(e)[:100],
                extra={"cache_key": key, "error": str(e)},
            )
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key (prefix will be auto-added)

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            full_key = self._prefixed_key(key)
            validated_key = validate_cache_key(full_key)
            await self.redis.delete(validated_key)
            logger.debug("Deleted cache key: %s", key)
            return True
        except Exception as e:
            logger.warning(
                "Cache delete failed for %s: %s",
                key,
                str(e)[:100],
                extra={"cache_key": key, "error": str(e)},
            )
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Uses SCAN for production-safe iteration (non-blocking).

        Args:
            pattern: Redis key pattern (e.g., "users:*", prefix auto-added)

        Returns:
            Number of keys deleted
        """
        try:
            # Add prefix to pattern if not already present
            full_pattern = self._prefixed_key(pattern)
            keys = []
            # Use SCAN instead of KEYS for production safety
            async for key in self.redis.scan_iter(match=full_pattern, count=100):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info("Invalidated %d keys matching %s", len(keys), pattern)
            return len(keys)
        except Exception as e:
            logger.warning(
                "Cache invalidation failed for pattern %s: %s",
                pattern,
                str(e)[:100],
            )
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key (prefix will be auto-added)

        Returns:
            True if key exists, False otherwise
        """
        try:
            full_key = self._prefixed_key(key)
            validated_key = validate_cache_key(full_key)
            return bool(await self.redis.exists(validated_key))
        except Exception as e:
            logger.warning("Cache exists check failed for %s: %s", key, str(e)[:100])
            return False

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key.

        Args:
            key: Cache key (prefix will be auto-added)

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            full_key = self._prefixed_key(key)
            validated_key = validate_cache_key(full_key)
            return await self.redis.ttl(validated_key)
        except Exception as e:
            logger.warning("Cache TTL check failed for %s: %s", key, str(e)[:100])
            return -2

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, and hit rate
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate_percent": round(hit_rate, 2),
        }

    def reset_stats(self) -> None:
        """Reset cache statistics counters."""
        self._hits = 0
        self._misses = 0

