"""
Test Exception Hierarchy
Tests for custom exception system
"""

import pytest
from nc1709.exceptions import (
    NC1709BaseException, AuthenticationError, ValidationError,
    ModelError, OllamaConnectionError, CircuitBreakerError,
    format_error_response, get_http_status
)


class TestNC1709BaseException:
    """Test base exception functionality"""
    
    def test_base_exception_creation(self):
        """Test basic exception creation"""
        exc = NC1709BaseException("Test message", "TEST_CODE", {"key": "value"})
        
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"key": "value"}
    
    def test_base_exception_defaults(self):
        """Test default values"""
        exc = NC1709BaseException("Test message")
        
        assert exc.error_code == "NC1709BaseException"
        assert exc.details == {}
    
    def test_to_dict(self):
        """Test dictionary conversion"""
        exc = NC1709BaseException("Test message", "TEST_CODE", {"detail": "info"})
        result = exc.to_dict()
        
        expected = {
            "error": True,
            "error_code": "TEST_CODE",
            "message": "Test message",
            "details": {"detail": "info"}
        }
        
        assert result == expected


class TestSpecificExceptions:
    """Test specific exception types"""
    
    def test_authentication_error(self):
        """Test authentication error"""
        exc = AuthenticationError("Invalid API key")
        
        assert isinstance(exc, NC1709BaseException)
        assert exc.message == "Invalid API key"
        assert exc.error_code == "AuthenticationError"
    
    def test_validation_error_with_field(self):
        """Test validation error with field information"""
        exc = ValidationError("Invalid format", field="email")
        
        assert exc.details["field"] == "email"
    
    def test_model_error_with_model_name(self):
        """Test model error with model information"""
        exc = ModelError("Model failed", model_name="test-model")
        
        assert exc.details["model_name"] == "test-model"
    
    def test_ollama_connection_error_with_endpoint(self):
        """Test Ollama connection error with endpoint"""
        exc = OllamaConnectionError("Connection failed", endpoint="http://localhost:11434")
        
        assert exc.details["endpoint"] == "http://localhost:11434"
    
    def test_circuit_breaker_error(self):
        """Test circuit breaker error"""
        exc = CircuitBreakerError()
        
        assert "circuit breaker open" in exc.message.lower()
        assert exc.details["circuit_breaker_status"] == "open"


class TestErrorFormatting:
    """Test error formatting functions"""
    
    def test_get_http_status_custom_exception(self):
        """Test HTTP status code mapping for custom exceptions"""
        auth_error = AuthenticationError("Invalid")
        assert get_http_status(auth_error) == 401
        
        validation_error = ValidationError("Invalid input")
        assert get_http_status(validation_error) == 400
        
        circuit_breaker_error = CircuitBreakerError()
        assert get_http_status(circuit_breaker_error) == 503
    
    def test_get_http_status_generic_exception(self):
        """Test HTTP status code for generic exceptions"""
        generic_error = ValueError("Some error")
        assert get_http_status(generic_error) == 500
    
    def test_format_error_response_nc1709_exception(self):
        """Test formatting NC1709 exceptions"""
        exc = ValidationError("Invalid field", field="email")
        response = format_error_response(exc)
        
        expected_keys = {"error", "error_code", "message", "details", "http_status"}
        assert set(response.keys()) == expected_keys
        assert response["error"] is True
        assert response["error_code"] == "ValidationError"
        assert response["http_status"] == 400
    
    def test_format_error_response_generic_exception(self):
        """Test formatting generic exceptions"""
        exc = ValueError("Generic error")
        response = format_error_response(exc)
        
        assert response["error"] is True
        assert response["error_code"] == "INTERNAL_ERROR"
        assert response["message"] == "Generic error"
        assert response["http_status"] == 500
        assert response["details"]["exception_type"] == "ValueError"


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy"""
    
    def test_model_error_inheritance(self):
        """Test ModelError inherits from NC1709BaseException"""
        exc = ModelError("Model error")
        
        assert isinstance(exc, NC1709BaseException)
        assert isinstance(exc, ModelError)
    
    def test_ollama_error_inheritance(self):
        """Test OllamaConnectionError inherits from ModelError"""
        exc = OllamaConnectionError("Connection error")
        
        assert isinstance(exc, NC1709BaseException)
        assert isinstance(exc, ModelError)
        assert isinstance(exc, OllamaConnectionError)
    
    def test_catch_base_exception(self):
        """Test catching base exception catches all NC1709 exceptions"""
        exceptions_to_test = [
            AuthenticationError("auth"),
            ValidationError("validation"),
            ModelError("model"),
            OllamaConnectionError("ollama"),
            CircuitBreakerError("circuit")
        ]
        
        for exc in exceptions_to_test:
            try:
                raise exc
            except NC1709BaseException as caught:
                assert caught is exc
            else:
                pytest.fail(f"Failed to catch {type(exc).__name__} as NC1709BaseException")


class TestExceptionChaining:
    """Test exception chaining and wrapping"""
    
    def test_exception_chaining(self):
        """Test exception chaining with __cause__"""
        original_error = ValueError("Original error")
        
        try:
            raise original_error
        except ValueError as e:
            wrapped_error = ModelError("Wrapped error")
            wrapped_error.__cause__ = e
            
            assert wrapped_error.__cause__ is original_error
    
    def test_exception_context_preservation(self):
        """Test that exception context is preserved"""
        def inner_function():
            raise ValueError("Inner error")
        
        def outer_function():
            try:
                inner_function()
            except ValueError:
                raise ModelError("Outer error")
        
        with pytest.raises(ModelError) as exc_info:
            outer_function()
        
        # Check that the context is preserved
        assert exc_info.value.__context__ is not None
        assert isinstance(exc_info.value.__context__, ValueError)