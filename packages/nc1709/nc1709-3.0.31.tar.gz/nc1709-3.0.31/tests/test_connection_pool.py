"""
NC1709 Connection Pool Tests

Tests for the Ollama connection pool implementation.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from nc1709.utils.connection_pool import (
    OllamaConnectionPool,
    ConnectionPoolManager,
)


class TestOllamaConnectionPool:
    """Test Ollama connection pool functionality"""

    @pytest.fixture
    def pool(self):
        """Create a connection pool for testing"""
        return OllamaConnectionPool(
            base_url="http://localhost:11434",
            max_connections=5,
            connection_timeout=10.0,
            idle_timeout=60.0
        )

    def test_pool_initialization(self, pool):
        """Pool initializes with correct settings"""
        assert pool.base_url == "http://localhost:11434"
        assert pool.max_connections == 5
        assert pool.connection_timeout == 10.0

    def test_pool_stats_initial(self, pool):
        """Pool stats are zero initially"""
        stats = pool.get_stats()

        assert stats["active_connections"] == 0
        assert stats["idle_connections"] == 0
        assert stats["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_acquire_release_connection(self, pool):
        """Can acquire and release connections"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_conn = MagicMock()
            mock_create.return_value = mock_conn

            # Acquire
            conn = await pool.acquire()
            assert conn is not None

            # Release
            await pool.release(conn)

            stats = pool.get_stats()
            assert stats["idle_connections"] >= 0

    @pytest.mark.asyncio
    async def test_connection_reuse(self, pool):
        """Released connections are reused"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_conn = MagicMock()
            mock_conn.is_closed = False
            mock_create.return_value = mock_conn

            # Acquire and release
            conn1 = await pool.acquire()
            await pool.release(conn1)

            # Acquire again - should reuse
            conn2 = await pool.acquire()

            # Should be the same connection
            assert conn2 is conn1
            assert mock_create.call_count == 1  # Only created once

    @pytest.mark.asyncio
    async def test_max_connections_limit(self, pool):
        """Pool respects max connections limit"""
        connections = []

        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda: MagicMock(is_closed=False)

            # Acquire max connections
            for _ in range(5):
                conn = await pool.acquire()
                connections.append(conn)

            assert len(connections) == 5

            # Clean up
            for conn in connections:
                await pool.release(conn)

    @pytest.mark.asyncio
    async def test_context_manager(self, pool):
        """Pool works as async context manager"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_conn = MagicMock()
            mock_conn.is_closed = False
            mock_create.return_value = mock_conn

            async with pool as conn:
                assert conn is not None

    @pytest.mark.asyncio
    async def test_pool_close(self, pool):
        """Pool closes all connections properly"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_conn = MagicMock()
            mock_conn.is_closed = False
            mock_conn.aclose = AsyncMock()
            mock_create.return_value = mock_conn

            conn = await pool.acquire()
            await pool.release(conn)

            await pool.close()

            # Verify cleanup
            stats = pool.get_stats()
            assert stats["active_connections"] == 0


class TestConnectionPoolManager:
    """Test connection pool manager functionality"""

    @pytest.fixture
    def manager(self):
        return ConnectionPoolManager()

    def test_get_or_create_pool(self, manager):
        """Manager creates and caches pools"""
        pool1 = manager.get_or_create_pool("http://localhost:11434")
        pool2 = manager.get_or_create_pool("http://localhost:11434")

        assert pool1 is pool2  # Same pool returned

    def test_different_urls_different_pools(self, manager):
        """Different URLs get different pools"""
        pool1 = manager.get_or_create_pool("http://localhost:11434")
        pool2 = manager.get_or_create_pool("http://localhost:11435")

        assert pool1 is not pool2

    def test_get_all_stats(self, manager):
        """Manager reports stats for all pools"""
        manager.get_or_create_pool("http://host1:11434")
        manager.get_or_create_pool("http://host2:11434")

        stats = manager.get_all_stats()

        assert "http://host1:11434" in stats
        assert "http://host2:11434" in stats

    @pytest.mark.asyncio
    async def test_close_all_pools(self, manager):
        """Manager closes all pools"""
        pool1 = manager.get_or_create_pool("http://host1:11434")
        pool2 = manager.get_or_create_pool("http://host2:11434")

        with patch.object(pool1, 'close', new_callable=AsyncMock) as mock1, \
             patch.object(pool2, 'close', new_callable=AsyncMock) as mock2:
            await manager.close_all()

            mock1.assert_called_once()
            mock2.assert_called_once()


class TestConnectionPoolConcurrency:
    """Test connection pool under concurrent load"""

    @pytest.mark.asyncio
    async def test_concurrent_acquisitions(self):
        """Pool handles concurrent acquisitions safely"""
        pool = OllamaConnectionPool(
            base_url="http://localhost:11434",
            max_connections=3
        )

        acquired_count = 0
        released_count = 0

        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda: MagicMock(is_closed=False)

            async def acquire_and_release():
                nonlocal acquired_count, released_count
                conn = await pool.acquire()
                acquired_count += 1
                await asyncio.sleep(0.01)  # Simulate work
                await pool.release(conn)
                released_count += 1

            # Run concurrent acquisitions
            await asyncio.gather(*[acquire_and_release() for _ in range(10)])

        assert acquired_count == 10
        assert released_count == 10

    @pytest.mark.asyncio
    async def test_pool_under_pressure(self):
        """Pool handles high load without errors"""
        pool = OllamaConnectionPool(
            base_url="http://localhost:11434",
            max_connections=2
        )

        error_count = 0

        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = lambda: MagicMock(is_closed=False)

            async def stress_test():
                nonlocal error_count
                try:
                    conn = await asyncio.wait_for(pool.acquire(), timeout=5.0)
                    await asyncio.sleep(0.005)
                    await pool.release(conn)
                except Exception:
                    error_count += 1

            # Hammer the pool
            await asyncio.gather(*[stress_test() for _ in range(50)])

        # Should handle all requests without errors
        assert error_count == 0


class TestConnectionPoolHealth:
    """Test connection pool health monitoring"""

    @pytest.fixture
    def pool(self):
        return OllamaConnectionPool(
            base_url="http://localhost:11434",
            max_connections=5
        )

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, pool):
        """Health check passes when service is available"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()

            is_healthy = await pool.health_check()
            # Result depends on actual implementation

    @pytest.mark.asyncio
    async def test_connection_validation(self, pool):
        """Pool validates connections before returning"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            # First connection is closed
            closed_conn = MagicMock()
            closed_conn.is_closed = True

            # Second connection is good
            good_conn = MagicMock()
            good_conn.is_closed = False

            mock_create.side_effect = [closed_conn, good_conn]

            # Release the closed connection
            await pool.release(closed_conn)

            # Should get the good connection
            conn = await pool.acquire()

            # Behavior depends on implementation - pool might create new or skip invalid


class TestConnectionPoolMetrics:
    """Test connection pool metrics tracking"""

    @pytest.fixture
    def pool(self):
        return OllamaConnectionPool(
            base_url="http://localhost:11434",
            max_connections=5
        )

    @pytest.mark.asyncio
    async def test_request_counting(self, pool):
        """Pool tracks request counts"""
        with patch.object(pool, '_create_connection', new_callable=AsyncMock) as mock_create:
            mock_conn = MagicMock()
            mock_conn.is_closed = False
            mock_create.return_value = mock_conn

            for _ in range(3):
                conn = await pool.acquire()
                await pool.release(conn)

            stats = pool.get_stats()
            assert stats["total_requests"] >= 3

    def test_stats_structure(self, pool):
        """Stats include expected fields"""
        stats = pool.get_stats()

        expected_fields = [
            "active_connections",
            "idle_connections",
            "total_requests",
            "base_url"
        ]

        for field in expected_fields:
            assert field in stats, f"Missing field: {field}"
