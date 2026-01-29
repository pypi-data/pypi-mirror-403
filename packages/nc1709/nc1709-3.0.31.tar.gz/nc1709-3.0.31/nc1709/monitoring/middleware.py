"""
NC1709 Enhanced Monitoring Middleware

FastAPI middleware for automatic metrics collection and request tracking.
"""

import time
import uuid
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import metrics_collector


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect metrics for all HTTP requests.
    
    Tracks:
    - Request count by endpoint, method, status code
    - Request duration 
    - Active connection count
    - API key usage patterns (anonymized)
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/metrics", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics collection for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Record request start
        start_time = time.time()
        
        # Update active connections (increment)
        current_connections = getattr(metrics_collector, '_active_connections', 0) + 1
        setattr(metrics_collector, '_active_connections', current_connections)
        metrics_collector.update_connection_count(current_connections)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record successful request metrics
            duration = time.time() - start_time
            api_key = self._extract_api_key(request)
            
            metrics_collector.record_request(
                method=request.method,
                endpoint=self._normalize_endpoint(request.url.path),
                status_code=response.status_code,
                duration=duration,
                api_key=api_key
            )
            
            # Add response headers for debugging
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            api_key = self._extract_api_key(request)
            
            metrics_collector.record_request(
                method=request.method,
                endpoint=self._normalize_endpoint(request.url.path),
                status_code=500,  # Internal server error
                duration=duration,
                api_key=api_key
            )
            
            # Re-raise the exception
            raise
        
        finally:
            # Update active connections (decrement)
            current_connections = max(0, getattr(metrics_collector, '_active_connections', 1) - 1)
            setattr(metrics_collector, '_active_connections', current_connections)
            metrics_collector.update_connection_count(current_connections)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers (anonymized)"""
        try:
            # Try Authorization header first
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header[7:]  # Remove "Bearer " prefix
            
            # Try X-API-Key header
            api_key = request.headers.get("x-api-key")
            if api_key:
                return api_key
            
            return None
        except Exception:
            return None
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics grouping"""
        # Replace dynamic IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        
        # Replace numeric IDs  
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace long alphanumeric strings (likely IDs)
        path = re.sub(r'/[a-zA-Z0-9]{16,}', '/{id}', path)
        
        return path


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Advanced request tracking middleware for debugging and monitoring.
    
    Provides:
    - Detailed request logging
    - Performance bottleneck detection  
    - User behavior analytics
    """
    
    def __init__(self, app, log_slow_requests: bool = True, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.log_slow_requests = log_slow_requests
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4())[:8])
        
        # Log request start (debug level)
        import logging
        logger = logging.getLogger("nc1709.requests")
        
        logger.debug(
            f"Request {request_id} started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log request completion
            log_level = logging.WARNING if duration > self.slow_request_threshold else logging.INFO
            
            logger.log(
                log_level,
                f"Request {request_id} completed: {response.status_code} in {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "slow_request": duration > self.slow_request_threshold
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Request {request_id} failed: {str(e)} after {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration
                },
                exc_info=True
            )
            
            raise


# Helper function to add to app
def add_monitoring_middleware(app, enable_request_tracking: bool = True):
    """
    Add monitoring middleware to FastAPI app.
    
    Args:
        app: FastAPI application instance
        enable_request_tracking: Whether to enable detailed request tracking
    """
    # Add metrics middleware (always enabled)
    app.add_middleware(MetricsMiddleware)
    
    # Add request tracking middleware (optional)
    if enable_request_tracking:
        app.add_middleware(RequestTrackingMiddleware)
    
    return app