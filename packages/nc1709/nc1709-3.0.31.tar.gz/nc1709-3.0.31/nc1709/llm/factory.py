"""
LLM Adapter Factory
Factory pattern implementation for creating LLM adapters
"""

from typing import Dict, Type, Union, Optional, Any
import os
import logging

from .base import BaseLLMAdapter, LLMConfig
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter, AzureOpenAIAdapter

logger = logging.getLogger(__name__)


class LLMAdapterFactory:
    """Factory for creating LLM adapters"""
    
    _adapters: Dict[str, Type[BaseLLMAdapter]] = {
        'ollama': OllamaAdapter,
        'openai': OpenAIAdapter,
        'azure_openai': AzureOpenAIAdapter,
        'gpt': OpenAIAdapter,  # Alias
        'azure': AzureOpenAIAdapter,  # Alias
    }
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[BaseLLMAdapter]) -> None:
        """Register a new adapter type"""
        cls._adapters[name.lower()] = adapter_class
        logger.info(f"Registered LLM adapter: {name}")
    
    @classmethod
    def list_adapters(cls) -> list[str]:
        """List available adapter types"""
        return list(cls._adapters.keys())
    
    @classmethod
    def create_adapter(
        cls, 
        adapter_type: str, 
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> BaseLLMAdapter:
        """
        Create an LLM adapter instance
        
        Args:
            adapter_type: Type of adapter ('ollama', 'openai', 'azure_openai')
            config: LLM configuration object
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured adapter instance
        """
        adapter_type = adapter_type.lower()
        
        if adapter_type not in cls._adapters:
            available = ', '.join(cls._adapters.keys())
            raise ValueError(f"Unknown adapter type '{adapter_type}'. Available: {available}")
        
        adapter_class = cls._adapters[adapter_type]
        
        # Create config if not provided
        if config is None:
            config = cls._create_default_config(adapter_type, **kwargs)
        
        # Merge any additional kwargs into config
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.extra_params[key] = value
        
        # Validate required configuration for adapter type
        cls._validate_config(adapter_type, config)
        
        try:
            adapter = adapter_class(config)
            logger.info(f"Created {adapter_type} adapter for model: {config.model}")
            return adapter
        except Exception as e:
            logger.error(f"Failed to create {adapter_type} adapter: {e}")
            raise
    
    @classmethod
    def _create_default_config(cls, adapter_type: str, **kwargs) -> LLMConfig:
        """Create default configuration for adapter type"""
        
        if adapter_type == 'ollama':
            return LLMConfig(
                model=kwargs.get('model', 'qwen2.5-coder:7b-instruct'),
                base_url=kwargs.get('base_url', os.getenv('OLLAMA_URL', 'http://localhost:11434')),
                temperature=kwargs.get('temperature', 0.1),
                timeout=kwargs.get('timeout', 300.0),
                extra_params=kwargs.get('extra_params', {})
            )
        
        elif adapter_type in ['openai', 'gpt']:
            return LLMConfig(
                model=kwargs.get('model', 'gpt-4'),
                api_key=kwargs.get('api_key', os.getenv('OPENAI_API_KEY')),
                base_url=kwargs.get('base_url', 'https://api.openai.com/v1'),
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4000),
                timeout=kwargs.get('timeout', 60.0),
                extra_params=kwargs.get('extra_params', {})
            )
        
        elif adapter_type in ['azure_openai', 'azure']:
            return LLMConfig(
                model=kwargs.get('model', 'gpt-4'),
                api_key=kwargs.get('api_key', os.getenv('AZURE_OPENAI_API_KEY')),
                base_url=kwargs.get('base_url', os.getenv('AZURE_OPENAI_ENDPOINT')),
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4000),
                timeout=kwargs.get('timeout', 60.0),
                extra_params={
                    'deployment_name': kwargs.get('deployment_name', kwargs.get('model', 'gpt-4')),
                    'api_version': kwargs.get('api_version', '2023-12-01-preview'),
                    **(kwargs.get('extra_params', {}))
                }
            )
        
        else:
            # Generic config
            return LLMConfig(
                model=kwargs.get('model', 'default'),
                **{k: v for k, v in kwargs.items() if k != 'model'}
            )
    
    @classmethod
    def _validate_config(cls, adapter_type: str, config: LLMConfig) -> None:
        """Validate configuration for specific adapter type"""
        
        if adapter_type == 'ollama':
            if not config.model:
                raise ValueError("Ollama adapter requires model to be specified")
        
        elif adapter_type in ['openai', 'gpt']:
            if not config.api_key:
                raise ValueError("OpenAI adapter requires API key")
            if not config.model:
                raise ValueError("OpenAI adapter requires model to be specified")
        
        elif adapter_type in ['azure_openai', 'azure']:
            if not config.api_key:
                raise ValueError("Azure OpenAI adapter requires API key")
            if not config.base_url:
                raise ValueError("Azure OpenAI adapter requires base_url (endpoint)")
            if not config.extra_params.get('deployment_name'):
                raise ValueError("Azure OpenAI adapter requires deployment_name")
    
    @classmethod
    def create_from_env(cls, adapter_type: Optional[str] = None) -> BaseLLMAdapter:
        """
        Create adapter from environment variables
        
        Args:
            adapter_type: Override adapter type, otherwise detect from environment
            
        Returns:
            Configured adapter instance
        """
        # Auto-detect adapter type if not specified
        if adapter_type is None:
            adapter_type = cls._detect_adapter_from_env()
        
        # Create config based on environment variables
        config_kwargs = cls._extract_config_from_env(adapter_type)
        
        return cls.create_adapter(adapter_type, **config_kwargs)
    
    @classmethod
    def _detect_adapter_from_env(cls) -> str:
        """Detect adapter type from environment variables"""
        
        # Check for Azure OpenAI
        if os.getenv('AZURE_OPENAI_API_KEY') and os.getenv('AZURE_OPENAI_ENDPOINT'):
            return 'azure_openai'
        
        # Check for OpenAI
        if os.getenv('OPENAI_API_KEY'):
            return 'openai'
        
        # Check for Ollama
        if os.getenv('OLLAMA_URL') or os.path.exists('/usr/local/bin/ollama'):
            return 'ollama'
        
        # Default to Ollama (most common for self-hosted)
        logger.warning("Could not detect LLM adapter from environment, defaulting to Ollama")
        return 'ollama'
    
    @classmethod
    def _extract_config_from_env(cls, adapter_type: str) -> Dict[str, Any]:
        """Extract configuration from environment variables"""
        config = {}
        
        # Common environment variables
        if os.getenv('LLM_MODEL'):
            config['model'] = os.getenv('LLM_MODEL')
        if os.getenv('LLM_TEMPERATURE'):
            config['temperature'] = float(os.getenv('LLM_TEMPERATURE'))
        if os.getenv('LLM_MAX_TOKENS'):
            config['max_tokens'] = int(os.getenv('LLM_MAX_TOKENS'))
        if os.getenv('LLM_TIMEOUT'):
            config['timeout'] = float(os.getenv('LLM_TIMEOUT'))
        
        # Adapter-specific environment variables
        if adapter_type == 'ollama':
            if os.getenv('OLLAMA_URL'):
                config['base_url'] = os.getenv('OLLAMA_URL')
            if not config.get('model'):
                config['model'] = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b-instruct')
        
        elif adapter_type in ['openai', 'gpt']:
            if os.getenv('OPENAI_API_KEY'):
                config['api_key'] = os.getenv('OPENAI_API_KEY')
            if os.getenv('OPENAI_BASE_URL'):
                config['base_url'] = os.getenv('OPENAI_BASE_URL')
            if not config.get('model'):
                config['model'] = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        elif adapter_type in ['azure_openai', 'azure']:
            if os.getenv('AZURE_OPENAI_API_KEY'):
                config['api_key'] = os.getenv('AZURE_OPENAI_API_KEY')
            if os.getenv('AZURE_OPENAI_ENDPOINT'):
                config['base_url'] = os.getenv('AZURE_OPENAI_ENDPOINT')
            if os.getenv('AZURE_OPENAI_DEPLOYMENT'):
                config['deployment_name'] = os.getenv('AZURE_OPENAI_DEPLOYMENT')
            if os.getenv('AZURE_OPENAI_API_VERSION'):
                config['api_version'] = os.getenv('AZURE_OPENAI_API_VERSION')
            if not config.get('model'):
                config['model'] = os.getenv('AZURE_OPENAI_MODEL', 'gpt-4')
        
        return config


# Convenience function for creating adapters
def create_adapter(
    adapter_type: str,
    model: str = None,
    **kwargs
) -> BaseLLMAdapter:
    """
    Convenience function for creating LLM adapters
    
    Args:
        adapter_type: Type of adapter ('ollama', 'openai', 'azure_openai')
        model: Model name to use
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured adapter instance
    """
    if model:
        kwargs['model'] = model
    
    return LLMAdapterFactory.create_adapter(adapter_type, **kwargs)


def create_adapter_from_env(adapter_type: Optional[str] = None) -> BaseLLMAdapter:
    """
    Create adapter from environment variables
    
    Args:
        adapter_type: Override adapter type, otherwise auto-detect
        
    Returns:
        Configured adapter instance
    """
    return LLMAdapterFactory.create_from_env(adapter_type)


def create_ollama_adapter(
    model: str = "qwen2.5-coder:7b-instruct",
    base_url: str = "http://localhost:11434",
    **kwargs
) -> OllamaAdapter:
    """Create Ollama adapter with sensible defaults"""
    return create_adapter('ollama', model=model, base_url=base_url, **kwargs)


def create_openai_adapter(
    model: str = "gpt-4",
    api_key: Optional[str] = None,
    **kwargs
) -> OpenAIAdapter:
    """Create OpenAI adapter with sensible defaults"""
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')
    return create_adapter('openai', model=model, api_key=api_key, **kwargs)