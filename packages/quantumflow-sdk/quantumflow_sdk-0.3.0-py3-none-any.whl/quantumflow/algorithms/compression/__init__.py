"""Compression Algorithms."""

from quantumflow.algorithms.compression.token_compression import TokenCompression
from quantumflow.algorithms.compression.qft_compression import QFTCompression
from quantumflow.algorithms.compression.amplitude_amplification import AmplitudeAmplification

__all__ = ["TokenCompression", "QFTCompression", "AmplitudeAmplification"]
