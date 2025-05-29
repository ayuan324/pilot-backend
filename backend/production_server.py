"""
Production FastAPI server for πlot
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    uvicorn.run(
        "production_server:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
