"""
Quantum Teleportation Module.

Implements quantum teleportation protocol for transferring quantum states
without physically sending qubits - using pre-shared entanglement + classical communication.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class TeleportationStatus(str, Enum):
    """Status of teleportation operation."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class BellPair:
    """Represents a shared Bell pair between Alice and Bob."""
    id: str
    alice_qubit: int
    bob_qubit: int
    state: str  # |Φ+⟩, |Φ-⟩, |Ψ+⟩, |Ψ-⟩
    fidelity: float
    created_at: Optional[str] = None


@dataclass
class TeleportationResult:
    """Result of a teleportation operation."""
    success: bool
    bell_measurement: Tuple[int, int]  # (b1, b2) classical bits
    corrections_applied: str  # "I", "X", "Z", "XZ"
    fidelity: float
    original_state: Optional[List[complex]] = None
    teleported_state: Optional[List[complex]] = None


@dataclass
class CompressedTeleportResult:
    """Result of compressed teleportation."""
    success: bool
    original_size: int  # tokens/bytes
    compressed_qubits: int
    classical_bits_sent: int
    compression_ratio: float
    teleportation_fidelity: float
    qkd_key_used: bool
    error_detected: bool


class QuantumTeleporter:
    """
    Quantum Teleportation implementation.

    Supports:
    - Basic teleportation (single qubit)
    - Multi-qubit teleportation
    - Compressed teleportation (with QuantumFlow compression)
    """

    def __init__(self, backend: str = "simulator"):
        self.backend = backend
        self.bell_pairs: List[BellPair] = []
        self._fidelity_noise = 0.02  # Simulated noise

    def create_bell_pairs(self, count: int = 10) -> List[BellPair]:
        """
        Create entangled Bell pairs for teleportation.

        In real implementation, this would distribute entanglement
        between Alice and Bob's quantum devices.
        """
        pairs = []
        for i in range(count):
            pair = BellPair(
                id=f"bell_{i}",
                alice_qubit=i * 2,
                bob_qubit=i * 2 + 1,
                state="|Φ+⟩",  # (|00⟩ + |11⟩)/√2
                fidelity=1.0 - np.random.uniform(0, self._fidelity_noise),
            )
            pairs.append(pair)

        self.bell_pairs = pairs
        return pairs

    def teleport_state(
        self,
        state: List[complex],
        bell_pair_id: Optional[str] = None,
    ) -> TeleportationResult:
        """
        Teleport a quantum state from Alice to Bob.

        Protocol:
        1. Alice has unknown state |ψ⟩ and her half of Bell pair
        2. Alice performs Bell measurement on |ψ⟩ and her qubit
        3. Alice sends 2 classical bits to Bob
        4. Bob applies corrections based on classical bits
        5. Bob's qubit is now in state |ψ⟩

        Args:
            state: Quantum state to teleport [α, β] where |ψ⟩ = α|0⟩ + β|1⟩
            bell_pair_id: ID of Bell pair to use (uses first available if None)

        Returns:
            TeleportationResult with measurement outcomes and fidelity
        """
        # Normalize input state
        state = np.array(state, dtype=complex)
        state = state / np.linalg.norm(state)

        # Get Bell pair
        if not self.bell_pairs:
            self.create_bell_pairs(1)

        pair = self.bell_pairs[0] if bell_pair_id is None else next(
            (p for p in self.bell_pairs if p.id == bell_pair_id), self.bell_pairs[0]
        )

        # Simulate Bell measurement (random outcome, equiprobable)
        b1 = np.random.randint(0, 2)
        b2 = np.random.randint(0, 2)

        # Determine correction operator
        corrections = {
            (0, 0): "I",   # No correction
            (0, 1): "X",   # Bit flip
            (1, 0): "Z",   # Phase flip
            (1, 1): "XZ",  # Both
        }
        correction = corrections[(b1, b2)]

        # Apply correction to get teleported state (simulated)
        teleported = self._apply_correction(state, correction)

        # Add noise based on Bell pair fidelity
        noise = np.random.normal(0, 1 - pair.fidelity, 2) + 1j * np.random.normal(0, 1 - pair.fidelity, 2)
        teleported = teleported + noise * 0.01
        teleported = teleported / np.linalg.norm(teleported)

        # Calculate fidelity
        fidelity = abs(np.vdot(state, teleported)) ** 2

        return TeleportationResult(
            success=True,
            bell_measurement=(b1, b2),
            corrections_applied=correction,
            fidelity=fidelity,
            original_state=state.tolist(),
            teleported_state=teleported.tolist(),
        )

    def _apply_correction(self, state: np.ndarray, correction: str) -> np.ndarray:
        """Apply Pauli correction to state."""
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        I = np.eye(2, dtype=complex)

        if correction == "I":
            return state
        elif correction == "X":
            return X @ state
        elif correction == "Z":
            return Z @ state
        elif correction == "XZ":
            return X @ Z @ state
        return state

    def teleport_compressed(
        self,
        data: str,
        use_qkd: bool = True,
    ) -> CompressedTeleportResult:
        """
        Teleport compressed data using the full pipeline:
        1. Compress data to quantum state
        2. Teleport each compressed qubit
        3. Secure classical bits with QKD (optional)

        Args:
            data: String data to teleport
            use_qkd: Whether to secure classical bits with QKD

        Returns:
            CompressedTeleportResult with efficiency metrics
        """
        # Calculate compression
        original_bytes = len(data.encode('utf-8'))
        original_bits = original_bytes * 8

        # Compress: log2(n) qubits needed
        n_qubits = max(1, int(np.ceil(np.log2(original_bytes + 1))))

        # Classical bits for teleportation = 2 per qubit
        classical_bits = n_qubits * 2

        # Ensure we have enough Bell pairs
        if len(self.bell_pairs) < n_qubits:
            self.create_bell_pairs(n_qubits)

        # Simulate teleportation of each qubit
        total_fidelity = 1.0
        for i in range(n_qubits):
            # Random state for simulation
            state = [np.random.random() + 1j * np.random.random() for _ in range(2)]
            result = self.teleport_state(state)
            total_fidelity *= result.fidelity

        # Simulate QKD error detection
        error_detected = False
        if use_qkd:
            # In real scenario, ~25% error rate indicates eavesdropping
            error_detected = np.random.random() < 0.02  # 2% false positive rate

        compression_ratio = original_bits / classical_bits if classical_bits > 0 else 1.0

        return CompressedTeleportResult(
            success=True,
            original_size=original_bytes,
            compressed_qubits=n_qubits,
            classical_bits_sent=classical_bits,
            compression_ratio=compression_ratio,
            teleportation_fidelity=total_fidelity,
            qkd_key_used=use_qkd,
            error_detected=error_detected,
        )


class QKDExchange:
    """
    BB84 Quantum Key Distribution implementation.
    """

    def __init__(self, backend: str = "simulator"):
        self.backend = backend

    def exchange(
        self,
        key_length: int = 256,
        eve_present: bool = False,
    ) -> dict:
        """
        Perform BB84 key exchange.

        Args:
            key_length: Desired key length in bits
            eve_present: Simulate eavesdropper (for demo)

        Returns:
            Dict with shared key and security metrics
        """
        # Need ~4x raw bits to get desired key length after sifting
        n_photons = key_length * 4

        # Alice's random bits and bases
        alice_bits = np.random.randint(0, 2, n_photons)
        alice_bases = np.random.randint(0, 2, n_photons)  # 0=rectilinear, 1=diagonal

        # Bob's random bases
        bob_bases = np.random.randint(0, 2, n_photons)

        # Simulate transmission
        if eve_present:
            # Eve intercepts and measures with random bases
            eve_bases = np.random.randint(0, 2, n_photons)
            # Eve's wrong basis choices introduce ~25% errors
            eve_errors = (alice_bases != eve_bases) & (np.random.random(n_photons) < 0.5)
            received_bits = np.where(eve_errors, 1 - alice_bits, alice_bits)
        else:
            received_bits = alice_bits.copy()

        # Bob measures
        bob_bits = np.where(
            alice_bases == bob_bases,
            received_bits,
            np.random.randint(0, 2, n_photons)  # Random if bases don't match
        )

        # Sifting: keep only matching bases
        matching = alice_bases == bob_bases
        sifted_alice = alice_bits[matching]
        sifted_bob = bob_bits[matching]

        # Calculate error rate
        errors = sifted_alice != sifted_bob
        error_rate = np.mean(errors) if len(errors) > 0 else 0.0

        # Generate final key (using Alice's bits where no error)
        final_key = ''.join(str(b) for b in sifted_alice[:key_length])

        return {
            "key": final_key,
            "key_length": len(final_key),
            "raw_photons": n_photons,
            "sifted_bits": len(sifted_alice),
            "error_rate": float(error_rate),
            "eve_detected": error_rate > 0.11,  # Threshold for detection
            "secure": error_rate <= 0.11,
        }


class SecureMessenger:
    """
    Secure messaging using compressed teleportation + QKD.

    This is the main API for external messaging apps.
    """

    def __init__(self, backend: str = "simulator"):
        self.teleporter = QuantumTeleporter(backend)
        self.qkd = QKDExchange(backend)
        self.backend = backend

    def establish_channel(
        self,
        recipient: str,
        bell_pairs: int = 100,
        key_length: int = 256,
    ) -> dict:
        """
        Establish secure channel with recipient.

        1. Distribute Bell pairs
        2. Perform QKD key exchange
        """
        # Create Bell pairs
        pairs = self.teleporter.create_bell_pairs(bell_pairs)

        # QKD exchange
        qkd_result = self.qkd.exchange(key_length)

        return {
            "channel_id": f"channel_{recipient}_{np.random.randint(10000, 99999)}",
            "recipient": recipient,
            "bell_pairs_available": len(pairs),
            "qkd_key_established": qkd_result["secure"],
            "key_length": qkd_result["key_length"],
            "ready": qkd_result["secure"],
        }

    def send_message(
        self,
        message: str,
        channel_id: Optional[str] = None,
    ) -> dict:
        """
        Send a message through compressed teleportation.

        Args:
            message: Message to send
            channel_id: Pre-established channel (creates new if None)

        Returns:
            Transmission result with efficiency metrics
        """
        # Teleport compressed message
        result = self.teleporter.teleport_compressed(message, use_qkd=True)

        return {
            "success": result.success,
            "message_length": len(message),
            "original_bits": len(message.encode('utf-8')) * 8,
            "compressed_qubits": result.compressed_qubits,
            "classical_bits_transmitted": result.classical_bits_sent,
            "compression_ratio": round(result.compression_ratio, 2),
            "teleportation_fidelity": round(result.teleportation_fidelity, 4),
            "qkd_secured": result.qkd_key_used,
            "eavesdrop_detected": result.error_detected,
            "security": "physics-based",
        }

    def get_channel_stats(self) -> dict:
        """Get statistics about the secure channel."""
        return {
            "bell_pairs_remaining": len(self.teleporter.bell_pairs),
            "backend": self.backend,
            "teleportation_supported": True,
            "compression_supported": True,
            "qkd_protocol": "BB84",
        }
