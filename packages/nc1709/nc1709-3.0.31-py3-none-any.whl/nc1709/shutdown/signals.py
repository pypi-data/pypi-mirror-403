"""
Signal Handler for Graceful Shutdown
Handles OS signals to trigger graceful shutdown
"""

import signal
import asyncio
import logging
import sys
from typing import Callable, Dict, Optional, Set
from .handler import get_shutdown_manager

logger = logging.getLogger(__name__)


class SignalHandler:
    """Handles OS signals for graceful shutdown"""
    
    def __init__(self):
        self.shutdown_manager = get_shutdown_manager()
        self.registered_signals: Set[int] = set()
        self.shutdown_initiated = False
        self.custom_handlers: Dict[int, Callable] = {}
        
    def register_signal(self, sig: int, custom_handler: Optional[Callable] = None) -> None:
        """
        Register a signal for graceful shutdown
        
        Args:
            sig: Signal number (e.g., signal.SIGTERM)
            custom_handler: Custom handler function (optional)
        """
        if sig in self.registered_signals:
            logger.warning(f"Signal {sig} already registered")
            return
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            
            if custom_handler:
                try:
                    custom_handler(signum, frame)
                except Exception as e:
                    logger.error(f"Custom signal handler failed: {e}")
            
            if not self.shutdown_initiated:
                self.shutdown_initiated = True
                # Schedule shutdown in event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._shutdown_async())
                    else:
                        loop.run_until_complete(self._shutdown_async())
                except RuntimeError:
                    # No event loop running, create one
                    asyncio.run(self._shutdown_async())
        
        signal.signal(sig, signal_handler)
        self.registered_signals.add(sig)
        self.custom_handlers[sig] = custom_handler
        
        logger.info(f"Registered signal handler for signal {sig}")
    
    async def _shutdown_async(self) -> None:
        """Async shutdown process"""
        try:
            logger.info("Starting async shutdown process...")
            success = await self.shutdown_manager.shutdown_all()
            
            if success:
                logger.info("Graceful shutdown completed successfully")
                exit_code = 0
            else:
                logger.error("Graceful shutdown completed with errors")
                exit_code = 1
            
            # Exit the process
            sys.exit(exit_code)
            
        except Exception as e:
            logger.error(f"Shutdown process failed: {e}")
            sys.exit(1)
    
    def register_common_signals(self) -> None:
        """Register common signals for graceful shutdown"""
        # SIGTERM - Termination request
        self.register_signal(signal.SIGTERM)
        
        # SIGINT - Interrupt from keyboard (Ctrl+C)
        self.register_signal(signal.SIGINT)
        
        # On Unix systems, also register SIGHUP
        if hasattr(signal, 'SIGHUP'):
            self.register_signal(signal.SIGHUP)
        
        # On Unix systems, register SIGUSR1 for graceful restart
        if hasattr(signal, 'SIGUSR1'):
            def restart_handler(signum, frame):
                logger.info("Received SIGUSR1, initiating graceful restart...")
                # Add restart logic here if needed
            
            self.register_signal(signal.SIGUSR1, restart_handler)
    
    def unregister_signal(self, sig: int) -> None:
        """Unregister a signal handler"""
        if sig in self.registered_signals:
            signal.signal(sig, signal.SIG_DFL)  # Restore default handler
            self.registered_signals.remove(sig)
            self.custom_handlers.pop(sig, None)
            logger.info(f"Unregistered signal handler for signal {sig}")
    
    def unregister_all(self) -> None:
        """Unregister all signal handlers"""
        for sig in list(self.registered_signals):
            self.unregister_signal(sig)


# Global signal handler
_global_signal_handler: Optional[SignalHandler] = None


def get_signal_handler() -> SignalHandler:
    """Get the global signal handler"""
    global _global_signal_handler
    
    if _global_signal_handler is None:
        _global_signal_handler = SignalHandler()
    
    return _global_signal_handler


def setup_signal_handlers() -> SignalHandler:
    """Setup common signal handlers for graceful shutdown"""
    handler = get_signal_handler()
    handler.register_common_signals()
    return handler


def register_shutdown_signal(sig: int, custom_handler: Optional[Callable] = None) -> None:
    """Register a signal for graceful shutdown"""
    handler = get_signal_handler()
    handler.register_signal(sig, custom_handler)


def cleanup_signal_handlers() -> None:
    """Cleanup all signal handlers"""
    handler = get_signal_handler()
    handler.unregister_all()


# Context manager for signal handling
class SignalHandlerContext:
    """Context manager for signal handling"""
    
    def __init__(self, setup_common: bool = True):
        self.setup_common = setup_common
        self.handler = None
    
    def __enter__(self) -> SignalHandler:
        self.handler = get_signal_handler()
        
        if self.setup_common:
            self.handler.register_common_signals()
        
        return self.handler
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            self.handler.unregister_all()