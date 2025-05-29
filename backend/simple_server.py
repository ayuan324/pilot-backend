#!/usr/bin/env python3
"""
Simplified πlot Backend Server

A minimal FastAPI server that can run with basic Python installation.
This allows testing core functionality without full dependency setup.
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Try to import required packages, fall back to simple alternatives
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️ FastAPI not available - install with: pip install fastapi uvicorn")
    FASTAPI_AVAILABLE = False

# Basic data structures (simplified versions of our models)
workflows_db = {}
executions_db = {}
templates_db = {
    "simple_chatbot": {
        "id": "simple_chatbot",
        "name": "Simple Chatbot",
        "description": "Basic conversational AI workflow",
        "category": "conversational",
        "difficulty": "beginner",
        "nodes": [
            {"id": "start", "type": "start", "config": {"name": "User Input"}},
            {"id": "llm", "type": "llm", "config": {"model": "gpt-3.5-turbo"}},
            {"id": "output", "type": "output", "config": {"name": "Response"}}
        ],
        "edges": [
            {"source": "start", "target": "llm"},
            {"source": "llm", "target": "output"}
        ]
    }
}

def create_simple_server():
    """Create a simple FastAPI server"""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available. Please install dependencies first.")
        return None

    app = FastAPI(
        title="πlot Backend (Simplified)",
        description="Simplified backend for testing core functionality",
        version="1.0.0-simple"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development only
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {
            "message": "πlot Backend API (Simplified)",
            "version": "1.0.0-simple",
            "status": "running",
            "endpoints": [
                "GET /health",
                "GET /api/v1/workflows/templates",
                "POST /api/v1/ai/analyze-prompt",
                "POST /api/v1/ai/generate-workflow"
            ]
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "version": "1.0.0-simple",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "in-memory (simplified)",
            "ai_service": "mock (simplified)"
        }

    @app.get("/api/v1/workflows/templates")
    async def get_templates():
        """Get workflow templates"""
        return {
            "templates": list(templates_db.values()),
            "count": len(templates_db)
        }

    @app.post("/api/v1/ai/analyze-prompt")
    async def analyze_prompt(request: Dict[str, Any]):
        """Analyze user prompt (simplified mock)"""
        prompt = request.get("prompt", "")

        # Simple keyword-based analysis
        intent = "other"
        if any(word in prompt.lower() for word in ["chatbot", "chat", "conversation"]):
            intent = "chatbot"
        elif any(word in prompt.lower() for word in ["content", "blog", "article", "write"]):
            intent = "content_generation"
        elif any(word in prompt.lower() for word in ["data", "analysis", "analyze"]):
            intent = "data_analysis"

        complexity = "simple" if len(prompt) < 50 else "medium" if len(prompt) < 100 else "complex"

        return {
            "success": True,
            "analysis": {
                "intent": intent,
                "complexity": complexity,
                "entities": prompt.split()[:5],  # First 5 words as entities
                "suggested_workflow": {
                    "name": f"Custom {intent.replace('_', ' ').title()}",
                    "description": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "estimated_nodes": 3 if complexity == "simple" else 5,
                    "node_types": ["start", "llm", "output"]
                },
                "confidence": 0.8
            }
        }

    @app.post("/api/v1/ai/generate-workflow")
    async def generate_workflow(request: Dict[str, Any]):
        """Generate workflow from prompt (simplified)"""
        prompt = request.get("prompt", "")

        # Generate a simple workflow structure
        workflow_id = str(uuid.uuid4())

        workflow = {
            "id": workflow_id,
            "name": f"Generated Workflow",
            "description": f"Auto-generated workflow for: {prompt[:50]}...",
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
                        "prompt_template": f"Process this request: {prompt}"
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
                "model": "simplified-generator",
                "generated_at": datetime.utcnow().isoformat()
            }
        }

    @app.get("/api/v1/ai/models")
    async def get_models():
        """Get available AI models"""
        return {
            "success": True,
            "models": [
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "OpenAI",
                    "cost_per_1k_tokens": 0.5
                },
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "provider": "OpenAI",
                    "cost_per_1k_tokens": 30
                }
            ]
        }

    return app

def run_server():
    """Run the simplified server"""
    if not FASTAPI_AVAILABLE:
        print("❌ Cannot run server - FastAPI not available")
        print("Install with: pip install fastapi uvicorn")
        return

    app = create_simple_server()

    try:
        import uvicorn
        print("🚀 Starting simplified πlot backend server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📖 API docs at: http://localhost:8000/docs")
        print("💡 This is a simplified version for testing")

        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except ImportError:
        print("❌ uvicorn not available - install with: pip install uvicorn")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")

def check_dependencies():
    """Check what dependencies are available"""
    print("🔍 Checking available dependencies...")

    deps = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("supabase", "Supabase client"),
        ("litellm", "LLM integration"),
        ("websockets", "WebSocket support")
    ]

    available = []
    missing = []

    for dep, description in deps:
        try:
            __import__(dep)
            available.append((dep, description))
            print(f"✅ {dep:12} - {description}")
        except ImportError:
            missing.append((dep, description))
            print(f"❌ {dep:12} - {description}")

    print(f"\n📊 Dependencies: {len(available)} available, {len(missing)} missing")

    if missing:
        print("\n📦 Install missing dependencies with:")
        print("pip install " + " ".join([dep for dep, _ in missing]))

    return len(missing) == 0

def show_openrouter_setup():
    """Show how to set up OpenRouter API key"""
    print("\n🔑 OpenRouter API Setup Guide:")
    print("=" * 50)
    print("1. Go to https://openrouter.ai")
    print("2. Sign up for a free account")
    print("3. Navigate to 'Keys' section")
    print("4. Click 'Create Key'")
    print("5. Copy your API key (starts with 'sk-or-v1-')")
    print("6. Update backend/.env file:")
    print("   OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here")
    print("\n💰 Pricing: Pay-per-use, starts from $0.001 per request")
    print("🎯 Features: Access to GPT-4, Claude, Gemini, and more")

def main():
    """Main function"""
    print("🚀 πlot Backend Setup & Test")
    print("=" * 50)

    # Check dependencies
    all_deps_available = check_dependencies()

    # Show OpenRouter setup
    show_openrouter_setup()

    print("\n🎯 Next Steps:")
    if not all_deps_available:
        print("1. Install missing dependencies")
        print("2. Configure OpenRouter API key in .env")
        print("3. Run: python3 simple_server.py")
    else:
        print("✅ All dependencies available!")
        print("1. Configure OpenRouter API key in .env")
        print("2. Ready to start server!")

        # Ask if user wants to start server
        try:
            choice = input("\n🤔 Start simplified server now? (y/n): ").lower()
            if choice in ['y', 'yes']:
                run_server()
        except KeyboardInterrupt:
            print("\n👋 Setup complete!")

if __name__ == "__main__":
    main()
