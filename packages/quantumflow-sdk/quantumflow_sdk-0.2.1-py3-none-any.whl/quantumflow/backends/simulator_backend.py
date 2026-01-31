"""
Simulator Backend - Local quantum simulator using Qiskit Aer.
"""

import time
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector

from quantumflow.backends.base_backend import (
    QuantumBackend,
    BackendType,
    ExecutionResult,
)


class SimulatorBackend(QuantumBackend):
    """Local quantum simulator using Qiskit Aer."""

    def __init__(self, method: str = "statevector", noise_model: Optional[object] = None):
        super().__init__(BackendType.SIMULATOR)
        self.method = method
        self.noise_model = noise_model
        self._simulator: Optional[AerSimulator] = None
        self._max_qubits = 30

    def connect(self) -> bool:
        try:
            self._simulator = AerSimulator(method=self.method)
            if self.noise_model:
                self._simulator.set_options(noise_model=self.noise_model)
            self._is_connected = True
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to initialize simulator: {e}")

    def disconnect(self) -> None:
        self._simulator = None
        self._is_connected = False

    def execute(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        optimization_level: int = 1,
    ) -> ExecutionResult:
        if not self._is_connected:
            self.connect()

        self.validate_circuit(circuit)
        start_time = time.perf_counter()

        # Get statevector if no measurements
        has_measurements = any(inst.operation.name == "measure" for inst in circuit.data)
        statevector = None if has_measurements else self.get_statevector(circuit)

        # Add measurements for sampling
        exec_circuit = circuit.copy()
        if not has_measurements:
            exec_circuit.measure_all()

        transpiled = transpile(exec_circuit, self._simulator, optimization_level=optimization_level)
        job = self._simulator.run(transpiled, shots=shots)
        counts = job.result().get_counts()

        return ExecutionResult(
            counts=counts,
            statevector=statevector,
            shots=shots,
            backend_name="aer_simulator",
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
            fidelity=1.0,
        )

    def get_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        return Statevector(circuit).data

    @property
    def max_qubits(self) -> int:
        return self._max_qubits

    @property
    def is_simulator(self) -> bool:
        return True
