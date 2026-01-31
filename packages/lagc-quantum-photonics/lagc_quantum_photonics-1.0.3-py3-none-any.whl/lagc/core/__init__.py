"""
LAGC Core Module
================

Core algorithms for quantum photonics simulation:
- graph_engine: XOR-based graph operations (Algorithm 1)
- tensor_slicer: CPU-optimized slicing engine (Algorithm 2)  
- recovery: Loss recovery and correction logic (Algorithm 3)
"""

from lagc.core.graph_engine import StabilizerGraph, GraphEngine
from lagc.core.tensor_slicer import TensorSlicer
from lagc.core.recovery import LossRecovery

__all__ = ["StabilizerGraph", "GraphEngine", "TensorSlicer", "LossRecovery"]

