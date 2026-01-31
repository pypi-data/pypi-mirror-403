"""
Token Compression Algorithm.

Enhanced version of Paper 1 compression with additional features:
- Adaptive qubit allocation
- Batch compression
- Streaming support
"""

import math
from dataclasses import dataclass
from typing import Optional, Iterator
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class CompressionConfig:
    """Configuration for token compression."""

    min_compression_ratio: float = 1.5
    max_qubits: int = 20
    adaptive: bool = True
    error_mitigation: bool = False


@dataclass
class CompressedBatch:
    """A batch of compressed tokens."""

    circuit: QuantumCircuit
    original_size: int
    compressed_size: int
    batch_index: int
    amplitudes: np.ndarray


class TokenCompression:
    """
    Advanced token compression using quantum amplitude encoding.

    Features:
    - Adaptive qubit allocation based on token distribution
    - Batch processing for large token sequences
    - Streaming compression for real-time applications

    Example:
        >>> tc = TokenCompression()
        >>> result = tc.compress([100, 200, 300, 400])
        >>> print(f"Ratio: {result.compression_ratio}x")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        config: Optional[CompressionConfig] = None,
    ):
        self.backend = get_backend(backend)
        self.config = config or CompressionConfig()
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def compress(
        self,
        tokens: list[int],
        n_qubits: Optional[int] = None,
    ) -> CompressedBatch:
        """
        Compress a list of tokens.

        Args:
            tokens: Integer tokens to compress
            n_qubits: Override automatic qubit calculation

        Returns:
            CompressedBatch with circuit and metadata
        """
        if not tokens:
            raise ValueError("Cannot compress empty token list")

        # Calculate optimal qubits
        if n_qubits is None:
            n_qubits = self._calculate_qubits(tokens)

        n_qubits = min(n_qubits, self.config.max_qubits)

        # Normalize to amplitudes
        amplitudes = self._tokens_to_amplitudes(tokens, n_qubits)

        # Build circuit
        circuit = self._build_circuit(amplitudes, n_qubits)

        return CompressedBatch(
            circuit=circuit,
            original_size=len(tokens),
            compressed_size=n_qubits,
            batch_index=0,
            amplitudes=amplitudes,
        )

    def compress_batch(
        self,
        tokens: list[int],
        batch_size: int = 256,
    ) -> list[CompressedBatch]:
        """
        Compress tokens in batches.

        Args:
            tokens: All tokens to compress
            batch_size: Max tokens per batch (must be power of 2)

        Returns:
            List of CompressedBatch objects
        """
        # Ensure batch_size is power of 2
        batch_size = 2 ** int(math.log2(batch_size))

        batches = []
        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]
            batch = self.compress(batch_tokens)
            batch.batch_index = i // batch_size
            batches.append(batch)

        return batches

    def compress_stream(
        self,
        token_iterator: Iterator[int],
        buffer_size: int = 64,
    ) -> Iterator[CompressedBatch]:
        """
        Stream compress tokens as they arrive.

        Args:
            token_iterator: Iterator yielding tokens
            buffer_size: Tokens to buffer before compression

        Yields:
            CompressedBatch objects
        """
        buffer = []
        batch_idx = 0

        for token in token_iterator:
            buffer.append(token)

            if len(buffer) >= buffer_size:
                batch = self.compress(buffer)
                batch.batch_index = batch_idx
                yield batch
                buffer = []
                batch_idx += 1

        # Final batch
        if buffer:
            batch = self.compress(buffer)
            batch.batch_index = batch_idx
            yield batch

    def decompress(
        self,
        batch: CompressedBatch,
        shots: int = 1024,
    ) -> list[int]:
        """
        Decompress a batch back to tokens.

        Args:
            batch: CompressedBatch to decompress
            shots: Measurement shots for reconstruction

        Returns:
            Reconstructed token list
        """
        self._ensure_connected()

        result = self.backend.execute(batch.circuit, shots=shots)

        # Reconstruct from statevector if available
        if result.statevector is not None:
            probs = np.abs(result.statevector) ** 2
        else:
            # Reconstruct from measurement counts
            probs = np.zeros(2 ** batch.compressed_size)
            for state, count in result.counts.items():
                idx = int(state, 2)
                probs[idx] = count / shots

        # Scale back to token range
        # This is approximate - exact reconstruction requires statevector
        max_prob = np.max(probs)
        if max_prob > 0:
            tokens = (probs[:batch.original_size] / max_prob * 255).astype(int)
        else:
            tokens = np.zeros(batch.original_size, dtype=int)

        return tokens.tolist()

    def _calculate_qubits(self, tokens: list[int]) -> int:
        """Calculate optimal qubit count based on token distribution."""
        n = len(tokens)
        base_qubits = max(1, math.ceil(math.log2(n)))

        if self.config.adaptive:
            # Analyze token distribution
            tokens_arr = np.array(tokens)
            variance = np.var(tokens_arr)

            # High variance = need more precision = more qubits
            if variance > 1000:
                base_qubits += 1

        return base_qubits

    def _tokens_to_amplitudes(
        self,
        tokens: list[int],
        n_qubits: int,
    ) -> np.ndarray:
        """Convert tokens to normalized quantum amplitudes."""
        target_size = 2 ** n_qubits

        tokens_arr = np.array(tokens, dtype=float)
        tokens_arr = np.maximum(tokens_arr, 1e-10)

        # Pad to target size
        if len(tokens_arr) < target_size:
            tokens_arr = np.pad(
                tokens_arr,
                (0, target_size - len(tokens_arr)),
                constant_values=1e-10
            )
        else:
            tokens_arr = tokens_arr[:target_size]

        # Normalize
        norm = np.linalg.norm(tokens_arr)
        return tokens_arr / norm if norm > 0 else tokens_arr

    def _build_circuit(
        self,
        amplitudes: np.ndarray,
        n_qubits: int,
    ) -> QuantumCircuit:
        """Build quantum circuit for amplitude encoding."""
        qc = QuantumCircuit(n_qubits, name="token_compress")
        qc.initialize(amplitudes, range(n_qubits))
        return qc

    @property
    def compression_ratio(self) -> float:
        """Expected compression ratio based on config."""
        return self.config.min_compression_ratio
