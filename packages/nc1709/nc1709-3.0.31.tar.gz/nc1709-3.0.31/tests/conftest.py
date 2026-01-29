"""
Test Configuration and Fixtures
Shared test fixtures for NC1709 Enhanced tests
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Generator, Dict, Any

# Import components for testing
from nc1709.agent.core import AgentConfig
from nc1709.agent.tools.base import ToolRegistry
from nc1709.di import DIContainer
from nc1709.llm.base import LLMConfig, LLMResponse
from nc1709.monitoring.metrics import MetricsCollector


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    llm = Mock()
    llm.chat = Mock(return_value="Mock LLM response")
    llm.model_name = "mock-model"
    return llm


@pytest.fixture
def mock_async_llm():
    """Mock async LLM for testing"""
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=LLMResponse(
        content="Mock async LLM response",
        model="mock-async-model",
        tokens_used=100,
        duration=0.5
    ))
    llm.health_check = AsyncMock(return_value=True)
    return llm


@pytest.fixture
def agent_config(mock_llm):
    """Basic agent configuration for testing"""
    return AgentConfig(
        llm=mock_llm,
        max_iterations=3,
        max_history=50,
        temperature=0.1,
        timeout=30.0
    )


@pytest.fixture
def llm_config():
    """Basic LLM configuration for testing"""
    return LLMConfig(
        model="test-model",
        temperature=0.1,
        max_tokens=1000,
        timeout=30.0
    )


@pytest.fixture
def test_container():
    """Dependency injection container for testing"""
    container = DIContainer("test")
    yield container
    container.clear()


@pytest.fixture
def tool_registry():
    """Tool registry for testing"""
    from nc1709.agent.tools.base import get_default_registry
    return get_default_registry()


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector"""
    collector = Mock(spec=MetricsCollector)
    collector.record_request = Mock()
    collector.record_model_inference = Mock()
    collector.record_tool_execution = Mock()
    return collector


@pytest.fixture
def sample_requests():
    """Sample request data for testing"""
    return [
        {
            "id": "req-1",
            "payload": {"message": "Hello"},
            "priority": 1
        },
        {
            "id": "req-2", 
            "payload": {"message": "World"},
            "priority": 5
        },
        {
            "id": "req-3",
            "payload": {"message": "Test"},
            "priority": 3
        }
    ]


@pytest.fixture
def mock_tool():
    """Mock tool for testing"""
    from nc1709.agent.tools.base import Tool, ToolResult
    
    class MockTool(Tool):
        def __init__(self, name="mock_tool", should_fail=False):
            super().__init__(name, "Mock tool for testing")
            self.should_fail = should_fail
            self.call_count = 0
        
        def execute(self, **kwargs) -> ToolResult:
            self.call_count += 1
            if self.should_fail:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="Mock tool failure"
                )
            return ToolResult(
                success=True,
                tool_name=self.name,
                output=f"Mock result with args: {kwargs}"
            )
    
    return MockTool()


@pytest.fixture
def failing_mock_tool():
    """Mock tool that always fails"""
    from tests.conftest import mock_tool
    tool = mock_tool
    tool.should_fail = True
    return tool


class MockOllamaServer:
    """Mock Ollama server for testing"""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
        self.should_fail = False
    
    def set_response(self, model: str, response: str):
        """Set response for a model"""
        self.responses[model] = response
    
    def set_failure(self, should_fail: bool = True):
        """Set whether requests should fail"""
        self.should_fail = should_fail
    
    async def generate(self, model: str, prompt: str, **kwargs):
        """Mock generate endpoint"""
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mock Ollama server error")
        
        response = self.responses.get(model, f"Mock response for {model}")
        return {
            "response": response,
            "done": True,
            "eval_count": 50,
            "prompt_eval_count": 20,
            "total_duration": 500000000  # nanoseconds
        }


@pytest.fixture
def mock_ollama_server():
    """Mock Ollama server fixture"""
    return MockOllamaServer()


@pytest.fixture
def environment_vars(monkeypatch):
    """Set up test environment variables"""
    test_env = {
        "NC1709_ENV": "test",
        "OLLAMA_URL": "http://localhost:11434",
        "NC1709_LOG_LEVEL": "DEBUG",
        "REDIS_URL": "redis://localhost:6379/1",  # Use test database
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env


@pytest.fixture
def circuit_breaker_config():
    """Circuit breaker configuration for testing"""
    return {
        "failure_threshold": 3,
        "recovery_timeout": 5.0,
        "expected_exception": Exception
    }


@pytest.fixture
async def async_request_queue():
    """Async request queue for testing"""
    from nc1709.async_request_queue import AsyncRequestQueue
    
    queue = AsyncRequestQueue(max_concurrent=2, max_queue_size=10)
    await queue.start()
    yield queue
    await queue.stop()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "async_test: mark test as asynchronous"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring Ollama server"
    )


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    import logging
    logging.getLogger("nc1709").setLevel(logging.DEBUG)
    

# Helper functions for tests
def assert_tool_result(result, expected_success=True, expected_output=None):
    """Helper to assert tool result properties"""
    assert result.success == expected_success
    if expected_output is not None:
        assert expected_output in result.output
    if not expected_success:
        assert result.error is not None


def create_mock_llm_response(content="Mock response", tokens=100, duration=0.5):
    """Create a mock LLM response"""
    return LLMResponse(
        content=content,
        model="mock-model",
        tokens_used=tokens,
        duration=duration
    )