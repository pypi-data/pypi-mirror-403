"""
Async Request Queue
Fully async implementation of the request queue system
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Request status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=False)
class AsyncRequest:
    """Async request container"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Any = None
    callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: RequestStatus = RequestStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    priority: int = 0
    timeout: float = 300.0

    def __lt__(self, other: 'AsyncRequest') -> bool:
        """
        Compare requests for priority queue ordering.
        Lower priority value = higher priority (processed first).
        For equal priorities, earlier created_at wins.
        """
        if not isinstance(other, AsyncRequest):
            return NotImplemented
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    def __le__(self, other: 'AsyncRequest') -> bool:
        """Less than or equal comparison for priority queue."""
        if not isinstance(other, AsyncRequest):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: 'AsyncRequest') -> bool:
        """Greater than comparison for priority queue."""
        if not isinstance(other, AsyncRequest):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: 'AsyncRequest') -> bool:
        """Greater than or equal comparison for priority queue."""
        if not isinstance(other, AsyncRequest):
            return NotImplemented
        return not self < other

    def get_duration(self) -> Optional[float]:
        """Get request processing duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def get_wait_time(self) -> Optional[float]:
        """Get time spent waiting in queue"""
        if self.started_at:
            return self.started_at - self.created_at
        return None


@dataclass
class QueueStats:
    """Queue statistics"""
    pending_requests: int = 0
    processing_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    total_processed: int = 0
    queue_size: int = 0


class AsyncRequestQueue:
    """Fully async request queue implementation"""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 1000,
        default_timeout: float = 300.0,
        max_retries: int = 3
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        
        # Queue and tracking
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._requests: Dict[str, AsyncRequest] = {}
        self._processing: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self._stats = QueueStats()
        self._wait_times: List[float] = []
        self._processing_times: List[float] = []
        
        # Control
        self._processor_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self) -> None:
        """Start the async queue processor"""
        if self._processor_task and not self._processor_task.done():
            return
        
        self._shutdown = False
        self._processor_task = asyncio.create_task(self._processor_loop())
        logger.info("Async request queue started")
    
    async def stop(self) -> None:
        """Stop the queue processor gracefully"""
        logger.info("Stopping async request queue...")
        self._shutdown = True
        
        # Cancel processor task
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all processing tasks
        for task in list(self._processing.values()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Mark remaining requests as cancelled
        while not self._queue.empty():
            try:
                _, request = self._queue.get_nowait()
                request.status = RequestStatus.CANCELLED
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        logger.info("Async request queue stopped")
    
    async def enqueue(
        self,
        payload: Any,
        callback: Optional[Callable] = None,
        priority: int = 0,
        timeout: Optional[float] = None,
        request_id: Optional[str] = None
    ) -> AsyncRequest:
        """Enqueue a request for async processing"""
        if self._shutdown:
            raise RuntimeError("Queue is shutting down")
        
        request = AsyncRequest(
            id=request_id or str(uuid.uuid4()),
            payload=payload,
            callback=callback,
            priority=priority,
            timeout=timeout or self.default_timeout
        )
        
        # Use negative priority for max-heap behavior (higher priority = lower number)
        await self._queue.put((-priority, request))
        self._requests[request.id] = request
        
        logger.debug(f"Enqueued request {request.id} with priority {priority}")
        return request
    
    async def wait_for_request(self, request_id: str, timeout: Optional[float] = None) -> AsyncRequest:
        """Wait for a specific request to complete"""
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        start_time = time.time()
        poll_timeout = timeout or request.timeout
        
        while request.status in [RequestStatus.PENDING, RequestStatus.PROCESSING]:
            if timeout and (time.time() - start_time) > poll_timeout:
                raise asyncio.TimeoutError(f"Request {request_id} timed out")
            
            await asyncio.sleep(0.1)
        
        return request
    
    async def get_request(self, request_id: str) -> Optional[AsyncRequest]:
        """Get request by ID"""
        return self._requests.get(request_id)
    
    async def _processor_loop(self) -> None:
        """Main async processing loop"""
        logger.info("Starting async processor loop")
        
        while not self._shutdown:
            try:
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
                # Process new requests if we have capacity
                if len(self._processing) < self.max_concurrent:
                    await self._try_start_new_request()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                logger.info("Processor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in processor loop: {e}")
                await asyncio.sleep(1.0)  # Back off on error
        
        logger.info("Async processor loop ended")
    
    async def _cleanup_completed_tasks(self) -> None:
        """Clean up completed processing tasks"""
        completed_ids = []
        
        for request_id, task in self._processing.items():
            if task.done():
                completed_ids.append(request_id)
        
        for request_id in completed_ids:
            task = self._processing.pop(request_id)
            request = self._requests[request_id]
            
            try:
                result = await task
                request.result = result
                request.status = RequestStatus.COMPLETED
                request.completed_at = time.time()
                
                # Update statistics
                self._update_stats(request)
                
                logger.debug(f"Request {request_id} completed successfully")
                
            except asyncio.CancelledError:
                request.status = RequestStatus.CANCELLED
                logger.debug(f"Request {request_id} was cancelled")
                
            except Exception as e:
                request.status = RequestStatus.FAILED
                request.error = str(e)
                request.completed_at = time.time()
                
                # Update statistics
                self._update_stats(request)
                
                logger.error(f"Request {request_id} failed: {e}")
    
    async def _try_start_new_request(self) -> bool:
        """Try to start a new request if queue has items"""
        try:
            priority, request = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            
            # Check if request is still valid
            if request.status != RequestStatus.PENDING:
                self._queue.task_done()
                return False
            
            # Start processing
            request.status = RequestStatus.PROCESSING
            request.started_at = time.time()
            
            # Create processing task
            task = asyncio.create_task(self._process_request(request))
            self._processing[request.id] = task
            
            self._queue.task_done()
            logger.debug(f"Started processing request {request.id}")
            return True
            
        except asyncio.TimeoutError:
            # No requests available
            return False
        except Exception as e:
            logger.error(f"Error starting new request: {e}")
            return False
    
    async def _process_request(self, request: AsyncRequest) -> Any:
        """Process a single request"""
        try:
            if request.callback:
                if asyncio.iscoroutinefunction(request.callback):
                    # Async callback
                    result = await asyncio.wait_for(
                        request.callback(request.payload),
                        timeout=request.timeout
                    )
                else:
                    # Sync callback - run in executor
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, request.callback, request.payload
                        ),
                        timeout=request.timeout
                    )
                return result
            else:
                # No callback, just return payload
                return request.payload
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request {request.id} timed out after {request.timeout}s")
        except Exception as e:
            logger.error(f"Request {request.id} processing failed: {e}")
            raise
    
    def _update_stats(self, request: AsyncRequest) -> None:
        """Update queue statistics"""
        # Update counters
        if request.status == RequestStatus.COMPLETED:
            self._stats.completed_requests += 1
        elif request.status == RequestStatus.FAILED:
            self._stats.failed_requests += 1
        
        self._stats.total_processed += 1
        
        # Update timing statistics
        wait_time = request.get_wait_time()
        if wait_time is not None:
            self._wait_times.append(wait_time)
            if len(self._wait_times) > 100:  # Keep last 100
                self._wait_times = self._wait_times[-100:]
            self._stats.average_wait_time = sum(self._wait_times) / len(self._wait_times)
        
        processing_time = request.get_duration()
        if processing_time is not None:
            self._processing_times.append(processing_time)
            if len(self._processing_times) > 100:  # Keep last 100
                self._processing_times = self._processing_times[-100:]
            self._stats.average_processing_time = sum(self._processing_times) / len(self._processing_times)
    
    def get_stats(self) -> QueueStats:
        """Get current queue statistics"""
        # Update current counts
        self._stats.pending_requests = self._queue.qsize()
        self._stats.processing_requests = len(self._processing)
        self._stats.queue_size = len(self._requests)
        
        return self._stats
    
    async def list_requests(
        self,
        status_filter: Optional[RequestStatus] = None,
        limit: int = 100
    ) -> List[AsyncRequest]:
        """List requests with optional filtering"""
        requests = list(self._requests.values())
        
        if status_filter:
            requests = [r for r in requests if r.status == status_filter]
        
        # Sort by created_at descending
        requests.sort(key=lambda x: x.created_at, reverse=True)
        
        return requests[:limit]
    
    async def stream_status_updates(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream queue status updates"""
        last_stats = None
        
        while not self._shutdown:
            current_stats = self.get_stats()
            
            # Only yield if stats changed
            if current_stats != last_stats:
                yield {
                    "timestamp": time.time(),
                    "stats": current_stats,
                    "active_requests": len(self._processing)
                }
                last_stats = current_stats
            
            await asyncio.sleep(1.0)


# Global async queue instance
_global_async_queue: Optional[AsyncRequestQueue] = None


async def get_async_queue() -> AsyncRequestQueue:
    """Get or create global async queue"""
    global _global_async_queue
    
    if _global_async_queue is None:
        _global_async_queue = AsyncRequestQueue()
        await _global_async_queue.start()
    
    return _global_async_queue


async def cleanup_async_queue() -> None:
    """Cleanup global async queue"""
    global _global_async_queue
    
    if _global_async_queue:
        await _global_async_queue.stop()
        _global_async_queue = None