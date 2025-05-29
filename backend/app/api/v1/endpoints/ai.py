"""
AI-related API endpoints for prompt analysis and model management
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ....core.security import get_current_user
from ....services.litellm_service import litellm_service
from ....models.workflow import WorkflowCreate


router = APIRouter()


class PromptAnalysisRequest(BaseModel):
    """Request model for prompt analysis"""
    prompt: str
    context: Dict[str, Any] = {}


class WorkflowGenerationRequest(BaseModel):
    """Request model for workflow generation"""
    prompt: str
    preferences: Dict[str, Any] = {}


class ModelTestRequest(BaseModel):
    """Request model for testing AI models"""
    model: str = "openai/gpt-3.5-turbo"
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 100


@router.post("/analyze-prompt")
async def analyze_prompt(
    request: PromptAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze user prompt to extract intent and suggest workflow structure
    """
    try:
        analysis = await litellm_service.analyze_intent(request.prompt)

        return {
            "success": True,
            "analysis": analysis,
            "user_id": current_user["id"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt analysis failed: {str(e)}"
        )


@router.post("/generate-workflow")
async def generate_workflow(
    request: WorkflowGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate a complete workflow structure from user prompt
    """
    try:
        # First analyze the prompt
        intent_analysis = await litellm_service.analyze_intent(request.prompt)

        # Then generate workflow structure
        workflow_structure = await litellm_service.generate_workflow_structure(intent_analysis)

        # Convert to WorkflowCreate model for validation
        try:
            workflow_create = WorkflowCreate(**workflow_structure)
            workflow_dict = workflow_create.dict()
        except Exception as validation_error:
            # If validation fails, return the raw structure with a warning
            workflow_dict = workflow_structure
            workflow_dict["validation_warning"] = f"Generated workflow may need manual adjustment: {str(validation_error)}"

        return {
            "success": True,
            "workflow": workflow_dict,
            "intent_analysis": intent_analysis,
            "generation_meta": workflow_structure.get("generation_meta", {}),
            "user_id": current_user["id"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow generation failed: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """
    Get list of available AI models
    """
    try:
        models = litellm_service.get_available_models()

        return {
            "success": True,
            "models": models,
            "count": len(models)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get models: {str(e)}"
        )


@router.post("/test-model")
async def test_model(
    request: ModelTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Test an AI model with custom messages
    """
    try:
        response = await litellm_service.completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return {
            "success": True,
            "response": response,
            "model": request.model,
            "user_id": current_user["id"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model test failed: {str(e)}"
        )


@router.post("/test-connection")
async def test_ai_connection(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Test the AI service connection
    """
    try:
        result = await litellm_service.test_connection()

        if result["status"] == "success":
            return {
                "success": True,
                "message": "AI service connection successful",
                "details": result,
                "user_id": current_user["id"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )


@router.post("/chat")
async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "openai/gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Simple chat completion endpoint for testing
    """
    try:
        response = await litellm_service.completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return {
            "success": True,
            "message": response["content"],
            "usage": response["usage"],
            "cost": response["cost"],
            "model": response["model"],
            "user_id": current_user["id"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        )
