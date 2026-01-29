"""
Dependency Injection Package
Simple dependency injection container for better testability and modularity
"""

from .container import DIContainer, get_container, Service, Singleton, LifetimeScope
from .decorators import inject, injectable, singleton
from .providers import Provider, InstanceProvider, FactoryProvider, ClassProvider
from .services import (
    ServiceProvider,
    services,
    get_service,
    inject as inject_services,
    ServiceContext,
)

__all__ = [
    # Container
    'DIContainer',
    'get_container',
    'Service',
    'Singleton',
    'LifetimeScope',
    # Decorators
    'inject',
    'injectable',
    'singleton',
    # Providers
    'Provider',
    'InstanceProvider',
    'FactoryProvider',
    'ClassProvider',
    # Service Locator
    'ServiceProvider',
    'services',
    'get_service',
    'inject_services',
    'ServiceContext',
]