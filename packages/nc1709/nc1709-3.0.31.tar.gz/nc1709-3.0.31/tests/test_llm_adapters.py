"""
Test LLM Adapters
Tests for the Strategy pattern LLM adapters
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from nc1709.llm import (
    LLMConfig, OllamaAdapter, OpenAIAdapter, LLMAdapterFactory,
    create_adapter, create_adapter_from_env
)
from nc1709.llm.base import (
    LLMResponse, LLMAdapterError, LLMTimeoutError, 
    LLMConnectionError, LLMModelError, LLMAuthError
)


class TestLLMConfig:
    """Test LLM configuration"""
    
    def test_config_creation(self):
        """Test basic config creation"""
        config = LLMConfig(
            model="test-model",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.extra_params == {}
    
    def test_config_defaults(self):
        """Test default values"""
        config = LLMConfig(model="test-model")
        
        assert config.temperature == 0.1
        assert config.timeout == 300.0
        assert config.extra_params == {}


class TestLLMResponse:
    """Test LLM response structure"""
    
    def test_response_creation(self):
        """Test LLM response creation"""
        response = LLMResponse(
            content="Test response",
            model="test-model",
            tokens_used=100,
            duration=0.5
        )
        
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.tokens_used == 100
        assert response.duration == 0.5
        assert response.metadata == {}


@pytest.mark.asyncio
class TestOllamaAdapter:
    """Test Ollama adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter initialization"""
        config = LLMConfig(model="test-model", base_url="http://localhost:11434")
        adapter = OllamaAdapter(config)
        
        assert adapter.config.model == "test-model"
        assert adapter.base_url == "http://localhost:11434"
    
    @patch('httpx.AsyncClient')
    async def test_chat_success(self, mock_client_class):
        """Test successful chat completion"""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Hello, world!"},
            "eval_count": 50,
            "prompt_eval_count": 20,
            "eval_duration": 1000000000,
            "prompt_eval_duration": 500000000,
            "total_duration": 1500000000
        }
        mock_client.post.return_value = mock_response
        
        config = LLMConfig(model="test-model")
        adapter = OllamaAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await adapter.chat(messages)
        
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.tokens_used == 70  # 50 + 20
        assert response.prompt_tokens == 20
        assert response.completion_tokens == 50
    
    @patch('httpx.AsyncClient')
    async def test_chat_model_not_found(self, mock_client_class):
        """Test chat with model not found error"""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.post.return_value = mock_response
        
        config = LLMConfig(model="nonexistent-model")
        adapter = OllamaAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(LLMModelError):
            await adapter.chat(messages)
    
    @patch('httpx.AsyncClient')
    async def test_chat_connection_error(self, mock_client_class):
        """Test chat with connection error"""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.post.side_effect = Exception("Connection refused")
        
        config = LLMConfig(model="test-model")
        adapter = OllamaAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(LLMAdapterError):
            await adapter.chat(messages)
    
    async def test_health_check(self):
        """Test health check"""
        config = LLMConfig(model="test-model")
        adapter = OllamaAdapter(config)
        
        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = await adapter.health_check()
            assert result is True
    
    async def test_health_check_failure(self):
        """Test health check failure"""
        config = LLMConfig(model="test-model")
        adapter = OllamaAdapter(config)
        
        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Connection error")
            mock_get_client.return_value = mock_client
            
            result = await adapter.health_check()
            assert result is False


@pytest.mark.asyncio
class TestOpenAIAdapter:
    """Test OpenAI adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter initialization"""
        config = LLMConfig(model="gpt-4", api_key="test-key")
        adapter = OpenAIAdapter(config)
        
        assert adapter.config.model == "gpt-4"
        assert adapter.api_key == "test-key"
    
    def test_adapter_no_api_key(self):
        """Test adapter without API key raises error"""
        config = LLMConfig(model="gpt-4")
        
        with pytest.raises(LLMAuthError):
            OpenAIAdapter(config)
    
    @patch('httpx.AsyncClient')
    async def test_chat_success(self, mock_client_class):
        """Test successful chat completion"""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Hello from GPT!"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "model": "gpt-4",
            "id": "chatcmpl-123"
        }
        mock_client.post.return_value = mock_response
        
        config = LLMConfig(model="gpt-4", api_key="test-key")
        adapter = OpenAIAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await adapter.chat(messages)
        
        assert response.content == "Hello from GPT!"
        assert response.model == "gpt-4"
        assert response.tokens_used == 15
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
    
    @patch('httpx.AsyncClient')
    async def test_chat_auth_error(self, mock_client_class):
        """Test chat with authentication error"""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        
        config = LLMConfig(model="gpt-4", api_key="invalid-key")
        adapter = OpenAIAdapter(config)
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(LLMAuthError):
            await adapter.chat(messages)


class TestLLMAdapterFactory:
    """Test LLM adapter factory"""
    
    def test_list_adapters(self):
        """Test listing available adapters"""
        adapters = LLMAdapterFactory.list_adapters()
        
        assert 'ollama' in adapters
        assert 'openai' in adapters
        assert 'azure_openai' in adapters
    
    def test_create_ollama_adapter(self):
        """Test creating Ollama adapter"""
        adapter = LLMAdapterFactory.create_adapter(
            'ollama',
            model='test-model',
            base_url='http://localhost:11434'
        )
        
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.config.model == 'test-model'
    
    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter"""
        adapter = LLMAdapterFactory.create_adapter(
            'openai',
            model='gpt-4',
            api_key='test-key'
        )
        
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.config.model == 'gpt-4'
    
    def test_create_adapter_unknown_type(self):
        """Test creating adapter with unknown type"""
        with pytest.raises(ValueError, match="Unknown adapter type"):
            LLMAdapterFactory.create_adapter('unknown', model='test')
    
    def test_register_custom_adapter(self):
        """Test registering custom adapter"""
        class CustomAdapter:
            def __init__(self, config):
                self.config = config
        
        LLMAdapterFactory.register_adapter('custom', CustomAdapter)
        
        adapter = LLMAdapterFactory.create_adapter('custom', model='test')
        assert isinstance(adapter, CustomAdapter)


class TestEnvironmentDetection:
    """Test environment-based adapter creation"""
    
    @patch.dict('os.environ', {'OLLAMA_URL': 'http://localhost:11434'})
    def test_detect_ollama_from_env(self):
        """Test detecting Ollama from environment"""
        adapter_type = LLMAdapterFactory._detect_adapter_from_env()
        assert adapter_type == 'ollama'
    
    @patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'OLLAMA_URL': ''  # Override Ollama
    })
    def test_detect_openai_from_env(self):
        """Test detecting OpenAI from environment"""
        adapter_type = LLMAdapterFactory._detect_adapter_from_env()
        assert adapter_type == 'openai'
    
    @patch.dict('os.environ', {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
        'OPENAI_API_KEY': '',  # Override OpenAI
        'OLLAMA_URL': ''  # Override Ollama
    })
    def test_detect_azure_from_env(self):
        """Test detecting Azure OpenAI from environment"""
        adapter_type = LLMAdapterFactory._detect_adapter_from_env()
        assert adapter_type == 'azure_openai'


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_create_adapter_function(self):
        """Test create_adapter convenience function"""
        adapter = create_adapter(
            'ollama',
            model='test-model'
        )
        
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.config.model == 'test-model'
    
    @patch.dict('os.environ', {'OLLAMA_URL': 'http://localhost:11434'})
    def test_create_adapter_from_env(self):
        """Test creating adapter from environment"""
        adapter = create_adapter_from_env()
        assert isinstance(adapter, OllamaAdapter)


class TestStreamingSupport:
    """Test streaming capabilities"""
    
    @pytest.mark.asyncio
    async def test_default_streaming(self):
        """Test default streaming implementation"""
        config = LLMConfig(model="test-model")
        adapter = OllamaAdapter(config)
        
        with patch.object(adapter, 'chat') as mock_chat:
            mock_chat.return_value = LLMResponse(content="Test response")
            
            messages = [{"role": "user", "content": "Hello"}]
            chunks = []
            
            async for chunk in adapter.stream_chat(messages):
                chunks.append(chunk)
            
            assert chunks == ["Test response"]