"""
NC1709 Rate Limiter Module

Implements token bucket algorithm for rate limiting API requests.
Provides protection against API abuse and ensures fair resource usage.

Algorithm: Token Bucket
- Tokens accumulate at a fixed rate up to a maximum (bucket size)
- Each request consumes one or more tokens
- If not enough tokens, request is delayed or rejected
"""

import asyncio
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded and blocking is disabled"""
    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitStrategy(Enum):
    """Strategy for handling rate limit exceeded"""
    BLOCK = "block"      # Wait until tokens available
    REJECT = "reject"    # Raise exception immediately
    DEGRADE = "degrade"  # Allow but mark as degraded


@dataclass
class RateLimiterConfig:
    """Configuration for rate limiter"""
    tokens_per_second: float = 10.0    # Token refill rate
    bucket_size: int = 100             # Maximum tokens in bucket
    initial_tokens: Optional[int] = None  # Starting tokens (default: bucket_size)
    strategy: RateLimitStrategy = RateLimitStrategy.BLOCK
    max_wait_time: float = 30.0        # Max seconds to wait for tokens


@dataclass
class RateLimiterStats:
    """Statistics for rate limiter"""
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    total_wait_time: float = 0.0
    tokens_consumed: int = 0


class TokenBucket:
    """
    Token Bucket rate limiter implementation.

    Thread-safe and async-compatible rate limiting using the token bucket algorithm.

    Example:
        limiter = TokenBucket(tokens_per_second=10, bucket_size=100)

        # Sync usage
        if limiter.acquire():
            make_request()

        # Async usage
        await limiter.acquire_async()
        await make_request()
    """

    def __init__(
        self,
        tokens_per_second: float = 10.0,
        bucket_size: int = 100,
        initial_tokens: Optional[int] = None,
        strategy: RateLimitStrategy = RateLimitStrategy.BLOCK,
        max_wait_time: float = 30.0
    ):
        """
        Initialize token bucket.

        Args:
            tokens_per_second: Rate at which tokens are added
            bucket_size: Maximum tokens the bucket can hold
            initial_tokens: Starting token count (defaults to bucket_size)
            strategy: How to handle rate limit exceeded
            max_wait_time: Maximum time to wait for tokens (BLOCK strategy)
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.strategy = strategy
        self.max_wait_time = max_wait_time

        # Current state
        self._tokens = float(initial_tokens if initial_tokens is not None else bucket_size)
        self._last_refill = time.monotonic()

        # Thread safety
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

        # Statistics
        self.stats = RateLimiterStats()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time. Must hold lock."""
        now = time.monotonic()
        elapsed = now - self._last_refill

        # Add tokens based on time elapsed
        tokens_to_add = elapsed * self.tokens_per_second
        self._tokens = min(self.bucket_size, self._tokens + tokens_to_add)
        self._last_refill = now

    def _try_consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Try to consume tokens. Must hold lock.

        Returns:
            Tuple of (success, wait_time_needed)
        """
        self._refill()

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True, 0.0

        # Calculate wait time for enough tokens
        tokens_needed = tokens - self._tokens
        wait_time = tokens_needed / self.tokens_per_second
        return False, wait_time

    def acquire(self, tokens: int = 1) -> bool:
        """
        Synchronously acquire tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens acquired, False if rejected

        Raises:
            RateLimitExceeded: If strategy is REJECT and no tokens available
        """
        self.stats.total_requests += 1
        start_time = time.monotonic()

        with self._lock:
            success, wait_time = self._try_consume(tokens)

            if success:
                self.stats.allowed_requests += 1
                self.stats.tokens_consumed += tokens
                return True

            if self.strategy == RateLimitStrategy.REJECT:
                self.stats.rejected_requests += 1
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {wait_time:.2f}s",
                    retry_after=wait_time
                )

            if self.strategy == RateLimitStrategy.DEGRADE:
                self.stats.allowed_requests += 1
                logger.warning(f"Rate limit degraded - allowing request without token")
                return True

        # BLOCK strategy - wait for tokens
        if wait_time > self.max_wait_time:
            self.stats.rejected_requests += 1
            raise RateLimitExceeded(
                f"Rate limit exceeded. Wait time {wait_time:.2f}s exceeds max {self.max_wait_time}s",
                retry_after=wait_time
            )

        time.sleep(wait_time)

        with self._lock:
            self._refill()
            self._tokens -= tokens
            self.stats.allowed_requests += 1
            self.stats.tokens_consumed += tokens
            self.stats.total_wait_time += time.monotonic() - start_time

        return True

    async def acquire_async(self, tokens: int = 1) -> bool:
        """
        Asynchronously acquire tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens acquired, False if rejected

        Raises:
            RateLimitExceeded: If strategy is REJECT and no tokens available
        """
        self.stats.total_requests += 1
        start_time = time.monotonic()

        async with self._async_lock:
            success, wait_time = self._try_consume(tokens)

            if success:
                self.stats.allowed_requests += 1
                self.stats.tokens_consumed += tokens
                return True

            if self.strategy == RateLimitStrategy.REJECT:
                self.stats.rejected_requests += 1
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {wait_time:.2f}s",
                    retry_after=wait_time
                )

            if self.strategy == RateLimitStrategy.DEGRADE:
                self.stats.allowed_requests += 1
                logger.warning(f"Rate limit degraded - allowing request without token")
                return True

        # BLOCK strategy - wait for tokens
        if wait_time > self.max_wait_time:
            self.stats.rejected_requests += 1
            raise RateLimitExceeded(
                f"Rate limit exceeded. Wait time {wait_time:.2f}s exceeds max {self.max_wait_time}s",
                retry_after=wait_time
            )

        await asyncio.sleep(wait_time)

        async with self._async_lock:
            self._refill()
            self._tokens -= tokens
            self.stats.allowed_requests += 1
            self.stats.tokens_consumed += tokens
            self.stats.total_wait_time += time.monotonic() - start_time

        return True

    def get_tokens(self) -> float:
        """Get current token count"""
        with self._lock:
            self._refill()
            return self._tokens

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.stats.total_requests,
            "allowed_requests": self.stats.allowed_requests,
            "rejected_requests": self.stats.rejected_requests,
            "rejection_rate": (
                self.stats.rejected_requests / self.stats.total_requests
                if self.stats.total_requests > 0 else 0
            ),
            "total_wait_time": self.stats.total_wait_time,
            "average_wait_time": (
                self.stats.total_wait_time / self.stats.allowed_requests
                if self.stats.allowed_requests > 0 else 0
            ),
            "tokens_consumed": self.stats.tokens_consumed,
            "current_tokens": self.get_tokens(),
            "bucket_size": self.bucket_size,
            "tokens_per_second": self.tokens_per_second,
        }

    def reset(self) -> None:
        """Reset the rate limiter to initial state"""
        with self._lock:
            self._tokens = float(self.bucket_size)
            self._last_refill = time.monotonic()
            self.stats = RateLimiterStats()


class RateLimiterRegistry:
    """
    Registry for managing multiple rate limiters.

    Allows creating and managing rate limiters for different resources
    (e.g., per-user, per-endpoint, per-API-key).
    """

    def __init__(self):
        self._limiters: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()
        self._default_config = RateLimiterConfig()

    def get_or_create(
        self,
        key: str,
        tokens_per_second: Optional[float] = None,
        bucket_size: Optional[int] = None,
        strategy: Optional[RateLimitStrategy] = None
    ) -> TokenBucket:
        """
        Get existing limiter or create new one for key.

        Args:
            key: Unique identifier (e.g., user_id, api_key, endpoint)
            tokens_per_second: Override default rate
            bucket_size: Override default bucket size
            strategy: Override default strategy

        Returns:
            TokenBucket for the key
        """
        with self._lock:
            if key not in self._limiters:
                self._limiters[key] = TokenBucket(
                    tokens_per_second=tokens_per_second or self._default_config.tokens_per_second,
                    bucket_size=bucket_size or self._default_config.bucket_size,
                    strategy=strategy or self._default_config.strategy,
                    max_wait_time=self._default_config.max_wait_time
                )
            return self._limiters[key]

    def get(self, key: str) -> Optional[TokenBucket]:
        """Get limiter for key if exists"""
        return self._limiters.get(key)

    def remove(self, key: str) -> bool:
        """Remove limiter for key"""
        with self._lock:
            if key in self._limiters:
                del self._limiters[key]
                return True
            return False

    def set_default_config(self, config: RateLimiterConfig) -> None:
        """Set default configuration for new limiters"""
        self._default_config = config

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all limiters"""
        return {
            key: limiter.get_stats()
            for key, limiter in self._limiters.items()
        }

    def reset_all(self) -> None:
        """Reset all limiters"""
        with self._lock:
            for limiter in self._limiters.values():
                limiter.reset()

    def cleanup_idle(self, max_idle_seconds: float = 3600) -> int:
        """
        Remove limiters that haven't been used recently.

        Args:
            max_idle_seconds: Remove limiters idle longer than this

        Returns:
            Number of limiters removed
        """
        now = time.monotonic()
        to_remove = []

        with self._lock:
            for key, limiter in self._limiters.items():
                idle_time = now - limiter._last_refill
                if idle_time > max_idle_seconds:
                    to_remove.append(key)

            for key in to_remove:
                del self._limiters[key]

        return len(to_remove)


# Decorator for rate limiting functions
def rate_limited(
    limiter: TokenBucket,
    tokens: int = 1
) -> Callable:
    """
    Decorator to rate limit a function.

    Example:
        limiter = TokenBucket(tokens_per_second=10)

        @rate_limited(limiter)
        def api_call():
            ...

        @rate_limited(limiter, tokens=5)  # Costs 5 tokens
        async def expensive_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                await limiter.acquire_async(tokens)
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                limiter.acquire(tokens)
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator


# Global rate limiter registry
_rate_limiter_registry: Optional[RateLimiterRegistry] = None


def get_rate_limiter_registry() -> RateLimiterRegistry:
    """Get or create the global rate limiter registry"""
    global _rate_limiter_registry
    if _rate_limiter_registry is None:
        _rate_limiter_registry = RateLimiterRegistry()
    return _rate_limiter_registry


def get_rate_limiter(
    key: str,
    tokens_per_second: float = 10.0,
    bucket_size: int = 100
) -> TokenBucket:
    """
    Convenience function to get a rate limiter for a key.

    Args:
        key: Unique identifier
        tokens_per_second: Token refill rate
        bucket_size: Maximum tokens

    Returns:
        TokenBucket for the key
    """
    return get_rate_limiter_registry().get_or_create(
        key,
        tokens_per_second=tokens_per_second,
        bucket_size=bucket_size
    )
