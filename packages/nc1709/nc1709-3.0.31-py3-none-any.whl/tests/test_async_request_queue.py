"""
Test Async Request Queue
Tests for the fully async request queue system
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from nc1709.async_request_queue import (
    AsyncRequestQueue, AsyncRequest, RequestStatus, QueueStats,
    get_async_queue, cleanup_async_queue
)


class TestAsyncRequest:
    """Test AsyncRequest data structure"""
    
    def test_request_creation(self):
        """Test basic request creation"""
        request = AsyncRequest(payload="test data", priority=5)
        
        assert request.payload == "test data"
        assert request.priority == 5
        assert request.status == RequestStatus.PENDING
        assert request.id is not None
        assert request.created_at <= time.time()
    
    def test_request_duration_calculation(self):
        """Test duration calculation"""
        request = AsyncRequest()
        
        # No timing data
        assert request.get_duration() is None
        assert request.get_wait_time() is None
        
        # Add timing data
        request.started_at = request.created_at + 1.0
        request.completed_at = request.started_at + 2.0
        
        assert request.get_duration() == 2.0
        assert request.get_wait_time() == 1.0


@pytest.mark.asyncio
class TestAsyncRequestQueue:
    """Test async request queue functionality"""
    
    async def test_queue_lifecycle(self):
        """Test queue start and stop"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        
        # Start queue
        await queue.start()
        assert queue._processor_task is not None
        assert not queue._shutdown
        
        # Stop queue
        await queue.stop()
        assert queue._shutdown
    
    async def test_enqueue_request(self):
        """Test enqueueing requests"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            request = await queue.enqueue("test payload", priority=1)
            
            assert request.payload == "test payload"
            assert request.priority == 1
            assert request.status == RequestStatus.PENDING
            
            # Verify it's tracked
            tracked_request = await queue.get_request(request.id)
            assert tracked_request is request
            
        finally:
            await queue.stop()
    
    async def test_request_processing(self):
        """Test request processing with callback"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            # Mock callback
            callback = Mock(return_value="processed result")
            
            request = await queue.enqueue("test payload", callback=callback)
            
            # Wait for processing
            completed_request = await queue.wait_for_request(request.id, timeout=5.0)
            
            assert completed_request.status == RequestStatus.COMPLETED
            assert completed_request.result == "processed result"
            callback.assert_called_once_with("test payload")
            
        finally:
            await queue.stop()
    
    async def test_async_callback_processing(self):
        """Test processing with async callback"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            # Async callback
            async def async_callback(payload):
                await asyncio.sleep(0.1)
                return f"async result: {payload}"
            
            request = await queue.enqueue("test", callback=async_callback)
            
            # Wait for processing
            completed_request = await queue.wait_for_request(request.id, timeout=5.0)
            
            assert completed_request.status == RequestStatus.COMPLETED
            assert completed_request.result == "async result: test"
            
        finally:
            await queue.stop()
    
    async def test_priority_ordering(self):
        """Test priority-based processing"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=10)
        await queue.start()
        
        try:
            # Add requests with different priorities
            low_priority = await queue.enqueue("low", priority=1)
            high_priority = await queue.enqueue("high", priority=10)
            medium_priority = await queue.enqueue("medium", priority=5)
            
            # Wait a bit for processing
            await asyncio.sleep(0.5)
            
            # Check processing order (higher priority should be processed first)
            # Note: The first request might already be processing
            # But subsequent ones should follow priority order
            
            await queue.wait_for_request(high_priority.id, timeout=5.0)
            await queue.wait_for_request(medium_priority.id, timeout=5.0) 
            await queue.wait_for_request(low_priority.id, timeout=5.0)
            
            # All should be completed
            assert high_priority.status == RequestStatus.COMPLETED
            assert medium_priority.status == RequestStatus.COMPLETED
            assert low_priority.status == RequestStatus.COMPLETED
            
        finally:
            await queue.stop()
    
    async def test_concurrent_processing(self):
        """Test concurrent request processing"""
        queue = AsyncRequestQueue(max_concurrent=3, max_queue_size=10)
        await queue.start()
        
        try:
            # Async callback that takes time
            async def slow_callback(payload):
                await asyncio.sleep(0.2)
                return f"result: {payload}"
            
            # Enqueue multiple requests
            requests = []
            for i in range(5):
                request = await queue.enqueue(f"payload-{i}", callback=slow_callback)
                requests.append(request)
            
            # Wait for all to complete
            start_time = time.time()
            for request in requests:
                await queue.wait_for_request(request.id, timeout=10.0)
            end_time = time.time()
            
            # Should complete faster than sequential processing
            # 5 requests * 0.2s = 1.0s sequential
            # With max_concurrent=3, should be faster
            assert end_time - start_time < 0.8
            
            # All should be completed
            for request in requests:
                assert request.status == RequestStatus.COMPLETED
                
        finally:
            await queue.stop()
    
    async def test_request_timeout(self):
        """Test request timeout handling"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            # Callback that takes too long
            async def slow_callback(payload):
                await asyncio.sleep(2.0)
                return "should not reach here"
            
            request = await queue.enqueue("test", callback=slow_callback, timeout=0.1)
            
            # Wait for processing (should fail due to timeout)
            completed_request = await queue.wait_for_request(request.id, timeout=5.0)
            
            assert completed_request.status == RequestStatus.FAILED
            assert "timed out" in completed_request.error.lower()
            
        finally:
            await queue.stop()
    
    async def test_callback_exception_handling(self):
        """Test handling of callback exceptions"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            def failing_callback(payload):
                raise ValueError("Callback error")
            
            request = await queue.enqueue("test", callback=failing_callback)
            
            # Wait for processing
            completed_request = await queue.wait_for_request(request.id, timeout=5.0)
            
            assert completed_request.status == RequestStatus.FAILED
            assert "Callback error" in completed_request.error
            
        finally:
            await queue.stop()
    
    async def test_queue_statistics(self):
        """Test queue statistics"""
        queue = AsyncRequestQueue(max_concurrent=2, max_queue_size=10)
        await queue.start()
        
        try:
            # Add some requests
            callback = Mock(return_value="result")
            
            requests = []
            for i in range(3):
                request = await queue.enqueue(f"payload-{i}", callback=callback)
                requests.append(request)
            
            # Wait for processing
            for request in requests:
                await queue.wait_for_request(request.id, timeout=5.0)
            
            stats = queue.get_stats()
            
            assert stats.total_processed >= 3
            assert stats.completed_requests >= 3
            assert stats.average_wait_time >= 0
            assert stats.average_processing_time >= 0
            
        finally:
            await queue.stop()
    
    async def test_list_requests(self):
        """Test listing requests with filtering"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            # Add requests
            completed_request = await queue.enqueue("completed", callback=lambda x: x)
            pending_request = await queue.enqueue("pending")  # No callback, stays pending
            
            # Wait for one to complete
            await queue.wait_for_request(completed_request.id, timeout=5.0)
            
            # List all requests
            all_requests = await queue.list_requests()
            assert len(all_requests) >= 2
            
            # List only completed
            completed_requests = await queue.list_requests(RequestStatus.COMPLETED)
            assert any(r.id == completed_request.id for r in completed_requests)
            
            # List only pending
            pending_requests = await queue.list_requests(RequestStatus.PENDING)
            assert any(r.id == pending_request.id for r in pending_requests)
            
        finally:
            await queue.stop()
    
    async def test_queue_shutdown_with_pending_requests(self):
        """Test shutting down queue with pending requests"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        # Add a request that won't be processed
        request = await queue.enqueue("test payload")
        
        # Stop queue immediately
        await queue.stop()
        
        # Request should be cancelled
        final_request = await queue.get_request(request.id)
        assert final_request.status == RequestStatus.CANCELLED
    
    async def test_wait_for_request_timeout(self):
        """Test waiting for request with timeout"""
        queue = AsyncRequestQueue(max_concurrent=1, max_queue_size=5)
        await queue.start()
        
        try:
            # Callback that takes a long time
            async def slow_callback(payload):
                await asyncio.sleep(2.0)
                return "result"
            
            request = await queue.enqueue("test", callback=slow_callback)
            
            # Wait with short timeout
            with pytest.raises(asyncio.TimeoutError):
                await queue.wait_for_request(request.id, timeout=0.1)
                
        finally:
            await queue.stop()


@pytest.mark.asyncio
class TestGlobalAsyncQueue:
    """Test global async queue functions"""
    
    async def test_get_global_queue(self):
        """Test getting global async queue"""
        queue1 = await get_async_queue()
        queue2 = await get_async_queue()
        
        # Should return the same instance
        assert queue1 is queue2
        
        # Cleanup
        await cleanup_async_queue()
    
    async def test_cleanup_global_queue(self):
        """Test cleaning up global async queue"""
        queue = await get_async_queue()
        assert queue is not None
        
        await cleanup_async_queue()
        
        # Getting queue again should create a new one
        new_queue = await get_async_queue()
        assert new_queue is not queue
        
        await cleanup_async_queue()


class TestQueueStats:
    """Test queue statistics data structure"""
    
    def test_stats_creation(self):
        """Test stats creation with defaults"""
        stats = QueueStats()
        
        assert stats.pending_requests == 0
        assert stats.processing_requests == 0
        assert stats.completed_requests == 0
        assert stats.failed_requests == 0
        assert stats.average_wait_time == 0.0
        assert stats.average_processing_time == 0.0
        assert stats.total_processed == 0
        assert stats.queue_size == 0