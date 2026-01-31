"""
Recovery: Loss Recovery and Error Mitigation (Algorithm 3)
===========================================================

Implements hardware-aware error correction and result calibration.
Applies fidelity estimation and log-probability weighting to simulation results.

Key Features:
- Fidelity estimation: F_final = Π(1-p_gate) × exp(-Σ loss_path)
- Log-probability weighting for numerical stability
- Hardware characteristic integration

Reference:
    Quantum error mitigation techniques for photonic systems
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """
    Result container for loss recovery and error mitigation.
    
    Attributes:
        raw_amplitude: Raw simulation amplitude
        corrected_amplitude: Amplitude after error mitigation
        fidelity: Estimated output state fidelity
        log_probability: Log-scale probability weight
        n_corrections: Number of error corrections applied
        metadata: Additional recovery information
    """
    raw_amplitude: complex
    corrected_amplitude: complex
    fidelity: float
    log_probability: float
    n_corrections: int
    metadata: Dict[str, Any]
    
    def __repr__(self) -> str:
        return (
            f"RecoveryResult(fidelity={self.fidelity:.4f}, "
            f"corrections={self.n_corrections})"
        )


class LossRecovery:
    """
    Handles photon loss recovery and hardware error mitigation.
    
    Integrates hardware characteristics into simulation results
    to account for realistic device imperfections.
    
    Attributes:
        p_gate: Gate error probability
        p_detection: Detection error probability
        p_source: Source error probability
        loss_paths: Tracked optical loss paths
    """
    
    def __init__(
        self,
        p_gate: float = 0.01,
        p_detection: float = 0.05,
        p_source: float = 0.02,
        coherence_time: float = 1.0
    ):
        """
        Initialize loss recovery module.
        
        Args:
            p_gate: Gate error probability (default 1%)
            p_detection: Detection error probability (default 5%)
            p_source: Source error probability (default 2%)
            coherence_time: Coherence time in arbitrary units
        """
        self.p_gate = p_gate
        self.p_detection = p_detection
        self.p_source = p_source
        self.coherence_time = coherence_time
        
        # Track loss paths for fidelity calculation
        self.loss_paths: List[float] = []
        self.n_gates: int = 0
        self.n_detections: int = 0
        
        logger.debug(
            f"LossRecovery initialized: p_gate={p_gate}, "
            f"p_detection={p_detection}, p_source={p_source}"
        )
    
    def register_gate(self, n: int = 1) -> None:
        """Register n gate operations for fidelity tracking."""
        self.n_gates += n
    
    def register_detection(self, n: int = 1) -> None:
        """Register n detection events for fidelity tracking."""
        self.n_detections += n
    
    def register_loss_path(self, loss_probability: float) -> None:
        """
        Register an optical loss path.
        
        Args:
            loss_probability: Probability of loss along this path
        """
        self.loss_paths.append(loss_probability)
    
    def estimate_fidelity(
        self,
        n_qubits: Optional[int] = None,
        custom_gate_count: Optional[int] = None,
        custom_loss_paths: Optional[List[float]] = None
    ) -> float:
        """
        Estimate final state fidelity.
        
        Formula: F_final = Π(1-p_gate)^n_gates × Π(1-p_det)^n_det × exp(-Σ loss_path)
        
        Args:
            n_qubits: Number of qubits (optional, for estimation)
            custom_gate_count: Override registered gate count
            custom_loss_paths: Override registered loss paths
            
        Returns:
            Estimated fidelity between 0 and 1
        """
        n_gates = custom_gate_count if custom_gate_count is not None else self.n_gates
        loss_paths = custom_loss_paths if custom_loss_paths is not None else self.loss_paths
        
        # Gate fidelity contribution
        gate_fidelity = (1 - self.p_gate) ** n_gates
        
        # Detection fidelity contribution
        detection_fidelity = (1 - self.p_detection) ** self.n_detections
        
        # Source fidelity
        source_fidelity = 1 - self.p_source
        
        # Loss path contribution (exponential decay)
        if loss_paths:
            total_loss = sum(loss_paths)
            loss_fidelity = np.exp(-total_loss)
        else:
            loss_fidelity = 1.0
        
        # Combined fidelity
        fidelity = gate_fidelity * detection_fidelity * source_fidelity * loss_fidelity
        
        logger.debug(
            f"Fidelity estimate: gate={gate_fidelity:.4f}, "
            f"detection={detection_fidelity:.4f}, loss={loss_fidelity:.4f}, "
            f"total={fidelity:.4f}"
        )
        
        return float(np.clip(fidelity, 0, 1))
    
    def apply_log_weighting(
        self,
        amplitudes: np.ndarray,
        loss_probabilities: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply log-probability weighting to prevent floating-point underflow.
        
        Converts probabilities to log-scale for numerical stability:
        log(P) = log(|amplitude|^2) + sum(log(1 - p_loss))
        
        Args:
            amplitudes: Complex amplitude array
            loss_probabilities: Per-amplitude loss probabilities
            
        Returns:
            Tuple of (log_probabilities, normalized_amplitudes)
        """
        # Convert to log probabilities
        log_probs = 2 * np.log(np.abs(amplitudes) + 1e-300)
        
        if loss_probabilities is not None:
            # Add log of survival probabilities
            log_survival = np.log(1 - loss_probabilities + 1e-300)
            log_probs += log_survival
        
        # Normalize in log space (subtract max for numerical stability)
        max_log_prob = np.max(log_probs)
        normalized_log_probs = log_probs - max_log_prob
        
        # Convert back to normalized amplitudes
        normalized_amplitudes = amplitudes * np.exp(normalized_log_probs / 2)
        
        # Renormalize
        norm = np.sqrt(np.sum(np.abs(normalized_amplitudes) ** 2))
        if norm > 0:
            normalized_amplitudes /= norm
        
        return log_probs, normalized_amplitudes
    
    def mitigate_errors(
        self,
        raw_result: complex,
        n_qubits: int,
        loss_rate: float = 0.0
    ) -> RecoveryResult:
        """
        Apply complete error mitigation pipeline to raw simulation result.
        
        Args:
            raw_result: Raw amplitude from tensor contraction
            n_qubits: Number of qubits in simulation
            loss_rate: Overall loss rate applied
            
        Returns:
            RecoveryResult with corrected amplitude and fidelity
        """
        # Estimate required corrections based on system size
        estimated_gates = n_qubits * 2  # Approximate gate count
        
        # Register paths
        self.register_gate(estimated_gates)
        self.register_loss_path(loss_rate * n_qubits)
        
        # Calculate fidelity
        fidelity = self.estimate_fidelity()
        
        # Apply fidelity correction to amplitude
        corrected_amplitude = raw_result * np.sqrt(fidelity)
        
        # Calculate log probability
        log_prob = np.log(np.abs(raw_result) ** 2 + 1e-300)
        log_prob += np.log(fidelity + 1e-300)
        
        result = RecoveryResult(
            raw_amplitude=raw_result,
            corrected_amplitude=corrected_amplitude,
            fidelity=fidelity,
            log_probability=float(log_prob),
            n_corrections=estimated_gates,
            metadata={
                'n_qubits': n_qubits,
                'loss_rate': loss_rate,
                'n_gates': self.n_gates,
                'n_loss_paths': len(self.loss_paths)
            }
        )
        
        logger.info(f"Error mitigation complete: fidelity={fidelity:.4f}")
        
        return result
    
    def zero_noise_extrapolation(
        self,
        results: List[Tuple[float, complex]]
    ) -> complex:
        """
        Perform zero-noise extrapolation from multiple noise levels.
        
        Fits results at different noise levels and extrapolates to zero noise.
        
        Args:
            results: List of (noise_level, amplitude) tuples
            
        Returns:
            Extrapolated zero-noise amplitude
        """
        if len(results) < 2:
            return results[0][1] if results else 0j
        
        # Sort by noise level
        results = sorted(results, key=lambda x: x[0])
        
        noise_levels = np.array([r[0] for r in results])
        amplitudes = np.array([r[1] for r in results])
        
        # Linear extrapolation to zero noise
        # For complex amplitudes, extrapolate real and imaginary separately
        real_coeffs = np.polyfit(noise_levels, amplitudes.real, 1)
        imag_coeffs = np.polyfit(noise_levels, amplitudes.imag, 1)
        
        zero_noise_real = np.polyval(real_coeffs, 0)
        zero_noise_imag = np.polyval(imag_coeffs, 0)
        
        return complex(zero_noise_real, zero_noise_imag)
    
    def probabilistic_error_cancellation(
        self,
        noisy_results: List[complex],
        quasi_probabilities: List[float]
    ) -> complex:
        """
        Apply probabilistic error cancellation.
        
        Uses quasi-probability decomposition to cancel errors statistically.
        
        Args:
            noisy_results: Results from different error configurations
            quasi_probabilities: Quasi-probability weights (can be negative)
            
        Returns:
            Error-cancelled result
        """
        if len(noisy_results) != len(quasi_probabilities):
            raise ValueError("Results and quasi-probabilities must have same length")
        
        # Weighted sum with quasi-probabilities
        result = sum(q * r for q, r in zip(quasi_probabilities, noisy_results))
        
        return complex(result)
    
    def reset(self) -> None:
        """Reset all tracked error information."""
        self.loss_paths = []
        self.n_gates = 0
        self.n_detections = 0
        logger.debug("LossRecovery state reset")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current recovery state for serialization."""
        return {
            'p_gate': self.p_gate,
            'p_detection': self.p_detection,
            'p_source': self.p_source,
            'coherence_time': self.coherence_time,
            'n_gates': self.n_gates,
            'n_detections': self.n_detections,
            'n_loss_paths': len(self.loss_paths),
            'total_loss': sum(self.loss_paths)
        }
    
    @classmethod
    def from_hardware_model(cls, hardware_params: Dict[str, Any]) -> 'LossRecovery':
        """
        Create LossRecovery from hardware model parameters.
        
        Args:
            hardware_params: Dictionary with hardware characteristics
            
        Returns:
            Configured LossRecovery instance
        """
        return cls(
            p_gate=hardware_params.get('gate_error', 0.01),
            p_detection=hardware_params.get('detection_error', 0.05),
            p_source=hardware_params.get('source_error', 0.02),
            coherence_time=hardware_params.get('coherence_time', 1.0)
        )


# =============================================================================
# Simple Loss Handler (User-requested simplified API)
# =============================================================================
class SimpleLossHandler:
    """
    Simplified loss handler for quick graph recovery operations.
    
    Provides a minimal interface for handling photon loss without
    the full error mitigation pipeline.
    
    Example:
        >>> from lagc.core import SimpleGraphEngine, SimpleLossHandler
        >>> engine = SimpleGraphEngine(10)
        >>> handler = SimpleLossHandler(engine)
        >>> handler.handle_loss(5)  # Handle loss at node 5
    """
    
    def __init__(self, engine):
        """
        Initialize with a graph engine.
        
        Args:
            engine: SimpleGraphEngine or object with adj, get_neighbors,
                   and local_complementation methods
        """
        self.engine = engine
    
    def handle_loss(self, lost_node: int) -> None:
        """
        Handle loss at a specific node by applying graph surgery.
        
        Algorithm:
        1. Get neighbors of lost node
        2. Apply local complementation at pivot neighbor
        3. Remove all edges to/from lost node
        
        Args:
            lost_node: Index of the lost node
        """
        neighbors = self.engine.get_neighbors(lost_node)
        
        if len(neighbors) > 0:
            # Apply local complementation at first neighbor (pivot)
            pivot = neighbors[0]
            self.engine.local_complementation(pivot)
        
        # Remove all edges connected to lost node
        if hasattr(self.engine, 'remove_node'):
            self.engine.remove_node(lost_node)
        else:
            # Fallback for adj matrix access
            self.engine.adj[lost_node, :] = 0
            self.engine.adj[:, lost_node] = 0
    
    def handle_multiple_losses(self, lost_nodes: List[int]) -> int:
        """
        Handle multiple node losses.
        
        Args:
            lost_nodes: List of lost node indices
            
        Returns:
            Number of recovery operations performed
        """
        count = 0
        for node in sorted(lost_nodes, reverse=True):
            self.handle_loss(node)
            count += 1
        return count


# =============================================================================
# Backward Compatibility Aliases
# =============================================================================
# RecoveryManager was the original name; LossRecovery is the preferred name
# to align with LAGC's "LossAware" branding
RecoveryManager = LossRecovery


