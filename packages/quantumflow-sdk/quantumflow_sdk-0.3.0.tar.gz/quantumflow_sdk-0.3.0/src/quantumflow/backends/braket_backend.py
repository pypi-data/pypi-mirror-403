"""
AWS Braket Backend - Connect to Amazon Braket quantum hardware and simulators.

Supports:
- IonQ (trapped ion)
- Rigetti (superconducting)
- OQC (superconducting)
- AWS Simulators: SV1, DM1, TN1
"""

import os
import time
from typing import Optional, Literal
import numpy as np

from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm2_dumps

from quantumflow.backends.base_backend import (
    QuantumBackend,
    BackendType,
    ExecutionResult,
)

# Braket imports - optional dependency
try:
    from braket.aws import AwsDevice, AwsQuantumTask
    from braket.circuits import Circuit as BraketCircuit
    from braket.devices import LocalSimulator
    BRAKET_AVAILABLE = True
except ImportError:
    BRAKET_AVAILABLE = False
    # Dummy classes for type hints when Braket not installed
    BraketCircuit = None
    AwsDevice = None
    AwsQuantumTask = None
    LocalSimulator = None


# Device ARNs
BRAKET_DEVICES = {
    # Hardware
    "ionq_aria": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1",
    "ionq_forte": "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1",
    "rigetti_aspen": "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3",
    "oqc_lucy": "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy",
    # Simulators
    "sv1": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    "dm1": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
    "tn1": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
}

SIMULATOR_DEVICES = {"sv1", "dm1", "tn1", "local"}


class BraketBackend(QuantumBackend):
    """AWS Braket quantum backend supporting hardware and simulators."""

    def __init__(
        self,
        device: str = "sv1",
        s3_bucket: Optional[str] = None,
        s3_prefix: str = "quantumflow",
        aws_region: Optional[str] = None,
    ):
        """
        Initialize Braket backend.

        Args:
            device: Device name (ionq_aria, ionq_forte, rigetti_aspen, oqc_lucy,
                   sv1, dm1, tn1, local)
            s3_bucket: S3 bucket for results (required for AWS devices)
            s3_prefix: S3 prefix for results
            aws_region: AWS region override
        """
        super().__init__(BackendType.AWS)

        if not BRAKET_AVAILABLE:
            raise ImportError(
                "AWS Braket SDK not installed. Install with: "
                "pip install amazon-braket-sdk"
            )

        self.device_name = device.lower()
        self.s3_bucket = s3_bucket or os.getenv("BRAKET_S3_BUCKET")
        self.s3_prefix = s3_prefix
        self.aws_region = aws_region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")

        self._device: Optional["AwsDevice"] = None
        self._local_simulator: Optional["LocalSimulator"] = None

        # Validate device
        if self.device_name not in BRAKET_DEVICES and self.device_name != "local":
            raise ValueError(
                f"Unknown device: {device}. "
                f"Available: {list(BRAKET_DEVICES.keys()) + ['local']}"
            )

    def connect(self) -> bool:
        """Connect to the Braket device."""
        try:
            if self.device_name == "local":
                self._local_simulator = LocalSimulator()
                self._is_connected = True
                return True

            device_arn = BRAKET_DEVICES[self.device_name]
            self._device = AwsDevice(device_arn)

            # Verify S3 bucket for non-local devices
            if not self.s3_bucket and self.device_name not in {"local"}:
                raise ValueError(
                    "S3 bucket required for AWS Braket devices. "
                    "Set BRAKET_S3_BUCKET env var or pass s3_bucket parameter."
                )

            self._is_connected = True
            return True

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Braket device: {e}")

    def disconnect(self) -> None:
        """Disconnect from the Braket device."""
        self._device = None
        self._local_simulator = None
        self._is_connected = False

    def _qiskit_to_braket(self, circuit: QuantumCircuit) -> "BraketCircuit":
        """
        Convert Qiskit circuit to Braket circuit.

        Uses OpenQASM 2.0 as intermediate representation.
        """
        # Get QASM representation
        qasm_str = qasm2_dumps(circuit)

        # Parse QASM to Braket circuit
        braket_circuit = BraketCircuit.from_ir(qasm_str)

        return braket_circuit

    def _qiskit_to_braket_manual(self, circuit: QuantumCircuit) -> "BraketCircuit":
        """
        Manual gate-by-gate conversion from Qiskit to Braket.

        Fallback if QASM conversion fails.
        """
        braket_circuit = BraketCircuit()

        # Gate mapping
        gate_map = {
            'h': lambda bc, q: bc.h(q[0]),
            'x': lambda bc, q: bc.x(q[0]),
            'y': lambda bc, q: bc.y(q[0]),
            'z': lambda bc, q: bc.z(q[0]),
            's': lambda bc, q: bc.s(q[0]),
            't': lambda bc, q: bc.t(q[0]),
            'sdg': lambda bc, q: bc.si(q[0]),
            'tdg': lambda bc, q: bc.ti(q[0]),
            'cx': lambda bc, q: bc.cnot(q[0], q[1]),
            'cz': lambda bc, q: bc.cz(q[0], q[1]),
            'swap': lambda bc, q: bc.swap(q[0], q[1]),
            'rx': lambda bc, q, p: bc.rx(q[0], p[0]),
            'ry': lambda bc, q, p: bc.ry(q[0], p[0]),
            'rz': lambda bc, q, p: bc.rz(q[0], p[0]),
        }

        for instruction in circuit.data:
            gate_name = instruction.operation.name.lower()
            qubits = [circuit.find_bit(q).index for q in instruction.qubits]
            params = list(instruction.operation.params)

            if gate_name == 'measure':
                continue  # Braket handles measurement differently
            elif gate_name == 'barrier':
                continue  # Skip barriers
            elif gate_name in gate_map:
                if params:
                    gate_map[gate_name](braket_circuit, qubits, params)
                else:
                    gate_map[gate_name](braket_circuit, qubits)
            else:
                raise ValueError(f"Unsupported gate: {gate_name}")

        return braket_circuit

    def execute(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        optimization_level: int = 1,
    ) -> ExecutionResult:
        """Execute a quantum circuit on Braket."""
        if not self._is_connected:
            self.connect()

        self.validate_circuit(circuit)
        start_time = time.perf_counter()

        # Convert Qiskit circuit to Braket
        try:
            braket_circuit = self._qiskit_to_braket(circuit)
        except Exception:
            # Fallback to manual conversion
            braket_circuit = self._qiskit_to_braket_manual(circuit)

        # Execute on device
        if self.device_name == "local":
            # Local simulator
            result = self._local_simulator.run(braket_circuit, shots=shots).result()
            counts = dict(result.measurement_counts)
        else:
            # AWS device
            s3_location = (self.s3_bucket, self.s3_prefix)
            task = self._device.run(braket_circuit, s3_location, shots=shots)
            result = task.result()
            counts = dict(result.measurement_counts)

        # Convert counts format (Braket uses different bit ordering)
        # Braket: qubit 0 is leftmost, Qiskit: qubit 0 is rightmost
        converted_counts = {}
        for bitstring, count in counts.items():
            # Reverse bit order to match Qiskit convention
            reversed_bits = bitstring[::-1]
            converted_counts[reversed_bits] = count

        execution_time = (time.perf_counter() - start_time) * 1000

        return ExecutionResult(
            counts=converted_counts,
            statevector=None,
            shots=shots,
            backend_name=f"braket_{self.device_name}",
            execution_time_ms=execution_time,
            fidelity=self._estimate_fidelity(),
            metadata={
                "device": self.device_name,
                "shots": shots,
                "is_simulator": self.is_simulator,
            },
        )

    def get_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """Get statevector from circuit (simulator only)."""
        if not self.is_simulator:
            raise NotImplementedError(
                "Statevector not available on real quantum hardware"
            )

        if not self._is_connected:
            self.connect()

        # Use local simulator for statevector
        if self._local_simulator is None:
            self._local_simulator = LocalSimulator()

        try:
            braket_circuit = self._qiskit_to_braket(circuit)
        except Exception:
            braket_circuit = self._qiskit_to_braket_manual(circuit)

        # Run with statevector simulator
        result = self._local_simulator.run(braket_circuit, shots=0).result()

        # Get statevector from result
        if hasattr(result, 'values') and len(result.values) > 0:
            return np.array(result.values[0])

        raise ValueError("Could not retrieve statevector from result")

    @property
    def max_qubits(self) -> int:
        """Maximum qubits supported by this device."""
        qubit_limits = {
            "ionq_aria": 25,
            "ionq_forte": 32,
            "rigetti_aspen": 80,
            "oqc_lucy": 8,
            "sv1": 34,
            "dm1": 17,
            "tn1": 50,
            "local": 26,
        }
        return qubit_limits.get(self.device_name, 26)

    @property
    def is_simulator(self) -> bool:
        """Whether this backend is a simulator."""
        return self.device_name in SIMULATOR_DEVICES

    def _estimate_fidelity(self) -> float:
        """Estimate fidelity based on device type."""
        fidelity_estimates = {
            "ionq_aria": 0.995,
            "ionq_forte": 0.997,
            "rigetti_aspen": 0.99,
            "oqc_lucy": 0.98,
            "sv1": 1.0,
            "dm1": 1.0,
            "tn1": 1.0,
            "local": 1.0,
        }
        return fidelity_estimates.get(self.device_name, 0.99)

    def get_device_status(self) -> dict:
        """Get current device status and availability."""
        if not self._is_connected:
            self.connect()

        if self.device_name == "local":
            return {
                "device": "local",
                "status": "AVAILABLE",
                "queue_depth": 0,
            }

        if self._device:
            return {
                "device": self.device_name,
                "status": str(self._device.status),
                "queue_depth": getattr(self._device, 'queue_depth', None),
                "provider": self._device.provider_name,
            }

        return {"device": self.device_name, "status": "UNKNOWN"}

    @staticmethod
    def list_available_devices() -> list[dict]:
        """List all available Braket devices."""
        devices = []
        for name, arn in BRAKET_DEVICES.items():
            devices.append({
                "name": name,
                "arn": arn,
                "is_simulator": name in SIMULATOR_DEVICES,
                "provider": arn.split("/")[-2] if "/" in arn else "amazon",
            })
        devices.append({
            "name": "local",
            "arn": None,
            "is_simulator": True,
            "provider": "local",
        })
        return devices
