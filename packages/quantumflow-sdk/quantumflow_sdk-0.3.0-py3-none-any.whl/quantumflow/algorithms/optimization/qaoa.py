"""
Quantum Approximate Optimization Algorithm (QAOA).

Solves combinatorial optimization problems like MaxCut, TSP, etc.
Hybrid quantum-classical algorithm using parameterized circuits.
"""

import math
from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QAOAResult:
    """Result from QAOA optimization."""

    circuit: QuantumCircuit
    optimal_params: np.ndarray
    best_solution: str
    best_cost: float
    cost_history: list[float]
    n_iterations: int


class QAOA:
    """
    Quantum Approximate Optimization Algorithm.

    Solves combinatorial optimization by:
    1. Encoding problem as cost Hamiltonian
    2. Alternating cost and mixer layers
    3. Classical optimization of parameters

    Supported problems:
    - MaxCut
    - Weighted MaxCut
    - Custom QUBO/Ising problems

    Example:
        >>> qaoa = QAOA(p=2)
        >>> edges = [(0, 1), (1, 2), (2, 0)]
        >>> result = qaoa.maxcut(edges, n_nodes=3)
        >>> print(f"Best cut: {result.best_solution}, Cost: {result.best_cost}")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        p: int = 1,
        shots: int = 1024,
    ):
        """
        Initialize QAOA.

        Args:
            backend: Quantum backend
            p: Number of QAOA layers (depth)
            shots: Measurement shots per evaluation
        """
        self.backend = get_backend(backend)
        self.p = p
        self.shots = shots
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def maxcut(
        self,
        edges: list[tuple[int, int]],
        n_nodes: int,
        weights: Optional[list[float]] = None,
        max_iterations: int = 100,
    ) -> QAOAResult:
        """
        Solve MaxCut problem.

        Args:
            edges: List of (i, j) edges
            n_nodes: Number of nodes
            weights: Optional edge weights
            max_iterations: Max optimization iterations

        Returns:
            QAOAResult with optimal solution
        """
        if weights is None:
            weights = [1.0] * len(edges)

        # Build cost function
        def cost_fn(bitstring: str) -> float:
            cost = 0
            for (i, j), w in zip(edges, weights):
                if bitstring[i] != bitstring[j]:
                    cost += w
            return cost

        return self._optimize(
            n_qubits=n_nodes,
            cost_hamiltonian=self._maxcut_hamiltonian(edges, weights, n_nodes),
            cost_fn=cost_fn,
            max_iterations=max_iterations,
        )

    def optimize_qubo(
        self,
        Q: np.ndarray,
        max_iterations: int = 100,
    ) -> QAOAResult:
        """
        Solve QUBO (Quadratic Unconstrained Binary Optimization).

        Args:
            Q: QUBO matrix (n x n)
            max_iterations: Max optimization iterations

        Returns:
            QAOAResult with optimal solution
        """
        n_qubits = Q.shape[0]

        def cost_fn(bitstring: str) -> float:
            x = np.array([int(b) for b in bitstring])
            return float(x @ Q @ x)

        return self._optimize(
            n_qubits=n_qubits,
            cost_hamiltonian=self._qubo_hamiltonian(Q),
            cost_fn=cost_fn,
            max_iterations=max_iterations,
        )

    def _optimize(
        self,
        n_qubits: int,
        cost_hamiltonian: Callable[[QuantumCircuit, float], None],
        cost_fn: Callable[[str], float],
        max_iterations: int,
    ) -> QAOAResult:
        """Run QAOA optimization loop."""
        self._ensure_connected()

        # Initialize parameters: gamma (cost), beta (mixer)
        params = np.random.uniform(0, np.pi, 2 * self.p)
        cost_history = []

        # Simple gradient-free optimization (COBYLA-style)
        best_params = params.copy()
        best_cost = float('inf')

        for iteration in range(max_iterations):
            # Evaluate current parameters
            circuit = self._build_circuit(n_qubits, params, cost_hamiltonian)
            result = self.backend.execute(circuit, shots=self.shots)

            # Calculate expected cost
            total_cost = 0
            for bitstring, count in result.counts.items():
                total_cost += cost_fn(bitstring) * count
            avg_cost = total_cost / self.shots

            cost_history.append(avg_cost)

            if avg_cost < best_cost:
                best_cost = avg_cost
                best_params = params.copy()

            # Simple parameter update (gradient approximation)
            for i in range(len(params)):
                delta = 0.1 * (np.random.random() - 0.5)
                params[i] += delta

        # Get best solution
        final_circuit = self._build_circuit(n_qubits, best_params, cost_hamiltonian)
        final_result = self.backend.execute(final_circuit, shots=self.shots)
        best_solution = max(final_result.counts, key=final_result.counts.get)

        return QAOAResult(
            circuit=final_circuit,
            optimal_params=best_params,
            best_solution=best_solution,
            best_cost=best_cost,
            cost_history=cost_history,
            n_iterations=max_iterations,
        )

    def _build_circuit(
        self,
        n_qubits: int,
        params: np.ndarray,
        cost_hamiltonian: Callable,
    ) -> QuantumCircuit:
        """Build QAOA circuit with given parameters."""
        qc = QuantumCircuit(n_qubits, n_qubits, name="qaoa")

        # Initial superposition
        qc.h(range(n_qubits))

        # QAOA layers
        for layer in range(self.p):
            gamma = params[2 * layer]
            beta = params[2 * layer + 1]

            # Cost layer
            cost_hamiltonian(qc, gamma)

            # Mixer layer (X rotations)
            for i in range(n_qubits):
                qc.rx(2 * beta, i)

        # Measure
        qc.measure(range(n_qubits), range(n_qubits))

        return qc

    def _maxcut_hamiltonian(
        self,
        edges: list[tuple[int, int]],
        weights: list[float],
        n_qubits: int,
    ) -> Callable:
        """Create MaxCut cost Hamiltonian."""
        def apply_cost(qc: QuantumCircuit, gamma: float):
            for (i, j), w in zip(edges, weights):
                qc.rzz(w * gamma, i, j)
        return apply_cost

    def _qubo_hamiltonian(self, Q: np.ndarray) -> Callable:
        """Create QUBO cost Hamiltonian."""
        n = Q.shape[0]

        def apply_cost(qc: QuantumCircuit, gamma: float):
            # Diagonal terms
            for i in range(n):
                if Q[i, i] != 0:
                    qc.rz(Q[i, i] * gamma, i)

            # Off-diagonal terms
            for i in range(n):
                for j in range(i + 1, n):
                    if Q[i, j] != 0 or Q[j, i] != 0:
                        coeff = Q[i, j] + Q[j, i]
                        qc.rzz(coeff * gamma / 2, i, j)

        return apply_cost
