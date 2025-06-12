"""
Workflow API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import StreamingResponse
import json

# from ....core.security import get_current_user
from ....database import get_supabase
from ....database.supabase_client import get_supabase_client
from ....models.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowTemplate, NodeType
)
from ....models.execution import ExecutionRequest, ExecutionResponse
from ....services.workflow_service import WorkflowService
from ....services.execution_service import ExecutionService
from ....services.litellm_service import litellm_service


# Temporary user placeholder
def get_current_user():
    return {"id": "test_user_id"}


router = APIRouter()

workflow_service = WorkflowService(supabase=get_supabase_client())


@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new workflow"""
    service = WorkflowService(supabase=get_supabase_client())

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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific workflow"""
    service = WorkflowService(supabase=get_supabase_client())

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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a workflow"""
    service = WorkflowService(supabase=get_supabase_client())

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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a workflow"""
    service = WorkflowService(supabase=get_supabase_client())

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


@router.post("/execute/{workflow_id}")
async def execute_workflow(
    workflow_id: str,
    execution_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Execute a workflow with given input data
    """
    try:
        # Get workflow
        workflow = await workflow_service.get_workflow(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Import execution service
        from ....services.workflow_execution_service import WorkflowExecutionService
        
        execution_service = WorkflowExecutionService(get_supabase_client())

        # Start execution
        execution_generator = execution_service.execute_workflow(
            workflow=workflow,
            input_data=execution_data.get("input_data", {}),
            user_id=current_user["id"]
        )

        # Collect all execution events
        events = []
        async for event in execution_generator:
            events.append(event)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "execution_events": events,
            "final_result": events[-1] if events else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/execute-stream/{workflow_id}")
async def execute_workflow_stream(
    workflow_id: str,
    execution_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Execute a workflow with streaming response for real-time updates
    """
    try:
        # Get workflow
        workflow = await workflow_service.get_workflow(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )

        # Import execution service
        from ....services.workflow_execution_service import WorkflowExecutionService
        
        execution_service = WorkflowExecutionService(get_supabase_client())

        async def generate_events():
            try:
                execution_generator = execution_service.execute_workflow(
                    workflow=workflow,
                    input_data=execution_data.get("input_data", {}),
                    user_id=current_user["id"]
                )

                async for event in execution_generator:
                    yield f"data: {json.dumps(event)}\n\n"
                    
                # Send completion signal
                yield f"data: {json.dumps({'type': 'stream_complete'})}\n\n"
                
            except Exception as e:
                error_event = {
                    "type": "stream_error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/validate")
async def validate_workflow(
    workflow_data: WorkflowCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate a workflow structure without saving it
    """
    try:
        # Basic validation
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

        # Check for start node
        start_nodes = [n for n in workflow_data.nodes if n.type == NodeType.START]
        if not start_nodes:
            validation_results["errors"].append("Workflow must have at least one START node")
            validation_results["valid"] = False

        # Check for end/answer node
        end_nodes = [n for n in workflow_data.nodes if n.type in [NodeType.ANSWER, NodeType.END]]
        if not end_nodes:
            validation_results["warnings"].append("Workflow should have an ANSWER or END node")

        # Check node connections
        node_ids = {n.id for n in workflow_data.nodes}
        for edge in workflow_data.edges:
            if edge.source not in node_ids:
                validation_results["errors"].append(f"Edge references non-existent source node: {edge.source}")
                validation_results["valid"] = False
            if edge.target not in node_ids:
                validation_results["errors"].append(f"Edge references non-existent target node: {edge.target}")
                validation_results["valid"] = False

        # Check for isolated nodes
        connected_nodes = set()
        for edge in workflow_data.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        isolated_nodes = node_ids - connected_nodes
        if len(isolated_nodes) > 1:  # Allow one isolated node (could be start)
            validation_results["warnings"].append(f"Found isolated nodes: {list(isolated_nodes)}")

        # Check LLM nodes have prompts
        for node in workflow_data.nodes:
            if node.type in [NodeType.LLM, NodeType.CHAT]:
                if not node.data.prompt:
                    validation_results["errors"].append(f"LLM node '{node.id}' requires a prompt")
                    validation_results["valid"] = False

        # Check variable usage
        all_variables = workflow_data.get_workflow_variables()
        defined_variables = {v.variable for v in workflow_data.variables}
        undefined_variables = set(all_variables) - defined_variables
        
        if undefined_variables:
            validation_results["warnings"].append(f"Variables used but not defined: {list(undefined_variables)}")

        return {
            "success": True,
            "validation": validation_results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow validation failed: {str(e)}"
        )


@router.post("/from-template", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow_from_template(
    template_id: str = Body(..., embed=True),
    custom_name: Optional[str] = Body(None, embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a workflow from a template"""
    service = WorkflowService(supabase=get_supabase_client())

    workflow = await service.create_from_template(template_id, current_user["id"], custom_name)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )

    return workflow
