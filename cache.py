"""Redis caching layer for loyalty-points-api."""
import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TTL = int(os.environ.get("CACHE_TTL_SECONDS", "300"))

_pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=20,
    socket_connect_timeout=2,
    socket_timeout=1,
    retry_on_timeout=True,
)


def _get_client() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


def get_cached(key: str) -> Optional[Any]:
    """Retrieve a value from cache. Returns None on miss or error."""
    try:
        client = _get_client()
        raw = client.get(key)
        if raw is not None:
            return json.loads(raw)
    except (redis.RedisError, json.JSONDecodeError) as exc:
        logger.warning("Cache read failed for key=%s: %s", key, exc)
    return None


def set_cached(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Store a value in cache with TTL."""
    try:
        client = _get_client()
        client.setex(key, ttl, json.dumps(value, default=str))
    except redis.RedisError as exc:
        logger.warning("Cache write failed for key=%s: %s", key, exc)


def invalidate(pattern: str) -> None:
    """Delete all keys matching the given pattern."""
    try:
        client = _get_client()
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
    except redis.RedisError as exc:
        logger.warning("Cache invalidation failed for pattern=%s: %s", pattern, exc)


def cached_route(key_prefix: str, ttl: int = DEFAULT_TTL) -> Callable:
    """Decorator for caching Flask route responses."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{':'.join(str(v) for v in kwargs.values())}"
            hit = get_cached(cache_key)
            if hit is not None:
                logger.debug("Cache hit for %s", cache_key)
                return hit
            result = fn(*args, **kwargs)
            set_cached(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
