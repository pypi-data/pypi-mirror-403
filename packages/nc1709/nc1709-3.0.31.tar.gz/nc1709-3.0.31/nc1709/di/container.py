"""
Dependency Injection Container
Simple but powerful DI container for NC1709
"""

import inspect
import threading
from typing import Any, Dict, Type, TypeVar, Generic, Callable, Optional, Union
from dataclasses import dataclass
from enum import Enum

T = TypeVar('T')


class LifetimeScope(Enum):
    """Lifetime scopes for services"""
    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # Single instance for container
    SCOPED = "scoped"        # Single instance per scope


@dataclass
class ServiceRegistration:
    """Registration information for a service"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    dependencies: list = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()
        self._scope_counter = 0
        
    def register(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], T, Callable[..., T]] = None,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """
        Register a service in the container
        
        Args:
            service_type: The interface/type to register
            implementation: Implementation class, instance, or factory function
            lifetime: Lifetime scope for the service
            
        Returns:
            Self for chaining
        """
        with self._lock:
            if implementation is None:
                # Self-registration (concrete class)
                implementation = service_type
            
            if inspect.isclass(implementation):
                # Class registration
                registration = ServiceRegistration(
                    service_type=service_type,
                    implementation_type=implementation,
                    lifetime=lifetime
                )
            elif callable(implementation):
                # Factory registration
                registration = ServiceRegistration(
                    service_type=service_type,
                    factory=implementation,
                    lifetime=lifetime
                )
            else:
                # Instance registration (always singleton)
                registration = ServiceRegistration(
                    service_type=service_type,
                    instance=implementation,
                    lifetime=LifetimeScope.SINGLETON
                )
                self._instances[service_type] = implementation
            
            self._services[service_type] = registration
            
        return self
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], T, Callable[..., T]] = None) -> 'DIContainer':
        """Register a service as singleton"""
        return self.register(service_type, implementation, LifetimeScope.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation: Union[Type[T], T, Callable[..., T]] = None) -> 'DIContainer':
        """Register a service as transient"""
        return self.register(service_type, implementation, LifetimeScope.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], implementation: Union[Type[T], T, Callable[..., T]] = None) -> 'DIContainer':
        """Register a service as scoped"""
        return self.register(service_type, implementation, LifetimeScope.SCOPED)
    
    def resolve(self, service_type: Type[T], scope: Optional[str] = None) -> T:
        """
        Resolve a service from the container
        
        Args:
            service_type: Type to resolve
            scope: Scope ID for scoped services
            
        Returns:
            Instance of the requested type
        """
        with self._lock:
            registration = self._services.get(service_type)
            
            if registration is None:
                # Try to auto-register if it's a concrete class
                if inspect.isclass(service_type) and not inspect.isabstract(service_type):
                    self.register(service_type, service_type)
                    registration = self._services[service_type]
                else:
                    raise ValueError(f"Service type {service_type} is not registered")
            
            # Handle different lifetime scopes
            if registration.lifetime == LifetimeScope.SINGLETON:
                return self._get_singleton(service_type, registration)
            elif registration.lifetime == LifetimeScope.SCOPED:
                return self._get_scoped(service_type, registration, scope)
            else:  # TRANSIENT
                return self._create_instance(registration)
    
    def _get_singleton(self, service_type: Type[T], registration: ServiceRegistration) -> T:
        """Get or create singleton instance"""
        if service_type in self._instances:
            return self._instances[service_type]
        
        instance = self._create_instance(registration)
        self._instances[service_type] = instance
        return instance
    
    def _get_scoped(self, service_type: Type[T], registration: ServiceRegistration, scope: Optional[str]) -> T:
        """Get or create scoped instance"""
        if scope is None:
            scope = "default"
        
        if scope not in self._scoped_instances:
            self._scoped_instances[scope] = {}
        
        if service_type in self._scoped_instances[scope]:
            return self._scoped_instances[scope][service_type]
        
        instance = self._create_instance(registration)
        self._scoped_instances[scope][service_type] = instance
        return instance
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create a new instance"""
        if registration.instance is not None:
            return registration.instance
        
        if registration.factory is not None:
            # Use factory function
            return self._call_with_injection(registration.factory)
        
        if registration.implementation_type is not None:
            # Create instance of implementation class
            return self._call_with_injection(registration.implementation_type)
        
        raise ValueError(f"Cannot create instance for registration: {registration}")
    
    def _call_with_injection(self, callable_obj: Callable) -> Any:
        """Call function/constructor with dependency injection"""
        if inspect.isclass(callable_obj):
            # Constructor injection
            signature = inspect.signature(callable_obj.__init__)
            parameters = list(signature.parameters.values())[1:]  # Skip 'self'
        else:
            # Function injection
            signature = inspect.signature(callable_obj)
            parameters = list(signature.parameters.values())
        
        kwargs = {}
        
        for param in parameters:
            param_type = param.annotation
            
            # Skip parameters without type annotations
            if param_type == inspect.Parameter.empty:
                continue
            
            # Handle optional parameters
            if param.default != inspect.Parameter.empty:
                try:
                    kwargs[param.name] = self.resolve(param_type)
                except ValueError:
                    # Service not registered, use default
                    continue
            else:
                kwargs[param.name] = self.resolve(param_type)
        
        return callable_obj(**kwargs)
    
    def create_scope(self) -> str:
        """Create a new scope and return its ID"""
        with self._lock:
            self._scope_counter += 1
            scope_id = f"scope_{self._scope_counter}"
            self._scoped_instances[scope_id] = {}
            return scope_id
    
    def dispose_scope(self, scope_id: str) -> None:
        """Dispose of a scope and all its instances"""
        with self._lock:
            if scope_id in self._scoped_instances:
                # Call dispose methods on instances if they exist
                for instance in self._scoped_instances[scope_id].values():
                    if hasattr(instance, 'dispose') and callable(instance.dispose):
                        try:
                            instance.dispose()
                        except Exception:
                            pass  # Ignore dispose errors
                
                del self._scoped_instances[scope_id]
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered"""
        return service_type in self._services
    
    def get_registrations(self) -> Dict[Type, ServiceRegistration]:
        """Get all registrations (for debugging)"""
        return self._services.copy()
    
    def clear(self) -> None:
        """Clear all registrations and instances"""
        with self._lock:
            # Dispose all instances
            for instance in self._instances.values():
                if hasattr(instance, 'dispose') and callable(instance.dispose):
                    try:
                        instance.dispose()
                    except Exception:
                        pass
            
            # Dispose all scoped instances
            for scope_instances in self._scoped_instances.values():
                for instance in scope_instances.values():
                    if hasattr(instance, 'dispose') and callable(instance.dispose):
                        try:
                            instance.dispose()
                        except Exception:
                            pass
            
            self._services.clear()
            self._instances.clear()
            self._scoped_instances.clear()


# Global container instance
_global_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """Get the global DI container"""
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DIContainer("global")
    
    return _global_container


def set_container(container: DIContainer) -> None:
    """Set the global DI container"""
    global _global_container
    with _container_lock:
        _global_container = container


# Convenience classes for registration
class Service:
    """Marker class for service registration"""
    pass


class Singleton:
    """Marker class for singleton registration"""
    pass