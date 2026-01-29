"""
Dependency Injection Providers
Advanced provider patterns for complex dependency scenarios
"""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar, Callable, Dict, Optional
import inspect

T = TypeVar('T')


class Provider(ABC):
    """Base class for dependency providers"""
    
    @abstractmethod
    def provide(self, container: 'DIContainer') -> Any:
        """Provide an instance of the service"""
        pass


class InstanceProvider(Provider):
    """Provider that returns a pre-created instance"""
    
    def __init__(self, instance: Any):
        self.instance = instance
    
    def provide(self, container: 'DIContainer') -> Any:
        return self.instance


class FactoryProvider(Provider):
    """Provider that uses a factory function"""
    
    def __init__(self, factory: Callable[..., Any]):
        self.factory = factory
    
    def provide(self, container: 'DIContainer') -> Any:
        # Analyze factory signature and inject dependencies
        signature = inspect.signature(self.factory)
        kwargs = {}
        
        for param_name, param in signature.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = container.resolve(param.annotation)
                except ValueError:
                    if param.default == inspect.Parameter.empty:
                        raise
                    # Use default value
        
        return self.factory(**kwargs)


class ClassProvider(Provider):
    """Provider that creates instances of a class"""
    
    def __init__(self, cls: Type[T]):
        self.cls = cls
    
    def provide(self, container: 'DIContainer') -> T:
        # Analyze constructor and inject dependencies
        signature = inspect.signature(self.cls.__init__)
        kwargs = {}
        
        # Skip 'self' parameter
        parameters = list(signature.parameters.values())[1:]
        
        for param in parameters:
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param.name] = container.resolve(param.annotation)
                except ValueError:
                    if param.default == inspect.Parameter.empty:
                        raise
        
        return self.cls(**kwargs)


class LazyProvider(Provider):
    """Provider that creates instances lazily"""
    
    def __init__(self, provider: Provider):
        self.provider = provider
        self._instance = None
        self._created = False
    
    def provide(self, container: 'DIContainer') -> Any:
        if not self._created:
            self._instance = self.provider.provide(container)
            self._created = True
        return self._instance


class ConditionalProvider(Provider):
    """Provider that chooses implementation based on conditions"""
    
    def __init__(self):
        self.conditions: list[tuple[Callable[[], bool], Provider]] = []
        self.default_provider: Optional[Provider] = None
    
    def when(self, condition: Callable[[], bool], provider: Provider) -> 'ConditionalProvider':
        """Add a condition and corresponding provider"""
        self.conditions.append((condition, provider))
        return self
    
    def otherwise(self, provider: Provider) -> 'ConditionalProvider':
        """Set default provider"""
        self.default_provider = provider
        return self
    
    def provide(self, container: 'DIContainer') -> Any:
        # Check conditions in order
        for condition, provider in self.conditions:
            if condition():
                return provider.provide(container)
        
        # Use default if available
        if self.default_provider:
            return self.default_provider.provide(container)
        
        raise ValueError("No condition matched and no default provider set")


class ConfigurationProvider(Provider):
    """Provider that creates instances based on configuration"""
    
    def __init__(self, config: Dict[str, Any], config_key: str):
        self.config = config
        self.config_key = config_key
    
    def provide(self, container: 'DIContainer') -> Any:
        if self.config_key not in self.config:
            raise ValueError(f"Configuration key '{self.config_key}' not found")
        
        config_value = self.config[self.config_key]
        
        # If it's a class name, resolve it
        if isinstance(config_value, str):
            # Try to import and create
            module_name, class_name = config_value.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            return ClassProvider(cls).provide(container)
        
        # If it's already an instance
        return config_value


class DecoratorProvider(Provider):
    """Provider that decorates another provider's output"""
    
    def __init__(self, base_provider: Provider, decorator: Callable[[Any], Any]):
        self.base_provider = base_provider
        self.decorator = decorator
    
    def provide(self, container: 'DIContainer') -> Any:
        instance = self.base_provider.provide(container)
        return self.decorator(instance)


class MultipleProvider(Provider):
    """Provider that returns multiple instances"""
    
    def __init__(self):
        self.providers: list[Provider] = []
    
    def add_provider(self, provider: Provider) -> 'MultipleProvider':
        """Add a provider to the collection"""
        self.providers.append(provider)
        return self
    
    def provide(self, container: 'DIContainer') -> list[Any]:
        return [provider.provide(container) for provider in self.providers]


# Convenience functions for creating providers
def instance(obj: Any) -> InstanceProvider:
    """Create an instance provider"""
    return InstanceProvider(obj)


def factory(func: Callable[..., Any]) -> FactoryProvider:
    """Create a factory provider"""
    return FactoryProvider(func)


def class_provider(cls: Type[T]) -> ClassProvider:
    """Create a class provider"""
    return ClassProvider(cls)


def lazy(provider: Provider) -> LazyProvider:
    """Create a lazy provider"""
    return LazyProvider(provider)


def conditional() -> ConditionalProvider:
    """Create a conditional provider"""
    return ConditionalProvider()


def configuration(config: Dict[str, Any], key: str) -> ConfigurationProvider:
    """Create a configuration provider"""
    return ConfigurationProvider(config, key)


def decorator(base_provider: Provider, decorator_func: Callable[[Any], Any]) -> DecoratorProvider:
    """Create a decorator provider"""
    return DecoratorProvider(base_provider, decorator_func)


def multiple() -> MultipleProvider:
    """Create a multiple provider"""
    return MultipleProvider()


# Forward reference fix
from .container import DIContainer