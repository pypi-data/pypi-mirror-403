"""
Graph Engine: XOR 기반 고속 퀀텀 그래프 연산 엔진
================================================

v1.0.7 - 간소화된 단일 클래스 구현
"""

import numpy as np
from typing import Optional, Set
import logging

logger = logging.getLogger(__name__)


class GraphEngine:
    """
    XOR 기반 고속 퀀텀 그래프 연산 엔진
    
    메모리 효율적인 numpy 배열 기반 구현.
    
    Example:
        >>> engine = GraphEngine(10)
        >>> engine.add_edge(0, 1)
        >>> engine.add_edge(1, 2)
        >>> engine.local_complementation(1)
    """
    
    def __init__(self, n_qubits: int):
        """
        그래프 엔진 초기화
        
        Args:
            n_qubits: 큐비트 수
        """
        self.n = n_qubits
        self.n_qubits = n_qubits  # 호환성을 위한 별칭
        # 메모리 효율을 위해 int8 사용
        self.adj = np.zeros((n_qubits, n_qubits), dtype=np.int8)
        self.node_states = np.ones(n_qubits, dtype=np.int8)
        self.lost_nodes: Set[int] = set()
        
        logger.debug(f"GraphEngine initialized with {n_qubits} qubits")
    
    def add_edge(self, u: int, v: int) -> None:
        """
        [핵심] 두 큐비트 사이에 CZ 게이트(얽힘) 적용
        
        Args:
            u: 첫 번째 큐비트 인덱스
            v: 두 번째 큐비트 인덱스
        """
        if 0 <= u < self.n and 0 <= v < self.n and u != v:
            self.adj[u, v] = self.adj[v, u] = 1
    
    def remove_edge(self, u: int, v: int) -> None:
        """엣지 제거"""
        if 0 <= u < self.n and 0 <= v < self.n:
            self.adj[u, v] = self.adj[v, u] = 0
    
    def has_edge(self, u: int, v: int) -> bool:
        """엣지 존재 여부 확인"""
        return bool(self.adj[u, v])
    
    def get_neighbors(self, node: int) -> np.ndarray:
        """
        특정 노드에 연결된 이웃 반환
        
        Args:
            node: 노드 인덱스
            
        Returns:
            이웃 노드 인덱스 배열
        """
        return np.where(self.adj[node] == 1)[0]
    
    def local_complementation(self, a: int) -> None:
        """
        Algorithm 1: 그래프 토폴로지 변환 (τ_a)
        
        노드 a의 이웃들 사이의 연결 상태를 XOR 반전
        
        Args:
            a: 중심 노드 인덱스
        """
        neighbors = self.get_neighbors(a)
        if len(neighbors) < 2:
            return
        sub_idx = np.ix_(neighbors, neighbors)
        self.adj[sub_idx] = 1 - self.adj[sub_idx]
        np.fill_diagonal(self.adj, 0)
        
        logger.debug(f"Local complementation at node {a}")
    
    def apply_loss_mask(self, p_loss: float, seed: Optional[int] = None) -> np.ndarray:
        """
        광자 손실 적용
        
        Args:
            p_loss: 손실 확률 (0~1)
            seed: 랜덤 시드
            
        Returns:
            손실된 노드 인덱스 배열
        """
        if seed is not None:
            np.random.seed(seed)
        
        survival = np.random.binomial(1, 1 - p_loss, self.n)
        self.node_states = survival.astype(np.int8)
        
        lost_indices = np.where(self.node_states == 0)[0]
        self.lost_nodes = set(lost_indices.tolist())
        
        logger.info(f"Applied loss p={p_loss}: {len(self.lost_nodes)}/{self.n} nodes lost")
        
        return lost_indices
    
    def recover_from_loss(self) -> int:
        """
        손실된 노드에 대해 그래프 수술 수행
        
        Returns:
            복구 연산 수행 횟수
        """
        count = 0
        for node in sorted(self.lost_nodes, reverse=True):
            neighbors = self.get_neighbors(node)
            if len(neighbors) > 0:
                self.local_complementation(neighbors[0])
            # 손실 노드의 모든 연결 제거
            self.adj[node, :] = 0
            self.adj[:, node] = 0
            count += 1
        
        logger.info(f"Recovery complete: {count} operations")
        return count
    
    def get_edge_count(self) -> int:
        """엣지 수 반환"""
        return int(np.sum(self.adj) // 2)
    
    def get_active_subgraph(self) -> 'GraphEngine':
        """활성 노드만 포함하는 서브그래프 반환"""
        active_indices = np.where(self.node_states == 1)[0]
        n_active = len(active_indices)
        
        subgraph = GraphEngine(n_active)
        
        # 인덱스 매핑
        index_map = {old: new for new, old in enumerate(active_indices)}
        
        for i, old_i in enumerate(active_indices):
            for old_j in self.get_neighbors(old_i):
                if old_j in index_map:
                    j = index_map[old_j]
                    if j > i:
                        subgraph.add_edge(i, j)
        
        return subgraph
    
    def get_graph_info(self) -> dict:
        """그래프 상태 정보 반환"""
        return {
            'n_qubits': self.n,
            'n_active': int(self.node_states.sum()),
            'n_lost': len(self.lost_nodes),
            'n_edges': self.get_edge_count(),
        }
    
    def copy(self) -> 'GraphEngine':
        """그래프 복사"""
        new_graph = GraphEngine(self.n)
        new_graph.adj = self.adj.copy()
        new_graph.node_states = self.node_states.copy()
        new_graph.lost_nodes = self.lost_nodes.copy()
        return new_graph
    
    def __repr__(self) -> str:
        info = self.get_graph_info()
        return f"GraphEngine(n={info['n_qubits']}, edges={info['n_edges']}, active={info['n_active']})"


# =============================================================================
# 별칭 설정 (하위 호환성)
# =============================================================================
StabilizerGraph = GraphEngine
SimpleGraphEngine = GraphEngine
