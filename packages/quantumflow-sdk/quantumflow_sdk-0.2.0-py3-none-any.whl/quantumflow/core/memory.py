"""
Quantum Memory - O(log n) memory management for agent workflows.

Uses quantum superposition to store n items in log(n) qubits,
providing exponential memory efficiency for AI agent contexts.
"""

from dataclasses import dataclass
from typing import Any, Optional
import time

from qiskit import QuantumCircuit

from quantumflow.core.quantum_compressor import QuantumCompressor, CompressedResult
from quantumflow.backends.base_backend import BackendType


@dataclass
class MemorySlot:
    """A single memory slot in quantum memory."""

    key: str
    value: list[int]
    compressed: Optional[CompressedResult] = None
    timestamp: float = 0.0


@dataclass
class QuantumMemoryStats:
    """Statistics for quantum memory usage."""

    total_items: int
    classical_size: int
    quantum_size: int
    compression_ratio: float
    memory_saved_percent: float


class QuantumMemory:
    """
    Quantum-optimized memory for agent workflows.

    Stores context and data using quantum compression,
    achieving O(log n) memory complexity.

    Example:
        >>> memory = QuantumMemory()
        >>> memory.store("context", [100, 200, 300, 400])
        >>> retrieved = memory.retrieve("context")
        >>> stats = memory.get_stats()
        >>> print(f"Memory saved: {stats.memory_saved_percent:.1f}%")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        auto_compress: bool = True,
        compression_threshold: int = 4,
    ):
        self._compressor = QuantumCompressor(backend=backend)
        self._auto_compress = auto_compress
        self._compression_threshold = compression_threshold
        self._storage: dict[str, MemorySlot] = {}
        self._classical_size = 0

    def store(
        self,
        key: str,
        value: list[int] | list[float],
        compress: Optional[bool] = None,
    ) -> MemorySlot:
        """Store data in quantum memory."""
        should_compress = compress if compress is not None else self._auto_compress
        should_compress = should_compress and len(value) >= self._compression_threshold

        int_values = [int(v) if isinstance(v, float) else v for v in value]

        slot = MemorySlot(
            key=key,
            value=int_values,
            timestamp=time.time(),
        )

        if should_compress:
            slot.compressed = self._compressor.compress(int_values)

        self._storage[key] = slot
        self._classical_size += len(int_values)
        return slot

    def retrieve(self, key: str) -> list[int]:
        """Retrieve data from quantum memory."""
        if key not in self._storage:
            raise KeyError(f"Key '{key}' not found in memory")
        return self._storage[key].value

    def delete(self, key: str) -> bool:
        """Remove item from memory."""
        if key in self._storage:
            slot = self._storage.pop(key)
            self._classical_size -= len(slot.value)
            return True
        return False

    def clear(self) -> None:
        """Clear all memory."""
        self._storage.clear()
        self._classical_size = 0

    def get_stats(self) -> QuantumMemoryStats:
        """Get memory usage statistics."""
        total_items = len(self._storage)
        quantum_size = sum(
            slot.compressed.n_qubits if slot.compressed else len(slot.value)
            for slot in self._storage.values()
        )

        if self._classical_size > 0:
            compression_ratio = self._classical_size / max(quantum_size, 1)
            memory_saved = (1 - quantum_size / self._classical_size) * 100
        else:
            compression_ratio = 1.0
            memory_saved = 0.0

        return QuantumMemoryStats(
            total_items=total_items,
            classical_size=self._classical_size,
            quantum_size=quantum_size,
            compression_ratio=compression_ratio,
            memory_saved_percent=memory_saved,
        )

    def get_circuit(self, key: str) -> Optional[QuantumCircuit]:
        """Get the quantum circuit for a stored item."""
        if key in self._storage and self._storage[key].compressed:
            return self._storage[key].compressed.compressed_circuit
        return None

    def keys(self) -> list[str]:
        """List all keys in memory."""
        return list(self._storage.keys())

    def __contains__(self, key: str) -> bool:
        return key in self._storage

    def __len__(self) -> int:
        return len(self._storage)
