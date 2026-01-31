"""QuantumFlow Backends - Quantum hardware and simulator backends."""

from quantumflow.backends.base_backend import (
    QuantumBackend,
    BackendType,
    ExecutionResult,
    get_backend,
)
from quantumflow.backends.simulator_backend import SimulatorBackend

# Lazy import for optional IBM backend
try:
    from quantumflow.backends.ibm_backend import IBMBackend
except ImportError:
    IBMBackend = None  # type: ignore

# Lazy import for optional AWS Braket backend
try:
    from quantumflow.backends.braket_backend import BraketBackend, BRAKET_DEVICES
except ImportError:
    BraketBackend = None  # type: ignore
    BRAKET_DEVICES = {}

__all__ = [
    "QuantumBackend",
    "BackendType",
    "ExecutionResult",
    "get_backend",
    "SimulatorBackend",
    "IBMBackend",
    "BraketBackend",
    "BRAKET_DEVICES",
]
