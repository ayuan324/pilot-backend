"""
Workflow API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import json

from ....core.security import get_current_user
from ....database import get_supabase
from ....models.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowTemplate
)
from ....models.execution import ExecutionRequest, ExecutionResponse
from ....services.workflow_service import WorkflowService
from ....services.execution_service import ExecutionService
from ....services.litellm_service import litellm_service


router = APIRouter()


@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new workflow"""
    service = WorkflowService(supabase)

    try:
        workflow = await service.create_workflow(workflow_data, current_user["id"])
        return workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/", response_model=List[Workflow])
async def list_workflows(
    include_public: bool = Query(True, description="Include public workflows"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List workflows for the current user"""
    service = WorkflowService(supabase)

    workflows = await service.list_workflows(
        current_user["id"],
        include_public=include_public,
        limit=limit,
        offset=offset
    )
    return workflows


@router.get("/search", response_model=List[Workflow])
async def search_workflows(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Search workflows by name or description"""
    service = WorkflowService(supabase)

    workflows = await service.search_workflows(q, current_user["id"], limit)
    return workflows


@router.get("/templates")
async def get_workflow_templates():
    """Get available workflow templates"""
    service = WorkflowService(None)  # Templates don't need database

    templates = await service.get_workflow_templates()
    return templates


@router.post("/templates/{template_id}", response_model=Workflow)
async def create_from_template(
    template_id: str,
    name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a workflow from a template"""
    service = WorkflowService(supabase)

    workflow = await service.create_from_template(template_id, current_user["id"], name)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )

    return workflow


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific workflow"""
    service = WorkflowService(supabase)

    workflow = await service.get_workflow(workflow_id, current_user["id"])

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return workflow


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a workflow"""
    service = WorkflowService(supabase)

    workflow = await service.update_workflow(workflow_id, workflow_data, current_user["id"])

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied"
        )

    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a workflow"""
    service = WorkflowService(supabase)

    success = await service.delete_workflow(workflow_id, current_user["id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied"
        )


@router.post("/{workflow_id}/publish", response_model=Workflow)
async def publish_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Publish a workflow (make it public)"""
    service = WorkflowService(supabase)

    workflow = await service.publish_workflow(workflow_id, current_user["id"])

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied"
        )

    return workflow


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Execute a workflow"""
    workflow_service = WorkflowService(supabase)
    execution_service = ExecutionService(supabase)

    # Get workflow
    workflow = await workflow_service.get_workflow(workflow_id, current_user["id"])
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Create execution
    execution = await execution_service.create_execution(workflow, request, current_user["id"])

    # Start async execution (fire and forget)
    import asyncio

    async def run_execution():
        async for event in execution_service.execute_workflow(workflow, execution):
            pass  # Events are handled via WebSocket

    asyncio.create_task(run_execution())

    return ExecutionResponse(
        execution_id=execution.id,
        status=execution.status,
        message="Workflow execution started"
    )


@router.get("/{workflow_id}/execute/{execution_id}/stream")
async def stream_execution(
    workflow_id: str,
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Stream real-time execution events"""
    workflow_service = WorkflowService(supabase)
    execution_service = ExecutionService(supabase)

    # Verify access
    workflow = await workflow_service.get_workflow(workflow_id, current_user["id"])
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    execution = await execution_service.get_execution(execution_id, current_user["id"])
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    async def event_stream():
        """Generate Server-Sent Events for execution updates"""
        async for event in execution_service.execute_workflow(workflow, execution):
            yield f"data: {json.dumps(event.dict())}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )
