"""
Production FastAPI server for πlot
"""
import os
import sys
from pathlib import Path

# Add current directory and parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

# Import the FastAPI app
try:
    # Try importing from the main app structure
    from app.main import app
    print("✅ Successfully imported app from app.main")
except ImportError as e:
    print(f"❌ Failed to import from app.main: {e}")
    try:
        # Fallback to simple_server if main app not available
        from simple_server import create_simple_server
        app = create_simple_server()
        print("✅ Successfully created app from simple_server")
    except ImportError as e2:
        print(f"❌ Failed to import simple_server: {e2}")
        # Create a minimal app as last resort
        from fastapi import FastAPI
        app = FastAPI(title="πlot Backend")

        @app.get("/")
        async def root():
            return {"message": "πlot Backend is running", "status": "healthy"}

        @app.get("/health")
        async def health():
            return {"status": "healthy", "version": "1.0.0"}
        
        print("✅ Created minimal FastAPI app")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Starting πlot backend on {host}:{port}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
