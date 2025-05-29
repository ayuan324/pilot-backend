"""
Production FastAPI server for πlot
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app
try:
    # Try importing from the main app structure
    from app.main import app
except ImportError:
    try:
        # Fallback to simple_server if main app not available
        from simple_server import create_simple_server
        app = create_simple_server()
    except ImportError:
        # Create a minimal app as last resort
        from fastapi import FastAPI
        app = FastAPI(title="πlot Backend")

        @app.get("/")
        async def root():
            return {"message": "πlot Backend is running"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Starting πlot backend on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
