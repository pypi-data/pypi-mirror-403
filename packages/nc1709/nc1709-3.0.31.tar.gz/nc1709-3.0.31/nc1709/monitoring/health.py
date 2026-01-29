"""
NC1709 Enhanced Health Checking System

Comprehensive health checks for all system components.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import httpx

from .metrics import metrics_collector, OLLAMA_HEALTH


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check definition"""
    
    def __init__(
        self,
        name: str,
        check_function: Callable,
        timeout: float = 5.0,
        critical: bool = True,
        description: Optional[str] = None
    ):
        self.name = name
        self.check_function = check_function
        self.timeout = timeout
        self.critical = critical  # If true, failure marks whole system as unhealthy
        self.description = description or f"Health check for {name}"
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_check_time: Optional[float] = None
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the health check with timeout"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.check_function(),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            check_result = {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "details": result if isinstance(result, dict) else {"result": result},
                "critical": self.critical
            }
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            check_result = {
                "status": HealthStatus.UNHEALTHY.value,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "error": f"Health check timeout after {self.timeout}s",
                "critical": self.critical
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            check_result = {
                "status": HealthStatus.UNHEALTHY.value,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "error": str(e),
                "critical": self.critical
            }
        
        self.last_result = check_result
        self.last_check_time = time.time()
        
        return check_result


class HealthChecker:
    """
    Comprehensive health checking system for NC1709.
    
    Monitors:
    - Ollama service connectivity and model availability
    - System resources (memory, disk, CPU)
    - Database connections (if applicable)
    - External service dependencies
    - Application-specific health indicators
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.checks: Dict[str, HealthCheck] = {}
        self.startup_time = time.time()
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        
        # Ollama service check
        self.register_check(
            "ollama_connection",
            self._check_ollama_connection,
            timeout=10.0,
            critical=True,
            description="Ollama service connectivity"
        )
        
        # Ollama model availability
        self.register_check(
            "ollama_models",
            self._check_ollama_models,
            timeout=15.0,
            critical=True,
            description="NC1709 model availability"
        )
        
        # System memory
        self.register_check(
            "system_memory",
            self._check_system_memory,
            timeout=2.0,
            critical=False,
            description="System memory usage"
        )
        
        # System disk space
        self.register_check(
            "system_disk",
            self._check_system_disk,
            timeout=2.0,
            critical=False,
            description="System disk usage"
        )
        
        # Application metrics
        self.register_check(
            "application_metrics",
            self._check_application_metrics,
            timeout=1.0,
            critical=False,
            description="Application metrics collection"
        )
    
    def register_check(
        self,
        name: str,
        check_function: Callable,
        timeout: float = 5.0,
        critical: bool = True,
        description: Optional[str] = None
    ):
        """Register a new health check"""
        self.checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            timeout=timeout,
            critical=critical,
            description=description
        )
    
    async def check_all(self) -> Dict[str, Any]:
        """Execute all health checks and return comprehensive status"""
        start_time = time.time()
        results = {}
        
        # Execute all checks concurrently
        check_tasks = {
            name: check.execute()
            for name, check in self.checks.items()
        }
        
        completed_checks = await asyncio.gather(
            *check_tasks.values(),
            return_exceptions=True
        )
        
        # Process results
        overall_status = HealthStatus.HEALTHY
        critical_failures = []
        
        for (name, check), result in zip(self.checks.items(), completed_checks):
            if isinstance(result, Exception):
                result = {
                    "status": HealthStatus.UNKNOWN.value,
                    "error": str(result),
                    "critical": check.critical
                }
            
            results[name] = result
            
            # Determine overall status
            if result["status"] == HealthStatus.UNHEALTHY.value:
                if result.get("critical", False):
                    critical_failures.append(name)
                    overall_status = HealthStatus.UNHEALTHY
                elif overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Calculate summary
        total_execution_time = time.time() - start_time
        uptime = time.time() - self.startup_time
        
        health_summary = {
            "status": overall_status.value,
            "timestamp": time.time(),
            "uptime_seconds": uptime,
            "total_check_time": total_execution_time,
            "critical_failures": critical_failures,
            "checks_passed": sum(1 for r in results.values() if r["status"] == HealthStatus.HEALTHY.value),
            "checks_total": len(results),
            "checks": results
        }
        
        # Update metrics
        metrics_collector.update_system_metrics()
        
        return health_summary
    
    async def check_single(self, check_name: str) -> Dict[str, Any]:
        """Execute a single health check by name"""
        if check_name not in self.checks:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": f"Health check '{check_name}' not found",
                "timestamp": time.time()
            }
        
        return await self.checks[check_name].execute()
    
    # Individual health check implementations
    
    async def _check_ollama_connection(self) -> Dict[str, Any]:
        """Check Ollama service connectivity"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                
                response_time = time.time() - start_time
                
                # Update metrics
                metrics_collector.record_ollama_health(True, response_time)
                
                return {
                    "connected": True,
                    "response_time": response_time,
                    "ollama_url": self.ollama_url,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            # Update metrics
            metrics_collector.record_ollama_health(False)
            
            raise Exception(f"Ollama connection failed: {str(e)}")
    
    async def _check_ollama_models(self) -> Dict[str, Any]:
        """Check NC1709 model availability in Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                
                models_data = response.json()
                models = models_data.get("models", [])
                
                nc1709_models = [
                    model for model in models 
                    if "qwen2.5-coder" in model.get("name", "").lower()
                ]
                
                if not nc1709_models:
                    raise Exception("NC1709 model (qwen2.5-coder) not found in Ollama")
                
                return {
                    "models_available": len(nc1709_models),
                    "total_models": len(models),
                    "nc1709_models": [model.get("name") for model in nc1709_models],
                    "model_sizes": [model.get("size") for model in nc1709_models]
                }
                
        except Exception as e:
            raise Exception(f"Model availability check failed: {str(e)}")
    
    async def _check_system_memory(self) -> Dict[str, Any]:
        """Check system memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # Consider warning if memory usage > 80%, critical if > 95%
            if memory.percent > 95:
                raise Exception(f"Critical memory usage: {memory.percent}%")
            
            return {
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "status": "warning" if memory.percent > 80 else "normal"
            }
            
        except ImportError:
            return {"status": "unknown", "reason": "psutil not available"}
    
    async def _check_system_disk(self) -> Dict[str, Any]:
        """Check system disk space"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            # Consider warning if disk usage > 85%, critical if > 95%
            if usage_percent > 95:
                raise Exception(f"Critical disk usage: {usage_percent:.1f}%")
            
            return {
                "usage_percent": round(usage_percent, 1),
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "status": "warning" if usage_percent > 85 else "normal"
            }
            
        except ImportError:
            return {"status": "unknown", "reason": "psutil not available"}
    
    async def _check_application_metrics(self) -> Dict[str, Any]:
        """Check application metrics collection"""
        try:
            summary = metrics_collector.get_summary()
            
            # Basic validation that metrics are working
            if "uptime_seconds" not in summary:
                raise Exception("Metrics collector not functioning properly")
            
            return {
                "metrics_collector": "functional",
                "uptime_seconds": summary.get("uptime_seconds", 0),
                "total_requests": summary.get("total_requests", 0),
                "active_connections": summary.get("active_connections", 0)
            }
            
        except Exception as e:
            raise Exception(f"Metrics collection check failed: {str(e)}")


# Global health checker instance
health_checker = HealthChecker()