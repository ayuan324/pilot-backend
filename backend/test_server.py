"""
中级版本 - 包含基本AI功能的πlot Backend
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 创建FastAPI应用
app = FastAPI(
    title="πlot Backend",
    description="AI Workflow Builder Backend",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://same-ublsviolz5y-latest.netlify.app",
        "http://localhost:3000",
        "*"  # 临时允许所有来源，生产环境应该限制
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class PromptAnalysisRequest(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}

class WorkflowGenerationRequest(BaseModel):
    prompt: str
    preferences: Dict[str, Any] = {}

# 模拟数据
WORKFLOW_TEMPLATES = {
    "simple_chatbot": {
        "id": "simple_chatbot",
        "name": "Simple Chatbot",
        "description": "Basic conversational AI workflow",
        "category": "conversational",
        "difficulty": "beginner",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "User Input"}
            },
            {
                "id": "llm",
                "type": "llm", 
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "AI Processing",
                    "model": "gpt-3.5-turbo",
                    "prompt_template": "You are a helpful assistant. Respond to: {input}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 500, "y": 100},
                "config": {"name": "Response"}
            }
        ],
        "edges": [
            {"source": "start", "target": "llm"},
            {"source": "llm", "target": "output"}
        ]
    },
    "content_generator": {
        "id": "content_generator",
        "name": "Content Generator",
        "description": "Generate blog posts or articles from a topic",
        "category": "content",
        "difficulty": "intermediate",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "Topic Input"}
            },
            {
                "id": "outline",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "Generate Outline",
                    "model": "gpt-3.5-turbo",
                    "prompt_template": "Create a detailed outline for: {input}"
                }
            },
            {
                "id": "content",
                "type": "llm",
                "position": {"x": 500, "y": 100},
                "config": {
                    "name": "Write Content",
                    "model": "gpt-4",
                    "prompt_template": "Write content based on: {outline}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 700, "y": 100},
                "config": {"name": "Final Article"}
            }
        ],
        "edges": [
            {"source": "start", "target": "outline"},
            {"source": "outline", "target": "content"},
            {"source": "content", "target": "output"}
        ]
    }
}

# 基础端点
@app.get("/")
async def root():
    return {
        "message": "πlot Backend API",
        "version": "1.0.0",
        "status": "running",
        "features": ["workflow_templates", "prompt_analysis", "workflow_generation"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "mock",
        "ai_service": "mock"
    }

# 工作流模板端点
@app.get("/api/v1/workflows/templates")
async def get_templates():
    """获取工作流模板"""
    return {
        "templates": list(WORKFLOW_TEMPLATES.values()),
        "count": len(WORKFLOW_TEMPLATES)
    }

# AI服务端点
@app.post("/api/v1/ai/analyze-prompt")
async def analyze_prompt(request: PromptAnalysisRequest):
    """分析用户提示词（模拟版本）"""
    prompt = request.prompt.lower()
    
    # 简单的关键词分析
    intent = "other"
    if any(word in prompt for word in ["chatbot", "chat", "conversation", "support"]):
        intent = "chatbot"
    elif any(word in prompt for word in ["content", "blog", "article", "write", "generate"]):
        intent = "content_generation"
    elif any(word in prompt for word in ["data", "analysis", "analyze", "report"]):
        intent = "data_analysis"
    elif any(word in prompt for word in ["automation", "workflow", "process"]):
        intent = "automation"
    
    # 复杂度分析
    complexity = "simple"
    if len(prompt) > 100:
        complexity = "complex"
    elif len(prompt) > 50:
        complexity = "medium"
    
    # 提取实体（简单的词汇提取）
    entities = [word for word in prompt.split() if len(word) > 4][:5]
    
    return {
        "success": True,
        "analysis": {
            "intent": intent,
            "complexity": complexity,
            "entities": entities,
            "suggested_workflow": {
                "name": f"Custom {intent.replace('_', ' ').title()}",
                "description": f"Auto-generated workflow for: {request.prompt[:50]}...",
                "estimated_nodes": 3 if complexity == "simple" else 5,
                "node_types": ["start", "llm", "output"]
            },
            "confidence": 0.85
        }
    }

@app.post("/api/v1/ai/generate-workflow")
async def generate_workflow(request: WorkflowGenerationRequest):
    """生成工作流（模拟版本）"""
    prompt = request.prompt
    
    # 基于提示词生成工作流
    workflow_id = str(uuid.uuid4())
    
    # 根据提示词类型选择模板
    prompt_lower = prompt.lower()
    if "chatbot" in prompt_lower or "support" in prompt_lower:
        base_template = WORKFLOW_TEMPLATES["simple_chatbot"]
        workflow_name = "AI Chatbot Workflow"
    elif "content" in prompt_lower or "blog" in prompt_lower:
        base_template = WORKFLOW_TEMPLATES["content_generator"]
        workflow_name = "Content Generation Workflow"
    else:
        # 默认简单工作流
        base_template = WORKFLOW_TEMPLATES["simple_chatbot"]
        workflow_name = "Custom AI Workflow"
    
    # 自定义工作流
    workflow = {
        "id": workflow_id,
        "name": workflow_name,
        "description": f"Auto-generated workflow for: {prompt}",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "Start"}
            },
            {
                "id": "process",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "AI Processing",
                    "model": "gpt-3.5-turbo",
                    "prompt_template": f"Process this request: {prompt}\n\nUser input: {{{{input}}}}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 500, "y": 100},
                "config": {"name": "Result"}
            }
        ],
        "edges": [
            {"source": "start", "target": "process"},
            {"source": "process", "target": "output"}
        ],
        "variables": [
            {"name": "input", "type": "string", "is_input": True},
            {"name": "output", "type": "string", "is_output": True}
        ]
    }
    
    return {
        "success": True,
        "workflow": workflow,
        "generation_meta": {
            "model": "mock-generator",
            "generated_at": datetime.utcnow().isoformat(),
            "prompt_analysis": {
                "intent": "auto-detected",
                "complexity": "medium"
            }
        }
    }

@app.get("/api/v1/ai/models")
async def get_models():
    """获取可用的AI模型"""
    return {
        "success": True,
        "models": [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "cost_per_1k_tokens": 0.5,
                "recommended_for": ["chatbots", "content_generation"]
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "cost_per_1k_tokens": 30,
                "recommended_for": ["complex_analysis", "reasoning"]
            },
            {
                "id": "claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "cost_per_1k_tokens": 3,
                "recommended_for": ["writing", "analysis"]
            }
        ],
        "count": 3
    }

# 运行服务器
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)