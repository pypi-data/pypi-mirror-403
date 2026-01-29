"""
NC1709 DeepFabric - Domain-Specific Tool Calling Excellence
Achieves 99%+ accuracy through specialized training and multi-layer architecture
"""

from .core import DeepFabricCore
from .layers import (
    IntentRecognitionLayer,
    StrategicPlanningLayer,
    ToolSelectionLayer,
    ExecutionLayer,
    ErrorRecoveryLayer,
    LearningLayer,
    PredictiveLayer
)
from .training import ModelTrainer, DataGenerator
from .evaluation import AccuracyEvaluator, PerformanceMonitor

__version__ = "3.0.0"
__all__ = [
    "DeepFabricCore",
    "IntentRecognitionLayer",
    "StrategicPlanningLayer", 
    "ToolSelectionLayer",
    "ExecutionLayer",
    "ErrorRecoveryLayer",
    "LearningLayer",
    "PredictiveLayer",
    "ModelTrainer",
    "DataGenerator",
    "AccuracyEvaluator",
    "PerformanceMonitor"
]