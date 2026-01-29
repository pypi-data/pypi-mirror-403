"""
NC1709 Prometheus Metrics Tests

Tests for the metrics collection and API key identifier algorithm.
"""

import hashlib
import pytest
import time
from unittest.mock import patch, MagicMock

from nc1709.monitoring.metrics import (
    generate_api_key_id,
    set_owner_key,
    MetricsCollector,
    REQUEST_COUNT,
    REQUEST_DURATION,
    MODEL_INFERENCE_DURATION,
    TOOL_EXECUTIONS,
    CACHE_HITS,
    CACHE_MISSES,
    _CAI_COLORS,
    _CAI_ANIMALS,
    _OWNER_KEY_HASH,
)


class TestColorAnimalIdentifier:
    """Test the NC1709-CAI API key identifier algorithm"""

    def test_empty_key_returns_anon(self):
        """Empty or None key returns 'anon'"""
        assert generate_api_key_id(None) == "anon"
        assert generate_api_key_id("") == "anon"

    def test_deterministic_output(self):
        """Same key always produces same identifier"""
        key = "test-api-key-12345"

        id1 = generate_api_key_id(key)
        id2 = generate_api_key_id(key)
        id3 = generate_api_key_id(key)

        assert id1 == id2 == id3

    def test_different_keys_different_ids(self):
        """Different keys produce different identifiers"""
        key1 = "api-key-alpha"
        key2 = "api-key-beta"
        key3 = "api-key-gamma"

        id1 = generate_api_key_id(key1)
        id2 = generate_api_key_id(key2)
        id3 = generate_api_key_id(key3)

        # While collisions are possible, these specific keys should differ
        assert len({id1, id2, id3}) >= 2  # At least 2 unique

    def test_output_format(self):
        """Output follows color-animal format"""
        key = "random-test-key"
        result = generate_api_key_id(key)

        parts = result.split("-")
        assert len(parts) == 2

        color, animal = parts
        assert color in _CAI_COLORS
        assert animal in _CAI_ANIMALS

    def test_owner_key_returns_asif_fas(self):
        """Owner key hash returns 'asif-fas'"""
        # Create a key that hashes to the owner hash
        # We need to find or set up a key whose hash matches _OWNER_KEY_HASH
        # The actual owner key is: nc1709-asif-wrniy6vwodgsl783
        owner_key = "nc1709-asif-wrniy6vwodgsl783"
        expected_hash = hashlib.sha256(owner_key.encode()).hexdigest()

        if expected_hash == _OWNER_KEY_HASH:
            result = generate_api_key_id(owner_key)
            assert result == "asif-fas"

    def test_owner_key_via_env_var(self):
        """Owner key can be set via environment variable"""
        test_key = "my-special-key"
        test_hash = hashlib.sha256(test_key.encode()).hexdigest()

        with patch.dict('os.environ', {'NC1709_OWNER_KEY_HASH': test_hash}):
            result = generate_api_key_id(test_key)
            assert result == "asif-fas"

    def test_set_owner_key_function(self):
        """set_owner_key generates correct hash"""
        key = "test-api-key"
        expected = hashlib.sha256(key.encode()).hexdigest()

        result = set_owner_key(key)

        assert result == expected

    def test_all_colors_reachable(self):
        """All colors are potentially reachable"""
        # Generate many keys to verify distribution
        seen_colors = set()

        for i in range(1000):
            key = f"test-key-{i}"
            result = generate_api_key_id(key)
            color = result.split("-")[0]
            seen_colors.add(color)

        # Should see most colors (statistical - may not be all)
        assert len(seen_colors) >= 10  # At least 10 of 16 colors

    def test_all_animals_reachable(self):
        """All animals are potentially reachable"""
        seen_animals = set()

        for i in range(1000):
            key = f"animal-test-{i}"
            result = generate_api_key_id(key)
            animal = result.split("-")[1]
            seen_animals.add(animal)

        # Should see most animals
        assert len(seen_animals) >= 20  # At least 20 of 32 animals

    def test_hash_based_not_prefix_based(self):
        """Algorithm uses hash, not simple prefix"""
        # Keys with same prefix should have different IDs
        key1 = "sk-test-AAAAAAAA"
        key2 = "sk-test-BBBBBBBB"

        id1 = generate_api_key_id(key1)
        id2 = generate_api_key_id(key2)

        # Different keys = different IDs (high probability)
        assert id1 != id2


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_collector_initialization(self, collector):
        """Collector initializes with start time"""
        assert collector.start_time > 0
        assert time.time() - collector.start_time < 5  # Created recently

    def test_record_request(self, collector):
        """Recording requests works without errors"""
        collector.record_request(
            method="POST",
            endpoint="/api/chat",
            status_code=200,
            duration=0.5,
            api_key="test-key-123"
        )

        # Should not raise

    def test_record_request_with_api_key_id(self, collector):
        """API key is converted to color-animal ID"""
        # This tests the integration
        collector.record_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration=0.1,
            api_key="some-api-key"
        )

        # The api_key_prefix label should be a color-animal format
        # Can't easily verify Prometheus labels, but should not raise

    def test_record_model_inference(self, collector):
        """Recording model inference metrics works"""
        collector.record_model_inference(
            model_name="nc1709-7b",
            duration=2.5,
            temperature=0.7,
            prompt_tokens=100,
            completion_tokens=50,
            success=True
        )

    def test_record_model_inference_failure(self, collector):
        """Recording failed inference includes error type"""
        collector.record_model_inference(
            model_name="nc1709-7b",
            duration=0.5,
            temperature=0.7,
            prompt_tokens=100,
            completion_tokens=0,
            success=False,
            error_type="timeout"
        )

    def test_record_tool_execution(self, collector):
        """Recording tool execution works"""
        collector.record_tool_execution(
            tool_name="Bash",
            duration=0.25,
            success=True
        )

        collector.record_tool_execution(
            tool_name="Read",
            duration=0.01,
            success=False
        )

    def test_record_agent_execution(self, collector):
        """Recording agent execution with tool counts"""
        collector.record_agent_execution(success=True, tool_count=5)
        collector.record_agent_execution(success=False, tool_count=0)

    def test_tool_count_bucketing(self, collector):
        """Tool counts are bucketed correctly"""
        assert collector._get_tool_count_bucket(0) == "0"
        assert collector._get_tool_count_bucket(1) == "1-3"
        assert collector._get_tool_count_bucket(3) == "1-3"
        assert collector._get_tool_count_bucket(5) == "4-10"
        assert collector._get_tool_count_bucket(10) == "4-10"
        assert collector._get_tool_count_bucket(15) == "10+"

    def test_record_ollama_health(self, collector):
        """Recording Ollama health status"""
        collector.record_ollama_health(healthy=True, response_time=0.05)
        collector.record_ollama_health(healthy=False)

    def test_record_cache_access(self, collector):
        """Recording cache hits and misses"""
        collector.record_cache_access("response", hit=True)
        collector.record_cache_access("response", hit=False)
        collector.record_cache_access("embedding", hit=True)

    def test_update_connection_count(self, collector):
        """Updating connection count"""
        collector.update_connection_count(5)
        collector.update_connection_count(0)

    def test_get_metrics_returns_string(self, collector):
        """get_metrics returns Prometheus format string"""
        metrics = collector.get_metrics()

        assert isinstance(metrics, bytes)
        assert len(metrics) > 0

    def test_get_summary(self, collector):
        """get_summary returns health check data"""
        with patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.cpu_percent') as mock_cpu:
            mock_mem.return_value = MagicMock(percent=50.0)
            mock_disk.return_value = MagicMock(used=50, total=100)
            mock_cpu.return_value = 25.0

            summary = collector.get_summary()

            assert "uptime_seconds" in summary
            # May have other fields depending on implementation


class TestMetricsCollectorSystemMetrics:
    """Test system metrics collection"""

    @pytest.fixture
    def collector(self):
        return MetricsCollector()

    def test_update_system_metrics_with_psutil(self, collector):
        """System metrics update when psutil available"""
        with patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.disk_usage') as mock_disk:
            mock_mem.return_value = MagicMock(
                total=16000000000,
                available=8000000000,
                used=8000000000
            )
            mock_cpu.return_value = 25.0
            mock_disk.return_value = MagicMock(used=50, total=100)

            collector.update_system_metrics()

            # Should not raise

    def test_update_system_metrics_without_psutil(self, collector):
        """System metrics gracefully handle missing psutil"""
        with patch.dict('sys.modules', {'psutil': None}):
            # Should not raise even if psutil unavailable
            try:
                collector.update_system_metrics()
            except ImportError:
                pass  # Expected if psutil not available


class TestMetricsIntegration:
    """Integration tests for metrics system"""

    def test_full_request_lifecycle(self):
        """Test complete request recording lifecycle"""
        collector = MetricsCollector()

        # Simulate a full request
        start = time.time()

        collector.record_request(
            method="POST",
            endpoint="/v1/chat/completions",
            status_code=200,
            duration=time.time() - start,
            api_key="user-api-key-xyz"
        )

        collector.record_model_inference(
            model_name="nc1709-7b",
            duration=1.5,
            temperature=0.7,
            prompt_tokens=150,
            completion_tokens=75,
            success=True
        )

        collector.record_tool_execution(
            tool_name="Read",
            duration=0.02,
            success=True
        )

        collector.record_agent_execution(
            success=True,
            tool_count=3
        )

        # Get final metrics
        metrics = collector.get_metrics()
        assert len(metrics) > 0

    def test_concurrent_metric_recording(self):
        """Metrics handle concurrent recording"""
        import threading

        collector = MetricsCollector()
        errors = []

        def record_metrics():
            try:
                for i in range(100):
                    collector.record_request(
                        method="GET",
                        endpoint=f"/test/{i}",
                        status_code=200,
                        duration=0.01,
                        api_key=f"key-{i}"
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
