"""
RTX GPU Optimization for NC1709 Training
Automatically adjusts batch sizes and parameters for RTX 3090/4090
"""

import torch
from typing import Dict, Any


class RTXOptimizer:
    """Optimizes training parameters for RTX GPUs"""
    
    # RTX GPU specifications
    RTX_SPECS = {
        "RTX 3090": {"vram_gb": 24, "compute_capability": 8.6},
        "RTX 4090": {"vram_gb": 24, "compute_capability": 8.9},
        "RTX 3080": {"vram_gb": 10, "compute_capability": 8.6},
        "RTX 4080": {"vram_gb": 16, "compute_capability": 8.9},
    }
    
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect RTX GPU type and specs"""
        if not torch.cuda.is_available():
            return {"name": "CPU", "vram_gb": 0}
            
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        return {
            "name": gpu_name,
            "vram_gb": vram_gb,
            "device_count": torch.cuda.device_count()
        }
    
    def optimize_training_params(self, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize training parameters for RTX GPU"""
        vram_gb = self.gpu_info["vram_gb"]
        
        # Optimize based on VRAM
        if vram_gb >= 24:  # RTX 3090/4090
            optimized = {
                **base_params,
                "batch_size": 4,
                "gradient_accumulation_steps": 8,
                "max_length": 2048,
                "learning_rate": 2e-4,
            }
        elif vram_gb >= 16:  # RTX 4080
            optimized = {
                **base_params,
                "batch_size": 2,
                "gradient_accumulation_steps": 16,
                "max_length": 1536,
                "learning_rate": 1.5e-4,
            }
        elif vram_gb >= 10:  # RTX 3080
            optimized = {
                **base_params,
                "batch_size": 1,
                "gradient_accumulation_steps": 32,
                "max_length": 1024,
                "learning_rate": 1e-4,
            }
        else:
            # Fallback for smaller GPUs
            optimized = {
                **base_params,
                "batch_size": 1,
                "gradient_accumulation_steps": 64,
                "max_length": 512,
                "learning_rate": 5e-5,
            }
        
        # Ensure effective batch size remains consistent
        effective_batch = optimized["batch_size"] * optimized["gradient_accumulation_steps"]
        optimized["effective_batch_size"] = effective_batch
        
        return optimized
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        if not torch.cuda.is_available():
            return {"used_gb": 0, "total_gb": 0, "utilization": 0}
            
        memory_used = torch.cuda.memory_allocated(0) / (1024**3)
        memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        return {
            "used_gb": memory_used,
            "total_gb": memory_total,
            "utilization": (memory_used / memory_total) * 100
        }