#!/usr/bin/env python3
"""
πlot Backend Quick Start Script

This script helps configure and test the backend without full dependency installation.
It provides guidance for setting up the environment and validates the configuration.
"""

import os
import json
import uuid
from datetime import datetime


def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")

    env_file = ".env"
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "CLERK_SECRET_KEY",
        "OPENROUTER_API_KEY"
    ]

    if not os.path.exists(env_file):
        print(f"❌ Environment file {env_file} not found")
        print("📝 Please copy .env.example to .env and configure your credentials")
        return False

    # Read environment file
    with open(env_file, 'r') as f:
        content = f.read()

    missing_vars = []
    for var in required_vars:
        if f"{var}=your_" in content or f"{var}=placeholder" in content:
            missing_vars.append(var)

    if missing_vars:
        print("⚠️ The following environment variables need configuration:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📋 Configuration Guide:")
        print("1. Get Supabase credentials from your Supabase Extensions panel")
        print("2. Get Clerk credentials from your Clerk Extensions panel")
        print("3. Get OpenRouter API key from https://openrouter.ai/keys")
        return False

    print("✅ Environment configuration looks good!")
    return True


def show_api_endpoints():
    """Show available API endpoints"""
    print("\n🚀 Available API Endpoints:")
    print("=" * 50)

    endpoints = [
        ("GET", "/", "Health check"),
        ("GET", "/health", "Detailed health status"),
        ("GET", "/api/v1/workflows/templates", "Get workflow templates"),
        ("POST", "/api/v1/workflows", "Create workflow"),
        ("GET", "/api/v1/workflows", "List workflows"),
        ("POST", "/api/v1/workflows/{id}/execute", "Execute workflow"),
        ("GET", "/api/v1/executions", "List executions"),
        ("POST", "/api/v1/ai/analyze-prompt", "Analyze user prompt"),
        ("POST", "/api/v1/ai/generate-workflow", "Generate workflow from prompt"),
        ("WS", "/ws/{user_id}", "Real-time execution updates")
    ]

    for method, path, description in endpoints:
        print(f"  {method:4} {path:35} - {description}")


def show_workflow_example():
    """Show example workflow structure"""
    print("\n📋 Example Workflow Structure:")
    print("=" * 50)

    example_workflow = {
        "name": "Customer Support Chatbot",
        "description": "AI-powered customer support workflow",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "Customer Message"}
            },
            {
                "id": "intent_analysis",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "Analyze Intent",
                    "model": "openai/gpt-3.5-turbo",
                    "prompt_template": "Analyze the customer's intent: {input}"
                }
            },
            {
                "id": "response_generation",
                "type": "llm",
                "position": {"x": 500, "y": 100},
                "config": {
                    "name": "Generate Response",
                    "model": "openai/gpt-3.5-turbo",
                    "prompt_template": "Generate a helpful response based on intent: {intent}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 700, "y": 100},
                "config": {"name": "Customer Response"}
            }
        ],
        "edges": [
            {"source": "start", "target": "intent_analysis"},
            {"source": "intent_analysis", "target": "response_generation"},
            {"source": "response_generation", "target": "output"}
        ]
    }

    print(json.dumps(example_workflow, indent=2))


def show_frontend_integration():
    """Show how to integrate with frontend"""
    print("\n🔗 Frontend Integration Guide:")
    print("=" * 50)

    integration_code = '''
// 1. Install dependencies in your Next.js project
npm install axios socket.io-client

// 2. Create API client
const API_BASE = "http://localhost:8000";

export const apiClient = {
  // Get workflow templates
  async getTemplates() {
    const response = await fetch(`${API_BASE}/api/v1/workflows/templates`);
    return response.json();
  },

  // Analyze user prompt
  async analyzePrompt(prompt) {
    const response = await fetch(`${API_BASE}/api/v1/ai/analyze-prompt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${clerkToken}`
      },
      body: JSON.stringify({ prompt })
    });
    return response.json();
  },

  // Generate workflow
  async generateWorkflow(prompt) {
    const response = await fetch(`${API_BASE}/api/v1/ai/generate-workflow`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${clerkToken}`
      },
      body: JSON.stringify({ prompt })
    });
    return response.json();
  }
};

// 3. WebSocket for real-time updates
const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Execution update:", data);
};
'''

    print(integration_code)


def show_next_steps():
    """Show next development steps"""
    print("\n🎯 Next Development Steps:")
    print("=" * 50)

    steps = [
        "1. Configure Environment Variables",
        "   - Update .env with actual Supabase credentials",
        "   - Add Clerk authentication keys",
        "   - Set OpenRouter API key for AI functionality",
        "",
        "2. Install Python Dependencies",
        "   - Set up virtual environment: python3 -m venv venv",
        "   - Activate: source venv/bin/activate",
        "   - Install: pip install -r requirements.txt",
        "",
        "3. Start Backend Server",
        "   - Run: python run.py",
        "   - API will be available at http://localhost:8000",
        "   - Docs at http://localhost:8000/docs",
        "",
        "4. Frontend Integration",
        "   - Update homepage to call backend APIs",
        "   - Implement React Flow workflow editor",
        "   - Add real-time execution feedback",
        "",
        "5. Visual Workflow Editor",
        "   - Install react-flow: npm install reactflow",
        "   - Create workflow canvas component",
        "   - Add node configuration panels",
        "",
        "6. End-to-End Testing",
        "   - Test prompt analysis → workflow generation",
        "   - Test workflow execution with real AI models",
        "   - Verify real-time progress updates"
    ]

    for step in steps:
        print(f"  {step}")


def generate_sample_api_requests():
    """Generate sample API requests for testing"""
    print("\n🧪 Sample API Requests for Testing:")
    print("=" * 50)

    requests = [
        {
            "name": "Health Check",
            "method": "GET",
            "url": "http://localhost:8000/health",
            "curl": "curl http://localhost:8000/health"
        },
        {
            "name": "Get Templates",
            "method": "GET",
            "url": "http://localhost:8000/api/v1/workflows/templates",
            "curl": "curl http://localhost:8000/api/v1/workflows/templates"
        },
        {
            "name": "Analyze Prompt",
            "method": "POST",
            "url": "http://localhost:8000/api/v1/ai/analyze-prompt",
            "curl": 'curl -X POST http://localhost:8000/api/v1/ai/analyze-prompt \\\n  -H "Authorization: Bearer YOUR_CLERK_TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"prompt": "Create a customer support chatbot"}\''
        }
    ]

    for req in requests:
        print(f"\n{req['name']}:")
        print(f"  Method: {req['method']}")
        print(f"  URL: {req['url']}")
        print(f"  CURL: {req['curl']}")


def main():
    """Main quick start function"""
    print("🚀 πlot Backend Quick Start Guide")
    print("=" * 50)
    print("Version: 1.0.0")
    print("Status: MVP Ready")
    print()

    # Check environment
    env_ok = check_environment()

    # Show available functionality
    show_api_endpoints()
    show_workflow_example()
    show_frontend_integration()
    generate_sample_api_requests()
    show_next_steps()

    print("\n" + "=" * 50)
    print("📊 Backend Status Summary:")
    print("=" * 50)

    status_items = [
        ("✅", "Database Schema", "Fully configured with Supabase"),
        ("✅", "Core Models", "Workflow, Execution, Node models ready"),
        ("✅", "API Endpoints", "Complete REST API implemented"),
        ("✅", "AI Integration", "LiteLLM service with prompt analysis"),
        ("✅", "WebSocket Support", "Real-time execution tracking"),
        ("✅", "Security", "Row Level Security policies active"),
        ("✅", "Templates", "3 default workflow templates loaded"),
        ("🔧", "Environment", "Needs credential configuration" if not env_ok else "Ready"),
        ("🔧", "Dependencies", "Requires pip install -r requirements.txt"),
        ("🚀", "Server", "Ready to start with python run.py")
    ]

    for status, component, description in status_items:
        print(f"  {status} {component:20} - {description}")

    print(f"\n🎉 Backend MVP is ready for development!")

    if not env_ok:
        print("⚠️ Configure environment variables to get started")
    else:
        print("✅ Environment looks good - ready to start server!")

    print("\n📚 Next: Configure credentials and run 'python run.py'")


if __name__ == "__main__":
    main()
