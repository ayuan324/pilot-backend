"""
Minimal test server for Railway deployment
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="πlot Backend Test")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "πlot Backend is running on Railway!",
        "status": "success",
        "port": os.environ.get("PORT", "8000")
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "πlot-backend",
        "environment": "production"
    }

@app.get("/test")
async def test():
    return {
        "message": "API is working!",
        "endpoints": [
            "GET /",
            "GET /health", 
            "GET /test"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)