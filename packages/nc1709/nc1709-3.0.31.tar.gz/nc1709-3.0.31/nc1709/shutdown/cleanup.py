"""
Cleanup Registry
Global registry for cleanup functions and resources
"""

import atexit
import logging
import threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CleanupPriority(Enum):
    """Cleanup priority levels"""
    CRITICAL = 0    # Must run (e.g., saving data)
    HIGH = 1        # Important (e.g., closing connections)
    MEDIUM = 2      # Normal (e.g., temp file cleanup)
    LOW = 3         # Nice to have (e.g., logging cleanup)


@dataclass
class CleanupItem:
    """A cleanup item to be executed"""
    name: str
    callback: Callable[[], Any]
    priority: CleanupPriority = CleanupPriority.MEDIUM
    timeout: float = 10.0
    args: tuple = ()
    kwargs: dict = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class CleanupRegistry:
    """Registry for cleanup functions"""
    
    def __init__(self):
        self.items: List[CleanupItem] = []
        self.executed = False
        self.lock = threading.Lock()
        
    def register(
        self,
        name: str,
        callback: Callable[[], Any],
        priority: CleanupPriority = CleanupPriority.MEDIUM,
        timeout: float = 10.0,
        *args,
        **kwargs
    ) -> None:
        """
        Register a cleanup function
        
        Args:
            name: Name of the cleanup task
            callback: Function to call
            priority: Priority level
            timeout: Maximum time to wait for cleanup
            *args, **kwargs: Arguments to pass to callback
        """
        with self.lock:
            if self.executed:
                logger.warning(f"Cannot register cleanup '{name}' - cleanup already executed")
                return
            
            item = CleanupItem(
                name=name,
                callback=callback,
                priority=priority,
                timeout=timeout,
                args=args,
                kwargs=kwargs
            )
            
            self.items.append(item)
            logger.debug(f"Registered cleanup task: {name} (priority: {priority.name})")
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a cleanup function by name
        
        Args:
            name: Name of the cleanup task to remove
            
        Returns:
            True if item was found and removed
        """
        with self.lock:
            for i, item in enumerate(self.items):
                if item.name == name:
                    self.items.pop(i)
                    logger.debug(f"Unregistered cleanup task: {name}")
                    return True
            return False
    
    def execute_cleanup(self) -> Dict[str, Any]:
        """
        Execute all cleanup functions
        
        Returns:
            Dictionary with cleanup results
        """
        with self.lock:
            if self.executed:
                logger.warning("Cleanup already executed")
                return {"status": "already_executed"}
            
            self.executed = True
        
        logger.info("Starting cleanup process...")
        
        # Sort by priority (critical first)
        sorted_items = sorted(self.items, key=lambda x: x.priority.value)
        
        results = {
            "status": "completed",
            "total_items": len(sorted_items),
            "successful": 0,
            "failed": 0,
            "items": {}
        }
        
        for item in sorted_items:
            result = self._execute_item(item)
            results["items"][item.name] = result
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                
                # If critical item failed, mark overall status as failed
                if item.priority == CleanupPriority.CRITICAL:
                    results["status"] = "failed"
        
        logger.info(f"Cleanup completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def _execute_item(self, item: CleanupItem) -> Dict[str, Any]:
        """Execute a single cleanup item"""
        result = {
            "success": False,
            "duration": 0.0,
            "error": None
        }
        
        import time
        start_time = time.time()
        
        try:
            logger.debug(f"Executing cleanup: {item.name}")
            
            # Execute with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Cleanup '{item.name}' timed out after {item.timeout}s")
            
            # Set timeout (Unix only)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(item.timeout))
            
            try:
                # Execute callback
                if item.args or item.kwargs:
                    item.callback(*item.args, **item.kwargs)
                else:
                    item.callback()
                
                result["success"] = True
                logger.debug(f"Cleanup '{item.name}' completed successfully")
                
            finally:
                # Cancel timeout
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
            
        except TimeoutError as e:
            result["error"] = str(e)
            logger.error(f"Cleanup '{item.name}' timed out: {e}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Cleanup '{item.name}' failed: {e}")
        
        result["duration"] = time.time() - start_time
        return result
    
    def get_items(self) -> List[CleanupItem]:
        """Get all registered cleanup items"""
        with self.lock:
            return self.items.copy()
    
    def clear(self) -> None:
        """Clear all registered cleanup items"""
        with self.lock:
            self.items.clear()
            self.executed = False
            logger.debug("Cleared all cleanup items")


# Global cleanup registry
_global_registry: Optional[CleanupRegistry] = None
_registry_lock = threading.Lock()


def get_cleanup_registry() -> CleanupRegistry:
    """Get the global cleanup registry"""
    global _global_registry
    
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = CleanupRegistry()
                # Register with atexit
                atexit.register(_global_registry.execute_cleanup)
    
    return _global_registry


# Convenience functions
def register_cleanup(
    name: str,
    callback: Callable[[], Any],
    priority: CleanupPriority = CleanupPriority.MEDIUM,
    timeout: float = 10.0,
    *args,
    **kwargs
) -> None:
    """Register a cleanup function with the global registry"""
    registry = get_cleanup_registry()
    registry.register(name, callback, priority, timeout, *args, **kwargs)


def unregister_cleanup(name: str) -> bool:
    """Unregister a cleanup function from the global registry"""
    registry = get_cleanup_registry()
    return registry.unregister(name)


def cleanup(
    name: Optional[str] = None,
    priority: CleanupPriority = CleanupPriority.MEDIUM,
    timeout: float = 10.0
):
    """
    Decorator to register a function as a cleanup task
    
    Args:
        name: Name for the cleanup task (uses function name if None)
        priority: Cleanup priority
        timeout: Maximum execution time
    """
    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        cleanup_name = name or func.__name__
        register_cleanup(cleanup_name, func, priority, timeout)
        return func
    
    return decorator


# Context manager for cleanup
class CleanupContext:
    """Context manager that ensures cleanup is executed"""
    
    def __init__(self, auto_cleanup: bool = True):
        self.auto_cleanup = auto_cleanup
        self.registry = CleanupRegistry()
        
    def __enter__(self) -> CleanupRegistry:
        return self.registry
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_cleanup:
            self.registry.execute_cleanup()


# Resource management helpers
class ManagedResource:
    """Base class for managed resources with automatic cleanup"""
    
    def __init__(self, name: str, cleanup_priority: CleanupPriority = CleanupPriority.MEDIUM):
        self.name = name
        self.cleanup_priority = cleanup_priority
        self._cleaned_up = False
        
        # Register cleanup
        register_cleanup(
            f"resource_{name}",
            self._cleanup,
            cleanup_priority
        )
    
    def _cleanup(self) -> None:
        """Cleanup implementation - override in subclasses"""
        if not self._cleaned_up:
            self.cleanup()
            self._cleaned_up = True
    
    def cleanup(self) -> None:
        """Override this method for specific cleanup logic"""
        pass
    
    def __del__(self):
        """Cleanup on deletion"""
        if not self._cleaned_up:
            try:
                self._cleanup()
            except Exception:
                pass  # Ignore cleanup errors in destructor


def execute_global_cleanup() -> Dict[str, Any]:
    """Execute global cleanup manually"""
    registry = get_cleanup_registry()
    return registry.execute_cleanup()