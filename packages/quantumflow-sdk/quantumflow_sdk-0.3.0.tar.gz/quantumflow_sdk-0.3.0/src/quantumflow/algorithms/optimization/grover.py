"""
Grover's Search Algorithm.

Provides quadratic speedup for unstructured search: O(sqrt(N)) vs O(N).
"""

import math
from dataclasses import dataclass
from typing import Optional, Callable, Union
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class GroverResult:
    """Result from Grover search."""

    circuit: QuantumCircuit
    found_state: str
    probability: float
    iterations: int
    n_qubits: int


class GroverSearch:
    """
    Grover's Quantum Search Algorithm.

    Finds marked items in an unstructured database with quadratic speedup.

    Features:
    - Automatic iteration count optimization
    - Custom oracle support
    - Multi-target search

    Example:
        >>> grover = GroverSearch()
        >>> result = grover.search(n_qubits=4, marked_states=[5, 10])
        >>> print(f"Found: {result.found_state} with P={result.probability:.2%}")
    """

    def __init__(self, backend: BackendType | str = BackendType.AUTO):
        self.backend = get_backend(backend)
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def search(
        self,
        n_qubits: int,
        marked_states: list[int],
        iterations: Optional[int] = None,
        shots: int = 1024,
    ) -> GroverResult:
        """
        Search for marked states.

        Args:
            n_qubits: Number of qubits (search space = 2^n)
            marked_states: States to find
            iterations: Grover iterations (optimal if None)
            shots: Measurement shots

        Returns:
            GroverResult with found state
        """
        self._ensure_connected()

        N = 2 ** n_qubits
        M = len(marked_states)

        # Calculate optimal iterations
        if iterations is None:
            if M > 0 and M < N:
                theta = math.asin(math.sqrt(M / N))
                iterations = max(1, int(round(math.pi / (4 * theta) - 0.5)))
            else:
                iterations = 1

        # Build circuit
        oracle = self._build_oracle(n_qubits, marked_states)
        circuit = self._build_circuit(n_qubits, oracle, iterations)

        # Execute
        result = self.backend.execute(circuit, shots=shots)

        # Find most likely state
        found_state = max(result.counts, key=result.counts.get)
        probability = result.counts[found_state] / shots

        return GroverResult(
            circuit=circuit,
            found_state=found_state,
            probability=probability,
            iterations=iterations,
            n_qubits=n_qubits,
        )

    def search_with_oracle(
        self,
        n_qubits: int,
        oracle: QuantumCircuit,
        n_solutions: int = 1,
        iterations: Optional[int] = None,
        shots: int = 1024,
    ) -> GroverResult:
        """
        Search using a custom oracle.

        Args:
            n_qubits: Number of qubits
            oracle: Custom oracle circuit
            n_solutions: Expected number of solutions
            iterations: Grover iterations
            shots: Measurement shots

        Returns:
            GroverResult
        """
        self._ensure_connected()

        N = 2 ** n_qubits

        if iterations is None:
            if n_solutions > 0 and n_solutions < N:
                theta = math.asin(math.sqrt(n_solutions / N))
                iterations = max(1, int(round(math.pi / (4 * theta) - 0.5)))
            else:
                iterations = 1

        circuit = self._build_circuit(n_qubits, oracle, iterations)
        result = self.backend.execute(circuit, shots=shots)

        found_state = max(result.counts, key=result.counts.get)
        probability = result.counts[found_state] / shots

        return GroverResult(
            circuit=circuit,
            found_state=found_state,
            probability=probability,
            iterations=iterations,
            n_qubits=n_qubits,
        )

    def _build_oracle(
        self,
        n_qubits: int,
        marked_states: list[int],
    ) -> QuantumCircuit:
        """Build oracle marking specified states."""
        oracle = QuantumCircuit(n_qubits, name="oracle")

        for state in marked_states:
            binary = format(state, f'0{n_qubits}b')

            # Flip qubits that should be |0⟩
            for i, bit in enumerate(reversed(binary)):
                if bit == '0':
                    oracle.x(i)

            # Multi-controlled Z gate
            if n_qubits == 1:
                oracle.z(0)
            elif n_qubits == 2:
                oracle.cz(0, 1)
            else:
                oracle.h(n_qubits - 1)
                oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
                oracle.h(n_qubits - 1)

            # Unflip
            for i, bit in enumerate(reversed(binary)):
                if bit == '0':
                    oracle.x(i)

        return oracle

    def _build_diffuser(self, n_qubits: int) -> QuantumCircuit:
        """Build Grover diffusion operator."""
        diffuser = QuantumCircuit(n_qubits, name="diffuser")

        diffuser.h(range(n_qubits))
        diffuser.x(range(n_qubits))

        # Multi-controlled Z
        diffuser.h(n_qubits - 1)
        if n_qubits > 1:
            diffuser.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        diffuser.h(n_qubits - 1)

        diffuser.x(range(n_qubits))
        diffuser.h(range(n_qubits))

        return diffuser

    def _build_circuit(
        self,
        n_qubits: int,
        oracle: QuantumCircuit,
        iterations: int,
    ) -> QuantumCircuit:
        """Build complete Grover circuit."""
        circuit = QuantumCircuit(n_qubits, n_qubits, name="grover")

        # Initial superposition
        circuit.h(range(n_qubits))

        # Grover iterations
        diffuser = self._build_diffuser(n_qubits)

        for _ in range(iterations):
            circuit.compose(oracle, inplace=True)
            circuit.compose(diffuser, inplace=True)

        # Measure
        circuit.measure(range(n_qubits), range(n_qubits))

        return circuit
