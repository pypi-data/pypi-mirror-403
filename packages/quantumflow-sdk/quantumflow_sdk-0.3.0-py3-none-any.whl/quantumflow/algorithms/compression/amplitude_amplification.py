"""
Amplitude Amplification Algorithm.

Generalization of Grover's algorithm for amplifying the probability
of marked states. Used in compression for selective retrieval.
"""

import math
from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class AmplificationResult:
    """Result from amplitude amplification."""

    circuit: QuantumCircuit
    n_qubits: int
    iterations: int
    target_probability: float
    amplified_probability: float


class AmplitudeAmplification:
    """
    Quantum Amplitude Amplification.

    Amplifies the amplitude of marked states, increasing their
    measurement probability from ~1/N to near certainty.

    Applications:
    - Selective token retrieval from compressed state
    - Search optimization
    - Probability boosting

    Example:
        >>> aa = AmplitudeAmplification()
        >>> result = aa.amplify(initial_circuit, oracle, n_qubits=4)
        >>> print(f"Amplified probability: {result.amplified_probability:.2%}")
    """

    def __init__(self, backend: BackendType | str = BackendType.AUTO):
        self.backend = get_backend(backend)

    def amplify(
        self,
        initial_state: QuantumCircuit,
        oracle: QuantumCircuit,
        n_qubits: int,
        iterations: Optional[int] = None,
        target_count: int = 1,
    ) -> AmplificationResult:
        """
        Apply amplitude amplification.

        Args:
            initial_state: Circuit preparing initial superposition
            oracle: Oracle marking target states (applies phase flip)
            n_qubits: Number of qubits
            iterations: Grover iterations (optimal if None)
            target_count: Number of marked states

        Returns:
            AmplificationResult with amplified circuit
        """
        N = 2 ** n_qubits

        # Calculate optimal iterations
        if iterations is None:
            if target_count > 0:
                theta = math.asin(math.sqrt(target_count / N))
                iterations = max(1, int(round(math.pi / (4 * theta) - 0.5)))
            else:
                iterations = 1

        # Initial probability
        initial_prob = target_count / N

        # Build amplification circuit
        circuit = self._build_circuit(
            initial_state, oracle, n_qubits, iterations
        )

        # Calculate amplified probability
        theta = math.asin(math.sqrt(target_count / N))
        amplified_prob = math.sin((2 * iterations + 1) * theta) ** 2

        return AmplificationResult(
            circuit=circuit,
            n_qubits=n_qubits,
            iterations=iterations,
            target_probability=initial_prob,
            amplified_probability=amplified_prob,
        )

    def create_oracle(
        self,
        n_qubits: int,
        marked_states: list[int],
    ) -> QuantumCircuit:
        """
        Create an oracle that marks specified states.

        Args:
            n_qubits: Number of qubits
            marked_states: List of state indices to mark

        Returns:
            Oracle circuit applying phase flip to marked states
        """
        oracle = QuantumCircuit(n_qubits, name="oracle")

        for state in marked_states:
            # Convert state to binary and apply X gates for 0s
            binary = format(state, f'0{n_qubits}b')

            # Apply X to qubits that should be |0⟩
            for i, bit in enumerate(reversed(binary)):
                if bit == '0':
                    oracle.x(i)

            # Multi-controlled Z
            if n_qubits == 1:
                oracle.z(0)
            elif n_qubits == 2:
                oracle.cz(0, 1)
            else:
                oracle.h(n_qubits - 1)
                oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
                oracle.h(n_qubits - 1)

            # Undo X gates
            for i, bit in enumerate(reversed(binary)):
                if bit == '0':
                    oracle.x(i)

        return oracle

    def _build_circuit(
        self,
        initial_state: QuantumCircuit,
        oracle: QuantumCircuit,
        n_qubits: int,
        iterations: int,
    ) -> QuantumCircuit:
        """Build the full amplitude amplification circuit."""
        circuit = QuantumCircuit(n_qubits, name="amplitude_amp")

        # Apply initial state preparation
        circuit.compose(initial_state, inplace=True)

        # Grover iterations
        diffuser = self._create_diffuser(n_qubits)

        for _ in range(iterations):
            # Oracle
            circuit.compose(oracle, inplace=True)
            # Diffuser
            circuit.compose(diffuser, inplace=True)

        return circuit

    def _create_diffuser(self, n_qubits: int) -> QuantumCircuit:
        """Create the Grover diffusion operator."""
        diffuser = QuantumCircuit(n_qubits, name="diffuser")

        # H gates
        diffuser.h(range(n_qubits))

        # X gates
        diffuser.x(range(n_qubits))

        # Multi-controlled Z
        diffuser.h(n_qubits - 1)
        if n_qubits > 1:
            diffuser.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        diffuser.h(n_qubits - 1)

        # X gates
        diffuser.x(range(n_qubits))

        # H gates
        diffuser.h(range(n_qubits))

        return diffuser
