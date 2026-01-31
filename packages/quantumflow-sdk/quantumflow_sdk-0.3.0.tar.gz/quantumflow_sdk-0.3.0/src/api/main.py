"""
QuantumFlow API - FastAPI Application.

Endpoints:
- POST /v1/compress - Token compression (Paper 1)
- POST /v1/gradient - Quantum backprop (Paper 2)
- GET /v1/backends - Available quantum backends
- POST /v1/memory/* - Quantum memory operations
- POST /v1/entangle - Create entangled states
- /auth/* - Authentication and API key management
"""

import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    CompressRequest, CompressResponse,
    GradientRequest, GradientResponse,
    BackendStatus, BackendsResponse,
    MemoryStoreRequest, MemoryStoreResponse,
    MemoryRetrieveResponse, MemoryStatsResponse,
    EntangleRequest, EntangleResponse,
    HealthResponse,
)
from api.auth import get_current_user, get_optional_user, get_db_session
from api.routes.auth_routes import router as auth_router
from api.routes.teleport_routes import router as teleport_router
from api.routes.algorithm_routes import router as algorithm_router

# Import billing routes (optional - only if Stripe is configured)
try:
    from quantumflow.api.routes.billing_routes import router as billing_router
    BILLING_ENABLED = True
except ImportError:
    BILLING_ENABLED = False
    billing_router = None

from quantumflow.core.quantum_compressor import QuantumCompressor
from quantumflow.core.quantum_backprop import QuantumBackprop
from quantumflow.core.entanglement import Entangler
from quantumflow.core.memory import QuantumMemory
from quantumflow.backends.base_backend import BackendType

from db.database import init_db
from db.models import User
from db import crud


# Global instances (initialized on startup)
_compressor: Optional[QuantumCompressor] = None
_backprop: Optional[QuantumBackprop] = None
_entangler: Optional[Entangler] = None
_memory: Optional[QuantumMemory] = None
_db_initialized: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize quantum components and database on startup."""
    global _compressor, _backprop, _entangler, _memory, _db_initialized

    # Initialize quantum components
    _compressor = QuantumCompressor(backend="simulator")
    _backprop = QuantumBackprop(backend="simulator")
    _entangler = Entangler(backend="simulator")
    _memory = QuantumMemory(backend="simulator")

    # Initialize database
    try:
        init_db()
        _db_initialized = True
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Running without database - some features will be limited")
        _db_initialized = False

    yield

    # Cleanup
    _compressor = None
    _backprop = None
    _entangler = None
    _memory = None


# Create FastAPI app
app = FastAPI(
    title="QuantumFlow API",
    description="Quantum-optimized AI agent workflow platform",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# Include teleportation & secure messaging routes
app.include_router(teleport_router)

# Include algorithm routes (QNN, Grover, QAOA, VQE, QSVM, QKD, QRNG, QFT)
app.include_router(algorithm_router)

# Include billing routes if available
if BILLING_ENABLED and billing_router:
    app.include_router(billing_router)


# === Health Endpoints ===

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        quantum_ready=_compressor is not None,
    )


@app.get("/", tags=["Health"])
async def root():
    """API root endpoint."""
    return {
        "name": "QuantumFlow API",
        "version": "0.1.0",
        "docs": "/docs",
        "database": "connected" if _db_initialized else "not connected",
    }


# === Compression Endpoints (Paper 1) ===

@app.post("/v1/compress", response_model=CompressResponse, tags=["Compression"])
async def compress_tokens(
    request: CompressRequest,
    http_request: Request,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Compress tokens using quantum amplitude encoding.

    Achieves 53% token reduction via quantum superposition.
    """
    if not _compressor:
        raise HTTPException(status_code=503, detail="Quantum compressor not initialized")

    start_time = time.perf_counter()

    try:
        if request.execute:
            result = _compressor.compress_and_execute(
                tokens=request.tokens,
                compression_level=request.compression_level,
                shots=request.shots,
            )
            fidelity = result.execution_result.fidelity if result.execution_result else None
        else:
            result = _compressor.compress(
                tokens=request.tokens,
                compression_level=request.compression_level,
            )
            fidelity = None

        execution_time = (time.perf_counter() - start_time) * 1000

        # Track usage if user is authenticated and db is available
        if user and _db_initialized:
            try:
                db = next(get_db_session())
                crud.create_usage_record(
                    db,
                    user_id=user.id,
                    endpoint="/v1/compress",
                    method="POST",
                    tokens_input=len(request.tokens),
                    tokens_output=result.n_qubits,
                    qubits_used=result.n_qubits,
                    execution_time_ms=execution_time,
                    ip_address=http_request.client.host if http_request.client else None,
                )
            except Exception:
                pass  # Don't fail request if usage tracking fails

        return CompressResponse(
            input_tokens=result.input_token_count,
            output_qubits=result.n_qubits,
            tokens_saved=result.tokens_saved,
            compression_ratio=result.compression_ratio,
            compression_percent=result.compression_percentage,
            fidelity=fidelity,
            execution_time_ms=execution_time,
            backend_used=request.backend,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Gradient Endpoints (Paper 2) ===

@app.post("/v1/gradient", response_model=GradientResponse, tags=["Backpropagation"])
async def compute_gradient(
    request: GradientRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Compute gradient using quantum teleportation protocol.

    Achieves 97.78% similarity with classical gradients.
    """
    if not _backprop:
        raise HTTPException(status_code=503, detail="Quantum backprop not initialized")

    start_time = time.perf_counter()

    try:
        result = _backprop.compute_gradient(
            input_state=np.array(request.input_state),
            target_state=np.array(request.target_state),
            weights=np.array(request.weights),
            shots=request.shots,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        return GradientResponse(
            gradients=result.gradients.tolist(),
            bit_x=result.bit_x,
            bit_z=result.bit_z,
            gradient_direction=result.gradient_direction,
            gradient_magnitude=result.gradient_magnitude,
            classical_similarity=abs(result.similarity),
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Backend Endpoints ===

@app.get("/v1/backends", response_model=BackendsResponse, tags=["Backends"])
async def list_backends():
    """List available quantum backends."""
    backends = [
        BackendStatus(
            name="simulator",
            status="online",
            is_simulator=True,
            max_qubits=30,
        ),
        BackendStatus(
            name="ibm",
            status="available",
            is_simulator=False,
            max_qubits=156,
            queue_position=None,
        ),
        # AWS Braket backends
        BackendStatus(
            name="aws_sv1",
            status="available",
            is_simulator=True,
            max_qubits=34,
        ),
        BackendStatus(
            name="aws_ionq",
            status="available",
            is_simulator=False,
            max_qubits=25,
        ),
        BackendStatus(
            name="aws_rigetti",
            status="available",
            is_simulator=False,
            max_qubits=80,
        ),
    ]
    return BackendsResponse(backends=backends)


# === Memory Endpoints ===

@app.post("/v1/memory/store", response_model=MemoryStoreResponse, tags=["Memory"])
async def memory_store(
    request: MemoryStoreRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """Store data in quantum memory."""
    if not _memory:
        raise HTTPException(status_code=503, detail="Quantum memory not initialized")

    try:
        slot = _memory.store(request.key, request.values, compress=request.compress)

        return MemoryStoreResponse(
            key=request.key,
            stored_count=len(request.values),
            qubits_used=slot.compressed.n_qubits if slot.compressed else None,
            compression_ratio=slot.compressed.compression_ratio if slot.compressed else None,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/memory/{key}", response_model=MemoryRetrieveResponse, tags=["Memory"])
async def memory_retrieve(
    key: str,
    user: Optional[User] = Depends(get_optional_user),
):
    """Retrieve data from quantum memory."""
    if not _memory:
        raise HTTPException(status_code=503, detail="Quantum memory not initialized")

    try:
        values = _memory.retrieve(key)
        return MemoryRetrieveResponse(key=key, values=values)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")


@app.delete("/v1/memory/{key}", tags=["Memory"])
async def memory_delete(
    key: str,
    user: Optional[User] = Depends(get_optional_user),
):
    """Delete data from quantum memory."""
    if not _memory:
        raise HTTPException(status_code=503, detail="Quantum memory not initialized")

    if _memory.delete(key):
        return {"deleted": True, "key": key}
    raise HTTPException(status_code=404, detail=f"Key '{key}' not found")


@app.get("/v1/memory", response_model=MemoryStatsResponse, tags=["Memory"])
async def memory_stats(user: Optional[User] = Depends(get_optional_user)):
    """Get quantum memory statistics."""
    if not _memory:
        raise HTTPException(status_code=503, detail="Quantum memory not initialized")

    stats = _memory.get_stats()
    return MemoryStatsResponse(
        total_items=stats.total_items,
        classical_size=stats.classical_size,
        quantum_size=stats.quantum_size,
        compression_ratio=stats.compression_ratio,
        memory_saved_percent=stats.memory_saved_percent,
    )


# === Entanglement Endpoints ===

@app.post("/v1/entangle", response_model=EntangleResponse, tags=["Entanglement"])
async def create_entanglement(
    request: EntangleRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """Create entangled state from multiple contexts."""
    if not _entangler:
        raise HTTPException(status_code=503, detail="Entangler not initialized")

    try:
        if len(request.contexts) == 2:
            state = _entangler.entangle_contexts(
                request.contexts[0],
                request.contexts[1],
            )
        else:
            state = _entangler.create_ghz_state(len(request.contexts))

        return EntangleResponse(
            n_qubits=state.n_qubits,
            n_parties=state.n_parties,
            entropy=state.entropy,
            is_maximally_entangled=state.is_maximally_entangled,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
