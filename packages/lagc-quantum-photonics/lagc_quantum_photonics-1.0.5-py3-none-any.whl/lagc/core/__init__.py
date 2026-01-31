"""
LAGC Core Module
================

Core algorithms for quantum photonics simulation:
- graph_engine: XOR-based graph operations (Algorithm 1)
- tensor_slicer: CPU-optimized slicing engine (Algorithm 2)  
- recovery: Loss recovery and correction logic (Algorithm 3)
"""

from .graph_engine import (
    GraphEngine,
    StabilizerGraph, 
    SimpleGraphEngine,
)
from .tensor_slicer import TensorSlicer, TensorNetwork
from .recovery import (
    LossRecovery,
    RecoveryResult,
    RecoveryManager,       # Backward compatibility alias
    SimpleLossHandler,     # Simple API
)

__all__ = [
    # Main classes
    "GraphEngine",
    "StabilizerGraph",
    "SimpleGraphEngine",
    "TensorSlicer",
    "TensorNetwork",
    "LossRecovery",
    "RecoveryResult",
    "SimpleLossHandler",
    # Aliases
    "RecoveryManager",
]
