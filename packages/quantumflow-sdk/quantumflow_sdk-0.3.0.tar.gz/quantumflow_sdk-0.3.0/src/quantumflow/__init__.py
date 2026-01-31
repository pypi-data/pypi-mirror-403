"""
QuantumFlow - Quantum-optimized AI agent workflow platform.

Core Features:
- 53% token compression via quantum superposition
- O(log n) memory through quantum entanglement
- Quantum teleportation for secure messaging
- BB84 QKD for unconditionally secure key exchange
- Workflow orchestration for chaining quantum operations
- Multi-backend support (IBM, AWS Braket, Simulator)

Installation:
    pip install quantumflow-sdk

Quick Start:
    from quantumflow import QuantumCompressor

    compressor = QuantumCompressor(backend="simulator")
    result = compressor.compress([100, 200, 150, 175])
    print(f"Compression: {result.compression_percentage}%")

Workflow Example:
    from quantumflow import QuantumWorkflow

    workflow = QuantumWorkflow()
    workflow.add_step("compress", params={"tokens": [100, 200, 150]})
    workflow.add_step("qkd", params={"key_length": 256})
    result = workflow.execute()
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
from quantumflow.core.workflow import QuantumWorkflow, WorkflowResult

__version__ = "0.2.1"
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
    # Workflow
    "QuantumWorkflow",
    "WorkflowResult",
]
