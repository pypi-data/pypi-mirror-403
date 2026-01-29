"""
NC1709 Circuit Breaker Tests

Tests for the circuit breaker pattern implementation.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from nc1709.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    CircuitBreakerTimeoutError,
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions"""

    @pytest.fixture
    def breaker(self):
        """Create a fresh circuit breaker for each test"""
        return CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            reset_timeout=1.0,
            success_threshold=2,
            timeout=5.0
        )

    def test_initial_state_is_closed(self, breaker):
        """Circuit breaker starts in CLOSED state"""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_keeps_closed(self, breaker):
        """Successful calls keep circuit CLOSED"""
        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats["successful_requests"] == 1

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self, breaker):
        """Multiple failures open the circuit"""
        async def failing_func():
            raise Exception("Service unavailable")

        # Fail until threshold reached
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count >= 3
        assert breaker.stats["failed_requests"] == 3

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_requests(self, breaker):
        """OPEN circuit rejects requests immediately"""
        async def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        # Now requests should be rejected
        async def should_not_run():
            pytest.fail("Function should not be called when circuit is open")

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await breaker.call(should_not_run)

        assert "open" in str(exc_info.value).lower()
        assert breaker.stats["rejected_requests"] >= 1

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self, breaker):
        """Circuit transitions to HALF_OPEN after reset timeout"""
        async def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(1.1)

        # Next call attempt should transition to HALF_OPEN
        async def recovery_func():
            return "recovered"

        result = await breaker.call(recovery_func)
        assert result == "recovered"
        # After successful call in half-open, may still be half-open or closed
        assert breaker.state in (CircuitState.HALF_OPEN, CircuitState.CLOSED)

    @pytest.mark.asyncio
    async def test_half_open_closes_on_success(self, breaker):
        """Circuit closes after enough successes in HALF_OPEN"""
        async def failing_func():
            raise Exception("fail")

        async def success_func():
            return "ok"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        # Wait for reset
        await asyncio.sleep(1.1)

        # Succeed enough times to close
        for _ in range(2):  # success_threshold = 2
            await breaker.call(success_func)

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_opens_on_failure(self, breaker):
        """Circuit re-opens on failure in HALF_OPEN state"""
        async def failing_func():
            raise Exception("fail")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        # Wait for reset
        await asyncio.sleep(1.1)

        # Fail in half-open state
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerTimeout:
    """Test circuit breaker timeout handling"""

    @pytest.mark.asyncio
    async def test_timeout_counts_as_failure(self):
        """Timed out requests count as failures"""
        breaker = CircuitBreaker(
            name="timeout_test",
            failure_threshold=2,
            timeout=0.1  # 100ms timeout
        )

        async def slow_func():
            await asyncio.sleep(0.5)  # 500ms - will timeout
            return "should not reach"

        with pytest.raises(CircuitBreakerTimeoutError):
            await breaker.call(slow_func)

        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_fast_func_no_timeout(self):
        """Fast functions complete successfully"""
        breaker = CircuitBreaker(
            name="fast_test",
            timeout=1.0
        )

        async def fast_func():
            await asyncio.sleep(0.01)
            return "fast result"

        result = await breaker.call(fast_func)
        assert result == "fast result"


class TestCircuitBreakerConcurrency:
    """Test circuit breaker race condition handling"""

    @pytest.mark.asyncio
    async def test_half_open_limits_concurrent_requests(self):
        """HALF_OPEN state limits concurrent test requests"""
        breaker = CircuitBreaker(
            name="concurrency_test",
            failure_threshold=2,
            reset_timeout=0.1,
            success_threshold=1
        )

        async def failing_func():
            raise Exception("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        await asyncio.sleep(0.15)  # Wait for half-open

        # Create blocking function
        call_count = 0
        async def slow_success():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)
            return "success"

        # Launch concurrent requests
        async def attempt_call():
            try:
                return await breaker.call(slow_success)
            except CircuitBreakerOpenError:
                return "rejected"

        results = await asyncio.gather(*[attempt_call() for _ in range(3)])

        # Only 1 should execute (half_open limit), others rejected
        success_count = sum(1 for r in results if r == "success")
        rejected_count = sum(1 for r in results if r == "rejected")

        assert success_count <= 1  # At most one test request allowed
        assert rejected_count >= 2  # Others should be rejected

    @pytest.mark.asyncio
    async def test_thread_safety_under_load(self):
        """Circuit breaker handles concurrent state changes safely"""
        breaker = CircuitBreaker(
            name="load_test",
            failure_threshold=5,
            timeout=1.0
        )

        success_count = 0
        failure_count = 0

        async def mixed_func(should_fail: bool):
            if should_fail:
                raise Exception("planned failure")
            return "success"

        async def make_call(fail: bool):
            nonlocal success_count, failure_count
            try:
                await breaker.call(mixed_func, fail)
                success_count += 1
            except (Exception, CircuitBreakerOpenError):
                failure_count += 1

        # Launch many concurrent requests
        tasks = [
            make_call(i % 3 == 0)  # Every 3rd call fails
            for i in range(20)
        ]
        await asyncio.gather(*tasks)

        # Verify stats are consistent
        total = breaker.stats["successful_requests"] + breaker.stats["failed_requests"] + breaker.stats["rejected_requests"]
        assert total == breaker.stats["total_requests"]


class TestCircuitBreakerManager:
    """Test circuit breaker manager functionality"""

    @pytest.fixture
    def manager(self):
        return CircuitBreakerManager()

    def test_create_breaker(self, manager):
        """Manager creates and tracks circuit breakers"""
        breaker = manager.create_breaker(
            "test_service",
            failure_threshold=5
        )

        assert breaker.name == "test_service"
        assert breaker.config.failure_threshold == 5
        assert manager.get_breaker("test_service") is breaker

    def test_get_nonexistent_breaker(self, manager):
        """Getting nonexistent breaker returns None"""
        assert manager.get_breaker("nonexistent") is None

    def test_get_all_states(self, manager):
        """Manager reports all breaker states"""
        manager.create_breaker("service_a")
        manager.create_breaker("service_b")

        states = manager.get_all_states()

        assert "service_a" in states
        assert "service_b" in states
        assert states["service_a"]["state"] == "closed"

    @pytest.mark.asyncio
    async def test_reset_all(self, manager):
        """Manager can reset all circuit breakers"""
        breaker_a = manager.create_breaker("a", failure_threshold=1)
        breaker_b = manager.create_breaker("b", failure_threshold=1)

        # Open both breakers
        async def fail():
            raise Exception("fail")

        for breaker in [breaker_a, breaker_b]:
            with pytest.raises(Exception):
                await breaker.call(fail)

        assert breaker_a.state == CircuitState.OPEN
        assert breaker_b.state == CircuitState.OPEN

        # Reset all
        await manager.reset_all()

        assert breaker_a.state == CircuitState.CLOSED
        assert breaker_b.state == CircuitState.CLOSED

    def test_health_summary(self, manager):
        """Manager provides health summary"""
        manager.create_breaker("healthy")

        summary = manager.get_health_summary()

        assert summary["total_breakers"] == 1
        assert summary["healthy_breakers"] == 1
        assert summary["failed_breakers"] == 0
        assert summary["overall_health"] == "healthy"


class TestCircuitBreakerStatistics:
    """Test circuit breaker statistics tracking"""

    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Circuit breaker tracks comprehensive statistics"""
        breaker = CircuitBreaker(
            name="stats_test",
            failure_threshold=10  # High to not open
        )

        async def success():
            return "ok"

        async def failure():
            raise Exception("fail")

        # Make some calls
        for _ in range(5):
            await breaker.call(success)

        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failure)

        state = breaker.get_state()

        assert state["stats"]["total_requests"] == 8
        assert state["stats"]["success_rate"] == 5 / 8
        assert state["name"] == "stats_test"
        assert "uptime_seconds" in state["stats"]

    @pytest.mark.asyncio
    async def test_state_transitions_counted(self):
        """State transitions are counted"""
        breaker = CircuitBreaker(
            name="transition_test",
            failure_threshold=1,
            reset_timeout=0.1,
            success_threshold=1
        )

        async def fail():
            raise Exception("fail")

        async def success():
            return "ok"

        # Open circuit
        with pytest.raises(Exception):
            await breaker.call(fail)

        # Wait and close
        await asyncio.sleep(0.15)
        await breaker.call(success)

        state = breaker.get_state()
        assert state["stats"]["state_transitions"] >= 2  # CLOSED->OPEN->HALF_OPEN->CLOSED


class TestCircuitBreakerReset:
    """Test manual circuit breaker reset"""

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        """Circuit can be manually reset"""
        breaker = CircuitBreaker(
            name="reset_test",
            failure_threshold=1
        )

        async def fail():
            raise Exception("fail")

        # Open the circuit
        with pytest.raises(Exception):
            await breaker.call(fail)

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        await breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration"""

    def test_default_config(self):
        """Default configuration is reasonable"""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.reset_timeout == 60.0
        assert config.success_threshold == 3
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Custom configuration is applied"""
        breaker = CircuitBreaker(
            name="custom",
            failure_threshold=10,
            reset_timeout=120.0,
            success_threshold=5,
            timeout=60.0
        )

        assert breaker.config.failure_threshold == 10
        assert breaker.config.reset_timeout == 120.0
        assert breaker.config.success_threshold == 5
        assert breaker.config.timeout == 60.0
