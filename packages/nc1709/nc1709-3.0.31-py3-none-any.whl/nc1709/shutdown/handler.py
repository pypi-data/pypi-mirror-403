"""
Shutdown Handler
Manages graceful shutdown process for NC1709 components
"""

import logging
import asyncio
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Phases of shutdown process"""
    STARTED = "started"
    STOPPING_NEW_REQUESTS = "stopping_new_requests"
    DRAINING_CONNECTIONS = "draining_connections"
    STOPPING_SERVICES = "stopping_services"
    CLEANUP = "cleanup"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ShutdownTask:
    """A task to execute during shutdown"""
    name: str
    callback: Callable[[], Any]
    phase: ShutdownPhase
    timeout: float = 30.0
    critical: bool = True  # If True, failure will mark shutdown as failed
    async_task: bool = False


class ShutdownHandler:
    """Handles graceful shutdown of individual components"""
    
    def __init__(self, name: str, timeout: float = 60.0):
        self.name = name
        self.timeout = timeout
        self.tasks: List[ShutdownTask] = []
        self.is_shutting_down = False
        self.shutdown_completed = False
        self.shutdown_failed = False
        self.current_phase = None
        
    def register_task(
        self,
        name: str,
        callback: Callable[[], Any],
        phase: ShutdownPhase = ShutdownPhase.CLEANUP,
        timeout: float = 30.0,
        critical: bool = True,
        async_task: bool = False
    ) -> None:
        """Register a shutdown task"""
        task = ShutdownTask(
            name=name,
            callback=callback,
            phase=phase,
            timeout=timeout,
            critical=critical,
            async_task=async_task
        )
        self.tasks.append(task)
        logger.debug(f"Registered shutdown task '{name}' for phase {phase.value}")
    
    async def shutdown(self) -> bool:
        """Execute graceful shutdown"""
        if self.is_shutting_down:
            logger.warning(f"Shutdown already in progress for {self.name}")
            return not self.shutdown_failed
        
        self.is_shutting_down = True
        logger.info(f"Starting graceful shutdown for {self.name}")
        
        try:
            # Group tasks by phase
            phases = {}
            for task in self.tasks:
                if task.phase not in phases:
                    phases[task.phase] = []
                phases[task.phase].append(task)
            
            # Execute phases in order
            phase_order = [
                ShutdownPhase.STOPPING_NEW_REQUESTS,
                ShutdownPhase.DRAINING_CONNECTIONS,
                ShutdownPhase.STOPPING_SERVICES,
                ShutdownPhase.CLEANUP
            ]
            
            for phase in phase_order:
                if phase in phases:
                    success = await self._execute_phase(phase, phases[phase])
                    if not success and any(task.critical for task in phases[phase]):
                        self.shutdown_failed = True
                        self.current_phase = ShutdownPhase.FAILED
                        logger.error(f"Critical failure in phase {phase.value}")
                        return False
            
            self.shutdown_completed = True
            self.current_phase = ShutdownPhase.COMPLETED
            logger.info(f"Graceful shutdown completed for {self.name}")
            return True
            
        except Exception as e:
            self.shutdown_failed = True
            self.current_phase = ShutdownPhase.FAILED
            logger.error(f"Shutdown failed for {self.name}: {e}")
            return False
    
    async def _execute_phase(self, phase: ShutdownPhase, tasks: List[ShutdownTask]) -> bool:
        """Execute all tasks in a phase"""
        self.current_phase = phase
        logger.info(f"Executing shutdown phase: {phase.value}")
        
        success = True
        
        # Execute tasks concurrently within timeout
        async with asyncio.timeout(max(task.timeout for task in tasks) + 5.0):
            results = await asyncio.gather(
                *[self._execute_task(task) for task in tasks],
                return_exceptions=True
            )
            
            # Check results
            for task, result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Task {task.name} failed: {result}")
                    if task.critical:
                        success = False
                elif result is False:
                    logger.warning(f"Task {task.name} returned False")
                    if task.critical:
                        success = False
                else:
                    logger.debug(f"Task {task.name} completed successfully")
        
        return success
    
    async def _execute_task(self, task: ShutdownTask) -> Any:
        """Execute a single shutdown task"""
        logger.debug(f"Executing shutdown task: {task.name}")
        
        try:
            if task.async_task:
                # Async task
                if asyncio.iscoroutinefunction(task.callback):
                    return await asyncio.wait_for(task.callback(), timeout=task.timeout)
                else:
                    # Run sync function in executor
                    return await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, task.callback),
                        timeout=task.timeout
                    )
            else:
                # Sync task
                return await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, task.callback),
                    timeout=task.timeout
                )
        except asyncio.TimeoutError:
            logger.error(f"Task {task.name} timed out after {task.timeout}s")
            return False
        except Exception as e:
            logger.error(f"Task {task.name} failed with exception: {e}")
            raise


class ShutdownManager:
    """Manages shutdown for multiple components"""
    
    def __init__(self):
        self.handlers: Dict[str, ShutdownHandler] = {}
        self.is_shutting_down = False
        self.shutdown_event = asyncio.Event()
        
    def register_handler(self, handler: ShutdownHandler) -> None:
        """Register a shutdown handler"""
        self.handlers[handler.name] = handler
        logger.debug(f"Registered shutdown handler: {handler.name}")
    
    def create_handler(self, name: str, timeout: float = 60.0) -> ShutdownHandler:
        """Create and register a new shutdown handler"""
        handler = ShutdownHandler(name, timeout)
        self.register_handler(handler)
        return handler
    
    async def shutdown_all(self, timeout: float = 120.0) -> bool:
        """Shutdown all registered handlers"""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            await self.shutdown_event.wait()
            return True
        
        self.is_shutting_down = True
        logger.info("Starting global shutdown process")
        
        try:
            # Shutdown all handlers concurrently
            async with asyncio.timeout(timeout):
                results = await asyncio.gather(
                    *[handler.shutdown() for handler in self.handlers.values()],
                    return_exceptions=True
                )
            
            # Check results
            all_success = True
            for handler, result in zip(self.handlers.values(), results):
                if isinstance(result, Exception):
                    logger.error(f"Handler {handler.name} failed: {result}")
                    all_success = False
                elif result is False:
                    logger.error(f"Handler {handler.name} shutdown failed")
                    all_success = False
                else:
                    logger.info(f"Handler {handler.name} shutdown successfully")
            
            if all_success:
                logger.info("Global shutdown completed successfully")
            else:
                logger.error("Some components failed to shutdown gracefully")
            
            self.shutdown_event.set()
            return all_success
            
        except asyncio.TimeoutError:
            logger.error(f"Global shutdown timed out after {timeout}s")
            self.shutdown_event.set()
            return False
        except Exception as e:
            logger.error(f"Global shutdown failed: {e}")
            self.shutdown_event.set()
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get shutdown status for all handlers"""
        return {
            "is_shutting_down": self.is_shutting_down,
            "handlers": {
                name: {
                    "is_shutting_down": handler.is_shutting_down,
                    "shutdown_completed": handler.shutdown_completed,
                    "shutdown_failed": handler.shutdown_failed,
                    "current_phase": handler.current_phase.value if handler.current_phase else None,
                    "task_count": len(handler.tasks)
                }
                for name, handler in self.handlers.items()
            }
        }


# Global shutdown manager
_global_manager: Optional[ShutdownManager] = None
_manager_lock = threading.Lock()


def get_shutdown_manager() -> ShutdownManager:
    """Get the global shutdown manager"""
    global _global_manager
    
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = ShutdownManager()
    
    return _global_manager


# Decorator for graceful shutdown
def graceful_shutdown(name: str, timeout: float = 60.0):
    """Decorator to add graceful shutdown to a class"""
    def decorator(cls):
        # Add shutdown handler to class
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Create shutdown handler
            self._shutdown_handler = ShutdownHandler(f"{cls.__name__}:{name}", timeout)
            get_shutdown_manager().register_handler(self._shutdown_handler)
            
            # Auto-register common cleanup methods
            for method_name in ['close', 'cleanup', 'dispose', 'shutdown']:
                if hasattr(self, method_name) and callable(getattr(self, method_name)):
                    method = getattr(self, method_name)
                    self._shutdown_handler.register_task(
                        f"{method_name}",
                        method,
                        ShutdownPhase.CLEANUP,
                        timeout=30.0
                    )
        
        cls.__init__ = new_init
        return cls
    
    return decorator


class GracefulShutdown:
    """Context manager for graceful shutdown"""
    
    def __init__(self, name: str, timeout: float = 60.0):
        self.name = name
        self.timeout = timeout
        self.handler = ShutdownHandler(name, timeout)
        self.manager = get_shutdown_manager()
        
    def __enter__(self) -> ShutdownHandler:
        self.manager.register_handler(self.handler)
        return self.handler
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Trigger shutdown on exit
        asyncio.create_task(self.handler.shutdown())