import hashlib
import inspect
import json
from functools import wraps

from important.redis_cache.redis_client import RedisClient


class RedisUtil:
    def __init__(self, redis_host, redis_port):
        self.redis_client = RedisClient(redis_host, redis_port)

    def _generate_cache_key(self, func, args, kwargs):
        """Helper method to generate cache key - used by both sync and async"""
        serialized_args = json.dumps(
            {"args": args, "kwargs": kwargs}, sort_keys=True, default=str
        )
        hashed_args = hashlib.sha256(serialized_args.encode()).hexdigest()
        return f"{func.__name__}:{hashed_args}"

    def cache(self, expiry=None):
        """
        A decorator that caches function results in Redis.
        Automatically detects and handles both sync and async functions.
        If the key exists, return the cached value. If not, call the function and cache the result.
        """
        def decorator(func):
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    cache_key = self._generate_cache_key(func, args, kwargs)
                    return await self.redis_client.async_fetch(
                        cache_key, func, expiry, *args, **kwargs
                    )
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    cache_key = self._generate_cache_key(func, args, kwargs)
                    return self.redis_client.fetch(cache_key, func, expiry, *args, **kwargs)
                return sync_wrapper

        return decorator
