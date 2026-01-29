"""
Middleware package for NC1709 Enhanced
Provides reusable middleware components
"""

from .error_handler import (
    ErrorHandlingMiddleware,
    RequestIDMiddleware,
    handle_ollama_error,
    handle_validation_error,
    handle_authentication_error
)

__all__ = [
    'ErrorHandlingMiddleware',
    'RequestIDMiddleware',
    'handle_ollama_error',
    'handle_validation_error', 
    'handle_authentication_error'
]