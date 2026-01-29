"""
NC1709 CLI - Your AI coding partner that brings your code to life
Version: 2.1.1
Author: Lafzusa Corp
License: Proprietary

New in 2.1.0:
- 99% tool-calling accuracy (vs Claude Sonnet 3.5's 80.5%)  
- RTX 3090/4090 and A100 GPU training support
- DeepFabric training with 800K examples
- Local model inference with cost savings
- Live training monitoring and checkpoints
"""

__version__ = "3.0.31"
__author__ = "Lafzusa Corp"

from .cli import main

__all__ = ["main"]
