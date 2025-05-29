"""
API v1 router
"""
from fastapi import APIRouter

from .endpoints import workflows, executions, ai

api_router = APIRouter()

api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
