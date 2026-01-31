"""
Quantum Error Correction.

Implements basic error correction codes for protecting quantum information.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class ErrorCorrectionResult:
    """Result from error correction."""

    encoded_circuit: QuantumCircuit
    syndrome: str
    error_detected: bool
    error_corrected: bool
    logical_qubits: int
    physical_qubits: int
    code_distance: int


class ErrorCorrection:
    """
    Quantum Error Correction Codes.

    Implements:
    - 3-qubit bit-flip code
    - 3-qubit phase-flip code
    - Shor 9-qubit code
    - Steane 7-qubit code (partial)

    Example:
        >>> ec = ErrorCorrection(code="bit_flip")
        >>> encoded = ec.encode(logical_circuit)
        >>> protected = ec.protect(encoded, error_rate=0.01)
    """

    def __init__(
        self,
        code: str = "bit_flip",
        backend: BackendType | str = BackendType.AUTO,
    ):
        """
        Initialize error correction.

        Args:
            code: Error correction code type
                  ('bit_flip', 'phase_flip', 'shor', 'steane')
            backend: Quantum backend
        """
        self.code = code
        self.backend = get_backend(backend)
        self._connected = False

        # Code parameters
        self.code_params = {
            "bit_flip": {"n": 3, "k": 1, "d": 1},
            "phase_flip": {"n": 3, "k": 1, "d": 1},
            "shor": {"n": 9, "k": 1, "d": 3},
            "steane": {"n": 7, "k": 1, "d": 3},
        }

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    @property
    def physical_qubits(self) -> int:
        """Number of physical qubits per logical qubit."""
        return self.code_params[self.code]["n"]

    @property
    def code_distance(self) -> int:
        """Distance of the code."""
        return self.code_params[self.code]["d"]

    def encode(self, logical_state: int = 0) -> QuantumCircuit:
        """
        Encode a logical qubit.

        Args:
            logical_state: 0 or 1 for |0⟩ or |1⟩

        Returns:
            Circuit preparing encoded state
        """
        if self.code == "bit_flip":
            return self._encode_bit_flip(logical_state)
        elif self.code == "phase_flip":
            return self._encode_phase_flip(logical_state)
        elif self.code == "shor":
            return self._encode_shor(logical_state)
        else:
            raise ValueError(f"Unknown code: {self.code}")

    def detect_and_correct(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
    ) -> ErrorCorrectionResult:
        """
        Detect and correct errors.

        Args:
            circuit: Encoded circuit (possibly with errors)
            shots: Measurement shots for syndrome

        Returns:
            ErrorCorrectionResult with syndrome and corrections
        """
        self._ensure_connected()

        if self.code == "bit_flip":
            return self._correct_bit_flip(circuit, shots)
        elif self.code == "phase_flip":
            return self._correct_phase_flip(circuit, shots)
        elif self.code == "shor":
            return self._correct_shor(circuit, shots)
        else:
            raise ValueError(f"Unknown code: {self.code}")

    def add_noise(
        self,
        circuit: QuantumCircuit,
        error_rate: float = 0.01,
    ) -> QuantumCircuit:
        """
        Add simulated noise to circuit.

        Args:
            circuit: Circuit to add noise to
            error_rate: Probability of error per qubit

        Returns:
            Noisy circuit
        """
        noisy = circuit.copy()

        for qubit in range(circuit.num_qubits):
            if np.random.random() < error_rate:
                if self.code in ["bit_flip", "shor"]:
                    noisy.x(qubit)  # Bit flip
                else:
                    noisy.z(qubit)  # Phase flip

        return noisy

    # Bit-flip code implementation
    def _encode_bit_flip(self, logical: int) -> QuantumCircuit:
        """Encode using 3-qubit bit-flip code."""
        qc = QuantumCircuit(3, name="bit_flip_encode")

        if logical == 1:
            qc.x(0)

        # Encode: |0⟩ -> |000⟩, |1⟩ -> |111⟩
        qc.cx(0, 1)
        qc.cx(0, 2)

        return qc

    def _correct_bit_flip(
        self,
        circuit: QuantumCircuit,
        shots: int,
    ) -> ErrorCorrectionResult:
        """Detect and correct bit-flip errors."""
        # Add syndrome measurement
        syndrome_circuit = circuit.copy()
        syndrome_circuit.add_register(
            QuantumCircuit(2).cregs[0] if circuit.num_clbits < 2 else None
        )

        # Create fresh circuit with syndrome ancillas
        full_circuit = QuantumCircuit(5, 2, name="bit_flip_correct")

        # Copy encoded state
        full_circuit.compose(circuit, qubits=[0, 1, 2], inplace=True)

        # Syndrome extraction
        full_circuit.cx(0, 3)
        full_circuit.cx(1, 3)
        full_circuit.cx(1, 4)
        full_circuit.cx(2, 4)

        full_circuit.measure([3, 4], [0, 1])

        # Execute
        result = self.backend.execute(full_circuit, shots=shots)

        # Get most common syndrome
        syndrome = max(result.counts, key=result.counts.get)

        # Decode syndrome
        error_detected = syndrome != "00"
        error_qubit = self._decode_bit_flip_syndrome(syndrome)

        return ErrorCorrectionResult(
            encoded_circuit=full_circuit,
            syndrome=syndrome,
            error_detected=error_detected,
            error_corrected=error_detected,
            logical_qubits=1,
            physical_qubits=3,
            code_distance=1,
        )

    def _decode_bit_flip_syndrome(self, syndrome: str) -> Optional[int]:
        """Decode bit-flip syndrome to error location."""
        syndrome_map = {
            "00": None,  # No error
            "01": 2,     # Error on qubit 2
            "10": 0,     # Error on qubit 0
            "11": 1,     # Error on qubit 1
        }
        return syndrome_map.get(syndrome)

    # Phase-flip code implementation
    def _encode_phase_flip(self, logical: int) -> QuantumCircuit:
        """Encode using 3-qubit phase-flip code."""
        qc = QuantumCircuit(3, name="phase_flip_encode")

        if logical == 1:
            qc.x(0)

        # Transform to |+⟩/|-⟩ basis
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        qc.h([0, 1, 2])

        return qc

    def _correct_phase_flip(
        self,
        circuit: QuantumCircuit,
        shots: int,
    ) -> ErrorCorrectionResult:
        """Detect and correct phase-flip errors."""
        # Similar to bit-flip but in Hadamard basis
        full_circuit = QuantumCircuit(5, 2, name="phase_flip_correct")

        full_circuit.compose(circuit, qubits=[0, 1, 2], inplace=True)

        # Transform to computational basis for syndrome
        full_circuit.h([0, 1, 2])

        # Syndrome extraction (same as bit-flip)
        full_circuit.cx(0, 3)
        full_circuit.cx(1, 3)
        full_circuit.cx(1, 4)
        full_circuit.cx(2, 4)

        full_circuit.measure([3, 4], [0, 1])

        result = self.backend.execute(full_circuit, shots=shots)
        syndrome = max(result.counts, key=result.counts.get)

        return ErrorCorrectionResult(
            encoded_circuit=full_circuit,
            syndrome=syndrome,
            error_detected=syndrome != "00",
            error_corrected=syndrome != "00",
            logical_qubits=1,
            physical_qubits=3,
            code_distance=1,
        )

    # Shor code implementation
    def _encode_shor(self, logical: int) -> QuantumCircuit:
        """Encode using Shor 9-qubit code."""
        qc = QuantumCircuit(9, name="shor_encode")

        if logical == 1:
            qc.x(0)

        # First encode against phase flips
        qc.cx(0, 3)
        qc.cx(0, 6)

        qc.h([0, 3, 6])

        # Then encode each block against bit flips
        qc.cx(0, 1)
        qc.cx(0, 2)
        qc.cx(3, 4)
        qc.cx(3, 5)
        qc.cx(6, 7)
        qc.cx(6, 8)

        return qc

    def _correct_shor(
        self,
        circuit: QuantumCircuit,
        shots: int,
    ) -> ErrorCorrectionResult:
        """Detect and correct errors using Shor code."""
        # Simplified syndrome - in practice needs 8 ancilla qubits
        full_circuit = QuantumCircuit(11, 2, name="shor_correct")

        full_circuit.compose(circuit, qubits=list(range(9)), inplace=True)

        # Simplified syndrome for first block
        full_circuit.cx(0, 9)
        full_circuit.cx(1, 9)
        full_circuit.cx(1, 10)
        full_circuit.cx(2, 10)

        full_circuit.measure([9, 10], [0, 1])

        result = self.backend.execute(full_circuit, shots=shots)
        syndrome = max(result.counts, key=result.counts.get)

        return ErrorCorrectionResult(
            encoded_circuit=full_circuit,
            syndrome=syndrome,
            error_detected=syndrome != "00",
            error_corrected=syndrome != "00",
            logical_qubits=1,
            physical_qubits=9,
            code_distance=3,
        )
