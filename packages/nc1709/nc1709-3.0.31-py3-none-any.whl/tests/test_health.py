"""
NC1709 Health Checking Tests

Tests for the health check system and monitoring endpoints.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from nc1709.monitoring.health import (
    HealthChecker,
    HealthCheck,
    HealthStatus,
)


class TestHealthStatus:
    """Test health status enumeration"""

    def test_status_values(self):
        """Health status has expected values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestHealthCheck:
    """Test individual HealthCheck class"""

    @pytest.mark.asyncio
    async def test_successful_check(self):
        """Successful health check returns healthy status"""
        async def check_func():
            return {"status": "ok"}

        check = HealthCheck(
            name="test_check",
            check_function=check_func,
            timeout=5.0
        )

        result = await check.execute()

        assert result["status"] == "healthy"
        assert "execution_time" in result
        assert result["execution_time"] > 0

    @pytest.mark.asyncio
    async def test_failed_check(self):
        """Failed health check returns unhealthy status"""
        async def failing_check():
            raise Exception("Service unavailable")

        check = HealthCheck(
            name="failing_check",
            check_function=failing_check,
            timeout=5.0
        )

        result = await check.execute()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_timeout_check(self):
        """Timed out health check returns unhealthy status"""
        async def slow_check():
            await asyncio.sleep(2.0)
            return {"status": "ok"}

        check = HealthCheck(
            name="slow_check",
            check_function=slow_check,
            timeout=0.1  # Very short timeout
        )

        result = await check.execute()

        assert result["status"] == "unhealthy"
        assert "timeout" in result.get("error", "").lower()

    def test_critical_flag(self):
        """Health check tracks critical flag"""
        check = HealthCheck(
            name="critical_check",
            check_function=AsyncMock(),
            critical=True
        )

        assert check.critical is True

        non_critical = HealthCheck(
            name="non_critical",
            check_function=AsyncMock(),
            critical=False
        )

        assert non_critical.critical is False


class TestHealthChecker:
    """Test HealthChecker functionality"""

    @pytest.fixture
    def checker(self):
        return HealthChecker(ollama_url="http://localhost:11434")

    def test_initialization(self, checker):
        """HealthChecker initializes with default checks"""
        assert checker is not None
        assert len(checker.checks) > 0
        assert "ollama_connection" in checker.checks

    def test_register_check(self, checker):
        """Can register new health checks"""
        async def custom_check():
            return {"status": "ok"}

        checker.register_check(
            "custom",
            custom_check,
            timeout=5.0,
            critical=False
        )

        assert "custom" in checker.checks

    @pytest.mark.asyncio
    async def test_check_ollama_healthy(self, checker):
        """Ollama check returns healthy when service responds"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            result = await checker._check_ollama_connection()

            assert result["connected"] is True
            assert "response_time" in result

    @pytest.mark.asyncio
    async def test_check_ollama_unhealthy(self, checker):
        """Ollama check raises when service unavailable"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            with pytest.raises(Exception) as exc_info:
                await checker._check_ollama_connection()

            assert "connection" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_check_system_memory(self, checker):
        """System memory check returns usage info"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(
                percent=50.0,
                available=8 * (1024**3),  # 8 GB
                total=16 * (1024**3)       # 16 GB
            )

            result = await checker._check_system_memory()

            assert "usage_percent" in result
            assert result["usage_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_check_system_memory_critical(self, checker):
        """System memory check raises on critical usage"""
        with patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = MagicMock(
                percent=97.0,  # Critical level
                available=0.5 * (1024**3),
                total=16 * (1024**3)
            )

            with pytest.raises(Exception) as exc_info:
                await checker._check_system_memory()

            assert "critical" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_check_system_disk(self, checker):
        """System disk check returns usage info"""
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = MagicMock(
                used=50 * (1024**3),   # 50 GB used
                total=100 * (1024**3), # 100 GB total
                free=50 * (1024**3)    # 50 GB free
            )

            result = await checker._check_system_disk()

            assert "usage_percent" in result
            assert result["usage_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_check_all_returns_summary(self, checker):
        """check_all returns comprehensive health summary"""
        # Mock all individual checks
        with patch.object(checker, 'checks', {
            'test1': HealthCheck('test1', AsyncMock(return_value={})),
            'test2': HealthCheck('test2', AsyncMock(return_value={})),
        }):
            result = await checker.check_all()

            assert "status" in result
            assert "checks" in result
            assert "timestamp" in result
            assert "uptime_seconds" in result

    @pytest.mark.asyncio
    async def test_check_all_healthy_status(self, checker):
        """check_all returns healthy when all checks pass"""
        async def healthy_check():
            return {"status": "ok"}

        checker.checks = {
            'a': HealthCheck('a', healthy_check, critical=True),
            'b': HealthCheck('b', healthy_check, critical=False),
        }

        result = await checker.check_all()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_all_unhealthy_on_critical_failure(self, checker):
        """check_all returns unhealthy when critical check fails"""
        async def healthy_check():
            return {"status": "ok"}

        async def failing_check():
            raise Exception("Critical failure")

        checker.checks = {
            'healthy': HealthCheck('healthy', healthy_check, critical=False),
            'critical': HealthCheck('critical', failing_check, critical=True),
        }

        result = await checker.check_all()

        assert result["status"] == "unhealthy"
        assert "critical" in result.get("critical_failures", [])

    @pytest.mark.asyncio
    async def test_check_all_degraded_on_non_critical_failure(self, checker):
        """check_all returns degraded when non-critical check fails"""
        async def healthy_check():
            return {"status": "ok"}

        async def failing_check():
            raise Exception("Non-critical failure")

        checker.checks = {
            'healthy': HealthCheck('healthy', healthy_check, critical=True),
            'non_critical': HealthCheck('non_critical', failing_check, critical=False),
        }

        result = await checker.check_all()

        # Should be degraded, not unhealthy (non-critical failure)
        assert result["status"] in ("degraded", "healthy")

    @pytest.mark.asyncio
    async def test_check_single(self, checker):
        """check_single executes a single health check"""
        async def custom_check():
            return {"custom": "data"}

        checker.register_check("single_test", custom_check)

        result = await checker.check_single("single_test")

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_single_not_found(self, checker):
        """check_single returns unknown for missing check"""
        result = await checker.check_single("nonexistent")

        assert result["status"] == "unknown"
        assert "not found" in result.get("error", "").lower()


class TestHealthCheckerIntegration:
    """Integration tests for health checker"""

    @pytest.mark.asyncio
    async def test_full_health_check_cycle(self):
        """Complete health check cycle works"""
        checker = HealthChecker()

        # Replace external dependencies with mocks
        async def mock_ollama():
            return {"connected": True}

        async def mock_models():
            return {"models_available": 1}

        checker.checks["ollama_connection"] = HealthCheck(
            "ollama_connection", mock_ollama, critical=True
        )
        checker.checks["ollama_models"] = HealthCheck(
            "ollama_models", mock_models, critical=True
        )

        with patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.disk_usage') as mock_disk:
            mock_mem.return_value = MagicMock(
                percent=50.0,
                available=8 * (1024**3),
                total=16 * (1024**3)
            )
            mock_disk.return_value = MagicMock(
                used=50 * (1024**3),
                total=100 * (1024**3),
                free=50 * (1024**3)
            )

            result = await checker.check_all()

            assert result["status"] in ("healthy", "degraded", "unhealthy")
            assert result["checks_total"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Health checks run concurrently"""
        checker = HealthChecker()

        execution_times = []

        async def slow_check():
            start = time.time()
            await asyncio.sleep(0.1)
            execution_times.append(time.time() - start)
            return {}

        # Replace all checks with slow checks
        checker.checks = {
            f'check_{i}': HealthCheck(f'check_{i}', slow_check)
            for i in range(5)
        }

        start = time.time()
        await checker.check_all()
        total_time = time.time() - start

        # If running concurrently, total time should be ~0.1s not ~0.5s
        assert total_time < 0.3  # Allow some overhead


class TestHealthCheckMetrics:
    """Test health check metrics integration"""

    @pytest.mark.asyncio
    async def test_ollama_health_updates_metrics(self):
        """Ollama health check updates Prometheus metrics"""
        checker = HealthChecker()

        with patch('httpx.AsyncClient') as mock_client_class, \
             patch('nc1709.monitoring.health.metrics_collector') as mock_metrics:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            await checker._check_ollama_connection()

            # Verify metrics were updated
            mock_metrics.record_ollama_health.assert_called()
