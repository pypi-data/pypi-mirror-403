"""
Graph Engine: XOR-based Graph Operations (Algorithm 1)
=======================================================

Implements efficient graph state manipulation using XOR operations on sparse matrices.
Manages millions of qubits with O(1) memory overhead for local complementation.

Key Operations:
- Local Complementation (τ_a): Inverts edges between neighbors of a node
- Loss Masking: Probabilistic node survival determination
- Graph Surgery: Topological defect correction

Reference:
    Raussendorf, R., Harrington, J., & Goyal, K. (2007). 
    Topological fault-tolerance in cluster state quantum computation.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from typing import Optional, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class StabilizerGraph:
    """
    Manages stabilizer graph state using sparse matrix representation.
    
    The graph state |G⟩ is represented by its adjacency matrix where:
    - Nodes represent qubits
    - Edges represent entanglement (CZ gates applied)
    
    Attributes:
        n_qubits: Number of qubits in the graph
        adj_matrix: Sparse adjacency matrix (scipy.sparse.csr_matrix)
        node_states: Array indicating node status (0=lost, 1=active)
        lost_nodes: Set of indices of lost nodes
    """
    
    def __init__(self, n_qubits: int):
        """
        Initialize an empty stabilizer graph.
        
        Args:
            n_qubits: Number of qubits in the graph state
        """
        self.n_qubits = n_qubits
        # Use lil_matrix for efficient construction, convert to csr later
        self._adj_lil = lil_matrix((n_qubits, n_qubits), dtype=np.int8)
        self._adj_csr: Optional[csr_matrix] = None
        self.node_states = np.ones(n_qubits, dtype=np.int8)
        self.lost_nodes: Set[int] = set()
        self._finalized = False
        
        logger.debug(f"Created StabilizerGraph with {n_qubits} qubits")
    
    @property
    def adj_matrix(self) -> csr_matrix:
        """Returns the CSR format adjacency matrix."""
        if not self._finalized:
            self._finalize()
        return self._adj_csr
    
    def _finalize(self) -> None:
        """Convert LIL matrix to CSR for efficient operations."""
        self._adj_csr = self._adj_lil.tocsr()
        self._finalized = True
        logger.debug("Adjacency matrix finalized to CSR format")
    
    def add_edge(self, i: int, j: int) -> None:
        """
        Add an edge between nodes i and j (apply CZ gate).
        
        Args:
            i: First node index
            j: Second node index
        """
        if i == j:
            return
        self._adj_lil[i, j] = 1
        self._adj_lil[j, i] = 1
        self._finalized = False
    
    def remove_edge(self, i: int, j: int) -> None:
        """
        Remove an edge between nodes i and j.
        
        Args:
            i: First node index
            j: Second node index
        """
        self._adj_lil[i, j] = 0
        self._adj_lil[j, i] = 0
        self._finalized = False
    
    def has_edge(self, i: int, j: int) -> bool:
        """Check if edge exists between nodes i and j."""
        if self._finalized:
            return bool(self._adj_csr[i, j])
        return bool(self._adj_lil[i, j])
    
    def get_neighbors(self, node_idx: int) -> np.ndarray:
        """
        Get all neighbors of a node.
        
        Args:
            node_idx: Index of the node
            
        Returns:
            Array of neighbor indices
        """
        if not self._finalized:
            self._finalize()
        return self._adj_csr[node_idx].indices.copy()
    
    def local_complementation(self, node_idx: int) -> None:
        """
        Apply local complementation τ_a at node a.
        
        This operation inverts all edges between neighbors of node_idx:
        - If neighbors i and j are connected, disconnect them
        - If neighbors i and j are not connected, connect them
        
        Mathematical operation: adj_matrix[N(a), N(a)] ^= 1
        
        Args:
            node_idx: Index of the node to perform local complementation on
        """
        if not self._finalized:
            self._finalize()
            
        neighbors = self.get_neighbors(node_idx)
        n_neighbors = len(neighbors)
        
        if n_neighbors < 2:
            # No edges to invert with less than 2 neighbors
            return
        
        logger.debug(f"Local complementation at node {node_idx} with {n_neighbors} neighbors")
        
        # Convert back to lil for efficient modification
        if self._finalized:
            self._adj_lil = self._adj_csr.tolil()
        
        # XOR operation on submatrix: invert edges between all pairs of neighbors
        for i in range(n_neighbors):
            for j in range(i + 1, n_neighbors):
                ni, nj = neighbors[i], neighbors[j]
                # XOR: 1 -> 0, 0 -> 1
                current = self._adj_lil[ni, nj]
                new_val = 1 - current
                self._adj_lil[ni, nj] = new_val
                self._adj_lil[nj, ni] = new_val
        
        self._finalized = False
    
    def fast_xor_update(self, node_idx: int) -> None:
        """
        CPU-optimized XOR update for local complementation.
        
        Alias for local_complementation with optimized implementation.
        Uses numpy vectorization where possible.
        
        Args:
            node_idx: Index of the node
        """
        if not self._finalized:
            self._finalize()
        
        neighbors = self.get_neighbors(node_idx)
        n_neighbors = len(neighbors)
        
        if n_neighbors < 2:
            return
        
        # Extract submatrix for neighbors
        submatrix = self._adj_csr[neighbors][:, neighbors].toarray()
        
        # XOR with all-ones matrix (except diagonal)
        ones = np.ones((n_neighbors, n_neighbors), dtype=np.int8)
        np.fill_diagonal(ones, 0)
        submatrix = (submatrix + ones) % 2
        
        # Update back to main matrix
        self._adj_lil = self._adj_csr.tolil()
        for i, ni in enumerate(neighbors):
            for j, nj in enumerate(neighbors):
                if i != j:
                    self._adj_lil[ni, nj] = submatrix[i, j]
        
        self._finalized = False
    
    def apply_loss_mask(self, p_loss: float, seed: Optional[int] = None) -> np.ndarray:
        """
        Apply random photon loss to nodes using binomial distribution.
        
        Each node survives independently with probability (1 - p_loss).
        
        Args:
            p_loss: Probability of losing each photon (0 to 1)
            seed: Random seed for reproducibility
            
        Returns:
            Array of lost node indices
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Each node survives with probability (1 - p_loss)
        # survival = 1 means active, survival = 0 means lost
        survival = np.random.binomial(1, 1 - p_loss, self.n_qubits)
        self.node_states = survival.astype(np.int8)
        
        # Track lost nodes
        lost_indices = np.where(self.node_states == 0)[0]
        self.lost_nodes = set(lost_indices.tolist())
        
        logger.info(f"Applied loss with p={p_loss}: {len(self.lost_nodes)}/{self.n_qubits} nodes lost")
        
        return lost_indices
    
    def recover_from_loss(self) -> int:
        """
        Perform graph surgery to recover from photon loss.
        
        For each lost node, apply local complementation to correct
        topological defects in the graph structure.
        
        Returns:
            Number of recovery operations performed
        """
        recovery_count = 0
        lost_nodes_sorted = sorted(self.lost_nodes, reverse=True)
        
        for node_idx in lost_nodes_sorted:
            # Apply local complementation at lost node
            self.local_complementation(node_idx)
            recovery_count += 1
            
            # Mark edges to this node for removal
            if not self._finalized:
                self._finalize()
            
            neighbors = self.get_neighbors(node_idx)
            self._adj_lil = self._adj_csr.tolil()
            
            # Remove all edges connected to lost node
            for neighbor in neighbors:
                self._adj_lil[node_idx, neighbor] = 0
                self._adj_lil[neighbor, node_idx] = 0
            
            self._finalized = False
        
        logger.info(f"Recovery complete: {recovery_count} operations performed")
        return recovery_count
    
    def get_active_subgraph(self) -> 'StabilizerGraph':
        """
        Extract subgraph containing only active (non-lost) nodes.
        
        Returns:
            New StabilizerGraph with only active nodes
        """
        active_indices = np.where(self.node_states == 1)[0]
        n_active = len(active_indices)
        
        subgraph = StabilizerGraph(n_active)
        
        if not self._finalized:
            self._finalize()
        
        # Map old indices to new indices
        index_map = {old: new for new, old in enumerate(active_indices)}
        
        # Copy edges between active nodes
        for i, old_i in enumerate(active_indices):
            neighbors = self.get_neighbors(old_i)
            for old_j in neighbors:
                if old_j in index_map:
                    j = index_map[old_j]
                    if j > i:  # Add each edge once
                        subgraph.add_edge(i, j)
        
        subgraph._finalize()
        return subgraph
    
    def get_edge_count(self) -> int:
        """Return the number of edges in the graph."""
        if not self._finalized:
            self._finalize()
        return self._adj_csr.nnz // 2
    
    def get_degree(self, node_idx: int) -> int:
        """Return the degree (number of neighbors) of a node."""
        return len(self.get_neighbors(node_idx))
    
    def get_graph_info(self) -> dict:
        """
        Get summary information about the graph state.
        
        Returns:
            Dictionary with graph statistics
        """
        if not self._finalized:
            self._finalize()
        
        active_count = int(self.node_states.sum())
        
        return {
            'n_qubits': self.n_qubits,
            'n_active': active_count,
            'n_lost': len(self.lost_nodes),
            'n_edges': self.get_edge_count(),
            'sparsity': 1 - (self._adj_csr.nnz / (self.n_qubits ** 2)),
            'memory_bytes': self._adj_csr.data.nbytes + self._adj_csr.indices.nbytes + self._adj_csr.indptr.nbytes
        }
    
    def copy(self) -> 'StabilizerGraph':
        """Create a deep copy of the graph."""
        new_graph = StabilizerGraph(self.n_qubits)
        if self._finalized:
            new_graph._adj_csr = self._adj_csr.copy()
            new_graph._adj_lil = new_graph._adj_csr.tolil()
            new_graph._finalized = True
        else:
            new_graph._adj_lil = self._adj_lil.copy()
            new_graph._finalized = False
        new_graph.node_states = self.node_states.copy()
        new_graph.lost_nodes = self.lost_nodes.copy()
        return new_graph
    
    def __repr__(self) -> str:
        info = self.get_graph_info()
        return (
            f"StabilizerGraph(n_qubits={info['n_qubits']}, "
            f"n_active={info['n_active']}, n_edges={info['n_edges']})"
        )
