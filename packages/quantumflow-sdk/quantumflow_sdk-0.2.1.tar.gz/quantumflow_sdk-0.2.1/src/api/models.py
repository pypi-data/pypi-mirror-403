"""
API Request/Response Models for QuantumFlow.
"""

from typing import Optional
from pydantic import BaseModel, Field


# === Compression Models ===

class CompressRequest(BaseModel):
    """Request to compress tokens."""

    tokens: list[int] = Field(..., description="List of integer tokens to compress")
    compression_level: float = Field(default=1.0, ge=0.0, le=1.0)
    backend: str = Field(default="auto", description="Backend: auto, simulator, ibm")
    execute: bool = Field(default=False, description="Execute on quantum backend")
    shots: int = Field(default=1024, ge=1, le=10000)


class CompressResponse(BaseModel):
    """Response from token compression."""

    input_tokens: int
    output_qubits: int
    tokens_saved: int
    compression_ratio: float
    compression_percent: float
    fidelity: Optional[float] = None
    execution_time_ms: Optional[float] = None
    backend_used: str


# === Gradient Models ===

class GradientRequest(BaseModel):
    """Request to compute quantum gradient."""

    input_state: list[float] = Field(..., description="Input state amplitudes")
    target_state: list[float] = Field(..., description="Target state amplitudes")
    weights: list[float] = Field(..., description="Current weight parameters")
    backend: str = Field(default="auto")
    shots: int = Field(default=1024, ge=1, le=10000)


class GradientResponse(BaseModel):
    """Response from quantum gradient computation."""

    gradients: list[float]
    bit_x: int
    bit_z: int
    gradient_direction: int
    gradient_magnitude: float
    classical_similarity: float
    execution_time_ms: float


# === Backend Models ===

class BackendStatus(BaseModel):
    """Status of a quantum backend."""

    name: str
    status: str
    is_simulator: bool
    max_qubits: int
    queue_position: Optional[int] = None


class BackendsResponse(BaseModel):
    """List of available backends."""

    backends: list[BackendStatus]


# === Memory Models ===

class MemoryStoreRequest(BaseModel):
    """Request to store data in quantum memory."""

    key: str = Field(..., min_length=1, max_length=256)
    values: list[int]
    compress: bool = Field(default=True)


class MemoryStoreResponse(BaseModel):
    """Response from memory store operation."""

    key: str
    stored_count: int
    qubits_used: Optional[int] = None
    compression_ratio: Optional[float] = None


class MemoryRetrieveResponse(BaseModel):
    """Response from memory retrieve operation."""

    key: str
    values: list[int]


class MemoryStatsResponse(BaseModel):
    """Quantum memory statistics."""

    total_items: int
    classical_size: int
    quantum_size: int
    compression_ratio: float
    memory_saved_percent: float


# === Entanglement Models ===

class EntangleRequest(BaseModel):
    """Request to create entangled state."""

    contexts: list[list[float]] = Field(..., min_length=2)
    backend: str = Field(default="auto")


class EntangleResponse(BaseModel):
    """Response from entanglement creation."""

    n_qubits: int
    n_parties: int
    entropy: float
    is_maximally_entangled: bool


# === Health Models ===

class HealthResponse(BaseModel):
    """API health status."""

    status: str
    version: str
    quantum_ready: bool
