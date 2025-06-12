"""
LiteLLM service for AI model integration with OpenRouter
"""
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
import litellm
from litellm import acompletion
import json
import time

from ..core.config import settings


class LiteLLMService:
    """Service for interacting with various LLM providers through LiteLLM"""

    def __init__(self):
        # Configure LiteLLM
        litellm.api_key = settings.OPENROUTER_API_KEY
        litellm.api_base = "https://openrouter.ai/api/v1"

        # Set default models for different providers
        self.default_models = {
            "openrouter": "openai/gpt-3.5-turbo",
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229",
            "google": "gemini-pro"
        }

        # Model pricing (tokens per dollar) - approximate
        self.model_pricing = {
            "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "openai/gpt-4": {"input": 30, "output": 60},
            "openai/gpt-4-turbo": {"input": 10, "output": 30},
            "anthropic/claude-3-sonnet-20240229": {"input": 3, "output": 15},
            "anthropic/claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "google/gemini-pro": {"input": 0.5, "output": 1.5},
            "meta-llama/llama-2-70b-chat": {"input": 0.7, "output": 0.8}
        }

    async def completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using LiteLLM
        """
        try:
            # Prepare the request
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
                **kwargs
            }

            # Add OpenRouter specific headers if using OpenRouter
            if "openai/" in model or "anthropic/" in model or "google/" in model:
                request_data["extra_headers"] = {
                    "HTTP-Referer": "https://pilot-ai.com",
                    "X-Title": "πlot AI Workflow Builder"
                }

            start_time = time.time()

            if stream:
                return await self._stream_completion(request_data)
            else:
                response = await acompletion(**request_data)
                end_time = time.time()

                # Calculate cost and metrics
                usage = response.usage if hasattr(response, 'usage') and response.usage else None
                cost = self._calculate_cost(model, usage) if usage else 0.0

                return {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens if usage else 0,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                        "total_tokens": usage.total_tokens if usage else 0
                    },
                    "cost": cost,
                    "response_time_ms": int((end_time - start_time) * 1000),
                    "finish_reason": response.choices[0].finish_reason
                }

        except Exception as e:
            raise Exception(f"LLM completion failed: {str(e)}")

    async def _stream_completion(self, request_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle streaming completion
        """
        try:
            start_time = time.time()
            full_content = ""
            total_tokens = 0

            async for chunk in await acompletion(**request_data):
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_content += content
                        total_tokens += len(content.split())  # Rough token estimate

                        yield {
                            "type": "content",
                            "content": content,
                            "full_content": full_content,
                            "tokens": total_tokens
                        }

                # Check for completion
                if chunk.choices and chunk.choices[0].finish_reason:
                    end_time = time.time()
                    cost = self._calculate_cost(request_data["model"], {"total_tokens": total_tokens})

                    yield {
                        "type": "complete",
                        "content": full_content,
                        "usage": {"total_tokens": total_tokens},
                        "cost": cost,
                        "response_time_ms": int((end_time - start_time) * 1000),
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                    break

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculate the cost of the API call based on token usage
        """
        if not usage or model not in self.model_pricing:
            return 0.0

        pricing = self.model_pricing[model]
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Cost is typically per 1M tokens, so we divide by 1,000,000
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    async def process_prompt_template(
        self,
        template: str,
        variables: Dict[str, Any],
        model: str = "openai/gpt-3.5-turbo",
        system_message: Optional[str] = None,
        **llm_params
    ) -> Dict[str, Any]:
        """
        Process a prompt template with variables and generate completion
        """
        try:
            # Replace variables in template
            prompt = self._replace_template_variables(template, variables)

            # Build messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            # Generate completion
            return await self.completion(messages, model=model, **llm_params)

        except Exception as e:
            raise Exception(f"Template processing failed: {str(e)}")

    def _replace_template_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Replace template variables in the format {variable_name}
        """
        try:
            # Simple string replacement for now
            result = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    # Convert value to string if it's not already
                    str_value = str(value) if not isinstance(value, str) else value
                    result = result.replace(placeholder, str_value)

            return result

        except Exception as e:
            raise Exception(f"Template variable replacement failed: {str(e)}")

    async def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user intent for workflow generation
        """
        analysis_prompt = f"""
        Analyze the following user request and extract key information for workflow generation.

        User Request: "{user_input}"

        Please respond with a JSON object containing:
        {{
            "intent": "string - primary intent (chatbot, content_generation, data_analysis, automation, api_integration, document_processing, other)",
            "complexity": "string - simple, medium, or complex",
            "entities": ["array of key entities or topics mentioned"],
            "input_types": ["array of expected input types: text, file, url, number, etc."],
            "output_types": ["array of expected output types: text, file, data, report, etc."],
            "processing_steps": ["array of main processing steps needed"],
            "suggested_workflow": {{
                "name": "string - suggested workflow name",
                "description": "string - brief description",
                "estimated_nodes": "number - estimated number of nodes needed (3-8)",
                "node_types": ["array of suggested node types from: start, llm, chat, condition, code, http-request, knowledge-retrieval, doc-extractor, template-transform, answer"],
                "use_cases": ["array of specific use cases this workflow addresses"]
            }},
            "confidence": "number - confidence score 0.0-1.0"
        }}

        Focus on practical, actionable workflow components that can be implemented with AI models.
        """

        try:
            response = await self.completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                model="openai/gpt-4",
                temperature=0.3,
                max_tokens=800
            )

            # Try to parse JSON response
            try:
                analysis_result = json.loads(response["content"])
                analysis_result["raw_response"] = response
                return analysis_result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "intent": "other",
                    "complexity": "simple",
                    "entities": [],
                    "input_types": ["text"],
                    "output_types": ["text"],
                    "processing_steps": ["process input", "generate output"],
                    "suggested_workflow": {
                        "name": "Custom Workflow",
                        "description": user_input[:100] + "...",
                        "estimated_nodes": 3,
                        "node_types": ["start", "llm", "answer"],
                        "use_cases": ["general purpose"]
                    },
                    "confidence": 0.5,
                    "raw_response": response,
                    "parsing_error": "Failed to parse JSON response"
                }

        except Exception as e:
            raise Exception(f"Intent analysis failed: {str(e)}")

    async def generate_workflow_structure(self, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed workflow structure based on intent analysis
        """
        workflow_prompt = f"""
        Based on the following intent analysis, generate a detailed, practical workflow structure.

        Intent Analysis: {json.dumps(intent_analysis, indent=2)}

        Generate a workflow with the following JSON structure:
        {{
            "name": "string - descriptive workflow name",
            "description": "string - clear description of what this workflow does",
            "nodes": [
                {{
                    "id": "string - unique node id (use descriptive names like 'start', 'analyze_input', 'generate_response')",
                    "type": "string - node type from: start, end, llm, chat, condition, if-else, code, template-transform, variable-assigner, http-request, tool, knowledge-retrieval, doc-extractor, loop, iteration, parameter-extractor, answer",
                    "position": {{"x": number, "y": number}},
                    "data": {{
                        "title": "string - human readable node title",
                        "desc": "string - brief description of what this node does",
                        "model": "string - AI model (for LLM/chat nodes): gpt-3.5-turbo, gpt-4, claude-3-sonnet-20240229",
                        "prompt": "string - detailed prompt template with variables in {{variable}} format (for LLM/chat nodes)",
                        "temperature": number - 0.1-1.0 (for LLM nodes),
                        "max_tokens": number - 100-2000 (for LLM nodes),
                        "code": "string - Python code (for code nodes)",
                        "code_language": "python3" (for code nodes),
                        "conditions": [array of condition objects] (for condition nodes),
                        "template": "string - template with {{variables}}" (for template-transform nodes),
                        "url": "string - API endpoint" (for http-request nodes),
                        "method": "GET/POST/PUT/DELETE" (for http-request nodes),
                        "file_types": ["csv", "pdf", "txt"] (for doc-extractor nodes)
                    }}
                }}
            ],
            "edges": [
                {{
                    "id": "string - unique edge id",
                    "source": "string - source node id",
                    "target": "string - target node id",
                    "type": "default",
                    "animated": false
                }}
            ],
            "variables": [
                {{
                    "variable": "string - variable name (like 'user_input', 'topic', 'file_content')",
                    "label": "string - human readable label",
                    "type": "string - variable type: string, paragraph, number, select, file",
                    "required": boolean,
                    "description": "string - what this variable is for"
                }}
            ]
        }}

        IMPORTANT GUIDELINES:
        1. Position nodes logically: start at x:100, then increment x by 300 for each step, y:200 for main flow
        2. Use meaningful node IDs and titles that describe their function
        3. Write detailed, specific prompts that include variable references like {{user_input}} or {{topic}}
        4. For LLM nodes, include clear instructions and context in the prompt
        5. Create a logical flow that actually solves the user's problem
        6. Include proper variable definitions that match what's used in prompts
        7. Use appropriate models: gpt-3.5-turbo for simple tasks, gpt-4 for complex reasoning
        8. Make sure the workflow is practical and executable

        Create a workflow that genuinely addresses the user's intent with 3-6 well-designed nodes.
        """

        try:
            response = await self.completion(
                messages=[{"role": "user", "content": workflow_prompt}],
                model="openai/gpt-4",
                temperature=0.4,
                max_tokens=2500
            )

            # Try to parse JSON response
            try:
                workflow_structure = json.loads(response["content"])
                
                # Validate and enhance the generated workflow
                workflow_structure = self._validate_and_enhance_workflow(workflow_structure, intent_analysis)
                
                workflow_structure["generation_meta"] = {
                    "model": "openai/gpt-4",
                    "tokens_used": response["usage"]["total_tokens"],
                    "cost": response["cost"],
                    "generated_at": time.time(),
                    "intent_analysis": intent_analysis
                }
                return workflow_structure
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse generated workflow JSON: {str(e)}")

        except Exception as e:
            raise Exception(f"Workflow generation failed: {str(e)}")

    def _validate_and_enhance_workflow(self, workflow: Dict[str, Any], intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance the generated workflow structure
        """
        # Ensure required fields exist
        if "nodes" not in workflow:
            workflow["nodes"] = []
        if "edges" not in workflow:
            workflow["edges"] = []
        if "variables" not in workflow:
            workflow["variables"] = []

        # Validate nodes have required fields
        for i, node in enumerate(workflow["nodes"]):
            if "id" not in node:
                node["id"] = f"node_{i}"
            if "type" not in node:
                node["type"] = "llm"
            if "position" not in node:
                node["position"] = {"x": 100 + i * 300, "y": 200}
            if "data" not in node:
                node["data"] = {}
            
            # Ensure data has title and desc
            if "title" not in node["data"]:
                node["data"]["title"] = f"Node {i+1}"
            if "desc" not in node["data"]:
                node["data"]["desc"] = f"Processing step {i+1}"

        # Ensure we have a start node
        start_nodes = [n for n in workflow["nodes"] if n["type"] == "start"]
        if not start_nodes and workflow["nodes"]:
            workflow["nodes"][0]["type"] = "start"

        # Ensure we have an answer/end node
        answer_nodes = [n for n in workflow["nodes"] if n["type"] in ["answer", "end"]]
        if not answer_nodes and workflow["nodes"]:
            workflow["nodes"][-1]["type"] = "answer"

        # Validate edges reference existing nodes
        node_ids = {node["id"] for node in workflow["nodes"]}
        valid_edges = []
        for edge in workflow["edges"]:
            if edge.get("source") in node_ids and edge.get("target") in node_ids:
                if "id" not in edge:
                    edge["id"] = f"{edge['source']}-{edge['target']}"
                if "type" not in edge:
                    edge["type"] = "default"
                if "animated" not in edge:
                    edge["animated"] = False
                valid_edges.append(edge)
        workflow["edges"] = valid_edges

        # Add default variables if none exist
        if not workflow["variables"]:
            if intent_analysis.get("input_types"):
                for i, input_type in enumerate(intent_analysis["input_types"][:3]):
                    var_name = f"input_{i+1}" if i > 0 else "user_input"
                    workflow["variables"].append({
                        "variable": var_name,
                        "label": f"Input {i+1}" if i > 0 else "User Input",
                        "type": "paragraph" if input_type == "text" else input_type,
                        "required": True,
                        "description": f"The {input_type} input for processing"
                    })

        return workflow

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the LiteLLM connection and API key
        """
        try:
            response = await self.completion(
                messages=[{"role": "user", "content": "Hello, this is a connection test. Please respond with 'Connection successful'."}],
                model="openai/gpt-3.5-turbo",
                max_tokens=50,
                temperature=0
            )

            return {
                "status": "success",
                "message": "LiteLLM connection successful",
                "response": response["content"],
                "model_used": response["model"],
                "tokens_used": response["usage"]["total_tokens"]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"LiteLLM connection failed: {str(e)}"
            }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models through OpenRouter
        """
        return [
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "Fast and efficient for most tasks",
                "cost_per_1k_tokens": self.model_pricing.get("openai/gpt-3.5-turbo", {}).get("input", 0.5),
                "recommended_for": ["chatbots", "content_generation", "general_tasks"]
            },
            {
                "id": "openai/gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "Most capable model for complex reasoning",
                "cost_per_1k_tokens": self.model_pricing.get("openai/gpt-4", {}).get("input", 30),
                "recommended_for": ["complex_analysis", "code_generation", "research"]
            },
            {
                "id": "openai/gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "description": "Faster GPT-4 with larger context window",
                "cost_per_1k_tokens": self.model_pricing.get("openai/gpt-4-turbo", {}).get("input", 10),
                "recommended_for": ["long_documents", "complex_workflows", "analysis"]
            },
            {
                "id": "anthropic/claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "description": "Balanced performance and capability",
                "cost_per_1k_tokens": self.model_pricing.get("anthropic/claude-3-sonnet-20240229", {}).get("input", 3),
                "recommended_for": ["writing", "analysis", "conversation"]
            },
            {
                "id": "anthropic/claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "provider": "Anthropic",
                "description": "Fast and cost-effective",
                "cost_per_1k_tokens": self.model_pricing.get("anthropic/claude-3-haiku-20240307", {}).get("input", 0.25),
                "recommended_for": ["simple_tasks", "quick_responses", "high_volume"]
            },
            {
                "id": "google/gemini-pro",
                "name": "Gemini Pro",
                "provider": "Google",
                "description": "Google's advanced multimodal model",
                "cost_per_1k_tokens": self.model_pricing.get("google/gemini-pro", {}).get("input", 0.5),
                "recommended_for": ["multimodal", "reasoning", "content_creation"]
            }
        ]


# Global LiteLLM service instance
litellm_service = LiteLLMService()
