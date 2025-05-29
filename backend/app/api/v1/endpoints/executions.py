"""
Execution API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ....core.security import get_current_user
from ....database import get_supabase
from ....models.execution import WorkflowExecution, ExecutionSummary
from ....services.execution_service import ExecutionService


router = APIRouter()


@router.get("/", response_model=List[WorkflowExecution])
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List executions for the current user"""
    service = ExecutionService(supabase)

    executions = await service.list_executions(
        current_user["id"],
        workflow_id=workflow_id,
        limit=limit,
        offset=offset
    )
    return executions


@router.get("/{execution_id}", response_model=WorkflowExecution)
async def get_execution(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific execution"""
    service = ExecutionService(supabase)

    execution = await service.get_execution(execution_id, current_user["id"])

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    return execution


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a running execution"""
    service = ExecutionService(supabase)

    execution = await service.get_execution(execution_id, current_user["id"])

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )

    if not execution.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution is not running"
        )

    # TODO: Implement cancellation logic
    return {"message": "Execution cancelled", "execution_id": execution_id}
