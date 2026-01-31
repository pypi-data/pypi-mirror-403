"""
Workflow API Routes.

Provides REST API endpoints for quantum workflow orchestration.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WorkflowStepRequest:
    """Request model for a workflow step."""
    type: str
    params: Optional[Dict[str, Any]] = None
    depends_on: Optional[List[str]] = None
    id: Optional[str] = None


@dataclass
class WorkflowRequest:
    """Request model for creating a workflow."""
    steps: List[Dict[str, Any]]
    backend: str = "simulator"


@dataclass
class WorkflowResponse:
    """Response model for workflow execution."""
    workflow_id: str
    status: str
    steps: List[Dict[str, Any]]
    total_duration_ms: float
    outputs: Dict[str, Any]
    error: Optional[str] = None


def create_workflow_routes():
    """
    Create workflow API routes.

    Returns a router that can be mounted on a FastAPI app.

    Example usage with FastAPI:
        from fastapi import FastAPI
        from quantumflow.api.routes.workflow_routes import create_workflow_routes

        app = FastAPI()
        workflow_router = create_workflow_routes()
        app.include_router(workflow_router, prefix="/v1/workflow")
    """
    try:
        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel
    except ImportError:
        # Return a dummy router if FastAPI is not installed
        return None

    router = APIRouter(tags=["workflow"])

    class WorkflowStepModel(BaseModel):
        type: str
        params: Optional[Dict[str, Any]] = None
        depends_on: Optional[List[str]] = None
        id: Optional[str] = None

    class CreateWorkflowModel(BaseModel):
        steps: List[WorkflowStepModel]
        backend: str = "simulator"

    class ExecuteWorkflowModel(BaseModel):
        workflow_id: Optional[str] = None
        steps: Optional[List[WorkflowStepModel]] = None
        backend: str = "simulator"

    @router.post("/create")
    async def create_workflow(request: CreateWorkflowModel) -> Dict[str, Any]:
        """
        Create a new workflow without executing it.

        Returns the workflow definition that can be executed later.
        """
        from quantumflow.core.workflow import QuantumWorkflow

        workflow = QuantumWorkflow(backend=request.backend)

        for step in request.steps:
            workflow.add_step(
                step_type=step.type,
                params=step.params,
                depends_on=step.depends_on,
                step_id=step.id,
            )

        return workflow.to_dict()

    @router.post("/execute")
    async def execute_workflow(request: ExecuteWorkflowModel) -> Dict[str, Any]:
        """
        Execute a quantum workflow.

        Can either:
        - Execute a new workflow by providing steps
        - Execute an existing workflow by providing workflow_id

        Returns execution results for all steps.
        """
        from quantumflow.core.workflow import QuantumWorkflow

        if not request.steps:
            raise HTTPException(
                status_code=400,
                detail="Steps are required to execute a workflow"
            )

        workflow = QuantumWorkflow(backend=request.backend)

        for step in request.steps:
            workflow.add_step(
                step_type=step.type,
                params=step.params,
                depends_on=step.depends_on,
                step_id=step.id,
            )

        result = workflow.execute()

        return {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "steps": result.steps,
            "total_duration_ms": result.total_duration_ms,
            "outputs": result.outputs,
            "error": result.error,
        }

    @router.post("/compress-and-teleport")
    async def compress_and_teleport(
        tokens: List[int],
        recipient: Optional[str] = None,
        backend: str = "simulator",
    ) -> Dict[str, Any]:
        """
        Convenience endpoint that combines compression and teleportation.

        This is a common workflow pattern for secure quantum messaging.
        """
        from quantumflow.core.workflow import QuantumWorkflow

        workflow = QuantumWorkflow(backend=backend)

        # Step 1: Compress tokens
        workflow.add_step(
            step_type="compress",
            params={"tokens": tokens},
            step_id="compression",
        )

        # Step 2: QKD key exchange
        workflow.add_step(
            step_type="qkd",
            params={"key_length": 256},
            step_id="key_exchange",
            depends_on=["compression"],
        )

        # Step 3: Create Bell pairs for teleportation
        workflow.add_step(
            step_type="teleport",
            params={"n_pairs": 10},
            step_id="teleportation",
            depends_on=["key_exchange"],
        )

        result = workflow.execute()

        return {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "compression": result.outputs.get("compression", {}),
            "qkd": result.outputs.get("key_exchange", {}),
            "teleportation": result.outputs.get("teleportation", {}),
            "total_duration_ms": result.total_duration_ms,
        }

    @router.get("/templates")
    async def get_workflow_templates() -> List[Dict[str, Any]]:
        """
        Get available workflow templates.

        Returns predefined workflow configurations for common use cases.
        """
        return [
            {
                "name": "secure_messaging",
                "description": "Compress tokens, exchange QKD key, and teleport",
                "steps": [
                    {"type": "compress", "params": {"tokens": []}, "id": "compress"},
                    {"type": "qkd", "params": {"key_length": 256}, "id": "qkd", "depends_on": ["compress"]},
                    {"type": "teleport", "params": {"n_pairs": 10}, "id": "teleport", "depends_on": ["qkd"]},
                ],
            },
            {
                "name": "quantum_ml_training",
                "description": "Quantum backpropagation workflow",
                "steps": [
                    {"type": "compress", "params": {"tokens": []}, "id": "compress_input"},
                    {"type": "backprop", "params": {}, "id": "gradient", "depends_on": ["compress_input"]},
                ],
            },
            {
                "name": "optimization",
                "description": "QAOA optimization workflow",
                "steps": [
                    {"type": "qaoa", "params": {"p": 2}, "id": "optimize"},
                ],
            },
        ]

    return router


# Export router for use with FastAPI
try:
    router = create_workflow_routes()
except Exception:
    router = None
