"""
Variational Quantum Eigensolver (VQE).

Finds ground state energy of molecular Hamiltonians.
Hybrid quantum-classical algorithm for quantum chemistry.
"""

import math
from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class VQEResult:
    """Result from VQE optimization."""

    circuit: QuantumCircuit
    optimal_params: np.ndarray
    ground_energy: float
    energy_history: list[float]
    n_iterations: int


class VQE:
    """
    Variational Quantum Eigensolver.

    Finds the ground state energy of a Hamiltonian by:
    1. Preparing parameterized ansatz state
    2. Measuring expectation value
    3. Classically optimizing parameters

    Example:
        >>> vqe = VQE(n_qubits=2)
        >>> # Simple H2 molecule Hamiltonian
        >>> H = [("ZZ", 0.5), ("XI", 0.3), ("IX", 0.3)]
        >>> result = vqe.run(H)
        >>> print(f"Ground energy: {result.ground_energy:.4f}")
    """

    def __init__(
        self,
        n_qubits: int,
        backend: BackendType | str = BackendType.AUTO,
        ansatz: str = "ry_linear",
        depth: int = 2,
        shots: int = 1024,
    ):
        """
        Initialize VQE.

        Args:
            n_qubits: Number of qubits
            backend: Quantum backend
            ansatz: Ansatz type ('ry_linear', 'ry_full', 'hardware_efficient')
            depth: Circuit depth (layers)
            shots: Measurement shots
        """
        self.n_qubits = n_qubits
        self.backend = get_backend(backend)
        self.ansatz_type = ansatz
        self.depth = depth
        self.shots = shots
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def run(
        self,
        hamiltonian: list[tuple[str, float]],
        max_iterations: int = 100,
        initial_params: Optional[np.ndarray] = None,
    ) -> VQEResult:
        """
        Run VQE to find ground state energy.

        Args:
            hamiltonian: List of (Pauli string, coefficient) tuples
                         e.g., [("ZZ", 0.5), ("XI", 0.3)]
            max_iterations: Maximum optimization iterations
            initial_params: Initial parameter values

        Returns:
            VQEResult with ground state energy
        """
        self._ensure_connected()

        # Initialize parameters
        n_params = self._count_params()
        if initial_params is None:
            params = np.random.uniform(-np.pi, np.pi, n_params)
        else:
            params = initial_params.copy()

        energy_history = []
        best_energy = float('inf')
        best_params = params.copy()

        # Optimization loop
        for iteration in range(max_iterations):
            energy = self._evaluate_energy(params, hamiltonian)
            energy_history.append(energy)

            if energy < best_energy:
                best_energy = energy
                best_params = params.copy()

            # Simple gradient descent with finite differences
            grad = self._compute_gradient(params, hamiltonian)
            params -= 0.1 * grad

        # Build final circuit
        final_circuit = self._build_ansatz(best_params)

        return VQEResult(
            circuit=final_circuit,
            optimal_params=best_params,
            ground_energy=best_energy,
            energy_history=energy_history,
            n_iterations=max_iterations,
        )

    def _count_params(self) -> int:
        """Count parameters in ansatz."""
        if self.ansatz_type == "ry_linear":
            return self.n_qubits * self.depth
        elif self.ansatz_type == "ry_full":
            return self.n_qubits * self.depth * 2
        elif self.ansatz_type == "hardware_efficient":
            return self.n_qubits * self.depth * 3
        return self.n_qubits * self.depth

    def _build_ansatz(self, params: np.ndarray) -> QuantumCircuit:
        """Build parameterized ansatz circuit."""
        qc = QuantumCircuit(self.n_qubits, name="vqe_ansatz")
        param_idx = 0

        for layer in range(self.depth):
            # Single qubit rotations
            for i in range(self.n_qubits):
                if self.ansatz_type == "hardware_efficient":
                    qc.ry(params[param_idx], i)
                    param_idx += 1
                    qc.rz(params[param_idx], i)
                    param_idx += 1
                else:
                    qc.ry(params[param_idx], i)
                    param_idx += 1

            # Entangling layer
            for i in range(self.n_qubits - 1):
                qc.cx(i, i + 1)

        return qc

    def _evaluate_energy(
        self,
        params: np.ndarray,
        hamiltonian: list[tuple[str, float]],
    ) -> float:
        """Evaluate expectation value of Hamiltonian."""
        total_energy = 0.0

        for pauli_string, coeff in hamiltonian:
            expectation = self._measure_pauli(params, pauli_string)
            total_energy += coeff * expectation

        return total_energy

    def _measure_pauli(self, params: np.ndarray, pauli_string: str) -> float:
        """Measure expectation value of a Pauli string."""
        qc = self._build_ansatz(params)

        # Add measurement basis rotations
        for i, p in enumerate(pauli_string):
            if p == 'X':
                qc.h(i)
            elif p == 'Y':
                qc.sdg(i)
                qc.h(i)
            # Z needs no rotation

        qc.measure_all()

        # Execute
        result = self.backend.execute(qc, shots=self.shots)

        # Calculate expectation
        expectation = 0.0
        for bitstring, count in result.counts.items():
            # Parity of measured bits
            parity = 1
            for i, p in enumerate(pauli_string):
                if p != 'I':
                    bit_idx = self.n_qubits - 1 - i
                    if bit_idx < len(bitstring) and bitstring[bit_idx] == '1':
                        parity *= -1
            expectation += parity * count

        return expectation / self.shots

    def _compute_gradient(
        self,
        params: np.ndarray,
        hamiltonian: list[tuple[str, float]],
    ) -> np.ndarray:
        """Compute parameter gradient using parameter shift rule."""
        grad = np.zeros_like(params)
        shift = np.pi / 2

        for i in range(len(params)):
            params_plus = params.copy()
            params_plus[i] += shift
            energy_plus = self._evaluate_energy(params_plus, hamiltonian)

            params_minus = params.copy()
            params_minus[i] -= shift
            energy_minus = self._evaluate_energy(params_minus, hamiltonian)

            grad[i] = (energy_plus - energy_minus) / 2

        return grad
