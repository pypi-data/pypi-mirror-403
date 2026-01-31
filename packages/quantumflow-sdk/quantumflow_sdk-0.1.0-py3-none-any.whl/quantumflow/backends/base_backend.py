"""
Base Quantum Backend - Abstract interface for quantum hardware/simulators.

Supports:
- IBM Quantum (ibm_fez, etc.)
- Google Quantum AI
- AWS Braket
- Local simulators (Qiskit Aer)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import numpy as np

from qiskit import QuantumCircuit


class BackendType(str, Enum):
    """Supported quantum backend types."""

    SIMULATOR = "simulator"
    IBM = "ibm"
    GOOGLE = "google"
    AWS = "aws"
    AUTO = "auto"


@dataclass
class ExecutionResult:
    """Result from quantum circuit execution."""

    counts: dict[str, int]
    statevector: Optional[np.ndarray] = None
    shots: int = 1024
    backend_name: str = "unknown"
    execution_time_ms: float = 0.0
    fidelity: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def probabilities(self) -> dict[str, float]:
        """Convert counts to probabilities."""
        total = sum(self.counts.values())
        return {k: v / total for k, v in self.counts.items()}

    @property
    def most_likely_state(self) -> str:
        """Get the most frequently measured state."""
        return max(self.counts, key=self.counts.get)

    def get_amplitude(self, state: str) -> complex:
        """Get amplitude for a specific basis state."""
        if self.statevector is None:
            raise ValueError("Statevector not available for this result")
        idx = int(state, 2)
        return self.statevector[idx]


class QuantumBackend(ABC):
    """Abstract base class for quantum backends."""

    def __init__(self, backend_type: BackendType = BackendType.SIMULATOR):
        self.backend_type = backend_type
        self._is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the quantum backend."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the quantum backend."""
        pass

    @abstractmethod
    def execute(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        optimization_level: int = 1,
    ) -> ExecutionResult:
        """Execute a quantum circuit on this backend."""
        pass

    @abstractmethod
    def get_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """Get the statevector from a circuit (simulator only)."""
        pass

    @property
    @abstractmethod
    def max_qubits(self) -> int:
        """Maximum number of qubits supported by this backend."""
        pass

    @property
    @abstractmethod
    def is_simulator(self) -> bool:
        """Whether this backend is a simulator."""
        pass

    @property
    def is_connected(self) -> bool:
        """Whether the backend is currently connected."""
        return self._is_connected

    def validate_circuit(self, circuit: QuantumCircuit) -> bool:
        """Validate that a circuit can run on this backend."""
        if circuit.num_qubits > self.max_qubits:
            raise ValueError(
                f"Circuit requires {circuit.num_qubits} qubits, "
                f"but backend only supports {self.max_qubits}"
            )
        return True

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def get_backend(
    backend_type: BackendType | str = BackendType.AUTO,
    **kwargs,
) -> QuantumBackend:
    """
    Factory function to get the appropriate quantum backend.

    Args:
        backend_type: Type of backend to use
        **kwargs: Backend-specific configuration

    Returns:
        Configured QuantumBackend instance
    """
    if isinstance(backend_type, str):
        backend_type = BackendType(backend_type.lower())

    if backend_type == BackendType.AUTO:
        # Try IBM first if available, fall back to simulator
        try:
            from quantumflow.backends.ibm_backend import IBMBackend
            if IBMBackend is not None:
                backend = IBMBackend(**kwargs)
                if backend.connect():
                    return backend
        except Exception:
            pass

        from quantumflow.backends.simulator_backend import SimulatorBackend
        return SimulatorBackend(**kwargs)

    elif backend_type == BackendType.SIMULATOR:
        from quantumflow.backends.simulator_backend import SimulatorBackend
        return SimulatorBackend(**kwargs)

    elif backend_type == BackendType.IBM:
        try:
            from quantumflow.backends.ibm_backend import IBMBackend
            return IBMBackend(**kwargs)
        except ImportError:
            raise ImportError("IBM backend requires qiskit-ibm-runtime. Install with: pip install qiskit-ibm-runtime")

    elif backend_type == BackendType.GOOGLE:
        raise NotImplementedError("Google Quantum backend not yet implemented")

    elif backend_type == BackendType.AWS:
        try:
            from quantumflow.backends.braket_backend import BraketBackend
            return BraketBackend(**kwargs)
        except ImportError:
            raise ImportError(
                "AWS Braket backend requires amazon-braket-sdk. "
                "Install with: pip install amazon-braket-sdk"
            )

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
