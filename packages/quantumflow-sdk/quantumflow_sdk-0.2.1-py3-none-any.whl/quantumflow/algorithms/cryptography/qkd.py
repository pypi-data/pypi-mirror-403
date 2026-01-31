"""
Quantum Key Distribution (QKD).

Implements BB84 protocol for secure key exchange.
"""

import secrets
from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QKDResult:
    """Result from QKD key generation."""

    shared_key: str
    key_length: int
    raw_key_length: int
    error_rate: float
    is_secure: bool
    alice_bases: str
    bob_bases: str


class QKD:
    """
    Quantum Key Distribution using BB84 Protocol.

    Enables two parties (Alice and Bob) to generate a shared secret key
    with information-theoretic security guaranteed by quantum mechanics.

    Protocol:
    1. Alice prepares qubits in random states (Z or X basis)
    2. Bob measures in random bases
    3. They compare bases publicly
    4. Keep only matching-basis measurements
    5. Check for eavesdropping via error rate

    Example:
        >>> qkd = QKD()
        >>> result = qkd.generate_key(key_length=128)
        >>> print(f"Shared key: {result.shared_key[:32]}...")
        >>> print(f"Secure: {result.is_secure}")
    """

    def __init__(
        self,
        backend: BackendType | str = BackendType.AUTO,
        error_threshold: float = 0.11,
    ):
        """
        Initialize QKD.

        Args:
            backend: Quantum backend
            error_threshold: Max tolerable error rate (11% for BB84)
        """
        self.backend = get_backend(backend)
        self.error_threshold = error_threshold
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def generate_key(
        self,
        key_length: int = 256,
        with_eavesdropper: bool = False,
    ) -> QKDResult:
        """
        Generate a shared cryptographic key.

        Args:
            key_length: Desired final key length in bits
            with_eavesdropper: Simulate eavesdropping (for testing)

        Returns:
            QKDResult with shared key
        """
        self._ensure_connected()

        # Need ~4x raw bits due to basis mismatch and error correction
        raw_length = key_length * 4

        # Step 1: Alice generates random bits and bases
        alice_bits = self._random_bits(raw_length)
        alice_bases = self._random_bits(raw_length)  # 0=Z, 1=X

        # Step 2: Alice prepares qubits
        alice_states = self._prepare_states(alice_bits, alice_bases)

        # Step 3: (Optional) Eve intercepts
        if with_eavesdropper:
            eve_bases = self._random_bits(raw_length)
            alice_states = self._eavesdrop(alice_states, eve_bases)

        # Step 4: Bob chooses random bases and measures
        bob_bases = self._random_bits(raw_length)
        bob_bits = self._measure_states(alice_states, bob_bases)

        # Step 5: Sifting - keep only matching bases
        sifted_alice = []
        sifted_bob = []

        for i in range(raw_length):
            if alice_bases[i] == bob_bases[i]:
                sifted_alice.append(alice_bits[i])
                sifted_bob.append(bob_bits[i])

        # Step 6: Error estimation (use subset)
        check_length = min(len(sifted_alice) // 4, 50)
        errors = sum(
            sifted_alice[i] != sifted_bob[i]
            for i in range(check_length)
        )
        error_rate = errors / check_length if check_length > 0 else 0

        # Remove check bits
        final_alice = sifted_alice[check_length:]
        final_bob = sifted_bob[check_length:]

        # Step 7: Check security
        is_secure = error_rate < self.error_threshold

        # Create key (truncate to desired length)
        shared_key = ''.join(str(b) for b in final_alice[:key_length])

        return QKDResult(
            shared_key=shared_key,
            key_length=len(shared_key),
            raw_key_length=raw_length,
            error_rate=error_rate,
            is_secure=is_secure,
            alice_bases=''.join(str(b) for b in alice_bases[:20]) + "...",
            bob_bases=''.join(str(b) for b in bob_bases[:20]) + "...",
        )

    def _random_bits(self, n: int) -> list[int]:
        """Generate n random bits."""
        return [secrets.randbelow(2) for _ in range(n)]

    def _prepare_states(
        self,
        bits: list[int],
        bases: list[int],
    ) -> list[tuple[int, int]]:
        """Prepare quantum states based on bits and bases."""
        return list(zip(bits, bases))

    def _measure_states(
        self,
        states: list[tuple[int, int]],
        bases: list[int],
    ) -> list[int]:
        """Measure states in given bases using quantum circuit."""
        results = []

        for (bit, prep_basis), meas_basis in zip(states, bases):
            circuit = QuantumCircuit(1, 1)

            # Prepare state
            if bit == 1:
                circuit.x(0)
            if prep_basis == 1:  # X basis
                circuit.h(0)

            # Measure in basis
            if meas_basis == 1:  # X basis
                circuit.h(0)
            circuit.measure(0, 0)

            # Execute
            result = self.backend.execute(circuit, shots=1)
            measured = int(list(result.counts.keys())[0])
            results.append(measured)

        return results

    def _eavesdrop(
        self,
        states: list[tuple[int, int]],
        eve_bases: list[int],
    ) -> list[tuple[int, int]]:
        """Simulate eavesdropper (introduces errors)."""
        disturbed = []

        for (bit, basis), eve_basis in zip(states, eve_bases):
            if eve_basis != basis:
                # Eve's measurement disturbs state (50% chance of error)
                if secrets.randbelow(2) == 0:
                    bit = 1 - bit  # Flip bit
            disturbed.append((bit, basis))

        return disturbed


class BB84(QKD):
    """Alias for QKD (BB84 protocol)."""
    pass
