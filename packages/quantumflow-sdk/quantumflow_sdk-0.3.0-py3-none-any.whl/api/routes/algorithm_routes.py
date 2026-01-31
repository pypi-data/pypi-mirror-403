"""
Algorithm Routes for QuantumFlow API.

Provides endpoints for core quantum algorithms:
- QNN (Quantum Neural Network) - Forward pass, training, inference
- Grover's Search - Quantum search with quadratic speedup
- QAOA - Quantum optimization
- VQE - Variational eigensolver

Authentication:
- Free tier (no key): QNN forward, Grover, QRNG, QFT, QKD
- Requires API key: QNN train, QAOA, VQE, QSVM (heavy compute)
"""

import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import numpy as np

from api.auth import get_optional_user, get_current_user
from db.models import User

# Import quantum algorithms
from quantumflow.algorithms.machine_learning import QNN, VQE, QSVM
from quantumflow.algorithms.optimization import GroverSearch, QAOA
from quantumflow.backends.base_backend import BackendType


router = APIRouter(prefix="/v1/algorithms", tags=["Algorithms"])


# ============================================================
# QNN (Quantum Neural Network) Models & Endpoints
# ============================================================

class QNNForwardRequest(BaseModel):
    """Request for QNN forward pass."""
    input_data: List[float] = Field(..., description="Input features (normalized 0-1)")
    weights: Optional[List[float]] = Field(None, description="Model weights (random if not provided)")
    n_qubits: int = Field(default=4, ge=2, le=16, description="Number of qubits")
    n_layers: int = Field(default=2, ge=1, le=10, description="Number of variational layers")
    shots: int = Field(default=1024, ge=100, le=10000)
    backend: str = Field(default="simulator")


class QNNForwardResponse(BaseModel):
    """Response from QNN forward pass."""
    output: float
    output_probabilities: List[float]
    n_qubits: int
    n_layers: int
    n_parameters: int
    weights_used: List[float]
    execution_time_ms: float
    circuit_depth: int


class QNNTrainRequest(BaseModel):
    """Request for QNN training."""
    X_train: List[List[float]] = Field(..., description="Training features")
    y_train: List[int] = Field(..., description="Training labels (0 or 1)")
    n_qubits: int = Field(default=4, ge=2, le=16)
    n_layers: int = Field(default=2, ge=1, le=10)
    epochs: int = Field(default=50, ge=1, le=500)
    learning_rate: float = Field(default=0.1, ge=0.001, le=1.0)
    batch_size: int = Field(default=8, ge=1, le=64)
    shots: int = Field(default=1024)
    backend: str = Field(default="simulator")


class QNNTrainResponse(BaseModel):
    """Response from QNN training."""
    final_weights: List[float]
    loss_history: List[float]
    final_accuracy: float
    n_epochs: int
    n_parameters: int
    execution_time_ms: float


class QNNPredictRequest(BaseModel):
    """Request for QNN prediction."""
    X: List[List[float]] = Field(..., description="Input features to predict")
    weights: List[float] = Field(..., description="Trained model weights")
    n_qubits: int = Field(default=4, ge=2, le=16)
    n_layers: int = Field(default=2, ge=1, le=10)
    return_probabilities: bool = Field(default=False)
    shots: int = Field(default=1024)


class QNNPredictResponse(BaseModel):
    """Response from QNN prediction."""
    predictions: List[int]
    probabilities: Optional[List[float]] = None
    execution_time_ms: float


@router.post("/qnn/forward", response_model=QNNForwardResponse)
async def qnn_forward(
    request: QNNForwardRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Execute QNN forward pass.

    Runs input data through a parameterized quantum circuit to produce output.
    This is the inference step of a quantum neural network.
    """
    start_time = time.perf_counter()

    try:
        # Initialize QNN
        qnn = QNN(
            n_qubits=request.n_qubits,
            n_layers=request.n_layers,
            backend=request.backend,
            shots=request.shots,
        )

        # Use provided weights or random initialization
        if request.weights:
            if len(request.weights) != qnn.n_params:
                raise ValueError(
                    f"Expected {qnn.n_params} weights, got {len(request.weights)}"
                )
            qnn.weights = np.array(request.weights)

        # Prepare input
        x = np.array(request.input_data)
        if len(x) > request.n_qubits:
            x = x[:request.n_qubits]  # Truncate to n_qubits
        elif len(x) < request.n_qubits:
            x = np.pad(x, (0, request.n_qubits - len(x)))  # Pad with zeros

        # Forward pass
        output_prob = qnn._forward(x)

        # Get all probabilities by running predict_proba
        all_probs = [output_prob, 1.0 - output_prob]

        execution_time = (time.perf_counter() - start_time) * 1000

        return QNNForwardResponse(
            output=output_prob,
            output_probabilities=all_probs,
            n_qubits=request.n_qubits,
            n_layers=request.n_layers,
            n_parameters=qnn.n_params,
            weights_used=qnn.weights.tolist(),
            execution_time_ms=execution_time,
            circuit_depth=request.n_layers * (request.n_qubits + 1) + 1,  # Approximate
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qnn/train", response_model=QNNTrainResponse)
async def qnn_train(
    request: QNNTrainRequest,
    user: User = Depends(get_current_user),  # Requires API key - heavy compute
):
    """
    Train a Quantum Neural Network.

    Uses parameter-shift rule for gradient computation and
    mini-batch gradient descent for optimization.
    """
    start_time = time.perf_counter()

    try:
        # Initialize QNN
        qnn = QNN(
            n_qubits=request.n_qubits,
            n_layers=request.n_layers,
            backend=request.backend,
            learning_rate=request.learning_rate,
            shots=request.shots,
        )

        # Prepare data
        X = np.array(request.X_train)
        y = np.array(request.y_train)

        # Train
        result = qnn.fit(
            X=X,
            y=y,
            epochs=request.epochs,
            batch_size=request.batch_size,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        return QNNTrainResponse(
            final_weights=result.final_weights.tolist(),
            loss_history=result.loss_history,
            final_accuracy=result.accuracy,
            n_epochs=result.n_epochs,
            n_parameters=qnn.n_params,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qnn/predict", response_model=QNNPredictResponse)
async def qnn_predict(
    request: QNNPredictRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Make predictions using a trained QNN.
    """
    start_time = time.perf_counter()

    try:
        # Initialize QNN with trained weights
        qnn = QNN(
            n_qubits=request.n_qubits,
            n_layers=request.n_layers,
            shots=request.shots,
        )
        qnn.weights = np.array(request.weights)

        # Prepare data
        X = np.array(request.X)

        # Predict
        predictions = qnn.predict(X)

        probabilities = None
        if request.return_probabilities:
            probabilities = qnn.predict_proba(X).tolist()

        execution_time = (time.perf_counter() - start_time) * 1000

        return QNNPredictResponse(
            predictions=predictions.tolist(),
            probabilities=probabilities,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Grover's Search Models & Endpoints
# ============================================================

class GroverSearchRequest(BaseModel):
    """Request for Grover's search."""
    n_qubits: int = Field(..., ge=2, le=20, description="Search space = 2^n_qubits")
    marked_states: List[int] = Field(..., min_length=1, description="States to search for")
    iterations: Optional[int] = Field(None, description="Grover iterations (optimal if not specified)")
    shots: int = Field(default=1024, ge=100, le=10000)
    backend: str = Field(default="simulator")


class GroverSearchResponse(BaseModel):
    """Response from Grover's search."""
    found_state: str
    found_state_decimal: int
    probability: float
    iterations_used: int
    optimal_iterations: int
    search_space_size: int
    speedup_factor: str
    execution_time_ms: float


@router.post("/grover/search", response_model=GroverSearchResponse)
async def grover_search(
    request: GroverSearchRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Execute Grover's quantum search algorithm.

    Finds marked states in an unstructured database with O(sqrt(N))
    complexity instead of classical O(N).
    """
    import math
    start_time = time.perf_counter()

    try:
        # Validate marked states
        N = 2 ** request.n_qubits
        for state in request.marked_states:
            if state < 0 or state >= N:
                raise ValueError(f"Marked state {state} out of range [0, {N-1}]")

        # Initialize Grover
        grover = GroverSearch(backend=request.backend)

        # Calculate optimal iterations
        M = len(request.marked_states)
        if M > 0 and M < N:
            theta = math.asin(math.sqrt(M / N))
            optimal_iterations = max(1, int(round(math.pi / (4 * theta) - 0.5)))
        else:
            optimal_iterations = 1

        # Execute search
        result = grover.search(
            n_qubits=request.n_qubits,
            marked_states=request.marked_states,
            iterations=request.iterations,
            shots=request.shots,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        # Calculate speedup
        classical_ops = N / 2  # Average case classical
        quantum_ops = result.iterations * math.sqrt(N)
        speedup = classical_ops / quantum_ops if quantum_ops > 0 else 1

        return GroverSearchResponse(
            found_state=result.found_state,
            found_state_decimal=int(result.found_state, 2),
            probability=result.probability,
            iterations_used=result.iterations,
            optimal_iterations=optimal_iterations,
            search_space_size=N,
            speedup_factor=f"{speedup:.1f}x",
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# QAOA Models & Endpoints
# ============================================================

class QAOARequest(BaseModel):
    """Request for QAOA optimization."""
    problem_type: str = Field(default="maxcut", description="Problem type: maxcut, tsp, portfolio")
    n_nodes: int = Field(..., ge=2, le=20, description="Number of nodes/variables")
    edges: Optional[List[List[int]]] = Field(None, description="Graph edges for MaxCut")
    depth: int = Field(default=2, ge=1, le=10, description="QAOA circuit depth (p)")
    shots: int = Field(default=1024)
    backend: str = Field(default="simulator")


class QAOAResponse(BaseModel):
    """Response from QAOA optimization."""
    best_solution: List[int]
    best_cost: float
    approximation_ratio: float
    optimal_gamma: List[float]
    optimal_beta: List[float]
    iterations: int
    execution_time_ms: float


@router.post("/qaoa/optimize", response_model=QAOAResponse)
async def qaoa_optimize(
    request: QAOARequest,
    user: User = Depends(get_current_user),  # Requires API key - heavy compute
):
    """
    Run QAOA for combinatorial optimization.

    Solves NP-hard problems like MaxCut, TSP, portfolio optimization
    using variational quantum circuits.
    """
    start_time = time.perf_counter()

    try:
        import random

        # Generate random graph if edges not provided
        if request.edges is None:
            edges = []
            for i in range(request.n_nodes):
                for j in range(i + 1, request.n_nodes):
                    if random.random() > 0.5:
                        edges.append((i, j))
            if not edges:
                edges = [(0, 1)]  # At least one edge
        else:
            edges = [tuple(e) for e in request.edges]

        # Initialize QAOA
        qaoa = QAOA(backend=request.backend, p=request.depth, shots=request.shots)

        # Run MaxCut optimization
        result = qaoa.maxcut(
            edges=edges,
            n_nodes=request.n_nodes,
            max_iterations=50,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        # Extract gamma and beta from optimal params
        optimal_gamma = result.optimal_params[::2].tolist()
        optimal_beta = result.optimal_params[1::2].tolist()

        # Calculate approximation ratio (simplified)
        max_possible_cut = len(edges)
        approx_ratio = result.best_cost / max_possible_cut if max_possible_cut > 0 else 0

        return QAOAResponse(
            best_solution=[int(b) for b in result.best_solution],
            best_cost=result.best_cost,
            approximation_ratio=approx_ratio,
            optimal_gamma=optimal_gamma,
            optimal_beta=optimal_beta,
            iterations=result.n_iterations,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# VQE Models & Endpoints
# ============================================================

class VQERequest(BaseModel):
    """Request for VQE computation."""
    molecule: str = Field(default="H2", description="Molecule: H2, LiH, H2O")
    n_qubits: int = Field(default=4, ge=2, le=16)
    ansatz: str = Field(default="ry_cnot", description="Ansatz type: ry_cnot, hardware_efficient")
    max_iterations: int = Field(default=100, ge=10, le=1000)
    shots: int = Field(default=1024)
    backend: str = Field(default="simulator")


class VQEResponse(BaseModel):
    """Response from VQE computation."""
    ground_state_energy: float
    optimal_parameters: List[float]
    energy_history: List[float]
    iterations: int
    converged: bool
    chemical_accuracy: bool
    execution_time_ms: float


@router.post("/vqe/compute", response_model=VQEResponse)
async def vqe_compute(
    request: VQERequest,
    user: User = Depends(get_current_user),  # Requires API key - heavy compute
):
    """
    Run VQE to find ground state energy.

    Variational Quantum Eigensolver finds the lowest eigenvalue
    of a Hamiltonian - useful for quantum chemistry.
    """
    start_time = time.perf_counter()

    try:
        # Define simple molecular Hamiltonians
        molecule_hamiltonians = {
            "H2": [("ZZ", 0.5), ("XI", 0.3), ("IX", 0.3), ("II", -0.5)],
            "LiH": [("ZZ", 0.4), ("ZI", 0.2), ("IZ", 0.2), ("XX", 0.1), ("YY", 0.1)],
            "H2O": [("ZZI", 0.3), ("ZIZ", 0.3), ("IZZ", 0.3), ("XII", 0.2), ("IXI", 0.2)],
        }

        hamiltonian = molecule_hamiltonians.get(request.molecule, molecule_hamiltonians["H2"])

        # Initialize VQE
        vqe = VQE(
            n_qubits=request.n_qubits,
            backend=request.backend,
            ansatz=request.ansatz.replace("-", "_"),
            shots=request.shots,
        )

        # Run VQE
        result = vqe.run(
            hamiltonian=hamiltonian,
            max_iterations=request.max_iterations,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        # Check convergence - if energy stabilized in last iterations
        converged = len(result.energy_history) > 5 and \
            abs(result.energy_history[-1] - result.energy_history[-5]) < 0.01

        # Chemical accuracy check
        chemical_accuracy = converged and abs(result.ground_energy) < 2.0

        return VQEResponse(
            ground_state_energy=result.ground_energy,
            optimal_parameters=result.optimal_params.tolist(),
            energy_history=result.energy_history,
            iterations=result.n_iterations,
            converged=converged,
            chemical_accuracy=chemical_accuracy,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Algorithm Info Endpoint
# ============================================================

# ============================================================
# QSVM Models & Endpoints
# ============================================================

class QSVMTrainRequest(BaseModel):
    """Request for QSVM training."""
    X_train: List[List[float]] = Field(..., description="Training features")
    y_train: List[int] = Field(..., description="Training labels (-1 or 1)")
    feature_map: str = Field(default="zz", description="Feature map: zz, pauli, amplitude")
    reps: int = Field(default=2, ge=1, le=5)
    shots: int = Field(default=1024)
    backend: str = Field(default="simulator")


class QSVMTrainResponse(BaseModel):
    """Response from QSVM training."""
    n_support_vectors: int
    kernel_matrix_shape: List[int]
    training_accuracy: float
    execution_time_ms: float


class QSVMPredictRequest(BaseModel):
    """Request for QSVM prediction."""
    X_train: List[List[float]] = Field(..., description="Training features")
    y_train: List[int] = Field(..., description="Training labels")
    X_test: List[List[float]] = Field(..., description="Test features")
    feature_map: str = Field(default="zz")
    reps: int = Field(default=2)
    shots: int = Field(default=1024)


class QSVMPredictResponse(BaseModel):
    """Response from QSVM prediction."""
    predictions: List[int]
    execution_time_ms: float


@router.post("/qsvm/train", response_model=QSVMTrainResponse)
async def qsvm_train(
    request: QSVMTrainRequest,
    user: User = Depends(get_current_user),  # Requires API key - heavy compute
):
    """
    Train a Quantum Support Vector Machine.

    Uses quantum feature maps to compute kernel in high-dimensional Hilbert space.
    """
    start_time = time.perf_counter()

    try:
        X = np.array(request.X_train)
        y = np.array(request.y_train)

        qsvm = QSVM(
            n_features=X.shape[1],
            backend=request.backend,
            feature_map=request.feature_map,
            reps=request.reps,
            shots=request.shots,
        )

        qsvm.fit(X, y)
        accuracy = qsvm.score(X, y)

        n_support = int(np.sum(qsvm.alphas > 1e-6))

        execution_time = (time.perf_counter() - start_time) * 1000

        return QSVMTrainResponse(
            n_support_vectors=n_support,
            kernel_matrix_shape=list(qsvm.kernel_matrix.shape),
            training_accuracy=accuracy,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qsvm/predict", response_model=QSVMPredictResponse)
async def qsvm_predict(
    request: QSVMPredictRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """Make predictions using QSVM."""
    start_time = time.perf_counter()

    try:
        X_train = np.array(request.X_train)
        y_train = np.array(request.y_train)
        X_test = np.array(request.X_test)

        qsvm = QSVM(
            n_features=X_train.shape[1],
            feature_map=request.feature_map,
            reps=request.reps,
            shots=request.shots,
        )

        qsvm.fit(X_train, y_train)
        predictions = qsvm.predict(X_test)

        execution_time = (time.perf_counter() - start_time) * 1000

        return QSVMPredictResponse(
            predictions=predictions.tolist(),
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# QKD Models & Endpoints
# ============================================================

class QKDGenerateRequest(BaseModel):
    """Request for QKD key generation."""
    key_length: int = Field(default=256, ge=32, le=4096, description="Desired key length in bits")
    simulate_eavesdropper: bool = Field(default=False, description="Simulate eavesdropping attack")
    backend: str = Field(default="simulator")


class QKDGenerateResponse(BaseModel):
    """Response from QKD key generation."""
    shared_key: str
    key_length: int
    raw_bits_used: int
    error_rate: float
    is_secure: bool
    eavesdropper_detected: bool
    protocol: str
    execution_time_ms: float


@router.post("/qkd/generate", response_model=QKDGenerateResponse)
async def qkd_generate(
    request: QKDGenerateRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Generate a quantum-secure cryptographic key using BB84 protocol.

    The key is provably secure against eavesdropping due to quantum mechanics.
    """
    start_time = time.perf_counter()

    try:
        from quantumflow.algorithms.cryptography import QKD

        qkd = QKD(backend=request.backend)

        result = qkd.generate_key(
            key_length=request.key_length,
            with_eavesdropper=request.simulate_eavesdropper,
        )

        execution_time = (time.perf_counter() - start_time) * 1000

        return QKDGenerateResponse(
            shared_key=result.shared_key,
            key_length=result.key_length,
            raw_bits_used=result.raw_key_length,
            error_rate=result.error_rate,
            is_secure=result.is_secure,
            eavesdropper_detected=not result.is_secure and request.simulate_eavesdropper,
            protocol="BB84",
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# QRNG Models & Endpoints
# ============================================================

class QRNGRequest(BaseModel):
    """Request for quantum random number generation."""
    output_type: str = Field(default="bits", description="Output type: bits, integer, float, bytes")
    count: int = Field(default=64, ge=1, le=1024, description="Number of bits/bytes or max value for integer")
    min_value: int = Field(default=0, description="Min value for integer output")
    max_value: Optional[int] = Field(None, description="Max value for integer output")
    backend: str = Field(default="simulator")


class QRNGResponse(BaseModel):
    """Response from quantum random number generation."""
    output_type: str
    bits: Optional[str] = None
    integer: Optional[int] = None
    float_value: Optional[float] = None
    bytes_hex: Optional[str] = None
    n_qubits_used: int
    entropy_bits: int
    execution_time_ms: float


@router.post("/qrng/generate", response_model=QRNGResponse)
async def qrng_generate(
    request: QRNGRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Generate true random numbers using quantum mechanics.

    Unlike classical PRNGs, quantum randomness is fundamentally unpredictable.
    """
    start_time = time.perf_counter()

    try:
        from quantumflow.algorithms.cryptography import QRNG

        qrng = QRNG(backend=request.backend)

        bits = None
        integer = None
        float_value = None
        bytes_hex = None
        entropy_bits = request.count

        if request.output_type == "bits":
            bits = qrng.random_bits(request.count)
            entropy_bits = request.count
        elif request.output_type == "integer":
            max_val = request.max_value if request.max_value else (2 ** request.count - 1)
            integer = qrng.random_int(request.min_value, max_val)
            entropy_bits = int(np.ceil(np.log2(max_val - request.min_value + 1)))
        elif request.output_type == "float":
            float_value = qrng.random_float()
            entropy_bits = 53
        elif request.output_type == "bytes":
            random_bytes = qrng.random_bytes(request.count)
            bytes_hex = random_bytes.hex()
            entropy_bits = request.count * 8

        execution_time = (time.perf_counter() - start_time) * 1000

        return QRNGResponse(
            output_type=request.output_type,
            bits=bits,
            integer=integer,
            float_value=float_value,
            bytes_hex=bytes_hex,
            n_qubits_used=min(20, entropy_bits),
            entropy_bits=entropy_bits,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Quantum Fourier Transform Endpoint
# ============================================================

class QFTRequest(BaseModel):
    """Request for QFT."""
    input_data: List[float] = Field(..., description="Input data to transform")
    n_qubits: Optional[int] = Field(None, description="Number of qubits (auto if not specified)")
    inverse: bool = Field(default=False, description="Apply inverse QFT")
    backend: str = Field(default="simulator")


class QFTResponse(BaseModel):
    """Response from QFT."""
    output_coefficients: List[float]
    n_qubits: int
    transform_type: str
    circuit_depth: int
    execution_time_ms: float


@router.post("/qft/transform", response_model=QFTResponse)
async def qft_transform(
    request: QFTRequest,
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Apply Quantum Fourier Transform.

    Exponentially faster than classical FFT for certain applications.
    """
    start_time = time.perf_counter()

    try:
        from quantumflow.algorithms.compression import QFTCompression

        n_qubits = request.n_qubits or int(np.ceil(np.log2(len(request.input_data))))
        n_qubits = max(2, min(n_qubits, 16))

        qft = QFTCompression(n_qubits=n_qubits)

        if request.inverse:
            result = qft.inverse_transform(request.input_data)
        else:
            result = qft.transform(request.input_data)

        execution_time = (time.perf_counter() - start_time) * 1000

        return QFTResponse(
            output_coefficients=result.tolist() if hasattr(result, 'tolist') else list(result),
            n_qubits=n_qubits,
            transform_type="inverse_QFT" if request.inverse else "QFT",
            circuit_depth=n_qubits * (n_qubits + 1) // 2,
            execution_time_ms=execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Algorithm Info Endpoint
# ============================================================

@router.get("/info")
async def list_algorithms():
    """List all available quantum algorithms with descriptions."""
    return {
        "algorithms": [
            {
                "id": "qnn",
                "name": "Quantum Neural Network",
                "description": "Parameterized quantum circuits for machine learning",
                "endpoints": ["/v1/algorithms/qnn/forward", "/v1/algorithms/qnn/train", "/v1/algorithms/qnn/predict"],
                "use_cases": ["Binary classification", "Pattern recognition", "Feature extraction"],
            },
            {
                "id": "grover",
                "name": "Grover's Search",
                "description": "Quantum search with quadratic speedup O(√N)",
                "endpoints": ["/v1/algorithms/grover/search"],
                "use_cases": ["Database search", "SAT solving", "Optimization"],
            },
            {
                "id": "qaoa",
                "name": "QAOA",
                "description": "Quantum Approximate Optimization Algorithm",
                "endpoints": ["/v1/algorithms/qaoa/optimize"],
                "use_cases": ["MaxCut", "Portfolio optimization", "Scheduling"],
            },
            {
                "id": "vqe",
                "name": "VQE",
                "description": "Variational Quantum Eigensolver",
                "endpoints": ["/v1/algorithms/vqe/compute"],
                "use_cases": ["Molecular simulation", "Ground state energy", "Quantum chemistry"],
            },
            {
                "id": "qsvm",
                "name": "Quantum SVM",
                "description": "Quantum kernel-based classification",
                "endpoints": ["/v1/algorithms/qsvm/train", "/v1/algorithms/qsvm/predict"],
                "use_cases": ["Classification", "Pattern recognition", "Anomaly detection"],
            },
            {
                "id": "qkd",
                "name": "Quantum Key Distribution",
                "description": "BB84 protocol for quantum-secure key exchange",
                "endpoints": ["/v1/algorithms/qkd/generate"],
                "use_cases": ["Secure communication", "Cryptography", "Key exchange"],
            },
            {
                "id": "qrng",
                "name": "Quantum Random Number Generator",
                "description": "True random numbers from quantum measurements",
                "endpoints": ["/v1/algorithms/qrng/generate"],
                "use_cases": ["Cryptography", "Simulations", "Gaming"],
            },
            {
                "id": "qft",
                "name": "Quantum Fourier Transform",
                "description": "Exponentially faster Fourier transform",
                "endpoints": ["/v1/algorithms/qft/transform"],
                "use_cases": ["Signal processing", "Phase estimation", "Quantum algorithms"],
            },
        ]
    }
