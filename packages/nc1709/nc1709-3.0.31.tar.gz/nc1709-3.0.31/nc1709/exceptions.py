#!/usr/bin/env python3
"""
Custom exception hierarchy for NC1709 Enhanced
Provides structured error handling with specific exception types
"""

from typing import Dict, Any, Optional


class NC1709BaseException(Exception):
    """Base exception for all NC1709 errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class AuthenticationError(NC1709BaseException):
    """Authentication and authorization errors"""
    pass


class ConfigurationError(NC1709BaseException):
    """Configuration and setup errors"""
    pass


class ModelError(NC1709BaseException):
    """Errors related to LLM model operations"""
    
    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if model_name:
            self.details["model_name"] = model_name


class OllamaConnectionError(ModelError):
    """Ollama service connection errors"""
    
    def __init__(self, message: str, endpoint: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if endpoint:
            self.details["endpoint"] = endpoint


class OllamaModelNotFoundError(ModelError):
    """Requested Ollama model not found"""
    pass


class OllamaTimeoutError(ModelError):
    """Ollama service timeout"""
    
    def __init__(self, message: str, timeout_duration: float = None, **kwargs):
        super().__init__(message, **kwargs)
        if timeout_duration:
            self.details["timeout_duration"] = timeout_duration


class CircuitBreakerError(ModelError):
    """Circuit breaker is open"""
    
    def __init__(self, message: str = "Service temporarily unavailable - circuit breaker open", **kwargs):
        super().__init__(message, **kwargs)
        self.details["circuit_breaker_status"] = "open"


class ConnectionPoolError(NC1709BaseException):
    """Connection pool related errors"""
    
    def __init__(self, message: str, pool_status: Dict[str, Any] = None, **kwargs):
        super().__init__(message, **kwargs)
        if pool_status:
            self.details["pool_status"] = pool_status


class RateLimitError(NC1709BaseException):
    """Rate limiting errors"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        if retry_after:
            self.details["retry_after"] = retry_after


class ValidationError(NC1709BaseException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if field:
            self.details["field"] = field


class AgentError(NC1709BaseException):
    """Agent processing errors"""
    
    def __init__(self, message: str, agent_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if agent_id:
            self.details["agent_id"] = agent_id


class DataProcessingError(NC1709BaseException):
    """Data processing and transformation errors"""
    
    def __init__(self, message: str, data_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if data_type:
            self.details["data_type"] = data_type


class MonitoringError(NC1709BaseException):
    """Monitoring and metrics collection errors"""
    pass


class DeploymentError(NC1709BaseException):
    """Deployment and infrastructure errors"""
    
    def __init__(self, message: str, component: str = None, **kwargs):
        super().__init__(message, **kwargs)
        if component:
            self.details["component"] = component


# Exception mapping for HTTP status codes
EXCEPTION_STATUS_MAP = {
    AuthenticationError: 401,
    ValidationError: 400,
    OllamaModelNotFoundError: 404,
    RateLimitError: 429,
    OllamaTimeoutError: 504,
    CircuitBreakerError: 503,
    ConnectionPoolError: 503,
    ConfigurationError: 500,
    ModelError: 500,
    OllamaConnectionError: 502,
    AgentError: 500,
    DataProcessingError: 500,
    MonitoringError: 500,
    DeploymentError: 500,
    NC1709BaseException: 500
}


def get_http_status(exception: Exception) -> int:
    """Get appropriate HTTP status code for exception"""
    for exc_type, status_code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exception, exc_type):
            return status_code
    return 500


def format_error_response(exception: Exception) -> Dict[str, Any]:
    """Format exception as standardized API error response"""
    if isinstance(exception, NC1709BaseException):
        response = exception.to_dict()
        response["http_status"] = get_http_status(exception)
        return response
    
    # Handle non-NC1709 exceptions
    return {
        "error": True,
        "error_code": "INTERNAL_ERROR",
        "message": str(exception),
        "details": {"exception_type": type(exception).__name__},
        "http_status": 500
    }

# Error suggestions for common errors
ERROR_SUGGESTIONS = {
    'permission denied': [
        'Try running with sudo or check file permissions',
        'Ensure you have write access to the directory',
    ],
    'file not found': [
        'Check if the file path is correct',
        'Use Tab completion to verify the path',
        'Run "ls" to see available files',
    ],
    'connection refused': [
        'Check if the server is running',
        'Verify the port number is correct',
        'Check firewall settings',
    ],
    'timeout': [
        'The operation took too long - try again',
        'Check your network connection',
        'Consider breaking the task into smaller parts',
    ],
    'syntax error': [
        'Check for missing brackets or quotes',
        'Verify indentation is correct',
        'Look for typos in keywords',
    ],
    'module not found': [
        'Install the missing package with pip',
        'Check if you are in the correct virtual environment',
        'Verify the module name spelling',
    ],
    'command not found': [
        'Check if the command is installed',
        'Verify the command is in your PATH',
        'Try using the full path to the command',
    ],
}

def get_error_suggestions(error_message: str) -> list:
    """Get suggestions for an error message"""
    error_lower = error_message.lower()
    suggestions = []
    
    for pattern, tips in ERROR_SUGGESTIONS.items():
        if pattern in error_lower:
            suggestions.extend(tips)
    
    return suggestions[:3]  # Return max 3 suggestions

def format_error_with_suggestions(error_message: str) -> str:
    """Format error with suggestions"""
    suggestions = get_error_suggestions(error_message)
    
    output = f"\033[31mError: {error_message}\033[0m"
    
    if suggestions:
        output += "\n\n\033[33mSuggestions:\033[0m"
        for i, suggestion in enumerate(suggestions, 1):
            output += f"\n  {i}. {suggestion}"
    
    return output
