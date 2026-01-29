"""
NC1709 Enhanced Connection Pooling

Provides efficient connection pooling for Ollama and other external services.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, AsyncContextManager
from contextlib import asynccontextmanager
import httpx

logger = logging.getLogger(__name__)


class OllamaConnectionPool:
    """
    Connection pool for Ollama service with automatic retry and health monitoring.
    
    Features:
    - Connection reuse and pooling
    - Automatic retry with exponential backoff
    - Health monitoring and metrics
    - Graceful degradation on failures
    """
    
    def __init__(
        self,
        base_url: str,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 300.0,
        retry_attempts: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Connection pool
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Health monitoring
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        self.is_healthy = True
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_requests": 0,
            "pool_hits": 0,
            "pool_misses": 0,
            "avg_response_time": 0.0,
            "last_error": None,
            "last_success": None
        }
    
    async def _ensure_initialized(self):
        """Ensure the connection pool is initialized"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            # Configure connection limits
            limits = httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_keepalive_connections
            )
            
            # Configure timeouts
            timeout = httpx.Timeout(
                connect=5.0,
                read=self.timeout,
                write=30.0,
                pool=5.0
            )
            
            # Create the client
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                limits=limits,
                timeout=timeout,
                headers={
                    "User-Agent": "NC1709-ConnectionPool/2.1.7",
                    "Connection": "keep-alive"
                }
            )
            
            self._initialized = True
            logger.info(f"Ollama connection pool initialized: {self.base_url}")
    
    @asynccontextmanager
    async def get_client(self) -> AsyncContextManager[httpx.AsyncClient]:
        """Get a client from the connection pool"""
        await self._ensure_initialized()
        
        if not self._client:
            raise RuntimeError("Connection pool not available")
        
        # Update pool statistics
        self.stats["pool_hits"] += 1
        
        try:
            yield self._client
        except Exception:
            self.stats["pool_misses"] += 1
            raise
    
    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request through the connection pool with automatic retry.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/generate')
            json_data: JSON payload for POST requests
            **kwargs: Additional httpx request parameters
            
        Returns:
            JSON response data
        """
        start_time = time.time()
        last_exception = None
        
        self.stats["total_requests"] += 1
        
        for attempt in range(self.retry_attempts + 1):
            try:
                async with self.get_client() as client:
                    # Make the request
                    if json_data:
                        response = await client.request(
                            method, 
                            endpoint, 
                            json=json_data, 
                            **kwargs
                        )
                    else:
                        response = await client.request(method, endpoint, **kwargs)
                    
                    response.raise_for_status()
                    
                    # Update success statistics
                    response_time = time.time() - start_time
                    self._update_success_stats(response_time)
                    
                    return response.json()
                    
            except Exception as e:
                last_exception = e
                
                # Don't retry on certain errors
                if isinstance(e, httpx.HTTPStatusError):
                    if e.response.status_code in [400, 401, 403, 404]:
                        # Client errors shouldn't be retried
                        break
                
                # Calculate backoff delay
                if attempt < self.retry_attempts:
                    delay = min(2 ** attempt, 30)  # Max 30 seconds
                    logger.warning(
                        f"Ollama request attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    self.stats["retry_requests"] += 1
                else:
                    logger.error(f"Ollama request failed after {self.retry_attempts + 1} attempts: {e}")
        
        # All attempts failed
        self._update_failure_stats(str(last_exception))
        raise last_exception
    
    def _update_success_stats(self, response_time: float):
        """Update statistics for successful requests"""
        self.stats["successful_requests"] += 1
        self.stats["last_success"] = time.time()
        self.is_healthy = True
        
        # Update average response time (exponential moving average)
        if self.stats["avg_response_time"] == 0:
            self.stats["avg_response_time"] = response_time
        else:
            alpha = 0.1  # Smoothing factor
            self.stats["avg_response_time"] = (
                alpha * response_time + 
                (1 - alpha) * self.stats["avg_response_time"]
            )
    
    def _update_failure_stats(self, error_message: str):
        """Update statistics for failed requests"""
        self.stats["failed_requests"] += 1
        self.stats["last_error"] = error_message
        self.is_healthy = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the Ollama service"""
        now = time.time()
        
        # Skip if recently checked
        if now - self.last_health_check < self.health_check_interval:
            return {"status": "cached", "healthy": self.is_healthy}
        
        try:
            # Simple health check request
            health_data = await self.request("GET", "/api/tags")
            self.is_healthy = True
            self.last_health_check = now
            
            return {
                "status": "checked",
                "healthy": True,
                "models": len(health_data.get("models", [])),
                "response_time": self.stats["avg_response_time"]
            }
            
        except Exception as e:
            self.is_healthy = False
            self.last_health_check = now
            
            return {
                "status": "checked",
                "healthy": False,
                "error": str(e),
                "last_success": self.stats.get("last_success")
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        total_requests = self.stats["total_requests"]
        
        return {
            "pool_config": {
                "base_url": self.base_url,
                "max_connections": self.max_connections,
                "max_keepalive": self.max_keepalive_connections,
                "timeout": self.timeout
            },
            "health": {
                "is_healthy": self.is_healthy,
                "last_health_check": self.last_health_check
            },
            "performance": {
                "total_requests": total_requests,
                "success_rate": (
                    self.stats["successful_requests"] / total_requests 
                    if total_requests > 0 else 0
                ),
                "retry_rate": (
                    self.stats["retry_requests"] / total_requests
                    if total_requests > 0 else 0
                ),
                "avg_response_time": self.stats["avg_response_time"],
                "pool_hit_rate": (
                    self.stats["pool_hits"] / (self.stats["pool_hits"] + self.stats["pool_misses"])
                    if (self.stats["pool_hits"] + self.stats["pool_misses"]) > 0 else 0
                )
            },
            "errors": {
                "failed_requests": self.stats["failed_requests"],
                "last_error": self.stats["last_error"]
            }
        }
    
    async def close(self):
        """Close the connection pool and cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False
            logger.info("Ollama connection pool closed")


class ConnectionPoolManager:
    """
    Manages multiple connection pools for different services.
    
    Provides centralized management of all connection pools with
    health monitoring and graceful shutdown.
    """
    
    def __init__(self):
        self.pools: Dict[str, OllamaConnectionPool] = {}
        self._shutdown_event = asyncio.Event()
    
    def create_ollama_pool(
        self, 
        name: str, 
        base_url: str, 
        **kwargs
    ) -> OllamaConnectionPool:
        """Create and register an Ollama connection pool"""
        pool = OllamaConnectionPool(base_url, **kwargs)
        self.pools[name] = pool
        logger.info(f"Created connection pool '{name}' for {base_url}")
        return pool
    
    def get_pool(self, name: str) -> Optional[OllamaConnectionPool]:
        """Get a connection pool by name"""
        return self.pools.get(name)
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Run health checks on all pools"""
        results = {}
        
        for name, pool in self.pools.items():
            try:
                health_result = await pool.health_check()
                results[name] = health_result
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e)
                }
        
        return results
    
    def get_stats_all(self) -> Dict[str, Any]:
        """Get statistics for all pools"""
        return {
            name: pool.get_stats() 
            for name, pool in self.pools.items()
        }
    
    async def shutdown_all(self):
        """Shutdown all connection pools gracefully"""
        logger.info("Shutting down all connection pools...")
        
        shutdown_tasks = [
            pool.close() for pool in self.pools.values()
        ]
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.pools.clear()
        self._shutdown_event.set()
        logger.info("All connection pools shut down")


# Global connection pool manager
pool_manager = ConnectionPoolManager()