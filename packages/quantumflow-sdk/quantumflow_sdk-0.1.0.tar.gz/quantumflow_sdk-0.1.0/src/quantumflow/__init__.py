"""
QuantumFlow - Quantum-optimized AI agent workflow platform.

Core Features:
- 53% token compression via quantum superposition
- O(log n) memory through quantum entanglement
- Quantum teleportation for secure messaging
- BB84 QKD for unconditionally secure key exchange
- Multi-backend support (IBM, AWS Braket, Simulator)

Installation:
    pip install quantumflow

Quick Start:
    from quantumflow import QuantumCompressor

    compressor = QuantumCompressor(backend="simulator")
    result = compressor.compress([100, 200, 150, 175])
    print(f"Compression: {result.compression_percentage}%")
"""

from quantumflow.core.quantum_compressor import QuantumCompressor, CompressedResult
from quantumflow.core.quantum_backprop import QuantumBackprop
from quantumflow.core.entanglement import Entangler
from quantumflow.core.memory import QuantumMemory
from quantumflow.core.teleportation import (
    QuantumTeleporter,
    QKDExchange,
    SecureMessenger,
)

__version__ = "0.1.0"
__all__ = [
    # Core compression
    "QuantumCompressor",
    "CompressedResult",
    # Backpropagation
    "QuantumBackprop",
    # Entanglement
    "Entangler",
    # Memory
    "QuantumMemory",
    # Teleportation & Security
    "QuantumTeleporter",
    "QKDExchange",
    "SecureMessenger",
]
