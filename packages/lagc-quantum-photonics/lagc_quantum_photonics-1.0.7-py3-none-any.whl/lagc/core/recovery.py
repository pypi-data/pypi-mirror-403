"""
Recovery: 광자 유실 복구 및 에러 완화
=====================================

v1.0.7 - 간소화된 복구 클래스
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from .graph_engine import GraphEngine

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """복구 결과 컨테이너"""
    raw_amplitude: complex
    corrected_amplitude: complex
    fidelity: float
    log_probability: float
    n_corrections: int
    metadata: Dict[str, Any]


class LossRecovery:
    """
    광자 유실 복구 매니저
    
    Examples:
        >>> from lagc.core import GraphEngine, LossRecovery
        >>> engine = GraphEngine(10)
        >>> recovery = LossRecovery(engine)
        >>> recovery.handle_loss(5)
    """
    
    def __init__(
        self,
        engine: Optional['GraphEngine'] = None,
        p_gate: float = 0.01,
        p_detection: float = 0.05,
        p_source: float = 0.02,
    ):
        """
        복구 매니저 초기화
        
        Args:
            engine: GraphEngine 인스턴스 (선택)
            p_gate: 게이트 에러 확률
            p_detection: 검출 에러 확률
            p_source: 소스 에러 확률
        """
        self.engine = engine
        self.p_gate = p_gate
        self.p_detection = p_detection
        self.p_source = p_source
        
        self.loss_paths: List[float] = []
        self.n_gates: int = 0
        self.n_detections: int = 0
    
    def handle_loss(self, lost_node: int) -> None:
        """
        [핵심] 특정 노드 유실 시 그래프 수술 수행
        
        Args:
            lost_node: 유실된 노드 인덱스
        """
        if self.engine is None:
            raise ValueError("No engine set. Pass engine to __init__ or set self.engine")
        
        neighbors = self.engine.get_neighbors(lost_node)
        if len(neighbors) > 0:
            # 첫 번째 이웃을 기준으로 그래프 변환
            self.engine.local_complementation(neighbors[0])
        
        # 유실된 노드의 모든 연결 제거
        self.engine.adj[lost_node, :] = 0
        self.engine.adj[:, lost_node] = 0
        
        logger.debug(f"Handled loss at node {lost_node}")
    
    def handle_multiple_losses(self, lost_nodes: List[int]) -> int:
        """여러 노드 손실 처리"""
        count = 0
        for node in sorted(lost_nodes, reverse=True):
            self.handle_loss(node)
            count += 1
        return count
    
    def register_gate(self, n: int = 1) -> None:
        """게이트 연산 등록"""
        self.n_gates += n
    
    def register_loss_path(self, loss_probability: float) -> None:
        """손실 경로 등록"""
        self.loss_paths.append(loss_probability)
    
    def estimate_fidelity(
        self,
        n_qubits: Optional[int] = None,
        custom_gate_count: Optional[int] = None,
    ) -> float:
        """
        충실도 추정
        
        F_final = (1-p_gate)^n_gates × (1-p_det)^n_det × exp(-Σ loss)
        """
        n_gates = custom_gate_count if custom_gate_count is not None else self.n_gates
        
        gate_fidelity = (1 - self.p_gate) ** n_gates
        detection_fidelity = (1 - self.p_detection) ** self.n_detections
        source_fidelity = 1 - self.p_source
        
        if self.loss_paths:
            loss_fidelity = np.exp(-sum(self.loss_paths))
        else:
            loss_fidelity = 1.0
        
        fidelity = gate_fidelity * detection_fidelity * source_fidelity * loss_fidelity
        return float(np.clip(fidelity, 0, 1))
    
    def mitigate_errors(
        self,
        raw_result: complex,
        n_qubits: int,
        loss_rate: float = 0.0
    ) -> RecoveryResult:
        """에러 완화 적용"""
        estimated_gates = n_qubits * 2
        self.register_gate(estimated_gates)
        self.register_loss_path(loss_rate * n_qubits)
        
        fidelity = self.estimate_fidelity()
        corrected_amplitude = raw_result * np.sqrt(fidelity)
        log_prob = np.log(np.abs(raw_result) ** 2 + 1e-300) + np.log(fidelity + 1e-300)
        
        return RecoveryResult(
            raw_amplitude=raw_result,
            corrected_amplitude=corrected_amplitude,
            fidelity=fidelity,
            log_probability=float(log_prob),
            n_corrections=estimated_gates,
            metadata={'n_qubits': n_qubits, 'loss_rate': loss_rate}
        )
    
    def reset(self) -> None:
        """상태 초기화"""
        self.loss_paths = []
        self.n_gates = 0
        self.n_detections = 0
    
    @classmethod
    def from_hardware_model(cls, hardware_params: Dict[str, Any]) -> 'LossRecovery':
        """하드웨어 모델에서 생성"""
        return cls(
            p_gate=hardware_params.get('gate_error', 0.01),
            p_detection=hardware_params.get('detection_error', 0.05),
            p_source=hardware_params.get('source_error', 0.02),
        )


# =============================================================================
# 하위 호환성 별칭
# =============================================================================
RecoveryManager = LossRecovery
SimpleLossHandler = LossRecovery
