"""
Cache Service - Redis caching layer for SkyModderAI.

Provides:
- Search result caching (100x faster for repeated queries)
- Lookup table caching (version info, credibility scores)
- Session caching (user state, preferences)
- Rate limit tracking (replaces in-memory)

Usage:
    from cache_service import get_cache, cached

    cache = get_cache()

    # Manual caching
    result = cache.get("search:skyrimse:texture mods")
    if result is None:
        result = do_expensive_search()
        cache.set("search:skyrimse:texture mods", result, ttl=3600)

    # Decorator caching
    @cached("search:{game}:{query}", ttl=3600)
    def search_game(query, game):
        return expensive_search(query, game)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Redis availability check
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Cache service will use in-memory fallback.")


class MemoryCache:
    """In-memory cache fallback when Redis is unavailable."""

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        import time

        if key in self._expiry and time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            self._stats["misses"] += 1
            return None
        value = self._cache.get(key)
        if value is not None:
            self._stats["hits"] += 1
        else:
            self._stats["misses"] += 1
        return value

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        import time

        self._cache[key] = value
        self._expiry[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern (simple prefix match)."""
        import re

        regex = re.compile(pattern.replace("*", ".*"))
        keys_to_delete = [k for k in self._cache.keys() if regex.match(k)]
        for key in keys_to_delete:
            self.delete(key)
        return len(keys_to_delete)


class RedisCache:
    """Redis-backed cache with serialization."""

    def __init__(
        self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None
    ):
        """Initialize Redis connection."""
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._stats = {"hits": 0, "misses": 0}
        self._test_connection()

    def _test_connection(self):
        """Test Redis connection."""
        try:
            self._client.ping()
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to memory cache.")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self._client.get(key)
            if value is None:
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        try:
            serialized = json.dumps(value)
            return self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.debug(f"Cache exists error for {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern (Redis glob pattern)."""
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache clear_pattern error for {pattern}: {e}")
            return 0

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter atomically."""
        try:
            return self._client.incr(key, amount)
        except Exception as e:
            logger.debug(f"Cache increment error for {key}: {e}")
            return 0

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key."""
        try:
            return self._client.expire(key, ttl)
        except Exception as e:
            logger.debug(f"Cache expire error for {key}: {e}")
            return False


class CacheService:
    """Unified cache service with automatic fallback."""

    def __init__(self):
        """Initialize cache with Redis or memory fallback."""
        self._cache = None

        # Try Redis first
        if REDIS_AVAILABLE:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_password = os.getenv("REDIS_PASSWORD")

            try:
                self._cache = RedisCache(host=redis_host, port=redis_port, password=redis_password)
                logger.info("Using Redis cache backend")
                return
            except Exception as e:
                logger.debug(f"Redis connection failed, falling back to memory cache: {e}")
                pass

        # Fallback to memory cache
        self._cache = MemoryCache()
        logger.info("Using in-memory cache backend")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (seconds)."""
        return self._cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return self._cache.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._cache.exists(key)

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        return self._cache.clear_pattern(pattern)

    # Convenience methods for common cache operations

    def cache_search(self, game: str, query: str) -> Optional[dict[str, Any]]:
        """Get cached search result."""
        key = f"search:{game}:{self._hash_query(query)}"
        return self.get(key)

    def set_search(
        self, game: str, query: str, results: list[dict[str, Any]], ttl: int = 3600
    ) -> bool:
        """Cache search result."""
        key = f"search:{game}:{self._hash_query(query)}"
        return self.set(key, results, ttl)

    def cache_lookup(self, lookup_type: str, **kwargs) -> Optional[Any]:
        """Get cached lookup result."""
        key_parts = [lookup_type] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key = f"lookup:{':'.join(key_parts)}"
        return self.get(key)

    def set_lookup(self, lookup_type: str, value: Any, ttl: int = 86400, **kwargs) -> bool:
        """Cache lookup result (default 24h TTL for lookups)."""
        key_parts = [lookup_type] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key = f"lookup:{':'.join(key_parts)}"
        return self.set(key, value, ttl)

    def cache_user(self, user_email: str, key: str) -> Optional[Any]:
        """Get cached user data."""
        return self.get(f"user:{user_email}:{key}")

    def set_user(self, user_email: str, key: str, value: Any, ttl: int = 1800) -> bool:
        """Cache user data (default 30min TTL)."""
        return self.set(f"user:{user_email}:{key}", value, ttl)

    def rate_limit(self, key: str, limit: int, window: int) -> tuple:
        """
        Check and update rate limit counter.

        Returns:
            (allowed: bool, current_count: int, reset_time: int)
        """
        import time

        current_time = int(time.time())
        window_key = f"ratelimit:{key}:{current_time // window}"

        current = self._cache.increment(window_key)
        if current == 1:
            self._cache.expire(window_key, window)

    def get_stats(self) -> dict[str, int]:
        """Get cache hit/miss statistics."""
        return self._cache._stats.copy()

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._cache._stats = {"hits": 0, "misses": 0}

        allowed = current <= limit
        reset_time = ((current_time // window) + 1) * window - current_time

        return allowed, current, reset_time

    def invalidate_search(self, game: str) -> int:
        """Invalidate all cached searches for a game."""
        return self.clear_pattern(f"search:{game}:*")

    def invalidate_all(self) -> int:
        """Invalidate all cached data (use with caution)."""
        return self.clear_pattern("*")

    @staticmethod
    def _hash_query(query: str) -> str:
        """Create short hash of query for cache key."""
        return hashlib.md5(query.lower().encode()).hexdigest()[:12]


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get or create cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(key_pattern: str, ttl: int = 3600):
    """
    Decorator for caching function results.

    Usage:
        @cached("search:{game}:{query}", ttl=3600)
        def search_game(query, game):
            return expensive_search(query, game)

    Args:
        key_pattern: Cache key pattern with {arg_name} placeholders
        ttl: Cache TTL in seconds
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function argument names
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Build cache key from pattern
            key = key_pattern
            for arg_name, arg_value in bound.arguments.items():
                key = key.replace(f"{{{arg_name}}}", str(arg_value))

            # Try cache
            cache = get_cache()
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cache miss for {key}, cached result")
            return result

        return wrapper

    return decorator


# Convenience functions for direct import
def cache_search_results(
    game: str, query: str, results: list[dict[str, Any]], ttl: int = 3600
) -> bool:
    """Cache search results."""
    return get_cache().set_search(game, query, results, ttl)


def get_cached_search_results(game: str, query: str) -> Optional[list[dict[str, Any]]]:
    """Get cached search results."""
    return get_cache().cache_search(game, query)


def invalidate_game_cache(game: str) -> int:
    """Invalidate all cached data for a game."""
    return get_cache().invalidate_search(game)
