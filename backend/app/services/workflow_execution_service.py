"""
Workflow execution service for running workflows
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from ..models.workflow import Workflow, Node, NodeType
from ..models.execution import WorkflowExecution, ExecutionStatus, NodeExecutionLog, NodeExecutionStatus
from ..services.litellm_service import litellm_service
from ..database.supabase_client import SupabaseClient


class WorkflowExecutionService:
    """Service for executing workflows step by step"""

    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    async def execute_workflow(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any],
        user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute a workflow and yield progress updates
        """
        # Create execution record
        execution = WorkflowExecution(
            id=f"exec_{int(time.time())}",
            workflow_id=workflow.id,
            user_id=user_id,
            input_data=input_data,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        try:
            yield {
                "type": "execution_started",
                "execution_id": execution.id,
                "workflow_name": workflow.name,
                "total_nodes": len(workflow.nodes)
            }

            # Build execution context
            context = {"variables": input_data.copy()}
            
            # Execute nodes in order
            executed_nodes = set()
            node_outputs = {}
            
            # Find start node
            start_nodes = [n for n in workflow.nodes if n.type == NodeType.START]
            if not start_nodes:
                raise Exception("No start node found in workflow")

            # Execute workflow using topological sort
            execution_order = self._get_execution_order(workflow)
            
            for i, node in enumerate(execution_order):
                if node.id in executed_nodes:
                    continue

                # Update progress
                progress = (i + 1) / len(execution_order)
                yield {
                    "type": "progress_update",
                    "progress": progress,
                    "current_node": node.data.title or node.id,
                    "node_id": node.id
                }

                # Execute node
                try:
                    node_result = await self._execute_node(node, context, node_outputs)
                    node_outputs[node.id] = node_result
                    executed_nodes.add(node.id)

                    # Add node result to context
                    context["variables"].update(node_result.get("outputs", {}))

                    yield {
                        "type": "node_completed",
                        "node_id": node.id,
                        "node_title": node.data.title or node.id,
                        "result": node_result,
                        "execution_time_ms": node_result.get("execution_time_ms", 0)
                    }

                except Exception as node_error:
                    yield {
                        "type": "node_failed",
                        "node_id": node.id,
                        "node_title": node.data.title or node.id,
                        "error": str(node_error)
                    }
                    
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = f"Node {node.id} failed: {str(node_error)}"
                    break

            # Complete execution
            if execution.status != ExecutionStatus.FAILED:
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.output_data = self._extract_final_outputs(workflow, node_outputs)

                yield {
                    "type": "execution_completed",
                    "execution_id": execution.id,
                    "output_data": execution.output_data,
                    "total_time_ms": execution.duration_ms
                }
            else:
                execution.completed_at = datetime.utcnow()
                yield {
                    "type": "execution_failed",
                    "execution_id": execution.id,
                    "error": execution.error_message,
                    "total_time_ms": execution.duration_ms
                }

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            yield {
                "type": "execution_failed",
                "execution_id": execution.id,
                "error": str(e)
            }

    def _get_execution_order(self, workflow: Workflow) -> List[Node]:
        """
        Get nodes in execution order using topological sort
        """
        # Build adjacency list
        graph = {node.id: [] for node in workflow.nodes}
        in_degree = {node.id: 0 for node in workflow.nodes}
        
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Convert node IDs back to Node objects
        node_map = {node.id: node for node in workflow.nodes}
        return [node_map[node_id] for node_id in result if node_id in node_map]

    async def _execute_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single node based on its type
        """
        start_time = time.time()
        
        try:
            if node.type == NodeType.START:
                result = await self._execute_start_node(node, context)
            elif node.type in [NodeType.LLM, NodeType.CHAT]:
                result = await self._execute_llm_node(node, context, node_outputs)
            elif node.type == NodeType.CODE:
                result = await self._execute_code_node(node, context, node_outputs)
            elif node.type == NodeType.CONDITION:
                result = await self._execute_condition_node(node, context, node_outputs)
            elif node.type == NodeType.HTTP_REQUEST:
                result = await self._execute_http_node(node, context, node_outputs)
            elif node.type == NodeType.TEMPLATE_TRANSFORM:
                result = await self._execute_template_node(node, context, node_outputs)
            elif node.type == NodeType.ANSWER:
                result = await self._execute_answer_node(node, context, node_outputs)
            else:
                result = {"outputs": {}, "logs": [f"Node type {node.type} not implemented yet"]}

            execution_time = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time
            result["status"] = "completed"
            
            return result

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return {
                "status": "failed",
                "error": str(e),
                "execution_time_ms": execution_time,
                "outputs": {},
                "logs": [f"Node execution failed: {str(e)}"]
            }

    async def _execute_start_node(self, node: Node, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute start node - pass through input variables"""
        return {
            "outputs": context["variables"],
            "logs": ["Workflow started with input variables"]
        }

    async def _execute_llm_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute LLM/Chat node"""
        if not node.data.prompt:
            raise Exception("LLM node requires a prompt")

        # Replace variables in prompt
        prompt = self._replace_variables(node.data.prompt, context["variables"], node_outputs)
        
        # Prepare messages
        messages = []
        if node.data.system_prompt:
            system_prompt = self._replace_variables(node.data.system_prompt, context["variables"], node_outputs)
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})

        # Call LLM
        response = await litellm_service.completion(
            messages=messages,
            model=node.data.model or "gpt-3.5-turbo",
            temperature=node.data.temperature or 0.7,
            max_tokens=node.data.max_tokens or 1000
        )

        return {
            "outputs": {
                "text": response["content"],
                f"{node.id}.text": response["content"]
            },
            "logs": [
                f"LLM call completed with model {response['model']}",
                f"Tokens used: {response['usage']['total_tokens']}",
                f"Cost: ${response['cost']:.6f}"
            ],
            "usage": response["usage"],
            "cost": response["cost"]
        }

    async def _execute_code_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute code node (simplified - in production, use sandboxed execution)"""
        if not node.data.code:
            raise Exception("Code node requires code")

        # Replace variables in code
        code = self._replace_variables(node.data.code, context["variables"], node_outputs)
        
        # Simple execution (WARNING: This is not secure for production)
        # In production, use a sandboxed environment like Docker or restricted Python
        try:
            # Create a restricted globals environment
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "print": print,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "sum": sum,
                    "max": max,
                    "min": min,
                    "abs": abs,
                    "round": round
                },
                "json": json,
                "time": time
            }
            
            # Add context variables
            safe_globals.update(context["variables"])
            
            # Execute code
            local_vars = {}
            exec(code, safe_globals, local_vars)
            
            # Extract result
            result_value = local_vars.get("result", "No result variable set")
            
            return {
                "outputs": {
                    "result": result_value,
                    f"{node.id}.result": result_value
                },
                "logs": [
                    "Code executed successfully",
                    f"Result: {str(result_value)[:100]}..."
                ]
            }

        except Exception as e:
            raise Exception(f"Code execution failed: {str(e)}")

    async def _execute_condition_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute condition node"""
        # Simple condition evaluation (can be enhanced)
        conditions = node.data.conditions or []
        if not conditions:
            return {"outputs": {"result": True}, "logs": ["No conditions specified, defaulting to true"]}

        # Evaluate conditions (simplified)
        results = []
        for condition in conditions:
            # This is a simplified implementation
            # In production, use a proper expression evaluator
            result = True  # Placeholder
            results.append(result)

        # Apply logical operator
        logical_op = node.data.logical_operator or "and"
        if logical_op == "and":
            final_result = all(results)
        else:  # or
            final_result = any(results)

        return {
            "outputs": {
                "result": final_result,
                f"{node.id}.result": final_result
            },
            "logs": [f"Condition evaluated to: {final_result}"]
        }

    async def _execute_http_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute HTTP request node"""
        import aiohttp
        
        if not node.data.url:
            raise Exception("HTTP node requires a URL")

        url = self._replace_variables(node.data.url, context["variables"], node_outputs)
        method = node.data.method or "GET"
        headers = node.data.headers or {}
        params = node.data.params or {}
        body = node.data.body or {}
        timeout = node.data.timeout or 30

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body if body else None
                ) as response:
                    response_text = await response.text()
                    
                    try:
                        response_json = await response.json()
                    except:
                        response_json = None

                    return {
                        "outputs": {
                            "status_code": response.status,
                            "headers": dict(response.headers),
                            "body": response_json or response_text,
                            f"{node.id}.status_code": response.status,
                            f"{node.id}.body": response_json or response_text
                        },
                        "logs": [
                            f"HTTP {method} request to {url}",
                            f"Response status: {response.status}",
                            f"Response length: {len(response_text)} characters"
                        ]
                    }

        except Exception as e:
            raise Exception(f"HTTP request failed: {str(e)}")

    async def _execute_template_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute template transform node"""
        if not node.data.template:
            raise Exception("Template node requires a template")

        # Replace variables in template
        output = self._replace_variables(node.data.template, context["variables"], node_outputs)

        return {
            "outputs": {
                "output": output,
                f"{node.id}.output": output
            },
            "logs": [f"Template processed, output length: {len(output)} characters"]
        }

    async def _execute_answer_node(
        self,
        node: Node,
        context: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute answer node - collect final output"""
        # Find the input for this node (from previous nodes)
        final_output = ""
        
        # Look for the most recent text output
        for node_id, output in reversed(list(node_outputs.items())):
            if "text" in output.get("outputs", {}):
                final_output = output["outputs"]["text"]
                break
            elif "output" in output.get("outputs", {}):
                final_output = output["outputs"]["output"]
                break
            elif "result" in output.get("outputs", {}):
                final_output = str(output["outputs"]["result"])
                break

        return {
            "outputs": {
                "answer": final_output,
                "final_output": final_output
            },
            "logs": ["Final answer prepared"]
        }

    def _replace_variables(
        self,
        text: str,
        variables: Dict[str, Any],
        node_outputs: Dict[str, Any]
    ) -> str:
        """
        Replace variables in text with actual values
        Supports formats: {{variable_name}} and {{node_id.output_name}}
        """
        import re
        
        # Find all variable references
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, text)
        
        result = text
        for match in matches:
            variable_name = match.strip()
            value = None
            
            # Check if it's a node output reference (node_id.output_name)
            if '.' in variable_name:
                node_id, output_name = variable_name.split('.', 1)
                if node_id in node_outputs and "outputs" in node_outputs[node_id]:
                    value = node_outputs[node_id]["outputs"].get(output_name)
            
            # Check regular variables
            if value is None:
                value = variables.get(variable_name)
            
            # Replace with value or keep original if not found
            if value is not None:
                result = result.replace(f"{{{{{variable_name}}}}}", str(value))
        
        return result

    def _extract_final_outputs(
        self,
        workflow: Workflow,
        node_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract final outputs from workflow execution"""
        final_outputs = {}
        
        # Find answer/end nodes
        answer_nodes = [n for n in workflow.nodes if n.type in [NodeType.ANSWER, NodeType.END]]
        
        if answer_nodes:
            for node in answer_nodes:
                if node.id in node_outputs:
                    final_outputs.update(node_outputs[node.id].get("outputs", {}))
        else:
            # If no answer nodes, use outputs from the last executed node
            if node_outputs:
                last_output = list(node_outputs.values())[-1]
                final_outputs.update(last_output.get("outputs", {}))
        
        return final_outputs 