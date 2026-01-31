"""
Tests for Quantum Token Compressor (Paper 1).
"""

import pytest
import numpy as np
import sys
sys.path.insert(0, "/Users/mandeepsingh/Desktop/quantumflow/backend/src")

from quantumflow.core.quantum_compressor import QuantumCompressor, CompressedResult


class TestQuantumCompressor:
    """Test suite for QuantumCompressor."""

    def test_compress_basic(self):
        """Test basic token compression."""
        compressor = QuantumCompressor(backend="simulator")
        tokens = [100, 200, 150, 175]

        result = compressor.compress(tokens)

        assert isinstance(result, CompressedResult)
        assert result.input_token_count == 4
        assert result.n_qubits == 2  # log2(4) = 2
        assert result.compression_ratio == 2.0
        assert result.compressed_circuit is not None

    def test_compression_ratio(self):
        """Test that compression achieves expected ratio."""
        compressor = QuantumCompressor(backend="simulator")

        # 8 tokens -> 3 qubits (2.67x compression)
        tokens = [10, 20, 30, 40, 50, 60, 70, 80]
        result = compressor.compress(tokens)

        assert result.n_qubits == 3
        assert result.compression_ratio > 2.0
        assert result.tokens_saved == 5

    def test_compression_percentage(self):
        """Test compression percentage calculation."""
        compressor = QuantumCompressor(backend="simulator")
        tokens = [100, 200, 300, 400, 500, 600, 700, 800]

        result = compressor.compress(tokens)

        # 8 tokens -> 3 qubits = 62.5% reduction
        assert result.compression_percentage > 50

    def test_amplitude_normalization(self):
        """Test that amplitudes are properly normalized."""
        compressor = QuantumCompressor(backend="simulator")
        tokens = [100, 200, 300, 400]

        result = compressor.compress(tokens)

        # Amplitudes should be unit normalized
        norm = np.linalg.norm(result.amplitudes)
        assert np.isclose(norm, 1.0, atol=1e-10)

    def test_execute_on_simulator(self):
        """Test execution on simulator backend."""
        compressor = QuantumCompressor(backend="simulator")
        tokens = [100, 200, 150, 175]

        result = compressor.compress_and_execute(tokens, shots=1024)

        assert result.execution_result is not None
        assert result.execution_result.counts is not None
        assert sum(result.execution_result.counts.values()) == 1024

    def test_empty_tokens_raises(self):
        """Test that empty token list raises error."""
        compressor = QuantumCompressor(backend="simulator")

        with pytest.raises(ValueError, match="empty"):
            compressor.compress([])

    def test_single_token(self):
        """Test compression of single token."""
        compressor = QuantumCompressor(backend="simulator")
        result = compressor.compress([100])

        assert result.n_qubits == 1
        assert result.compression_ratio == 1.0


class TestCompressedResult:
    """Test CompressedResult dataclass."""

    def test_tokens_saved(self):
        """Test tokens_saved calculation."""
        compressor = QuantumCompressor(backend="simulator")
        result = compressor.compress([10, 20, 30, 40, 50, 60, 70, 80])

        assert result.tokens_saved == result.input_token_count - result.n_qubits

    def test_metadata(self):
        """Test that metadata is populated."""
        compressor = QuantumCompressor(backend="simulator")
        result = compressor.compress([100, 200], compression_level=0.8)

        assert "compression_level" in result.metadata
        assert result.metadata["compression_level"] == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
