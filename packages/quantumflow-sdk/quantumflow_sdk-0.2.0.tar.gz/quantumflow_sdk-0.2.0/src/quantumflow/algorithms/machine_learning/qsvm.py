"""
Quantum Support Vector Machine (QSVM).

Uses quantum feature maps for kernel-based classification.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QSVMResult:
    """Result from QSVM classification."""

    predictions: np.ndarray
    kernel_matrix: Optional[np.ndarray]
    support_vectors: Optional[np.ndarray]
    accuracy: float


class QSVM:
    """
    Quantum Support Vector Machine.

    Uses quantum circuits as feature maps to compute kernel values,
    enabling classification in high-dimensional Hilbert space.

    Feature maps:
    - ZZ Feature Map: Entangling features with ZZ gates
    - Pauli Feature Map: General Pauli rotations
    - Amplitude Encoding: Direct amplitude encoding

    Example:
        >>> qsvm = QSVM(n_features=2)
        >>> qsvm.fit(X_train, y_train)
        >>> predictions = qsvm.predict(X_test)
    """

    def __init__(
        self,
        n_features: int,
        backend: BackendType | str = BackendType.AUTO,
        feature_map: str = "zz",
        reps: int = 2,
        shots: int = 1024,
    ):
        """
        Initialize QSVM.

        Args:
            n_features: Number of input features
            backend: Quantum backend
            feature_map: Type of feature map ('zz', 'pauli', 'amplitude')
            reps: Number of feature map repetitions
            shots: Measurement shots for kernel estimation
        """
        self.n_features = n_features
        self.n_qubits = n_features
        self.backend = get_backend(backend)
        self.feature_map_type = feature_map
        self.reps = reps
        self.shots = shots
        self._connected = False

        # Training data
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.alphas: Optional[np.ndarray] = None
        self.kernel_matrix: Optional[np.ndarray] = None

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'QSVM':
        """
        Fit the QSVM classifier.

        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (n_samples,) with values in {-1, 1}

        Returns:
            self
        """
        self._ensure_connected()

        self.X_train = X
        self.y_train = y

        # Compute kernel matrix
        n_samples = len(X)
        self.kernel_matrix = np.zeros((n_samples, n_samples))

        for i in range(n_samples):
            for j in range(i, n_samples):
                k = self._compute_kernel(X[i], X[j])
                self.kernel_matrix[i, j] = k
                self.kernel_matrix[j, i] = k

        # Solve dual SVM problem (simplified)
        self.alphas = self._solve_dual(self.kernel_matrix, y)

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Test features (n_samples, n_features)

        Returns:
            Predicted labels
        """
        if self.X_train is None:
            raise ValueError("Model not fitted. Call fit() first.")

        self._ensure_connected()

        predictions = []

        for x in X:
            # Compute kernel with all training points
            decision = 0.0
            for i, (x_train, y_train, alpha) in enumerate(
                zip(self.X_train, self.y_train, self.alphas)
            ):
                if alpha > 1e-6:  # Support vector
                    k = self._compute_kernel(x, x_train)
                    decision += alpha * y_train * k

            predictions.append(1 if decision >= 0 else -1)

        return np.array(predictions)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute classification accuracy."""
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def _compute_kernel(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """Compute quantum kernel between two data points."""
        # Build circuit: U(x1)† U(x2)
        circuit = QuantumCircuit(self.n_qubits, self.n_qubits)

        # Apply feature map for x2
        self._apply_feature_map(circuit, x2)

        # Apply inverse feature map for x1
        self._apply_feature_map_inverse(circuit, x1)

        # Measure
        circuit.measure(range(self.n_qubits), range(self.n_qubits))

        # Execute
        result = self.backend.execute(circuit, shots=self.shots)

        # Kernel = probability of measuring |0...0⟩
        zero_state = '0' * self.n_qubits
        zero_count = result.counts.get(zero_state, 0)

        return zero_count / self.shots

    def _apply_feature_map(self, circuit: QuantumCircuit, x: np.ndarray):
        """Apply feature map encoding data point x."""
        for rep in range(self.reps):
            # Hadamard layer
            circuit.h(range(self.n_qubits))

            # Feature encoding
            if self.feature_map_type == "zz":
                self._zz_feature_map(circuit, x)
            elif self.feature_map_type == "pauli":
                self._pauli_feature_map(circuit, x)
            else:
                self._amplitude_feature_map(circuit, x)

    def _apply_feature_map_inverse(self, circuit: QuantumCircuit, x: np.ndarray):
        """Apply inverse feature map."""
        for rep in range(self.reps - 1, -1, -1):
            # Inverse feature encoding
            if self.feature_map_type == "zz":
                self._zz_feature_map(circuit, -x)
            elif self.feature_map_type == "pauli":
                self._pauli_feature_map(circuit, -x)
            else:
                self._amplitude_feature_map(circuit, -x)

            # Hadamard layer
            circuit.h(range(self.n_qubits))

    def _zz_feature_map(self, circuit: QuantumCircuit, x: np.ndarray):
        """ZZ feature map."""
        # Single qubit rotations
        for i in range(min(len(x), self.n_qubits)):
            circuit.rz(2 * x[i], i)

        # Two-qubit ZZ interactions
        for i in range(self.n_qubits - 1):
            j = i + 1
            if i < len(x) and j < len(x):
                circuit.cx(i, j)
                circuit.rz(2 * (np.pi - x[i]) * (np.pi - x[j]), j)
                circuit.cx(i, j)

    def _pauli_feature_map(self, circuit: QuantumCircuit, x: np.ndarray):
        """Pauli feature map with X, Y, Z rotations."""
        for i in range(min(len(x), self.n_qubits)):
            circuit.rx(x[i], i)
            circuit.ry(x[i], i)
            circuit.rz(x[i], i)

    def _amplitude_feature_map(self, circuit: QuantumCircuit, x: np.ndarray):
        """Simple amplitude-based encoding."""
        for i in range(min(len(x), self.n_qubits)):
            circuit.ry(x[i] * np.pi, i)

    def _solve_dual(self, K: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Solve SVM dual problem (simplified version).

        In practice, use proper QP solver like CVXOPT.
        """
        n = len(y)
        # Simple heuristic: set alphas based on kernel values
        alphas = np.zeros(n)

        for i in range(n):
            # Points with low kernel similarity to same-class points
            same_class = y == y[i]
            diff_class = ~same_class

            same_kernel = np.mean(K[i, same_class]) if any(same_class) else 0
            diff_kernel = np.mean(K[i, diff_class]) if any(diff_class) else 0

            # Higher alpha for boundary points
            alphas[i] = max(0, 1 - same_kernel + diff_kernel)

        # Normalize
        if np.sum(alphas) > 0:
            alphas = alphas / np.sum(alphas)

        return alphas
