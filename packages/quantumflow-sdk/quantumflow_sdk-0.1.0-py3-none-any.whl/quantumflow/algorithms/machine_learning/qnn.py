"""
Quantum Neural Network (QNN).

Parameterized quantum circuits for machine learning tasks.
Integrates with Paper 2's quantum backpropagation.
"""

from dataclasses import dataclass
from typing import Optional, Callable
import numpy as np
from qiskit import QuantumCircuit

from quantumflow.backends.base_backend import QuantumBackend, get_backend, BackendType


@dataclass
class QNNResult:
    """Result from QNN training."""

    final_weights: np.ndarray
    loss_history: list[float]
    accuracy: float
    n_epochs: int


class QNN:
    """
    Quantum Neural Network.

    A parameterized quantum circuit that can be trained for:
    - Binary classification
    - Multi-class classification
    - Regression

    Architecture:
    - Input encoding layer (amplitude or angle encoding)
    - Variational layers (parameterized rotations + entanglement)
    - Measurement layer

    Example:
        >>> qnn = QNN(n_qubits=4, n_layers=3)
        >>> result = qnn.fit(X_train, y_train, epochs=100)
        >>> predictions = qnn.predict(X_test)
    """

    def __init__(
        self,
        n_qubits: int,
        n_layers: int = 2,
        backend: BackendType | str = BackendType.AUTO,
        learning_rate: float = 0.1,
        shots: int = 1024,
    ):
        """
        Initialize QNN.

        Args:
            n_qubits: Number of qubits
            n_layers: Number of variational layers
            backend: Quantum backend
            learning_rate: Learning rate for optimization
            shots: Measurement shots
        """
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.backend = get_backend(backend)
        self.learning_rate = learning_rate
        self.shots = shots
        self._connected = False

        # Initialize weights: 3 parameters per qubit per layer (rx, ry, rz)
        self.n_params = n_qubits * n_layers * 3
        self.weights = np.random.uniform(-np.pi, np.pi, self.n_params)

    def _ensure_connected(self):
        if not self._connected:
            self.backend.connect()
            self._connected = True

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        batch_size: int = 8,
    ) -> QNNResult:
        """
        Train the QNN.

        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (n_samples,)
            epochs: Number of training epochs
            batch_size: Mini-batch size

        Returns:
            QNNResult with training history
        """
        self._ensure_connected()

        loss_history = []

        for epoch in range(epochs):
            epoch_loss = 0.0

            # Mini-batch training
            indices = np.random.permutation(len(X))

            for i in range(0, len(X), batch_size):
                batch_idx = indices[i:i + batch_size]
                X_batch = X[batch_idx]
                y_batch = y[batch_idx]

                # Forward pass and gradient computation
                batch_loss, gradients = self._compute_batch_gradient(X_batch, y_batch)
                epoch_loss += batch_loss

                # Update weights
                self.weights -= self.learning_rate * gradients

            epoch_loss /= (len(X) / batch_size)
            loss_history.append(epoch_loss)

        # Compute final accuracy
        predictions = self.predict(X)
        accuracy = np.mean(predictions == y)

        return QNNResult(
            final_weights=self.weights.copy(),
            loss_history=loss_history,
            accuracy=accuracy,
            n_epochs=epochs,
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Input features (n_samples, n_features)

        Returns:
            Predicted labels
        """
        self._ensure_connected()

        predictions = []

        for x in X:
            prob = self._forward(x)
            predictions.append(1 if prob > 0.5 else 0)

        return np.array(predictions)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: Input features

        Returns:
            Probabilities for class 1
        """
        self._ensure_connected()

        probs = []
        for x in X:
            prob = self._forward(x)
            probs.append(prob)

        return np.array(probs)

    def _forward(self, x: np.ndarray) -> float:
        """Forward pass for a single input."""
        circuit = self._build_circuit(x, self.weights)
        result = self.backend.execute(circuit, shots=self.shots)

        # Probability of measuring |1⟩ on first qubit
        ones_count = sum(
            count for state, count in result.counts.items()
            if state[-1] == '1'
        )

        return ones_count / self.shots

    def _build_circuit(
        self,
        x: np.ndarray,
        weights: np.ndarray,
    ) -> QuantumCircuit:
        """Build QNN circuit."""
        circuit = QuantumCircuit(self.n_qubits, 1, name="qnn")

        # Input encoding
        self._encode_input(circuit, x)

        # Variational layers
        param_idx = 0
        for layer in range(self.n_layers):
            # Single qubit rotations
            for i in range(self.n_qubits):
                circuit.rx(weights[param_idx], i)
                param_idx += 1
                circuit.ry(weights[param_idx], i)
                param_idx += 1
                circuit.rz(weights[param_idx], i)
                param_idx += 1

            # Entangling layer (ring topology)
            for i in range(self.n_qubits):
                circuit.cx(i, (i + 1) % self.n_qubits)

        # Measure first qubit
        circuit.measure(0, 0)

        return circuit

    def _encode_input(self, circuit: QuantumCircuit, x: np.ndarray):
        """Encode input features into quantum state."""
        # Angle encoding: each feature -> rotation angle
        for i in range(min(len(x), self.n_qubits)):
            circuit.ry(x[i] * np.pi, i)

        # Initialize unmapped qubits
        for i in range(len(x), self.n_qubits):
            circuit.h(i)

    def _compute_batch_gradient(
        self,
        X_batch: np.ndarray,
        y_batch: np.ndarray,
    ) -> tuple[float, np.ndarray]:
        """Compute gradient using parameter shift rule."""
        batch_loss = 0.0
        gradients = np.zeros_like(self.weights)
        shift = np.pi / 2

        for x, y in zip(X_batch, y_batch):
            # Forward pass
            pred = self._forward(x)
            loss = (pred - y) ** 2
            batch_loss += loss

            # Parameter shift gradient
            for i in range(len(self.weights)):
                # Shift +
                weights_plus = self.weights.copy()
                weights_plus[i] += shift
                circuit_plus = self._build_circuit(x, weights_plus)
                result_plus = self.backend.execute(circuit_plus, shots=self.shots)
                ones_plus = sum(
                    c for s, c in result_plus.counts.items() if s[-1] == '1'
                )
                pred_plus = ones_plus / self.shots

                # Shift -
                weights_minus = self.weights.copy()
                weights_minus[i] -= shift
                circuit_minus = self._build_circuit(x, weights_minus)
                result_minus = self.backend.execute(circuit_minus, shots=self.shots)
                ones_minus = sum(
                    c for s, c in result_minus.counts.items() if s[-1] == '1'
                )
                pred_minus = ones_minus / self.shots

                # Gradient
                d_pred = (pred_plus - pred_minus) / 2
                d_loss = 2 * (pred - y) * d_pred
                gradients[i] += d_loss

        # Average over batch
        batch_loss /= len(X_batch)
        gradients /= len(X_batch)

        return batch_loss, gradients
