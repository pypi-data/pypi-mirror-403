"""
NC1709 Rate Limiter Tests

Tests for the token bucket rate limiting implementation.
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import patch

from nc1709.utils.rate_limiter import (
    TokenBucket,
    RateLimiterRegistry,
    RateLimitExceeded,
    RateLimitStrategy,
    RateLimiterConfig,
    rate_limited,
    get_rate_limiter,
    get_rate_limiter_registry,
)


class TestTokenBucket:
    """Test TokenBucket functionality"""

    def test_initial_tokens(self):
        """Bucket starts with configured tokens"""
        bucket = TokenBucket(
            tokens_per_second=10,
            bucket_size=100,
            initial_tokens=50
        )
        assert bucket.get_tokens() == 50

    def test_default_initial_tokens(self):
        """Bucket defaults to bucket_size tokens"""
        bucket = TokenBucket(bucket_size=100)
        assert bucket.get_tokens() == 100

    def test_acquire_consumes_tokens(self):
        """Acquiring consumes tokens"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)

        bucket.acquire(10)
        assert bucket.get_tokens() < 100

    def test_tokens_refill_over_time(self):
        """Tokens refill based on rate"""
        bucket = TokenBucket(
            tokens_per_second=100,
            bucket_size=100,
            initial_tokens=0
        )

        # Wait for some refill
        time.sleep(0.1)

        # Should have ~10 tokens (100 * 0.1)
        tokens = bucket.get_tokens()
        assert 5 < tokens < 15  # Allow some margin

    def test_bucket_size_limit(self):
        """Tokens don't exceed bucket size"""
        bucket = TokenBucket(
            tokens_per_second=1000,
            bucket_size=50,
            initial_tokens=50
        )

        time.sleep(0.1)

        # Should still be capped at 50
        assert bucket.get_tokens() == 50

    def test_reject_strategy(self):
        """REJECT strategy raises exception"""
        bucket = TokenBucket(
            bucket_size=10,
            initial_tokens=0,
            strategy=RateLimitStrategy.REJECT
        )

        with pytest.raises(RateLimitExceeded) as exc_info:
            bucket.acquire(5)

        assert exc_info.value.retry_after > 0

    def test_block_strategy_waits(self):
        """BLOCK strategy waits for tokens"""
        bucket = TokenBucket(
            tokens_per_second=100,
            bucket_size=100,
            initial_tokens=0,
            strategy=RateLimitStrategy.BLOCK
        )

        start = time.time()
        bucket.acquire(5)  # Should wait ~50ms
        elapsed = time.time() - start

        assert elapsed > 0.03  # At least some waiting
        assert elapsed < 0.5   # But not too long

    def test_degrade_strategy_allows(self):
        """DEGRADE strategy allows without tokens"""
        bucket = TokenBucket(
            bucket_size=10,
            initial_tokens=0,
            strategy=RateLimitStrategy.DEGRADE
        )

        result = bucket.acquire(5)
        assert result is True

    def test_max_wait_time_enforced(self):
        """Max wait time causes rejection"""
        bucket = TokenBucket(
            tokens_per_second=0.1,  # Very slow
            bucket_size=100,
            initial_tokens=0,
            strategy=RateLimitStrategy.BLOCK,
            max_wait_time=0.1  # Very short max wait
        )

        with pytest.raises(RateLimitExceeded):
            bucket.acquire(100)  # Would need 1000 seconds

    @pytest.mark.asyncio
    async def test_async_acquire(self):
        """Async acquire works correctly"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)

        result = await bucket.acquire_async(10)
        assert result is True
        assert bucket.get_tokens() < 100

    @pytest.mark.asyncio
    async def test_async_block_strategy(self):
        """Async BLOCK strategy waits"""
        bucket = TokenBucket(
            tokens_per_second=100,
            bucket_size=100,
            initial_tokens=0,
            strategy=RateLimitStrategy.BLOCK
        )

        start = time.time()
        await bucket.acquire_async(5)
        elapsed = time.time() - start

        assert elapsed > 0.03

    def test_statistics_tracking(self):
        """Statistics are tracked correctly"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)

        bucket.acquire(10)
        bucket.acquire(20)

        stats = bucket.get_stats()

        assert stats["total_requests"] == 2
        assert stats["allowed_requests"] == 2
        assert stats["tokens_consumed"] == 30

    def test_reset(self):
        """Reset restores initial state"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)

        bucket.acquire(50)
        assert bucket.get_tokens() < 100

        bucket.reset()

        assert bucket.get_tokens() == 100
        assert bucket.stats.total_requests == 0


class TestTokenBucketConcurrency:
    """Test thread safety of TokenBucket"""

    def test_concurrent_sync_acquire(self):
        """Sync acquire is thread-safe"""
        bucket = TokenBucket(
            tokens_per_second=1000,
            bucket_size=1000,
            initial_tokens=1000
        )

        errors = []
        acquired = []

        def worker():
            try:
                for _ in range(100):
                    bucket.acquire(1)
                    acquired.append(1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(acquired) == 1000

    @pytest.mark.asyncio
    async def test_concurrent_async_acquire(self):
        """Async acquire is safe with concurrent access"""
        bucket = TokenBucket(
            tokens_per_second=1000,
            bucket_size=1000,
            initial_tokens=1000
        )

        async def worker():
            for _ in range(100):
                await bucket.acquire_async(1)

        await asyncio.gather(*[worker() for _ in range(10)])

        # All 1000 tokens should be consumed
        stats = bucket.get_stats()
        assert stats["tokens_consumed"] == 1000


class TestRateLimiterRegistry:
    """Test RateLimiterRegistry functionality"""

    @pytest.fixture
    def registry(self):
        return RateLimiterRegistry()

    def test_get_or_create(self, registry):
        """get_or_create creates new limiter"""
        limiter = registry.get_or_create("test_key")

        assert limiter is not None
        assert isinstance(limiter, TokenBucket)

    def test_get_returns_same_limiter(self, registry):
        """Same key returns same limiter"""
        limiter1 = registry.get_or_create("key")
        limiter2 = registry.get_or_create("key")

        assert limiter1 is limiter2

    def test_different_keys_different_limiters(self, registry):
        """Different keys get different limiters"""
        limiter1 = registry.get_or_create("key1")
        limiter2 = registry.get_or_create("key2")

        assert limiter1 is not limiter2

    def test_custom_config(self, registry):
        """Custom config is applied"""
        limiter = registry.get_or_create(
            "custom",
            tokens_per_second=50,
            bucket_size=200
        )

        assert limiter.tokens_per_second == 50
        assert limiter.bucket_size == 200

    def test_remove(self, registry):
        """Remove deletes limiter"""
        registry.get_or_create("to_remove")
        assert registry.get("to_remove") is not None

        registry.remove("to_remove")
        assert registry.get("to_remove") is None

    def test_get_all_stats(self, registry):
        """get_all_stats returns all limiter stats"""
        registry.get_or_create("a")
        registry.get_or_create("b")

        stats = registry.get_all_stats()

        assert "a" in stats
        assert "b" in stats

    def test_reset_all(self, registry):
        """reset_all resets all limiters"""
        limiter1 = registry.get_or_create("a", initial_tokens=100)
        limiter2 = registry.get_or_create("b", initial_tokens=100)

        limiter1.acquire(50)
        limiter2.acquire(50)

        registry.reset_all()

        assert limiter1.get_tokens() == limiter1.bucket_size
        assert limiter2.get_tokens() == limiter2.bucket_size


class TestRateLimitedDecorator:
    """Test rate_limited decorator"""

    def test_sync_function_rate_limited(self):
        """Sync functions are rate limited"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)
        call_count = 0

        @rate_limited(bucket, tokens=10)
        def my_function():
            nonlocal call_count
            call_count += 1
            return "result"

        # Should succeed 10 times (100 tokens / 10 per call)
        for _ in range(10):
            my_function()

        assert call_count == 10
        assert bucket.get_tokens() < 5  # ~0 tokens left

    @pytest.mark.asyncio
    async def test_async_function_rate_limited(self):
        """Async functions are rate limited"""
        bucket = TokenBucket(bucket_size=100, initial_tokens=100)
        call_count = 0

        @rate_limited(bucket, tokens=10)
        async def my_async_function():
            nonlocal call_count
            call_count += 1
            return "result"

        for _ in range(10):
            await my_async_function()

        assert call_count == 10


class TestGlobalRateLimiter:
    """Test global rate limiter functions"""

    def test_get_rate_limiter(self):
        """get_rate_limiter returns limiter"""
        limiter = get_rate_limiter("test_global")
        assert isinstance(limiter, TokenBucket)

    def test_get_rate_limiter_registry(self):
        """get_rate_limiter_registry returns registry"""
        registry = get_rate_limiter_registry()
        assert isinstance(registry, RateLimiterRegistry)


class TestRateLimitExceeded:
    """Test RateLimitExceeded exception"""

    def test_exception_has_retry_after(self):
        """Exception includes retry_after"""
        exc = RateLimitExceeded("Test", retry_after=5.0)

        assert exc.retry_after == 5.0
        assert "Test" in str(exc)
