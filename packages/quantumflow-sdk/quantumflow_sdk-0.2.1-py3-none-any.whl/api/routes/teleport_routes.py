"""
Quantum Teleportation & Secure Messaging API Routes.

Endpoints for quantum teleportation, QKD, and secure messaging
that can be consumed by external applications.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from quantumflow.core.teleportation import (
    QuantumTeleporter,
    QKDExchange,
    SecureMessenger,
)
from api.auth import get_optional_user
from db.models import User

router = APIRouter(prefix="/v1/quantum", tags=["Quantum Teleportation"])

# Global instances
_teleporter: Optional[QuantumTeleporter] = None
_qkd: Optional[QKDExchange] = None
_messenger: Optional[SecureMessenger] = None


def get_teleporter() -> QuantumTeleporter:
    global _teleporter
    if _teleporter is None:
        _teleporter = QuantumTeleporter(backend="simulator")
    return _teleporter


def get_qkd() -> QKDExchange:
    global _qkd
    if _qkd is None:
        _qkd = QKDExchange(backend="simulator")
    return _qkd


def get_messenger() -> SecureMessenger:
    global _messenger
    if _messenger is None:
        _messenger = SecureMessenger(backend="simulator")
    return _messenger


# ==================== Request/Response Models ====================


class TeleportStateRequest(BaseModel):
    """Request to teleport a quantum state."""
    state_real: List[float]  # Real parts [α_r, β_r]
    state_imag: List[float] = [0.0, 0.0]  # Imaginary parts [α_i, β_i]
    bell_pair_id: Optional[str] = None


class TeleportStateResponse(BaseModel):
    """Response from teleportation."""
    success: bool
    bell_measurement: List[int]
    corrections_applied: str
    fidelity: float
    original_state: Optional[List[dict]] = None
    teleported_state: Optional[List[dict]] = None


class CreateBellPairsRequest(BaseModel):
    """Request to create Bell pairs."""
    count: int = 10


class BellPairResponse(BaseModel):
    """Bell pair information."""
    id: str
    state: str
    fidelity: float


class QKDExchangeRequest(BaseModel):
    """Request for QKD key exchange."""
    key_length: int = 256
    simulate_eve: bool = False


class QKDExchangeResponse(BaseModel):
    """Response from QKD exchange."""
    key: str
    key_length: int
    raw_photons: int
    sifted_bits: int
    error_rate: float
    eve_detected: bool
    secure: bool


class EstablishChannelRequest(BaseModel):
    """Request to establish secure channel."""
    recipient: str
    bell_pairs: int = 100
    key_length: int = 256


class ChannelResponse(BaseModel):
    """Secure channel information."""
    channel_id: str
    recipient: str
    bell_pairs_available: int
    qkd_key_established: bool
    key_length: int
    ready: bool


class SendMessageRequest(BaseModel):
    """Request to send secure message."""
    message: str
    channel_id: Optional[str] = None


class SendMessageResponse(BaseModel):
    """Response from sending message."""
    success: bool
    message_length: int
    original_bits: int
    compressed_qubits: int
    classical_bits_transmitted: int
    compression_ratio: float
    teleportation_fidelity: float
    qkd_secured: bool
    eavesdrop_detected: bool
    security: str


class CompressedTeleportRequest(BaseModel):
    """Request for compressed teleportation."""
    data: str
    use_qkd: bool = True


class CompressedTeleportResponse(BaseModel):
    """Response from compressed teleportation."""
    success: bool
    original_size: int
    compressed_qubits: int
    classical_bits_sent: int
    compression_ratio: float
    teleportation_fidelity: float
    qkd_key_used: bool
    error_detected: bool


# ==================== Teleportation Endpoints ====================


@router.post("/teleport", response_model=TeleportStateResponse)
async def teleport_state(
    request: TeleportStateRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Teleport a quantum state from Alice to Bob.

    Uses pre-shared Bell pairs and classical communication
    to transfer a quantum state without sending qubits.

    The state is specified as |ψ⟩ = α|0⟩ + β|1⟩ where α and β
    are complex numbers.
    """
    teleporter = get_teleporter()

    # Construct complex state
    if len(request.state_real) != 2 or len(request.state_imag) != 2:
        raise HTTPException(status_code=400, detail="State must have 2 amplitudes")

    state = [
        complex(request.state_real[0], request.state_imag[0]),
        complex(request.state_real[1], request.state_imag[1]),
    ]

    result = teleporter.teleport_state(state, request.bell_pair_id)

    # Convert complex to dict for JSON
    def complex_to_dict(c):
        return {"real": c.real, "imag": c.imag}

    return TeleportStateResponse(
        success=result.success,
        bell_measurement=list(result.bell_measurement),
        corrections_applied=result.corrections_applied,
        fidelity=result.fidelity,
        original_state=[complex_to_dict(c) for c in result.original_state] if result.original_state else None,
        teleported_state=[complex_to_dict(c) for c in result.teleported_state] if result.teleported_state else None,
    )


@router.post("/teleport/compressed", response_model=CompressedTeleportResponse)
async def teleport_compressed(
    request: CompressedTeleportRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Teleport compressed data using the full pipeline:

    1. Compress data into quantum state (N bytes → log(N) qubits)
    2. Teleport each compressed qubit using Bell pairs
    3. Secure classical correction bits with QKD (optional)

    This achieves massive bandwidth reduction while maintaining
    physics-based security.
    """
    teleporter = get_teleporter()
    result = teleporter.teleport_compressed(request.data, request.use_qkd)

    return CompressedTeleportResponse(
        success=result.success,
        original_size=result.original_size,
        compressed_qubits=result.compressed_qubits,
        classical_bits_sent=result.classical_bits_sent,
        compression_ratio=result.compression_ratio,
        teleportation_fidelity=result.teleportation_fidelity,
        qkd_key_used=result.qkd_key_used,
        error_detected=result.error_detected,
    )


@router.post("/bell-pairs", response_model=List[BellPairResponse])
async def create_bell_pairs(
    request: CreateBellPairsRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Create entangled Bell pairs for teleportation.

    In a real system, this would distribute entanglement
    between quantum devices. Each pair can be used for
    one teleportation operation.
    """
    teleporter = get_teleporter()
    pairs = teleporter.create_bell_pairs(request.count)

    return [
        BellPairResponse(id=p.id, state=p.state, fidelity=p.fidelity)
        for p in pairs
    ]


@router.get("/bell-pairs")
async def list_bell_pairs(
    user: Optional[User] = Depends(get_optional_user),
):
    """List available Bell pairs."""
    teleporter = get_teleporter()
    return {
        "count": len(teleporter.bell_pairs),
        "pairs": [
            {"id": p.id, "state": p.state, "fidelity": p.fidelity}
            for p in teleporter.bell_pairs
        ],
    }


# ==================== QKD Endpoints ====================


@router.post("/qkd/exchange", response_model=QKDExchangeResponse)
async def qkd_exchange(
    request: QKDExchangeRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Perform BB84 quantum key distribution.

    Establishes a shared secret key between Alice and Bob
    using polarized photons. Any eavesdropping attempt
    introduces detectable errors (~25% error rate).

    Set simulate_eve=true to see how eavesdropping is detected.
    """
    qkd = get_qkd()
    result = qkd.exchange(request.key_length, request.simulate_eve)

    return QKDExchangeResponse(**result)


# ==================== Secure Messaging Endpoints ====================


@router.post("/channel", response_model=ChannelResponse)
async def establish_channel(
    request: EstablishChannelRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Establish a secure quantum channel with a recipient.

    This creates:
    1. Bell pairs for teleportation
    2. QKD key for securing classical bits

    Use the returned channel_id for subsequent messages.
    """
    messenger = get_messenger()
    result = messenger.establish_channel(
        request.recipient,
        request.bell_pairs,
        request.key_length,
    )

    return ChannelResponse(**result)


@router.post("/message", response_model=SendMessageResponse)
async def send_secure_message(
    request: SendMessageRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Send a message using compressed quantum teleportation.

    The message is:
    1. Compressed into quantum state (log N qubits)
    2. Teleported via pre-shared Bell pairs
    3. Classical bits encrypted with QKD key

    Returns efficiency metrics showing bandwidth savings
    compared to classical transmission.

    Example for 1000 byte message:
    - Classical: 8000 bits
    - Compressed Teleport: ~20 classical bits
    """
    messenger = get_messenger()
    result = messenger.send_message(request.message, request.channel_id)

    return SendMessageResponse(**result)


@router.get("/channel/stats")
async def get_channel_stats(
    user: Optional[User] = Depends(get_optional_user),
):
    """Get statistics about the secure quantum channel."""
    messenger = get_messenger()
    return messenger.get_channel_stats()


# ==================== Demo Endpoint ====================


@router.post("/demo/full-pipeline")
async def demo_full_pipeline(
    message: str = "Hello, quantum world!",
    simulate_eve: bool = False,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Demo the full quantum secure messaging pipeline.

    Shows step-by-step:
    1. QKD key exchange
    2. Bell pair creation
    3. Message compression
    4. Quantum teleportation
    5. Security verification

    Perfect for understanding how the system works.
    """
    messenger = get_messenger()
    qkd = get_qkd()
    teleporter = get_teleporter()

    # Step 1: QKD
    qkd_result = qkd.exchange(key_length=128, eve_present=simulate_eve)

    # Step 2: Bell pairs
    pairs = teleporter.create_bell_pairs(10)

    # Step 3-4: Compressed teleportation
    teleport_result = teleporter.teleport_compressed(message, use_qkd=True)

    return {
        "message": message,
        "steps": {
            "1_qkd_exchange": {
                "key_length": qkd_result["key_length"],
                "error_rate": round(qkd_result["error_rate"], 4),
                "eve_detected": qkd_result["eve_detected"],
                "secure": qkd_result["secure"],
            },
            "2_bell_pairs": {
                "created": len(pairs),
                "average_fidelity": round(sum(p.fidelity for p in pairs) / len(pairs), 4),
            },
            "3_compression": {
                "original_bytes": teleport_result.original_size,
                "compressed_qubits": teleport_result.compressed_qubits,
                "ratio": round(teleport_result.compression_ratio, 2),
            },
            "4_teleportation": {
                "classical_bits_sent": teleport_result.classical_bits_sent,
                "fidelity": round(teleport_result.teleportation_fidelity, 4),
            },
            "5_security": {
                "qkd_secured": teleport_result.qkd_key_used,
                "eavesdrop_detected": teleport_result.error_detected or qkd_result["eve_detected"],
                "protection": "physics-based (no-cloning theorem)",
            },
        },
        "efficiency": {
            "classical_transmission": f"{teleport_result.original_size * 8} bits",
            "quantum_transmission": f"{teleport_result.classical_bits_sent} classical bits",
            "bandwidth_saved": f"{round((1 - teleport_result.classical_bits_sent / (teleport_result.original_size * 8)) * 100, 1)}%",
        },
    }
