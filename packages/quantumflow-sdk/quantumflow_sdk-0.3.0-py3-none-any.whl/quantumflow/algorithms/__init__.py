"""
QuantumFlow Algorithm Library.

Categories:
- compression: Token compression, QFT, amplitude amplification
- optimization: QAOA, Grover, quantum annealing
- machine_learning: VQE, QSVM, QNN
- cryptography: QKD, QRNG
- utility: Error correction, circuit optimization
"""

from quantumflow.algorithms.compression import (
    TokenCompression,
    QFTCompression,
    AmplitudeAmplification,
)
from quantumflow.algorithms.optimization import (
    QAOA,
    GroverSearch,
    QuantumAnnealing,
)
from quantumflow.algorithms.machine_learning import (
    VQE,
    QSVM,
    QNN,
)
from quantumflow.algorithms.cryptography import (
    QKD,
    QRNG,
)

__all__ = [
    # Compression
    "TokenCompression",
    "QFTCompression",
    "AmplitudeAmplification",
    # Optimization
    "QAOA",
    "GroverSearch",
    "QuantumAnnealing",
    # ML
    "VQE",
    "QSVM",
    "QNN",
    # Crypto
    "QKD",
    "QRNG",
]
