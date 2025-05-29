"""
Execution service for workflow execution management
"""
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import asyncio
from ..models.execution import (
    WorkflowExecution, WorkflowExecutionCreate, ExecutionRequest,
    ExecutionEvent, ExecutionEventType, ExecutionStatus,
    NodeExecutionLog, NodeExecutionStatus
)
from ..models.workflow import Workflow, NodeType
from ..database.supabase_client import SupabaseClient
from .litellm_service import litellm_service


class ExecutionService:
    """Service for workflow execution management"""

    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.active_executions: Dict[str, WorkflowExecution] = {}

    async def create_execution(
        self,
        workflow: Workflow,
        request: ExecutionRequest,
        user_id: str
    ) -> WorkflowExecution:
        """Create a new workflow execution"""
        execution_id = str(uuid.uuid4())

        # Create execution record
        execution_data = {
            "id": execution_id,
            "workflow_id": workflow.id,
            "user_id": user_id,
            "input_data": request.input_data,
            "status": ExecutionStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Insert into database
        result = self.supabase.client.table("workflow_executions").insert(execution_data).execute()

        if not result.data:
            raise Exception(f"Failed to create execution: {result}")

        # Create execution object
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow.id,
            user_id=user_id,
            input_data=request.input_data,
            status=ExecutionStatus.PENDING
        )

        # Store in active executions
        self.active_executions[execution_id] = execution

        return execution

    async def get_execution(self, execution_id: str, user_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        # Check active executions first
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            if execution.user_id == user_id:
                return execution

        # Query database
        result = self.supabase.client.table("workflow_executions").select("*").eq("id", execution_id).eq("user_id", user_id).execute()

        if result.data:
            return self._db_to_execution(result.data[0])
        return None

    async def list_executions(
        self,
        user_id: str,
        workflow_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List executions for a user"""
        query = self.supabase.client.table("workflow_executions").select("*").eq("user_id", user_id)

        if workflow_id:
            query = query.eq("workflow_id", workflow_id)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return [self._db_to_execution(row) for row in result.data or []]

    async def execute_workflow(
        self,
        workflow: Workflow,
        execution: WorkflowExecution
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute a workflow and yield real-time events"""
        try:
            # Update execution status
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            await self._update_execution_status(execution)

            # Start execution event
            yield execution.add_event(
                ExecutionEventType.WORKFLOW_STARTED,
                message=f"Started executing workflow: {workflow.name}"
            )

            # Find start nodes
            start_nodes = [node for node in workflow.nodes if node.type == NodeType.START]
            if not start_nodes:
                raise Exception("No start node found in workflow")

            # Initialize execution context
            context = ExecutionContext(execution.input_data.copy())

            # Execute workflow
            completed_nodes = set()
            total_nodes = len(workflow.nodes)

            for i, node in enumerate(workflow.nodes):
                # Update progress
                progress = i / total_nodes
                execution.update_progress(progress)
                yield execution.events[-1]  # Progress event

                # Execute node
                yield execution.add_event(
                    ExecutionEventType.NODE_STARTED,
                    node_id=node.id,
                    message=f"Executing node: {node.config.name or node.type}"
                )

                try:
                    # Create node log
                    node_log = NodeExecutionLog(
                        execution_id=execution.id,
                        node_id=node.id,
                        node_type=node.type.value,
                        node_name=node.config.name or node.type.value,
                        status=NodeExecutionStatus.RUNNING,
                        input_data=context.get_node_input(node.id),
                        started_at=datetime.utcnow()
                    )
                    execution.add_node_log(node_log)

                    # Execute the node
                    result = await self._execute_node(node, context)

                    # Update node log
                    node_log.status = NodeExecutionStatus.COMPLETED
                    node_log.completed_at = datetime.utcnow()
                    node_log.output_data = result
                    node_log.execution_time_ms = node_log.duration_ms

                    # Update context
                    context.set_node_output(node.id, result)
                    completed_nodes.add(node.id)

                    yield execution.add_event(
                        ExecutionEventType.NODE_COMPLETED,
                        node_id=node.id,
                        data=result,
                        message=f"Completed node: {node.config.name or node.type}"
                    )

                except Exception as e:
                    # Node execution failed
                    node_log.status = NodeExecutionStatus.FAILED
                    node_log.completed_at = datetime.utcnow()
                    node_log.error_message = str(e)

                    yield execution.add_event(
                        ExecutionEventType.NODE_FAILED,
                        node_id=node.id,
                        error=str(e),
                        message=f"Failed to execute node: {node.config.name or node.type}"
                    )

                    # Stop execution on node failure
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = f"Node {node.id} failed: {str(e)}"
                    break

            # Complete execution
            if execution.status != ExecutionStatus.FAILED:
                execution.status = ExecutionStatus.COMPLETED
                execution.output_data = context.get_final_output()
                execution.update_progress(1.0)

            execution.completed_at = datetime.utcnow()
            await self._update_execution_status(execution)

            # Final event
            if execution.status == ExecutionStatus.COMPLETED:
                yield execution.add_event(
                    ExecutionEventType.WORKFLOW_COMPLETED,
                    data=execution.output_data,
                    message="Workflow execution completed successfully"
                )
            else:
                yield execution.add_event(
                    ExecutionEventType.WORKFLOW_FAILED,
                    error=execution.error_message,
                    message="Workflow execution failed"
                )

        except Exception as e:
            # Workflow execution failed
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await self._update_execution_status(execution)

            yield execution.add_event(
                ExecutionEventType.WORKFLOW_FAILED,
                error=str(e),
                message=f"Workflow execution failed: {str(e)}"
            )

        finally:
            # Remove from active executions
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]

    async def _execute_node(self, node, context: 'ExecutionContext') -> Dict[str, Any]:
        """Execute a single node"""
        try:
            if node.type == NodeType.START:
                return {"output": context.get_input_data()}

            elif node.type == NodeType.LLM:
                # Real LLM execution using LiteLLM
                prompt_template = node.config.prompt_template or "Process this input: {input}"
                model = node.config.model or "openai/gpt-3.5-turbo"
                temperature = node.config.temperature or 0.7
                max_tokens = node.config.max_tokens or 1000
                system_message = node.config.system_message

                # Get node input variables
                input_variables = context.get_node_input(node.id)

                # Execute LLM
                response = await litellm_service.process_prompt_template(
                    template=prompt_template,
                    variables=input_variables,
                    model=model,
                    system_message=system_message,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                return {
                    "output": response["content"],
                    "tokens_used": response["usage"]["total_tokens"],
                    "cost": response["cost"],
                    "model": response["model"],
                    "response_time_ms": response["response_time_ms"]
                }

            elif node.type == NodeType.CONDITION:
                # Simple condition evaluation
                condition_logic = node.config.condition_logic or "true"
                input_value = context.get_variable("input", "")

                # Simple evaluation (in production, use safer evaluation)
                try:
                    # Replace common variables
                    condition = condition_logic.replace("{input}", f'"{input_value}"')
                    condition = condition.replace("{input_length}", str(len(str(input_value))))

                    # Basic safety check
                    if any(dangerous in condition.lower() for dangerous in ['import', 'exec', 'eval', '__']):
                        result = False
                    else:
                        result = eval(condition)

                    return {
                        "output": input_value,
                        "condition_result": bool(result),
                        "condition_logic": condition_logic
                    }
                except:
                    return {
                        "output": input_value,
                        "condition_result": False,
                        "error": "Invalid condition logic"
                    }

            elif node.type == NodeType.HTTP_REQUEST:
                # HTTP request execution
                import httpx

                method = node.config.method or "GET"
                url = node.config.url
                headers = node.config.headers or {}
                body = node.config.body or {}

                if not url:
                    raise Exception("HTTP node requires URL")

                # Replace variables in URL and body
                url = context.replace_variables(url)
                if isinstance(body, str):
                    body = context.replace_variables(body)

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=body if method in ["POST", "PUT", "PATCH"] else None
                    )

                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text

                    return {
                        "output": response_data,
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "url": str(response.url)
                    }

            elif node.type == NodeType.CODE:
                # Code execution (simplified - in production, use sandboxed execution)
                code = node.config.code or ""
                language = node.config.language or "python"

                if language == "python":
                    # Very basic Python execution (DANGEROUS - use sandbox in production)
                    local_vars = {
                        "input_data": context.get_input_data(),
                        "variables": context.variables.copy()
                    }

                    try:
                        exec(code, {"__builtins__": {}}, local_vars)
                        return {
                            "output": local_vars.get("result", "Code executed"),
                            "variables": local_vars.get("variables", {})
                        }
                    except Exception as e:
                        return {
                            "output": f"Code execution error: {str(e)}",
                            "error": str(e)
                        }
                else:
                    return {
                        "output": f"Language {language} not supported",
                        "error": f"Unsupported language: {language}"
                    }

            elif node.type == NodeType.VARIABLE:
                # Variable manipulation
                var_name = node.config.variable_name
                var_value = node.config.variable_value

                if var_name:
                    context.set_variable(var_name, var_value)

                return {
                    "output": var_value,
                    "variable_name": var_name,
                    "variable_value": var_value
                }

            elif node.type == NodeType.OUTPUT:
                # Output node
                output_template = node.config.output_template
                if output_template:
                    output = context.replace_variables(output_template)
                else:
                    output = context.get_variable("input", "")

                return {"output": output}

            else:
                # Default fallback
                return {
                    "output": context.get_variable("input", ""),
                    "message": f"Node type {node.type} executed with default handler"
                }

        except Exception as e:
            raise Exception(f"Node execution failed: {str(e)}")

    async def _update_execution_status(self, execution: WorkflowExecution):
        """Update execution status in database"""
        update_data = {
            "status": execution.status.value,
            "updated_at": datetime.utcnow().isoformat()
        }

        if execution.started_at:
            update_data["started_at"] = execution.started_at.isoformat()
        if execution.completed_at:
            update_data["completed_at"] = execution.completed_at.isoformat()
        if execution.output_data:
            update_data["output_data"] = execution.output_data
        if execution.error_message:
            update_data["error_message"] = execution.error_message

        self.supabase.client.table("workflow_executions").update(update_data).eq("id", execution.id).execute()

    def _db_to_execution(self, db_row: Dict[str, Any]) -> WorkflowExecution:
        """Convert database row to WorkflowExecution model"""
        return WorkflowExecution(
            id=db_row["id"],
            workflow_id=db_row["workflow_id"],
            user_id=db_row["user_id"],
            input_data=db_row.get("input_data", {}),
            output_data=db_row.get("output_data"),
            status=ExecutionStatus(db_row["status"]),
            started_at=datetime.fromisoformat(db_row["started_at"].replace("Z", "+00:00")) if db_row.get("started_at") else None,
            completed_at=datetime.fromisoformat(db_row["completed_at"].replace("Z", "+00:00")) if db_row.get("completed_at") else None,
            error_message=db_row.get("error_message")
        )


class ExecutionContext:
    """Execution context for workflow runs"""

    def __init__(self, input_data: Dict[str, Any]):
        self.variables = input_data.copy()
        self.node_outputs: Dict[str, Any] = {}

    def get_input_data(self) -> Dict[str, Any]:
        """Get original input data"""
        return self.variables

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value"""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any):
        """Set a variable value"""
        self.variables[name] = value

    def get_node_input(self, node_id: str) -> Dict[str, Any]:
        """Get input data for a specific node"""
        return self.variables

    def set_node_output(self, node_id: str, output: Dict[str, Any]):
        """Set output data for a specific node"""
        self.node_outputs[node_id] = output

        # Update variables with node output
        if "output" in output:
            self.variables["input"] = output["output"]

    def get_final_output(self) -> Dict[str, Any]:
        """Get final workflow output"""
        return {
            "result": self.variables.get("input", ""),
            "variables": self.variables,
            "node_outputs": self.node_outputs
        }

    def replace_variables(self, template: str) -> str:
        """Replace variables in a template string"""
        result = template
        for key, value in self.variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                str_value = str(value) if not isinstance(value, str) else value
                result = result.replace(placeholder, str_value)
        return result
