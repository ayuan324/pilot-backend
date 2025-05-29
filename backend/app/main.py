"""
πlot Backend - FastAPI Application
"""
import sentry_sdk
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
from typing import Dict

from .core.config import settings
from .api.v1.api import api_router


# Initialize Sentry if DSN provided
if settings.SENTRY_DSN and settings.SENTRY_DSN.startswith("https://"):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0 if settings.DEBUG else 0.1,
        environment="development" if settings.DEBUG else "production"
    )

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="πlot - AI Workflow Builder Backend",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except:
                # Connection might be closed, remove it
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        for user_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Connection might be closed, remove it
                self.disconnect(user_id)


manager = ConnectionManager()


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "πlot Backend API",
        "version": settings.VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back for testing
            await manager.send_personal_message(
                {"type": "echo", "message": f"Received: {data}"},
                user_id
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if settings.DEBUG:
        import traceback
        traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    print(f"🚀 πlot Backend starting up...")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print(f"🌐 CORS origins: {settings.get_cors_origins()}")
    print(f"📊 Sentry enabled: {bool(settings.SENTRY_DSN)}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 πlot Backend shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
