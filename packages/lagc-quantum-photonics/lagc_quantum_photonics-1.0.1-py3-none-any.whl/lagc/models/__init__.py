"""
LAGC Models Module
==================

Hardware and topology models for quantum photonics simulation:
- hardware: Hardware noise and loss models (JSON-based)
- topologies: Standard lattice generators (3D RHG, 2D Cluster, etc.)
"""

from lagc.models.hardware import HardwareModel
from lagc.models.topologies import TopologyGenerator

__all__ = ["HardwareModel", "TopologyGenerator"]
