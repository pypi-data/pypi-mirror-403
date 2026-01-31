"""
Quantum Workflow Orchestration Module.

Provides workflow orchestration for chaining quantum operations like:
- Token compression
- QKD key exchange
- Quantum teleportation
- Algorithm execution

Example:
    from quantumflow.core.workflow import QuantumWorkflow

    workflow = QuantumWorkflow()
    workflow.add_step("compress", tokens=[100, 200, 150])
    workflow.add_step("qkd", key_length=256)
    workflow.add_step("teleport", use_compression=True)
    result = workflow.execute()
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time
import uuid


class StepType(Enum):
    """Types of workflow steps."""
    COMPRESS = "compress"
    DECOMPRESS = "decompress"
    QKD = "qkd"
    TELEPORT = "teleport"
    BACKPROP = "backprop"
    QAOA = "qaoa"
    VQE = "vqe"
    CUSTOM = "custom"


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step in a quantum workflow."""
    id: str
    step_type: StepType
    params: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    depends_on: List[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        """Duration of step execution in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return None


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    status: str
    steps: List[Dict[str, Any]]
    total_duration_ms: float
    outputs: Dict[str, Any]
    error: Optional[str] = None


class QuantumWorkflow:
    """
    Orchestrates quantum operations in a workflow.

    Supports:
    - Sequential step execution
    - Dependency management between steps
    - Error handling and recovery
    - Step result passing to subsequent steps
    """

    def __init__(self, backend: str = "simulator"):
        """
        Initialize a quantum workflow.

        Args:
            backend: Quantum backend to use (simulator, ibm, braket)
        """
        self.workflow_id = str(uuid.uuid4())
        self.backend = backend
        self.steps: List[WorkflowStep] = []
        self._step_results: Dict[str, Any] = {}

    def add_step(
        self,
        step_type: str,
        params: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        step_id: Optional[str] = None,
    ) -> str:
        """
        Add a step to the workflow.

        Args:
            step_type: Type of step (compress, qkd, teleport, etc.)
            params: Parameters for the step
            depends_on: List of step IDs this step depends on
            step_id: Optional custom step ID

        Returns:
            The ID of the created step
        """
        if step_id is None:
            step_id = f"step_{len(self.steps) + 1}"

        step = WorkflowStep(
            id=step_id,
            step_type=StepType(step_type),
            params=params or {},
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        return step_id

    def _execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: The step to execute

        Returns:
            Result of the step execution
        """
        from quantumflow.core.quantum_compressor import QuantumCompressor
        from quantumflow.core.teleportation import QKDExchange, QuantumTeleporter

        step.status = StepStatus.RUNNING
        step.started_at = time.time()

        try:
            result = {}

            if step.step_type == StepType.COMPRESS:
                compressor = QuantumCompressor(backend=self.backend)
                tokens = step.params.get("tokens", [])
                compressed = compressor.compress(tokens)
                result = {
                    "amplitudes": compressed.amplitudes.tolist() if hasattr(compressed.amplitudes, 'tolist') else compressed.amplitudes,
                    "n_qubits": compressed.n_qubits,
                    "compression_percentage": compressed.compression_percentage,
                    "input_token_count": compressed.input_token_count,
                }

            elif step.step_type == StepType.QKD:
                qkd = QKDExchange(backend=self.backend)
                key_length = step.params.get("key_length", 256)
                qkd_result = qkd.exchange(key_length=key_length)
                result = qkd_result

            elif step.step_type == StepType.TELEPORT:
                teleporter = QuantumTeleporter(backend=self.backend)
                state = step.params.get("state")
                if state:
                    teleport_result = teleporter.teleport_state(state)
                    result = {
                        "fidelity": teleport_result.fidelity,
                        "corrections_applied": teleport_result.corrections_applied,
                    }
                else:
                    # Create Bell pairs
                    n_pairs = step.params.get("n_pairs", 10)
                    pairs = teleporter.create_bell_pairs(n_pairs)
                    result = {"bell_pairs_created": n_pairs}

            elif step.step_type == StepType.BACKPROP:
                from quantumflow.core.quantum_backprop import QuantumBackprop
                backprop = QuantumBackprop(backend=self.backend)
                bp_result = backprop.compute_gradient(
                    input_state=step.params.get("input_state", [0.5, 0.5]),
                    target_state=step.params.get("target_state", [0.8, 0.2]),
                    weights=step.params.get("weights", [0.3, 0.7]),
                )
                result = {
                    "gradients": bp_result.gradients,
                    "similarity": bp_result.similarity,
                }

            elif step.step_type == StepType.QAOA:
                from quantumflow.algorithms.optimization.qaoa import QuantumQAOA
                qaoa = QuantumQAOA(backend=self.backend)
                qaoa_result = qaoa.optimize(
                    problem=step.params.get("problem", {}),
                    p=step.params.get("p", 2),
                )
                result = qaoa_result

            elif step.step_type == StepType.VQE:
                from quantumflow.algorithms.machine_learning.vqe import QuantumVQE
                vqe = QuantumVQE(backend=self.backend)
                vqe_result = vqe.find_ground_state(
                    hamiltonian=step.params.get("hamiltonian", {}),
                )
                result = vqe_result

            else:
                # Custom step - just pass through params
                result = step.params

            step.status = StepStatus.COMPLETED
            step.result = result
            step.completed_at = time.time()

            return result

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = time.time()
            raise

    def execute(self) -> WorkflowResult:
        """
        Execute all steps in the workflow.

        Returns:
            WorkflowResult with all step results
        """
        start_time = time.time()
        outputs = {}
        error = None

        try:
            for step in self.steps:
                # Check dependencies
                for dep_id in step.depends_on:
                    dep_step = next((s for s in self.steps if s.id == dep_id), None)
                    if dep_step and dep_step.status != StepStatus.COMPLETED:
                        step.status = StepStatus.SKIPPED
                        step.error = f"Dependency {dep_id} not completed"
                        continue

                # Execute the step
                result = self._execute_step(step)
                self._step_results[step.id] = result
                outputs[step.id] = result

        except Exception as e:
            error = str(e)

        end_time = time.time()

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status="completed" if error is None else "failed",
            steps=[
                {
                    "id": s.id,
                    "type": s.step_type.value,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                    "duration_ms": s.duration_ms,
                }
                for s in self.steps
            ],
            total_duration_ms=(end_time - start_time) * 1000,
            outputs=outputs,
            error=error,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation."""
        return {
            "workflow_id": self.workflow_id,
            "backend": self.backend,
            "steps": [
                {
                    "id": s.id,
                    "type": s.step_type.value,
                    "params": s.params,
                    "depends_on": s.depends_on,
                }
                for s in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuantumWorkflow":
        """Create workflow from dictionary representation."""
        workflow = cls(backend=data.get("backend", "simulator"))
        workflow.workflow_id = data.get("workflow_id", workflow.workflow_id)

        for step_data in data.get("steps", []):
            workflow.add_step(
                step_type=step_data["type"],
                params=step_data.get("params", {}),
                depends_on=step_data.get("depends_on", []),
                step_id=step_data.get("id"),
            )

        return workflow
