"""
Workflow service for database operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from ..models.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowInDB,
    WORKFLOW_TEMPLATES
)
from ..database.supabase_client import SupabaseClient


class WorkflowService:
    """Service for workflow database operations"""

    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    async def create_workflow(self, workflow_data: WorkflowCreate, user_id: str) -> Workflow:
        """Create a new workflow"""
        # Prepare workflow data for database
        db_data = {
            "id": str(uuid.uuid4()),
            "name": workflow_data.name,
            "description": workflow_data.description,
            "user_id": user_id,
            "workflow_data": {
                "nodes": [node.dict() for node in workflow_data.nodes],
                "edges": [edge.dict() for edge in workflow_data.edges],
                "variables": [var.dict() for var in workflow_data.variables],
                "tags": workflow_data.tags
            },
            "status": "draft",
            "is_public": workflow_data.is_public,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert into database
        result = self.supabase.client.table("workflows").insert(db_data).execute()

        if result.data:
            return self._db_to_workflow(result.data[0])
        else:
            raise Exception(f"Failed to create workflow: {result}")

    async def get_workflow(self, workflow_id: str, user_id: Optional[str] = None) -> Optional[Workflow]:
        """Get a workflow by ID"""
        query = self.supabase.client.table("workflows").select("*").eq("id", workflow_id)

        # If user_id provided, ensure user owns the workflow or it's public
        if user_id:
            query = query.or_(f"user_id.eq.{user_id},is_public.eq.true")
        else:
            query = query.eq("is_public", True)

        result = query.execute()

        if result.data:
            return self._db_to_workflow(result.data[0])
        return None

    async def list_workflows(
        self,
        user_id: str,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows for a user"""
        query = self.supabase.client.table("workflows").select("*")

        if include_public:
            query = query.or_(f"user_id.eq.{user_id},is_public.eq.true")
        else:
            query = query.eq("user_id", user_id)

        query = query.order("updated_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return [self._db_to_workflow(row) for row in result.data or []]

    async def update_workflow(
        self,
        workflow_id: str,
        workflow_data: WorkflowUpdate,
        user_id: str
    ) -> Optional[Workflow]:
        """Update a workflow"""
        # First check if user owns the workflow
        existing = await self.get_workflow(workflow_id, user_id)
        if not existing or existing.user_id != user_id:
            return None

        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if workflow_data.name is not None:
            update_data["name"] = workflow_data.name
        if workflow_data.description is not None:
            update_data["description"] = workflow_data.description
        if workflow_data.is_public is not None:
            update_data["is_public"] = workflow_data.is_public

        # Update workflow_data if any structural changes
        if any([
            workflow_data.nodes is not None,
            workflow_data.edges is not None,
            workflow_data.variables is not None,
            workflow_data.tags is not None
        ]):
            current_workflow_data = existing.dict()

            if workflow_data.nodes is not None:
                current_workflow_data["nodes"] = [node.dict() for node in workflow_data.nodes]
            if workflow_data.edges is not None:
                current_workflow_data["edges"] = [edge.dict() for edge in workflow_data.edges]
            if workflow_data.variables is not None:
                current_workflow_data["variables"] = [var.dict() for var in workflow_data.variables]
            if workflow_data.tags is not None:
                current_workflow_data["tags"] = workflow_data.tags

            update_data["workflow_data"] = {
                "nodes": current_workflow_data["nodes"],
                "edges": current_workflow_data["edges"],
                "variables": current_workflow_data["variables"],
                "tags": current_workflow_data["tags"]
            }

        # Execute update
        result = self.supabase.client.table("workflows").update(update_data).eq("id", workflow_id).execute()

        if result.data:
            return self._db_to_workflow(result.data[0])
        return None

    async def delete_workflow(self, workflow_id: str, user_id: str) -> bool:
        """Delete a workflow"""
        # Check ownership
        existing = await self.get_workflow(workflow_id, user_id)
        if not existing or existing.user_id != user_id:
            return False

        # Delete workflow
        result = self.supabase.client.table("workflows").delete().eq("id", workflow_id).execute()

        return len(result.data or []) > 0

    async def publish_workflow(self, workflow_id: str, user_id: str) -> Optional[Workflow]:
        """Publish a workflow (make it public)"""
        return await self.update_workflow(
            workflow_id,
            WorkflowUpdate(is_public=True, status="published"),
            user_id
        )

    async def search_workflows(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Workflow]:
        """Search workflows by name or description"""
        supabase_query = self.supabase.client.table("workflows").select("*")

        # Text search in name and description
        supabase_query = supabase_query.or_(
            f"name.ilike.%{query}%,description.ilike.%{query}%"
        )

        # Include public workflows and user's own workflows
        if user_id:
            supabase_query = supabase_query.or_(f"user_id.eq.{user_id},is_public.eq.true")
        else:
            supabase_query = supabase_query.eq("is_public", True)

        supabase_query = supabase_query.limit(limit)

        result = supabase_query.execute()

        return [self._db_to_workflow(row) for row in result.data or []]

    async def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        return {
            "templates": [template.dict() for template in WORKFLOW_TEMPLATES.values()],
            "categories": list(set(t.category for t in WORKFLOW_TEMPLATES.values())),
            "count": len(WORKFLOW_TEMPLATES)
        }

    async def create_from_template(
        self,
        template_id: str,
        user_id: str,
        custom_name: Optional[str] = None
    ) -> Optional[Workflow]:
        """Create a workflow from a template"""
        if template_id not in WORKFLOW_TEMPLATES:
            return None

        template = WORKFLOW_TEMPLATES[template_id]

        # Create workflow from template
        workflow_data = WorkflowCreate(
            name=custom_name or f"{template.name} (Copy)",
            description=template.description,
            nodes=template.workflow.nodes,
            edges=template.workflow.edges,
            variables=template.workflow.variables,
            tags=template.tags
        )

        return await self.create_workflow(workflow_data, user_id)

    def _db_to_workflow(self, db_row: Dict[str, Any]) -> Workflow:
        """Convert database row to Workflow model"""
        workflow_data = db_row.get("workflow_data", {})

        return Workflow(
            id=db_row["id"],
            name=db_row["name"],
            description=db_row.get("description"),
            user_id=db_row["user_id"],
            status=db_row.get("status", "draft"),
            is_public=db_row.get("is_public", False),
            nodes=[],  # Will be populated from workflow_data
            edges=[],  # Will be populated from workflow_data
            variables=[],  # Will be populated from workflow_data
            tags=workflow_data.get("tags", []),
            created_at=datetime.fromisoformat(db_row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(db_row["updated_at"].replace("Z", "+00:00")),
            last_executed_at=None,  # TODO: implement
            execution_count=0  # TODO: implement
        )
