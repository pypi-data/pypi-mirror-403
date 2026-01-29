#!/usr/bin/env python3
"""
Error handling middleware for NC1709 Enhanced
Provides standardized error responses and logging
"""

import logging
import traceback
from typing import Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..exceptions import (
    NC1709BaseException, 
    format_error_response, 
    get_http_status
)
from ..monitoring.metrics import (
    ERROR_COUNT,
    REQUEST_DURATION,
    time
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time()
        
        try:
            response = await call_next(request)
            
            # Record successful request metrics
            duration = time() - start_time
            REQUEST_DURATION.observe(
                duration,
                method=request.method,
                endpoint=str(request.url.path),
                status_code=str(response.status_code)
            )
            
            return response
            
        except Exception as exc:
            # Record error metrics
            duration = time() - start_time
            error_type = type(exc).__name__
            
            ERROR_COUNT.inc(
                error_type=error_type,
                endpoint=str(request.url.path),
                method=request.method
            )
            
            REQUEST_DURATION.observe(
                duration,
                method=request.method,
                endpoint=str(request.url.path),
                status_code="500"  # Default, will be updated below
            )
            
            # Handle different exception types
            return await self._handle_exception(exc, request)
    
    async def _handle_exception(self, exc: Exception, request: Request) -> JSONResponse:
        """Handle and format exceptions into appropriate responses"""
        
        # Get error details
        error_response = format_error_response(exc)
        status_code = error_response["http_status"]
        
        # Log the error with appropriate level
        if isinstance(exc, NC1709BaseException):
            # Custom exceptions - log at appropriate level
            if status_code >= 500:
                logger.error(
                    f"NC1709 Error ({exc.error_code}): {exc.message}",
                    extra={
                        "error_code": exc.error_code,
                        "details": exc.details,
                        "path": str(request.url.path),
                        "method": request.method,
                        "client_ip": self._get_client_ip(request)
                    }
                )
            else:
                logger.warning(
                    f"NC1709 Client Error ({exc.error_code}): {exc.message}",
                    extra={
                        "error_code": exc.error_code,
                        "details": exc.details,
                        "path": str(request.url.path),
                        "method": request.method,
                        "client_ip": self._get_client_ip(request)
                    }
                )
        else:
            # Unexpected exceptions - always log as error with traceback
            logger.error(
                f"Unhandled exception: {str(exc)}",
                extra={
                    "exception_type": type(exc).__name__,
                    "path": str(request.url.path),
                    "method": request.method,
                    "client_ip": self._get_client_ip(request),
                    "traceback": traceback.format_exc()
                }
            )
        
        # Add request context to error response
        error_response["request_id"] = getattr(request.state, "request_id", "unknown")
        error_response["timestamp"] = time()
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first (common in production behind proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        return request.client.host if request.client else "unknown"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs for tracking"""
    
    async def dispatch(self, request: Request, call_next):
        import uuid
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


# Utility functions for manual error handling
def handle_ollama_error(exc: Exception, model_name: str = None) -> None:
    """Convert Ollama-related exceptions to NC1709 exceptions"""
    from ..exceptions import (
        OllamaConnectionError,
        OllamaTimeoutError, 
        OllamaModelNotFoundError
    )
    
    error_msg = str(exc).lower()
    
    if "connection" in error_msg or "connect" in error_msg:
        raise OllamaConnectionError(
            f"Failed to connect to Ollama service: {exc}",
            model_name=model_name
        )
    elif "timeout" in error_msg:
        raise OllamaTimeoutError(
            f"Ollama service timeout: {exc}",
            model_name=model_name
        )
    elif "not found" in error_msg or "404" in error_msg:
        raise OllamaModelNotFoundError(
            f"Model '{model_name}' not found in Ollama",
            model_name=model_name
        )
    else:
        # Generic Ollama error
        raise OllamaConnectionError(
            f"Ollama service error: {exc}",
            model_name=model_name
        )


def handle_validation_error(field: str, message: str) -> None:
    """Raise validation error with field context"""
    from ..exceptions import ValidationError
    raise ValidationError(message, field=field)


def handle_authentication_error(message: str = "Invalid API key") -> None:
    """Raise authentication error"""
    from ..exceptions import AuthenticationError
    raise AuthenticationError(message)