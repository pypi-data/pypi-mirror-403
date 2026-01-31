"""
LAGC Core Module
================

Core algorithms for quantum photonics simulation:
- graph_engine: XOR-based graph operations (Algorithm 1)
- tensor_slicer: CPU-optimized slicing engine (Algorithm 2)  
- recovery: Loss recovery and correction logic (Algorithm 3)
"""

from .graph_engine import GraphEngine, StabilizerGraph
from .tensor_slicer import TensorSlicer, TensorNetwork
from .recovery import LossRecovery, RecoveryResult, RecoveryManager

__all__ = [
    "GraphEngine",
    "StabilizerGraph", 
    "TensorSlicer",
    "TensorNetwork",
    "LossRecovery",
    "RecoveryResult",
    "RecoveryManager",  # Backward compatibility alias
]
