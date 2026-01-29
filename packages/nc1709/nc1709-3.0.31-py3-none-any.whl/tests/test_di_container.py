"""
Test Dependency Injection Container
Tests for the DI system
"""

import pytest
from unittest.mock import Mock
from nc1709.di import (
    DIContainer, LifetimeScope, injectable, singleton, inject,
    get_container, Service, Singleton
)


class TestDIContainer:
    """Test basic DI container functionality"""
    
    def test_container_creation(self):
        """Test container creation"""
        container = DIContainer("test")
        assert container.name == "test"
    
    def test_register_class(self):
        """Test registering a class"""
        container = DIContainer()
        
        class TestService:
            pass
        
        container.register(TestService)
        assert container.is_registered(TestService)
    
    def test_register_with_implementation(self):
        """Test registering interface with implementation"""
        container = DIContainer()
        
        class IService:
            pass
        
        class ServiceImpl(IService):
            pass
        
        container.register(IService, ServiceImpl)
        instance = container.resolve(IService)
        assert isinstance(instance, ServiceImpl)
    
    def test_register_instance(self):
        """Test registering an instance"""
        container = DIContainer()
        instance = Mock()
        
        container.register(Mock, instance)
        resolved = container.resolve(Mock)
        assert resolved is instance
    
    def test_register_factory(self):
        """Test registering a factory function"""
        container = DIContainer()
        
        def create_service():
            return Mock(factory_created=True)
        
        container.register(Mock, create_service)
        instance = container.resolve(Mock)
        assert instance.factory_created is True


class TestLifetimeScopes:
    """Test lifetime scope management"""
    
    def test_transient_lifetime(self):
        """Test transient lifetime creates new instances"""
        container = DIContainer()
        
        class Service:
            pass
        
        container.register_transient(Service)
        
        instance1 = container.resolve(Service)
        instance2 = container.resolve(Service)
        
        assert instance1 is not instance2
    
    def test_singleton_lifetime(self):
        """Test singleton lifetime reuses instances"""
        container = DIContainer()
        
        class Service:
            pass
        
        container.register_singleton(Service)
        
        instance1 = container.resolve(Service)
        instance2 = container.resolve(Service)
        
        assert instance1 is instance2
    
    def test_scoped_lifetime(self):
        """Test scoped lifetime"""
        container = DIContainer()
        
        class Service:
            pass
        
        container.register_scoped(Service)
        
        scope1 = container.create_scope()
        scope2 = container.create_scope()
        
        # Same scope = same instance
        instance1a = container.resolve(Service, scope1)
        instance1b = container.resolve(Service, scope1)
        assert instance1a is instance1b
        
        # Different scope = different instance
        instance2 = container.resolve(Service, scope2)
        assert instance1a is not instance2


class TestDependencyInjection:
    """Test automatic dependency injection"""
    
    def test_constructor_injection(self):
        """Test constructor dependency injection"""
        container = DIContainer()
        
        class Database:
            pass
        
        class Service:
            def __init__(self, db: Database):
                self.db = db
        
        container.register_singleton(Database)
        container.register(Service)
        
        service = container.resolve(Service)
        assert isinstance(service.db, Database)
    
    def test_multiple_dependencies(self):
        """Test injection with multiple dependencies"""
        container = DIContainer()
        
        class Logger:
            pass
        
        class Database:
            pass
        
        class Service:
            def __init__(self, logger: Logger, db: Database):
                self.logger = logger
                self.db = db
        
        container.register_singleton(Logger)
        container.register_singleton(Database)
        container.register(Service)
        
        service = container.resolve(Service)
        assert isinstance(service.logger, Logger)
        assert isinstance(service.db, Database)
    
    def test_optional_dependencies(self):
        """Test optional dependencies with defaults"""
        container = DIContainer()
        
        class Config:
            pass
        
        class Service:
            def __init__(self, config: Config = None):
                self.config = config or "default_config"
        
        container.register(Service)
        
        service = container.resolve(Service)
        assert service.config == "default_config"
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are handled gracefully"""
        container = DIContainer()
        
        class ServiceA:
            def __init__(self, service_b: 'ServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        container.register(ServiceA)
        container.register(ServiceB)
        
        # This should raise an error or handle gracefully
        with pytest.raises(RecursionError):
            container.resolve(ServiceA)


class TestDecorators:
    """Test DI decorators"""
    
    def test_injectable_decorator(self):
        """Test @injectable decorator"""
        container = get_container()
        
        @injectable
        class Service:
            pass
        
        assert container.is_registered(Service)
        instance = container.resolve(Service)
        assert isinstance(instance, Service)
    
    def test_singleton_decorator(self):
        """Test @singleton decorator"""
        container = get_container()
        
        @singleton
        class SingletonService:
            pass
        
        instance1 = container.resolve(SingletonService)
        instance2 = container.resolve(SingletonService)
        assert instance1 is instance2
    
    def test_inject_decorator(self):
        """Test @inject decorator"""
        container = DIContainer()
        
        class Database:
            def query(self):
                return "data"
        
        container.register_singleton(Database)
        
        @inject
        def get_data(db: Database):
            return db.query()
        
        # Manual injection test
        result = get_data()
        assert result == "data"


class TestErrorHandling:
    """Test error handling in DI container"""
    
    def test_unregistered_service(self):
        """Test resolving unregistered service"""
        container = DIContainer()
        
        class UnregisteredService:
            pass
        
        # Should auto-register concrete classes
        instance = container.resolve(UnregisteredService)
        assert isinstance(instance, UnregisteredService)
    
    def test_abstract_class_resolution(self):
        """Test resolving abstract class without registration"""
        container = DIContainer()
        
        from abc import ABC, abstractmethod
        
        class AbstractService(ABC):
            @abstractmethod
            def do_something(self):
                pass
        
        with pytest.raises(ValueError):
            container.resolve(AbstractService)
    
    def test_clear_container(self):
        """Test clearing container"""
        container = DIContainer()
        
        class Service:
            def dispose(self):
                self.disposed = True
        
        instance = Mock()
        instance.dispose = Mock()
        
        container.register(Service, instance)
        resolved = container.resolve(Service)
        
        container.clear()
        
        # Dispose should have been called
        instance.dispose.assert_called_once()
        
        # Should no longer be registered
        assert not container.is_registered(Service)


class TestScopeManagement:
    """Test scope creation and disposal"""
    
    def test_create_and_dispose_scope(self):
        """Test scope lifecycle"""
        container = DIContainer()
        
        class Service:
            def __init__(self):
                self.disposed = False
            
            def dispose(self):
                self.disposed = True
        
        container.register_scoped(Service)
        
        scope_id = container.create_scope()
        service = container.resolve(Service, scope_id)
        
        assert not service.disposed
        
        container.dispose_scope(scope_id)
        
        assert service.disposed
    
    def test_scope_isolation(self):
        """Test that scopes are isolated"""
        container = DIContainer()
        
        class Counter:
            def __init__(self):
                self.count = 0
            
            def increment(self):
                self.count += 1
                return self.count
        
        container.register_scoped(Counter)
        
        scope1 = container.create_scope()
        scope2 = container.create_scope()
        
        counter1 = container.resolve(Counter, scope1)
        counter2 = container.resolve(Counter, scope2)
        
        assert counter1.increment() == 1
        assert counter2.increment() == 1  # Independent counter
        assert counter1.increment() == 2  # Same instance in scope1