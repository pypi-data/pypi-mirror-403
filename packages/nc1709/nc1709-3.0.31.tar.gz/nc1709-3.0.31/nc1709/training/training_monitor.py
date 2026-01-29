"""
Training Monitor for NC1709
Real-time monitoring of training progress
"""

import time
import logging
from typing import Dict, Any


class TrainingMonitor:
    """Monitor training progress and metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log training metrics"""
        elapsed = time.time() - self.start_time
        self.logger.info(f"Training metrics at {elapsed:.1f}s: {metrics}")
        
    def check_progress(self) -> Dict[str, Any]:
        """Check current training progress"""
        elapsed = time.time() - self.start_time
        return {
            "elapsed_time": elapsed,
            "status": "running"
        }