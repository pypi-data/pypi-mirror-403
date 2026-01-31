"""
Quantum Random Number Generator (QRNG).

Generates true random numbers using quantum mechanics.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QRNGResult:
    """Result from quantum random number generation."""

    bits: str
    integer: int
    float_value: float
    n_qubits_used: int
    entropy_bits: int


class QRNG:
    """
    Quantum Random Number Generator.

    Generates cryptographically secure random numbers using
    quantum superposition and measurement.

    Unlike classical PRNGs:
    - Randomness is fundamental, not pseudo
    - Information-theoretically unpredictable
    - Certified by quantum mechanics

    Example:
        >>> qrng = QRNG()
        >>> bits = qrng.random_bits(128)
        >>> number = qrng.random_int(0, 1000)
        >>> value = qrng.random_float()
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        max_qubits: int = 20,
    ):
        """
        Initialize QRNG.

        Args:
            backend: Quantum backend
            max_qubits: Maximum qubits per generation
        """
        self.backend = get_backend(backend)
        self.max_qubits = max_qubits
        self._connected = False
        self._buffer: list[int] = []

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def random_bits(self, n: int) -> str:
        """
        Generate n random bits.

        Args:
            n: Number of bits to generate

        Returns:
            String of '0' and '1' characters
        """
        self._ensure_connected()

        bits = []

        while len(bits) < n:
            # Generate batch of bits
            batch_size = min(self.max_qubits, n - len(bits))
            batch = self._generate_batch(batch_size)
            bits.extend(batch)

        return ''.join(str(b) for b in bits[:n])

    def random_int(self, min_val: int = 0, max_val: int = 2**32 - 1) -> int:
        """
        Generate random integer in range [min_val, max_val].

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            Random integer
        """
        range_size = max_val - min_val + 1
        bits_needed = int(np.ceil(np.log2(range_size))) + 1

        # Rejection sampling to avoid bias
        while True:
            bits = self.random_bits(bits_needed)
            value = int(bits, 2)
            if value < range_size:
                return min_val + value

    def random_float(self) -> float:
        """
        Generate random float in [0, 1).

        Returns:
            Random float with 53 bits of precision
        """
        # IEEE 754 double has 53 bits of mantissa
        bits = self.random_bits(53)
        value = int(bits, 2)
        return value / (2**53)

    def random_bytes(self, n: int) -> bytes:
        """
        Generate n random bytes.

        Args:
            n: Number of bytes

        Returns:
            Random bytes
        """
        bits = self.random_bits(n * 8)
        return int(bits, 2).to_bytes(n, byteorder='big')

    def random_gaussian(self, mean: float = 0.0, std: float = 1.0) -> float:
        """
        Generate Gaussian distributed random number.

        Uses Box-Muller transform.

        Args:
            mean: Mean of distribution
            std: Standard deviation

        Returns:
            Gaussian random number
        """
        u1 = self.random_float()
        u2 = self.random_float()

        # Avoid log(0)
        while u1 < 1e-10:
            u1 = self.random_float()

        # Box-Muller transform
        z = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)

        return mean + std * z

    def random_choice(self, items: list) -> any:
        """
        Randomly select an item from list.

        Args:
            items: List to choose from

        Returns:
            Randomly selected item
        """
        if not items:
            raise ValueError("Cannot choose from empty list")

        idx = self.random_int(0, len(items) - 1)
        return items[idx]

    def random_shuffle(self, items: list) -> list:
        """
        Randomly shuffle a list.

        Args:
            items: List to shuffle

        Returns:
            Shuffled copy of list
        """
        result = items.copy()
        n = len(result)

        # Fisher-Yates shuffle
        for i in range(n - 1, 0, -1):
            j = self.random_int(0, i)
            result[i], result[j] = result[j], result[i]

        return result

    def _generate_batch(self, n_qubits: int) -> list[int]:
        """Generate batch of random bits using quantum circuit."""
        circuit = QuantumCircuit(n_qubits, n_qubits)

        # Put all qubits in superposition
        circuit.h(range(n_qubits))

        # Measure
        circuit.measure(range(n_qubits), range(n_qubits))

        # Execute with single shot
        result = self.backend.execute(circuit, shots=1)

        # Extract bits
        bitstring = list(result.counts.keys())[0]
        return [int(b) for b in bitstring]

    def get_result(self, n_bits: int) -> QRNGResult:
        """
        Generate random bits with full result details.

        Args:
            n_bits: Number of bits

        Returns:
            QRNGResult with all details
        """
        bits = self.random_bits(n_bits)

        return QRNGResult(
            bits=bits,
            integer=int(bits, 2) if bits else 0,
            float_value=int(bits, 2) / (2**n_bits) if bits else 0.0,
            n_qubits_used=min(self.max_qubits, n_bits),
            entropy_bits=n_bits,
        )
