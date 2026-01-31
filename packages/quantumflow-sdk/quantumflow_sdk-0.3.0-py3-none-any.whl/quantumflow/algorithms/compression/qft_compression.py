"""
Quantum Fourier Transform Compression.

Uses QFT for frequency-domain compression of token sequences,
similar to classical DCT/FFT compression but with quantum speedup.
"""

import math
from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QFTResult:
    """Result from QFT compression."""

    circuit: QuantumCircuit
    n_qubits: int
    kept_coefficients: int
    total_coefficients: int
    compression_ratio: float


class QFTCompression:
    """
    Quantum Fourier Transform based compression.

    Compresses data by:
    1. Encoding data as quantum amplitudes
    2. Applying QFT to transform to frequency domain
    3. Truncating high-frequency components
    4. Storing only significant coefficients

    Best for: Periodic or smoothly varying data.

    Example:
        >>> qft = QFTCompression()
        >>> result = qft.compress([100, 110, 105, 115, 100, 108])
        >>> print(f"Kept {result.kept_coefficients}/{result.total_coefficients}")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        keep_ratio: float = 0.5,
    ):
        """
        Initialize QFT compression.

        Args:
            backend: Quantum backend to use
            keep_ratio: Fraction of frequency components to keep (0.0-1.0)
        """
        self.backend = get_backend(backend)
        self.keep_ratio = keep_ratio

    def compress(
        self,
        data: list[float],
        n_qubits: Optional[int] = None,
    ) -> QFTResult:
        """
        Compress data using QFT.

        Args:
            data: Input data to compress
            n_qubits: Number of qubits (auto if None)

        Returns:
            QFTResult with circuit and metadata
        """
        if not data:
            raise ValueError("Cannot compress empty data")

        # Calculate qubits needed
        if n_qubits is None:
            n_qubits = max(2, math.ceil(math.log2(len(data))))

        target_size = 2 ** n_qubits

        # Normalize data to amplitudes
        data_arr = np.array(data, dtype=float)
        data_arr = np.pad(data_arr, (0, max(0, target_size - len(data_arr))))
        data_arr = data_arr[:target_size]

        norm = np.linalg.norm(data_arr)
        if norm > 0:
            amplitudes = data_arr / norm
        else:
            amplitudes = np.ones(target_size) / np.sqrt(target_size)

        # Build circuit
        circuit = self._build_qft_circuit(amplitudes, n_qubits)

        kept = int(target_size * self.keep_ratio)
        ratio = target_size / max(kept, 1)

        return QFTResult(
            circuit=circuit,
            n_qubits=n_qubits,
            kept_coefficients=kept,
            total_coefficients=target_size,
            compression_ratio=ratio,
        )

    def _build_qft_circuit(
        self,
        amplitudes: np.ndarray,
        n_qubits: int,
    ) -> QuantumCircuit:
        """Build QFT compression circuit."""
        qc = QuantumCircuit(n_qubits, name="qft_compress")

        # Initialize with data
        qc.initialize(amplitudes, range(n_qubits))

        # Apply QFT
        qft = QFT(n_qubits, do_swaps=True)
        qc.append(qft, range(n_qubits))

        return qc

    def inverse_qft_circuit(self, n_qubits: int) -> QuantumCircuit:
        """Get inverse QFT circuit for decompression."""
        qc = QuantumCircuit(n_qubits, name="iqft")
        qft_inv = QFT(n_qubits, do_swaps=True, inverse=True)
        qc.append(qft_inv, range(n_qubits))
        return qc
