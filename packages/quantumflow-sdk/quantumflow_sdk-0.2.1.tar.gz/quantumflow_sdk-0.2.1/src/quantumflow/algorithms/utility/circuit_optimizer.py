"""
Quantum Circuit Optimizer.

Optimizes quantum circuits for better performance on real hardware.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit, transpile

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class OptimizationResult:
    """Result from circuit optimization."""

    original_circuit: QuantumCircuit
    optimized_circuit: QuantumCircuit
    original_depth: int
    optimized_depth: int
    original_gates: int
    optimized_gates: int
    depth_reduction: float
    gate_reduction: float


class CircuitOptimizer:
    """
    Quantum Circuit Optimizer.

    Applies various optimization techniques:
    - Gate cancellation
    - Gate fusion
    - Commutation optimization
    - Hardware-specific transpilation

    Example:
        >>> opt = CircuitOptimizer()
        >>> result = opt.optimize(circuit)
        >>> print(f"Depth reduced by {result.depth_reduction:.1%}")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        optimization_level: int = 2,
    ):
        """
        Initialize optimizer.

        Args:
            backend: Target backend for optimization
            optimization_level: 0-3 (higher = more optimization)
        """
        self.backend = get_backend(backend)
        self.optimization_level = optimization_level

    def optimize(
        self,
        circuit: QuantumCircuit,
        target_basis: Optional[list[str]] = None,
    ) -> OptimizationResult:
        """
        Optimize a quantum circuit.

        Args:
            circuit: Circuit to optimize
            target_basis: Target gate set (e.g., ['cx', 'u3'])

        Returns:
            OptimizationResult with optimized circuit
        """
        original_depth = circuit.depth()
        original_gates = sum(circuit.count_ops().values())

        # Apply optimizations
        optimized = self._apply_optimizations(circuit)

        # Transpile for target
        if target_basis:
            optimized = transpile(
                optimized,
                basis_gates=target_basis,
                optimization_level=self.optimization_level,
            )
        else:
            optimized = transpile(
                optimized,
                optimization_level=self.optimization_level,
            )

        optimized_depth = optimized.depth()
        optimized_gates = sum(optimized.count_ops().values())

        depth_reduction = 1 - (optimized_depth / original_depth) if original_depth > 0 else 0
        gate_reduction = 1 - (optimized_gates / original_gates) if original_gates > 0 else 0

        return OptimizationResult(
            original_circuit=circuit,
            optimized_circuit=optimized,
            original_depth=original_depth,
            optimized_depth=optimized_depth,
            original_gates=original_gates,
            optimized_gates=optimized_gates,
            depth_reduction=depth_reduction,
            gate_reduction=gate_reduction,
        )

    def _apply_optimizations(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """Apply custom optimization passes using transpile."""
        # Use transpile with high optimization level
        return transpile(circuit, optimization_level=3)

    def cancel_redundant_gates(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """Cancel adjacent inverse gates."""
        return transpile(circuit, optimization_level=2)

    def fuse_single_qubit_gates(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """Fuse consecutive single-qubit gates."""
        return transpile(circuit, optimization_level=2)

    def optimize_for_hardware(
        self,
        circuit: QuantumCircuit,
        coupling_map: Optional[list[list[int]]] = None,
    ) -> QuantumCircuit:
        """
        Optimize circuit for specific hardware topology.

        Args:
            circuit: Circuit to optimize
            coupling_map: Hardware qubit connectivity

        Returns:
            Hardware-optimized circuit
        """
        return transpile(
            circuit,
            coupling_map=coupling_map,
            optimization_level=self.optimization_level,
        )

    def estimate_cost(self, circuit: QuantumCircuit) -> dict:
        """
        Estimate circuit execution cost.

        Returns:
            Dict with depth, gate counts, estimated time
        """
        ops = circuit.count_ops()

        # Rough gate time estimates (in microseconds)
        gate_times = {
            'x': 0.02, 'y': 0.02, 'z': 0.02,
            'h': 0.02, 's': 0.02, 't': 0.02,
            'rx': 0.03, 'ry': 0.03, 'rz': 0.03,
            'cx': 0.3, 'cz': 0.3,
            'ccx': 0.9, 'swap': 0.6,
            'measure': 1.0,
        }

        total_time = sum(
            ops.get(gate, 0) * gate_times.get(gate, 0.1)
            for gate in ops
        )

        two_qubit_gates = ops.get('cx', 0) + ops.get('cz', 0) + ops.get('swap', 0)

        return {
            'depth': circuit.depth(),
            'total_gates': sum(ops.values()),
            'two_qubit_gates': two_qubit_gates,
            'estimated_time_us': total_time,
            'gate_counts': dict(ops),
        }

    def compare_circuits(
        self,
        circuit1: QuantumCircuit,
        circuit2: QuantumCircuit,
    ) -> dict:
        """Compare two circuits."""
        cost1 = self.estimate_cost(circuit1)
        cost2 = self.estimate_cost(circuit2)

        return {
            'circuit1': cost1,
            'circuit2': cost2,
            'depth_diff': cost1['depth'] - cost2['depth'],
            'gate_diff': cost1['total_gates'] - cost2['total_gates'],
            'time_diff_us': cost1['estimated_time_us'] - cost2['estimated_time_us'],
        }
