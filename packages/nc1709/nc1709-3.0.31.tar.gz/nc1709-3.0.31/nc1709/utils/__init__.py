"""
NC1709 Enhanced Utilities

Common utilities for connection pooling, circuit breakers, sanitization,
rate limiting, schema validation, and system helpers.
"""

from .connection_pool import OllamaConnectionPool, ConnectionPoolManager
from .circuit_breaker import CircuitBreaker, CircuitState
from .sanitizer import (
    sanitize_command,
    sanitize_path,
    sanitize_string,
    sanitize_tool_parameters,
    is_safe_command,
    is_safe_path,
    escape_shell_arg,
    get_safe_filename,
    SanitizationLevel,
    SanitizationResult,
)
from .rate_limiter import (
    TokenBucket,
    RateLimiterRegistry,
    RateLimitExceeded,
    RateLimitStrategy,
    RateLimiterConfig,
    rate_limited,
    get_rate_limiter,
    get_rate_limiter_registry,
)
from .schema_validator import (
    JSONSchemaValidator,
    ValidationResult,
    ValidationError,
    validate_tool_parameters as validate_tool_params_schema,
    create_parameter_schema,
)

__all__ = [
    # Connection Pool
    'OllamaConnectionPool',
    'ConnectionPoolManager',
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitState',
    # Sanitization (NC1709-SAN)
    'sanitize_command',
    'sanitize_path',
    'sanitize_string',
    'sanitize_tool_parameters',
    'is_safe_command',
    'is_safe_path',
    'escape_shell_arg',
    'get_safe_filename',
    'SanitizationLevel',
    'SanitizationResult',
    # Rate Limiting
    'TokenBucket',
    'RateLimiterRegistry',
    'RateLimitExceeded',
    'RateLimitStrategy',
    'RateLimiterConfig',
    'rate_limited',
    'get_rate_limiter',
    'get_rate_limiter_registry',
    # Schema Validation
    'JSONSchemaValidator',
    'ValidationResult',
    'ValidationError',
    'validate_tool_params_schema',
    'create_parameter_schema',
]