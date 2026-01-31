"""
LAGC: LossAware-GraphCompiler
=============================

A CPU-only, loss-aware quantum graph compiler for photonic quantum computing.

Features
--------
- **CPU Only**: No GPU required - runs on standard hardware
- **Loss Aware**: Realistic photon loss modeling with automatic graph recovery
- **Memory Efficient**: Recursive tensor slicing within RAM limits
- **Hardware Based**: Realistic noise models and error mitigation

Quick Start
-----------
>>> from lagc import LAGC
>>> 
>>> # Create simulator
>>> sim = LAGC(ram_limit_gb=8, hardware='realistic')
>>> 
>>> # Build 3D RHG lattice
>>> sim.create_lattice('3d_rhg', 5, 5, 5)
>>> 
>>> # Apply 5% photon loss
>>> sim.apply_loss(p_loss=0.05)
>>> 
>>> # Run simulation
>>> result = sim.run_simulation()
>>> print(f"Fidelity: {result.fidelity:.4f}")

Links
-----
- Documentation: https://lagc.readthedocs.io
- Repository: https://github.com/quantum-dev/lagc
- PyPI: https://pypi.org/project/lagc
"""

# =============================================================================
# Dependency Check (Item 3)
# =============================================================================
def _check_dependencies():
    """Verify required dependencies are installed."""
    missing = []
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy>=1.21.0")
    
    try:
        import scipy
    except ImportError:
        missing.append("scipy>=1.7.0")
    
    try:
        import opt_einsum
    except ImportError:
        missing.append("opt-einsum>=3.3.0")
    
    try:
        import networkx
    except ImportError:
        missing.append("networkx>=2.6.0")
    
    if missing:
        raise ImportError(
            f"LAGC requires the following packages: {', '.join(missing)}.\n"
            f"Install with: pip install {' '.join(missing)}"
        )

_check_dependencies()

# =============================================================================
# Version Info
# =============================================================================
__version__ = "1.0.5"
__author__ = "LAGC Research Team"
__email__ = "lagc@quantum-photonics.dev"
__license__ = "MIT"

# =============================================================================
# Primary API (User-facing)
# =============================================================================
from lagc.main import LAGC, SimulationResult, quick_simulation

# =============================================================================
# Core Classes (Power users)
# =============================================================================
from lagc.core import (
    GraphEngine,
    StabilizerGraph,
    LossRecovery,
    RecoveryManager,  # Backward compatibility alias
    TensorSlicer,
)

# =============================================================================
# Models
# =============================================================================
from lagc.models import HardwareModel, HardwareParams, TopologyGenerator

# =============================================================================
# Public API (Item 5 - Simplified)
# =============================================================================
__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # === Primary API (most users only need these) ===
    "LAGC",
    "SimulationResult",
    "quick_simulation",
    
    # === Core Classes (power users) ===
    "GraphEngine",
    "StabilizerGraph",
    "LossRecovery",
    
    # === Models ===
    "HardwareModel",
    "HardwareParams",
    "TopologyGenerator",
    
    # === Utilities ===
    "info",
    "get_version",
]

# Note: Internal classes like TensorContractor, ParallelScheduler, 
# ContractionResult, TensorNetwork are NOT exposed at top level.
# Access via: from lagc.simulation import TensorContractor


def get_version() -> str:
    """Return the version string."""
    return __version__


def info() -> None:
    """Print LAGC library information."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LAGC: LossAware-GraphCompiler v{__version__}                      ║
╠══════════════════════════════════════════════════════════════╣
║  CPU-only loss-aware quantum graph compiler                  ║
║  For photonic quantum computing simulation                   ║
╠══════════════════════════════════════════════════════════════╣
║  Repository: https://github.com/quantum-dev/lagc             ║
║  Docs: https://lagc.readthedocs.io                           ║
╚══════════════════════════════════════════════════════════════╝

Quick Start:
  >>> from lagc import LAGC
  >>> sim = LAGC(ram_limit_gb=8, hardware='realistic')
  >>> sim.create_lattice('3d_rhg', 5, 5, 5)
  >>> sim.apply_loss(p_loss=0.05)
  >>> result = sim.run_simulation()

Available topologies: 3d_rhg, 2d_cluster, linear, ghz, ring, complete
Hardware presets: ideal, realistic, near_term, experimental, future
""")
