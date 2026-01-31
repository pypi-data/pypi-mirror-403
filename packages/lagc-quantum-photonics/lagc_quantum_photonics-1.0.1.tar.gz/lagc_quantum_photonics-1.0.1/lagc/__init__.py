"""
LAGC: LossAware-GraphCompiler
=============================

CPU 전용 손실 인식 양자 그래프 컴파일러
광자 양자 컴퓨팅 연구를 위한 고성능 시뮬레이션 라이브러리

Features
--------
- **CPU 전용**: GPU 없이 RAM만으로 대규모 시뮬레이션
- **손실 인식**: 실제 광자 손실 모델링 및 자동 그래프 복구
- **메모리 효율**: 재귀적 텐서 슬라이싱으로 RAM 제한 내 처리
- **하드웨어 기반**: 현실적인 노이즈 모델과 에러 완화

Quick Start
-----------
>>> from lagc import LAGC
>>> 
>>> # 시뮬레이터 생성
>>> sim = LAGC(ram_limit_gb=8, hardware='realistic')
>>> 
>>> # 3D RHG 격자 생성
>>> sim.create_lattice('3d_rhg', 5, 5, 5)
>>> 
>>> # 5% 광자 손실 적용
>>> sim.apply_loss(p_loss=0.05)
>>> 
>>> # 시뮬레이션 실행
>>> result = sim.run_simulation()
>>> print(f"Fidelity: {result.fidelity:.4f}")

Modules
-------
- `lagc.core`: 핵심 알고리즘 (그래프 엔진, 텐서 슬라이싱, 복구)
- `lagc.models`: 하드웨어 및 토폴로지 모델
- `lagc.simulation`: 텐서 수축 및 병렬 스케줄링
- `lagc.utils`: 메모리 관리 및 유틸리티

Links
-----
- Documentation: https://lagc.readthedocs.io
- Repository: https://github.com/quantum-dev/lagc
- PyPI: https://pypi.org/project/lagc
"""

__version__ = "1.0.0"
__author__ = "LAGC Research Team"
__email__ = "lagc@quantum-photonics.dev"
__license__ = "MIT"

# =============================================================================
# Main API: Primary user interface
# =============================================================================
from lagc.main import LAGC, SimulationResult, quick_simulation

# =============================================================================
# Core: Fundamental algorithms
# =============================================================================
from lagc.core.graph_engine import StabilizerGraph
from lagc.core.tensor_slicer import TensorSlicer, TensorNetwork
from lagc.core.recovery import LossRecovery, RecoveryResult

# =============================================================================
# Models: Hardware and topology definitions
# =============================================================================
from lagc.models.hardware import HardwareModel, HardwareParams
from lagc.models.topologies import TopologyGenerator

# =============================================================================
# Simulation: Execution engines
# =============================================================================
from lagc.simulation.contraction import TensorContractor, ContractionResult
from lagc.simulation.scheduler import ParallelScheduler

# =============================================================================
# Utils: Helper functions
# =============================================================================
from lagc.utils.memory import MemoryManager, get_memory_stats, get_available_memory

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Main API
    "LAGC",
    "SimulationResult",
    "quick_simulation",
    
    # Core
    "StabilizerGraph",
    "TensorSlicer",
    "TensorNetwork",
    "LossRecovery",
    "RecoveryResult",
    
    # Models
    "HardwareModel",
    "HardwareParams",
    "TopologyGenerator",
    
    # Simulation
    "TensorContractor",
    "ContractionResult",
    "ParallelScheduler",
    
    # Utils
    "MemoryManager",
    "get_memory_stats",
    "get_available_memory",
]


def get_version() -> str:
    """Return the version string."""
    return __version__


def info() -> None:
    """Print LAGC library information."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  LAGC: LossAware-GraphCompiler v{__version__}                      ║
╠══════════════════════════════════════════════════════════════╣
║  CPU 전용 손실 인식 양자 그래프 컴파일러                      ║
║  광자 양자 컴퓨팅 연구를 위한 고성능 시뮬레이션 라이브러리    ║
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
