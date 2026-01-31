"""
Quantum Annealing Simulation.

Simulates quantum annealing for optimization problems.
Note: True quantum annealing requires specialized hardware (D-Wave).
"""

import math
from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class AnnealingResult:
    """Result from quantum annealing."""

    circuit: QuantumCircuit
    best_solution: str
    best_energy: float
    energy_history: list[float]
    n_steps: int


class QuantumAnnealing:
    """
    Quantum Annealing Simulation using gate-based circuits.

    Simulates the annealing process by:
    1. Starting in ground state of transverse field
    2. Slowly evolving to problem Hamiltonian
    3. Measuring final state

    Best for: Optimization problems expressible as Ising models.

    Example:
        >>> qa = QuantumAnnealing()
        >>> J = {(0,1): -1, (1,2): -1}  # Ferromagnetic coupling
        >>> result = qa.anneal(J, h={}, n_qubits=3)
        >>> print(f"Ground state: {result.best_solution}")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        n_steps: int = 20,
    ):
        """
        Initialize quantum annealing.

        Args:
            backend: Quantum backend
            n_steps: Number of annealing steps (Trotter steps)
        """
        self.backend = get_backend(backend)
        self.n_steps = n_steps
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def anneal(
        self,
        J: dict[tuple[int, int], float],
        h: dict[int, float],
        n_qubits: int,
        shots: int = 1024,
    ) -> AnnealingResult:
        """
        Run quantum annealing for Ising problem.

        Hamiltonian: H = -sum_ij J_ij * Z_i * Z_j - sum_i h_i * Z_i

        Args:
            J: Coupling strengths {(i,j): strength}
            h: Local fields {i: field}
            n_qubits: Number of qubits
            shots: Measurement shots

        Returns:
            AnnealingResult with ground state
        """
        self._ensure_connected()

        # Build annealing circuit
        circuit = self._build_annealing_circuit(J, h, n_qubits)

        # Execute
        result = self.backend.execute(circuit, shots=shots)

        # Find ground state (lowest energy)
        best_solution = None
        best_energy = float('inf')

        for bitstring, count in result.counts.items():
            energy = self._calculate_energy(bitstring, J, h)
            if energy < best_energy:
                best_energy = energy
                best_solution = bitstring

        # Simulate energy history (for visualization)
        energy_history = self._simulate_energy_history(best_energy)

        return AnnealingResult(
            circuit=circuit,
            best_solution=best_solution or "0" * n_qubits,
            best_energy=best_energy,
            energy_history=energy_history,
            n_steps=self.n_steps,
        )

    def anneal_qubo(
        self,
        Q: np.ndarray,
        shots: int = 1024,
    ) -> AnnealingResult:
        """
        Run quantum annealing for QUBO problem.

        Args:
            Q: QUBO matrix
            shots: Measurement shots

        Returns:
            AnnealingResult
        """
        n_qubits = Q.shape[0]

        # Convert QUBO to Ising
        J, h, offset = self._qubo_to_ising(Q)

        result = self.anneal(J, h, n_qubits, shots)
        result.best_energy += offset

        return result

    def _build_annealing_circuit(
        self,
        J: dict[tuple[int, int], float],
        h: dict[int, float],
        n_qubits: int,
    ) -> QuantumCircuit:
        """Build circuit simulating quantum annealing."""
        circuit = QuantumCircuit(n_qubits, n_qubits, name="annealing")

        # Start in |+⟩^n (ground state of transverse field)
        circuit.h(range(n_qubits))

        # Annealing schedule: s goes from 0 to 1
        dt = 1.0 / self.n_steps

        for step in range(self.n_steps):
            s = (step + 1) / self.n_steps  # Annealing parameter

            # Transverse field (decreasing)
            gamma = (1 - s) * math.pi / 4
            for i in range(n_qubits):
                circuit.rx(2 * gamma * dt, i)

            # Problem Hamiltonian (increasing)
            beta = s * math.pi / 4

            # ZZ interactions
            for (i, j), strength in J.items():
                circuit.rzz(2 * strength * beta * dt, i, j)

            # Z terms
            for i, field in h.items():
                circuit.rz(2 * field * beta * dt, i)

        # Measure
        circuit.measure(range(n_qubits), range(n_qubits))

        return circuit

    def _calculate_energy(
        self,
        bitstring: str,
        J: dict[tuple[int, int], float],
        h: dict[int, float],
    ) -> float:
        """Calculate Ising energy for a bitstring."""
        # Convert to spins (+1/-1)
        spins = [1 if b == '0' else -1 for b in bitstring]

        energy = 0.0

        # Coupling terms
        for (i, j), strength in J.items():
            energy -= strength * spins[i] * spins[j]

        # Field terms
        for i, field in h.items():
            energy -= field * spins[i]

        return energy

    def _qubo_to_ising(
        self,
        Q: np.ndarray,
    ) -> tuple[dict, dict, float]:
        """Convert QUBO to Ising formulation."""
        n = Q.shape[0]
        J = {}
        h = {}
        offset = 0.0

        for i in range(n):
            for j in range(i, n):
                if i == j:
                    h[i] = Q[i, i] / 2
                    offset += Q[i, i] / 2
                else:
                    coupling = (Q[i, j] + Q[j, i]) / 4
                    if coupling != 0:
                        J[(i, j)] = coupling
                    h[i] = h.get(i, 0) + (Q[i, j] + Q[j, i]) / 4
                    h[j] = h.get(j, 0) + (Q[i, j] + Q[j, i]) / 4
                    offset += (Q[i, j] + Q[j, i]) / 4

        return J, h, offset

    def _simulate_energy_history(self, final_energy: float) -> list[float]:
        """Simulate energy evolution during annealing."""
        history = []
        for step in range(self.n_steps):
            s = step / self.n_steps
            # Energy decreases as we anneal
            energy = final_energy + (1 - s) * abs(final_energy) * 2
            history.append(energy)
        history.append(final_energy)
        return history
