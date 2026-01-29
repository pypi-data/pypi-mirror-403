"""
Dependency Injection Decorators
Decorators for marking classes and methods for dependency injection
"""

import inspect
import functools
from typing import Type, TypeVar, Callable, Any, Optional

from .container import get_container, LifetimeScope

T = TypeVar('T')


def injectable(cls: Type[T]) -> Type[T]:
    """
    Mark a class as injectable
    
    This decorator automatically registers the class in the DI container
    and enables constructor injection.
    """
    # Auto-register the class
    container = get_container()
    if not container.is_registered(cls):
        container.register(cls, cls, LifetimeScope.TRANSIENT)
    
    # Store original init
    original_init = cls.__init__
    
    @functools.wraps(original_init)
    def new_init(self, *args, **kwargs):
        # If no arguments provided, try dependency injection
        if not args and not kwargs:
            try:
                # Get constructor signature
                signature = inspect.signature(original_init)
                parameters = list(signature.parameters.values())[1:]  # Skip 'self'
                
                # Inject dependencies
                for param in parameters:
                    param_type = param.annotation
                    
                    if param_type != inspect.Parameter.empty:
                        if param.name not in kwargs:
                            try:
                                kwargs[param.name] = container.resolve(param_type)
                            except ValueError:
                                # If dependency can't be resolved and has default, skip
                                if param.default == inspect.Parameter.empty:
                                    raise
            except Exception:
                # If injection fails, call original init with provided args
                pass
        
        original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    return cls


def singleton(cls: Type[T]) -> Type[T]:
    """
    Mark a class as a singleton
    
    This decorator registers the class as a singleton in the DI container.
    """
    container = get_container()
    container.register_singleton(cls, cls)
    
    # Apply injectable decorator
    return injectable(cls)


def inject(func: Callable) -> Callable:
    """
    Enable dependency injection for a function
    
    This decorator allows functions to receive dependencies as parameters.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        container = get_container()
        
        # Get function signature
        signature = inspect.signature(func)
        parameters = list(signature.parameters.values())
        
        # Skip parameters that are already provided
        provided_params = set()
        
        # Handle positional arguments
        for i, arg in enumerate(args):
            if i < len(parameters):
                provided_params.add(parameters[i].name)
        
        # Handle keyword arguments
        provided_params.update(kwargs.keys())
        
        # Inject missing dependencies
        for param in parameters:
            if param.name not in provided_params:
                param_type = param.annotation
                
                if param_type != inspect.Parameter.empty:
                    try:
                        kwargs[param.name] = container.resolve(param_type)
                    except ValueError:
                        # If dependency can't be resolved and has default, skip
                        if param.default == inspect.Parameter.empty:
                            raise
        
        return func(*args, **kwargs)
    
    return wrapper


def scoped_inject(scope: Optional[str] = None):
    """
    Enable scoped dependency injection for a function
    
    Args:
        scope: Scope ID to use, if None will use default scope
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            
            # Get function signature
            signature = inspect.signature(func)
            parameters = list(signature.parameters.values())
            
            # Skip parameters that are already provided
            provided_params = set()
            
            # Handle positional arguments
            for i, arg in enumerate(args):
                if i < len(parameters):
                    provided_params.add(parameters[i].name)
            
            # Handle keyword arguments
            provided_params.update(kwargs.keys())
            
            # Inject missing dependencies with scope
            for param in parameters:
                if param.name not in provided_params:
                    param_type = param.annotation
                    
                    if param_type != inspect.Parameter.empty:
                        try:
                            kwargs[param.name] = container.resolve(param_type, scope)
                        except ValueError:
                            # If dependency can't be resolved and has default, skip
                            if param.default == inspect.Parameter.empty:
                                raise
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def auto_register(*service_types, lifetime: LifetimeScope = LifetimeScope.TRANSIENT):
    """
    Auto-register a class for multiple service types
    
    Args:
        *service_types: Service types to register this class for
        lifetime: Lifetime scope for registration
    """
    def decorator(cls: Type[T]) -> Type[T]:
        container = get_container()
        
        # Register for all specified service types
        for service_type in service_types:
            container.register(service_type, cls, lifetime)
        
        # If no service types specified, register for self
        if not service_types:
            container.register(cls, cls, lifetime)
        
        return injectable(cls)
    
    return decorator


# Convenience decorators for specific lifetimes
def transient(cls: Type[T]) -> Type[T]:
    """Mark class as transient (new instance each time)"""
    return auto_register(lifetime=LifetimeScope.TRANSIENT)(cls)


def scoped(cls: Type[T]) -> Type[T]:
    """Mark class as scoped (one instance per scope)"""
    return auto_register(lifetime=LifetimeScope.SCOPED)(cls)