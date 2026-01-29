"""
NC1709 Enhanced Circuit Breaker Pattern

Implements circuit breaker pattern to handle service failures gracefully.
"""

import asyncio
import time
import logging
from typing import Callable, Any, Optional, Dict, Type
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation - requests pass through
    OPEN = "open"           # Failing - reject requests immediately
    HALF_OPEN = "half_open" # Testing - allow limited requests to test recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5              # Failures to open circuit
    reset_timeout: float = 60.0             # Seconds before trying to close circuit
    success_threshold: int = 3              # Successes in half-open to close circuit
    timeout: float = 30.0                   # Request timeout
    expected_exception: Type[Exception] = Exception  # Exceptions that count as failures


class CircuitBreaker:
    """
    Circuit breaker implementation for handling external service failures.
    
    The circuit breaker prevents cascading failures by:
    1. Tracking failures and automatically opening when threshold reached
    2. Rejecting requests immediately when open (fail fast)
    3. Periodically testing if service has recovered (half-open)
    4. Closing circuit when service is healthy again
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, reject requests immediately  
    - HALF_OPEN: Testing recovery, allow limited requests
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        success_threshold: int = 3,
        timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception
        )
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0

        # Request tracking
        self._lock = asyncio.Lock()
        self._half_open_in_flight = 0  # Track in-flight requests during HALF_OPEN
        self._max_half_open_requests = 1  # Only allow 1 test request at a time
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rejected_requests": 0,
            "state_transitions": 0,
            "last_failure": None,
            "last_success": None,
            "uptime": time.time()
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            Function result

        Raises:
            CircuitBreakerError: When circuit is open
            Original exception: When function fails
        """
        # Atomically check state and acquire slot if allowed
        async with self._lock:
            # Check if we should reject the request
            reject, reason = await self._should_reject_request_atomic()
            if reject:
                self.stats["rejected_requests"] += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is {self.state.value}. {reason}"
                )

            # If HALF_OPEN, increment in-flight counter while holding lock
            is_half_open_request = self.state == CircuitState.HALF_OPEN
            if is_half_open_request:
                self._half_open_in_flight += 1

            self.stats["total_requests"] += 1

        try:
            # Execute function with timeout (outside lock to allow concurrency)
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )

            # Record success (with lock)
            await self._on_success()
            return result

        except asyncio.TimeoutError:
            await self._on_failure("timeout")
            raise CircuitBreakerTimeoutError(
                f"Request timeout after {self.config.timeout}s"
            )

        except self.config.expected_exception as e:
            await self._on_failure(str(e))
            raise

        except Exception as e:
            # Unexpected exceptions don't count as circuit breaker failures
            logger.warning(f"Unexpected error in circuit breaker '{self.name}': {e}")
            raise

        finally:
            # Decrement in-flight counter if this was a half-open request
            if is_half_open_request:
                async with self._lock:
                    self._half_open_in_flight = max(0, self._half_open_in_flight - 1)
    
    async def _should_reject_request_atomic(self) -> tuple[bool, str]:
        """
        Determine if request should be rejected based on circuit state.
        Must be called while holding self._lock.

        Returns:
            Tuple of (should_reject, reason_message)
        """
        now = time.time()

        if self.state == CircuitState.CLOSED:
            return False, ""

        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if now - self.last_failure_time >= self.config.reset_timeout:
                await self._transition_to_half_open()
                # Now in HALF_OPEN, check if we can accept this request
                if self._half_open_in_flight >= self._max_half_open_requests:
                    return True, "Test request already in progress."
                return False, ""
            return True, "Service unavailable."

        elif self.state == CircuitState.HALF_OPEN:
            # In half-open state, limit concurrent test requests
            if self._half_open_in_flight >= self._max_half_open_requests:
                return True, "Test request already in progress."
            return False, ""

        return False, ""

    async def _should_reject_request(self) -> bool:
        """
        Legacy method - Determine if request should be rejected.
        Deprecated: Use _should_reject_request_atomic() instead.
        """
        reject, _ = await self._should_reject_request_atomic()
        return reject
    
    async def _on_success(self):
        """Handle successful request - thread-safe with lock"""
        async with self._lock:
            self.stats["successful_requests"] += 1
            self.stats["last_success"] = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1

                # If we have enough successes, close the circuit
                if self.success_count >= self.config.success_threshold:
                    await self._transition_to_closed()

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self, error_message: str):
        """Handle failed request - thread-safe with lock"""
        async with self._lock:
            self.stats["failed_requests"] += 1
            self.stats["last_failure"] = error_message
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()

            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens the circuit
                await self._transition_to_open()
    
    async def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.stats["state_transitions"] += 1
        
        logger.warning(
            f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
            f"Will retry in {self.config.reset_timeout}s"
        )
    
    async def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.stats["state_transitions"] += 1
        
        logger.info(f"Circuit breaker '{self.name}' half-open. Testing recovery...")
    
    async def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.stats["state_transitions"] += 1
        
        logger.info(f"Circuit breaker '{self.name}' closed. Service recovered.")
    
    async def reset(self):
        """Manually reset circuit breaker to closed state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = 0
            
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state and statistics"""
        total_requests = self.stats["total_requests"]
        uptime = time.time() - self.stats["uptime"]
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "reset_timeout": self.config.reset_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            },
            "stats": {
                "total_requests": total_requests,
                "success_rate": (
                    self.stats["successful_requests"] / total_requests 
                    if total_requests > 0 else 0
                ),
                "rejection_rate": (
                    self.stats["rejected_requests"] / total_requests
                    if total_requests > 0 else 0
                ),
                "state_transitions": self.stats["state_transitions"],
                "uptime_seconds": uptime,
                "last_failure": self.stats["last_failure"],
                "last_success": self.stats["last_success"]
            }
        }


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors"""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Raised when request times out"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services.
    
    Provides centralized circuit breaker management with monitoring
    and configuration capabilities.
    """
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def create_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        success_threshold: int = 3,
        timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception
    ) -> CircuitBreaker:
        """Create and register a new circuit breaker"""
        
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception
        )
        
        self.breakers[name] = breaker
        logger.info(f"Created circuit breaker: {name}")
        return breaker
    
    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self.breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            await breaker.reset()
        
        logger.info("All circuit breakers reset")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all circuit breakers"""
        total_breakers = len(self.breakers)
        open_breakers = sum(
            1 for breaker in self.breakers.values()
            if breaker.state == CircuitState.OPEN
        )
        half_open_breakers = sum(
            1 for breaker in self.breakers.values()
            if breaker.state == CircuitState.HALF_OPEN
        )
        
        return {
            "total_breakers": total_breakers,
            "healthy_breakers": total_breakers - open_breakers - half_open_breakers,
            "degraded_breakers": half_open_breakers,
            "failed_breakers": open_breakers,
            "overall_health": "healthy" if open_breakers == 0 else "degraded"
        }


# Global circuit breaker manager
breaker_manager = CircuitBreakerManager()