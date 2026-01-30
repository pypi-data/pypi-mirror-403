import asyncio
import pytest
from time import sleep
from important.redis_cache.redis_util import RedisUtil


@pytest.fixture
def redis_util():
    """Fixture to provide a RedisUtil instance with localhost connection."""
    util = RedisUtil(redis_host="localhost", redis_port=6379)
    util.redis_client.flushall()
    yield util
    util.redis_client.flushall()


class TestSyncCacheDecorator:
    """Test synchronous cache decorator."""

    def test_basic_caching_and_different_args(self, redis_util):
        """Test basic caching works and different args create different cache entries."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=60)
        def multiply(a, b):
            call_count["count"] += 1
            return a * b

        # First call executes function
        assert multiply(2, 3) == 6
        assert call_count["count"] == 1

        # Same args use cache
        assert multiply(2, 3) == 6
        assert call_count["count"] == 1

        # Different args execute function
        assert multiply(3, 4) == 12
        assert call_count["count"] == 2

    def test_cache_expiry(self, redis_util):
        """Test that cache expires after TTL."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=1)
        def get_value(x):
            call_count["count"] += 1
            return x

        assert get_value("test") == "test"
        assert call_count["count"] == 1

        # Should use cache
        assert get_value("test") == "test"
        assert call_count["count"] == 1

        # Wait for expiry
        sleep(1.5)
        assert get_value("test") == "test"
        assert call_count["count"] == 2

    def test_none_not_cached(self, redis_util):
        """Test that None return values are not cached."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=60)
        def maybe_none(value):
            call_count["count"] += 1
            return None if value == "none" else value

        # None not cached - called twice
        assert maybe_none("none") is None
        assert maybe_none("none") is None
        assert call_count["count"] == 2

        # Non-None cached
        assert maybe_none("value") == "value"
        assert maybe_none("value") == "value"
        assert call_count["count"] == 3


class TestAsyncCacheDecorator:
    """Test asynchronous cache decorator."""

    @pytest.mark.asyncio
    async def test_basic_caching_and_different_args(self, redis_util):
        """Test basic async caching and different args."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=60)
        async def multiply(a, b):
            call_count["count"] += 1
            await asyncio.sleep(0.01)
            return a * b

        # First call executes
        assert await multiply(2, 3) == 6
        assert call_count["count"] == 1

        # Same args use cache
        assert await multiply(2, 3) == 6
        assert call_count["count"] == 1

        # Different args execute
        assert await multiply(3, 4) == 12
        assert call_count["count"] == 2

    @pytest.mark.asyncio
    async def test_cache_expiry(self, redis_util):
        """Test async cache expiry."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=1)
        async def get_value(x):
            call_count["count"] += 1
            return x

        assert await get_value("test") == "test"
        assert call_count["count"] == 1

        await asyncio.sleep(1.5)
        assert await get_value("test") == "test"
        assert call_count["count"] == 2

    @pytest.mark.asyncio
    async def test_none_not_cached(self, redis_util):
        """Test that None is not cached in async functions."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=60)
        async def maybe_none(value):
            call_count["count"] += 1
            return None if value == "none" else value

        assert await maybe_none("none") is None
        assert await maybe_none("none") is None
        assert call_count["count"] == 2


class TestCacheKeyGeneration:
    """Test cache key generation behavior."""

    def test_kwargs_order_independence(self, redis_util):
        """Test that kwargs in different order produce the same cache key."""
        call_count = {"count": 0}

        @redis_util.cache(expiry=60)
        def func(a, b, c=None, d=None):
            call_count["count"] += 1
            return f"{a}-{b}-{c}-{d}"

        result1 = func(1, 2, c=3, d=4)
        result2 = func(1, 2, d=4, c=3)
        
        assert result1 == result2
        assert call_count["count"] == 1  # Should use cache
