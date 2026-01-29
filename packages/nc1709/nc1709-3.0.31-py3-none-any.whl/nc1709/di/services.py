"""
NC1709 Service Provider

Provides a centralized service locator pattern for dependency injection.
This allows singletons to be easily replaced in tests while maintaining
backwards compatibility with the existing codebase.

Usage:
    from nc1709.di.services import services

    # Get a service
    metrics = services.get('metrics_collector')

    # In tests, override services
    services.register('metrics_collector', mock_metrics)

    # Reset to defaults
    services.reset()
"""

import threading
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceDefinition:
    """Definition of a service"""
    name: str
    factory: Callable[[], Any]
    singleton: bool = True
    instance: Any = None


class ServiceProvider:
    """
    Service provider for dependency injection.

    Provides a centralized way to manage services (singletons and factories)
    with support for testing overrides.

    Features:
    - Lazy initialization of singletons
    - Factory support for transient services
    - Test overrides that don't affect production code
    - Thread-safe service creation
    """

    def __init__(self):
        self._services: Dict[str, ServiceDefinition] = {}
        self._overrides: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def register(
        self,
        name: str,
        factory_or_instance: Any,
        singleton: bool = True,
        override: bool = False
    ) -> None:
        """
        Register a service.

        Args:
            name: Service name
            factory_or_instance: Either a factory callable or an instance
            singleton: If True, only create one instance
            override: If True, register as a test override
        """
        if override:
            self._overrides[name] = factory_or_instance
            logger.debug(f"Registered override for service: {name}")
            return

        # Determine if it's a factory or instance
        if callable(factory_or_instance) and not isinstance(factory_or_instance, type):
            factory = factory_or_instance
            instance = None
        else:
            factory = lambda x=factory_or_instance: x
            instance = factory_or_instance if not callable(factory_or_instance) else None

        with self._lock:
            self._services[name] = ServiceDefinition(
                name=name,
                factory=factory,
                singleton=singleton,
                instance=instance
            )
        logger.debug(f"Registered service: {name} (singleton={singleton})")

    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a service by name.

        Args:
            name: Service name
            default: Default value if service not found

        Returns:
            Service instance
        """
        # Check overrides first (for testing)
        if name in self._overrides:
            override = self._overrides[name]
            if callable(override):
                return override()
            return override

        # Check registered services
        if name not in self._services:
            logger.debug(f"Service not found: {name}")
            return default

        service = self._services[name]

        # Return existing instance for singletons
        if service.singleton and service.instance is not None:
            return service.instance

        # Create new instance
        with self._lock:
            # Double-check after acquiring lock
            if service.singleton and service.instance is not None:
                return service.instance

            try:
                instance = service.factory()
                if service.singleton:
                    service.instance = instance
                return instance
            except Exception as e:
                logger.error(f"Error creating service {name}: {e}")
                return default

    def has(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services or name in self._overrides

    def override(self, name: str, instance: Any) -> None:
        """
        Override a service (for testing).

        Args:
            name: Service name
            instance: Override instance or factory
        """
        self._overrides[name] = instance
        logger.debug(f"Set override for: {name}")

    def clear_override(self, name: str) -> None:
        """Clear a specific override"""
        self._overrides.pop(name, None)

    def clear_all_overrides(self) -> None:
        """Clear all overrides"""
        self._overrides.clear()
        logger.debug("Cleared all service overrides")

    def reset(self) -> None:
        """Reset all services to uninitialized state"""
        with self._lock:
            for service in self._services.values():
                service.instance = None
            self._overrides.clear()
        logger.debug("Reset all services")

    def get_names(self) -> list:
        """Get list of all registered service names"""
        return list(self._services.keys())

    def initialize_defaults(self) -> None:
        """
        Initialize default NC1709 services.

        This registers the standard singletons from the codebase
        as services that can be injected or overridden.
        """
        if self._initialized:
            return

        # Import lazily to avoid circular imports
        def _import_and_get(module_path: str, getter_name: str):
            """Helper to lazily import and call a getter function"""
            def factory():
                import importlib
                parts = module_path.rsplit('.', 1)
                if len(parts) == 2:
                    module = importlib.import_module(parts[0])
                    getter = getattr(module, getter_name, None)
                    if getter:
                        return getter()
                return None
            return factory

        # Register core services
        default_services = [
            # Monitoring
            ('metrics_collector', 'nc1709.monitoring.metrics', 'metrics_collector'),
            ('health_checker', 'nc1709.monitoring.health', 'health_checker'),

            # Utils
            ('breaker_manager', 'nc1709.utils.circuit_breaker', 'breaker_manager'),
            ('pool_manager', 'nc1709.utils.connection_pool', 'pool_manager'),

            # Core
            ('config', 'nc1709.config', 'get_config'),
            ('logger', 'nc1709.logger', 'get_logger'),

            # DI
            ('container', 'nc1709.di.container', 'get_container'),
        ]

        for name, module_path, attr_or_getter in default_services:
            try:
                if attr_or_getter.startswith('get_'):
                    # It's a getter function
                    self.register(name, _import_and_get(module_path, attr_or_getter))
                else:
                    # It's a module attribute
                    def make_factory(m, a):
                        def factory():
                            import importlib
                            mod = importlib.import_module(m)
                            return getattr(mod, a, None)
                        return factory
                    self.register(name, make_factory(module_path, attr_or_getter))
            except Exception as e:
                logger.warning(f"Could not register default service {name}: {e}")

        self._initialized = True
        logger.info("Initialized default NC1709 services")


# Global service provider instance
services = ServiceProvider()


def get_service(name: str, default: Any = None) -> Any:
    """
    Convenience function to get a service.

    Args:
        name: Service name
        default: Default value if not found

    Returns:
        Service instance
    """
    if not services._initialized:
        services.initialize_defaults()
    return services.get(name, default)


def inject(*service_names: str):
    """
    Decorator to inject services into a function.

    Usage:
        @inject('metrics_collector', 'config')
        def my_function(metrics, config, other_arg):
            ...

    Services are injected as the first positional arguments.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            injected = [get_service(name) for name in service_names]
            return func(*injected, *args, **kwargs)
        return wrapper
    return decorator


class ServiceContext:
    """
    Context manager for temporarily overriding services.

    Usage:
        with ServiceContext({'metrics_collector': mock_metrics}):
            # mock_metrics is used here
            run_tests()
        # Original metrics_collector is restored
    """

    def __init__(self, overrides: Dict[str, Any]):
        self.overrides = overrides
        self._previous = {}

    def __enter__(self):
        for name, instance in self.overrides.items():
            self._previous[name] = services._overrides.get(name)
            services.override(name, instance)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for name in self.overrides:
            if self._previous.get(name) is not None:
                services._overrides[name] = self._previous[name]
            else:
                services.clear_override(name)
        return False
