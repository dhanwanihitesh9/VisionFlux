"""
Main FastAPI application
"""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import cameras, alerts, prompts, dashboard
from app.services.camera_manager import CameraManager
from app.services.ai_detector import AIDetector

logger = logging.getLogger(__name__)


def create_app(camera_manager: CameraManager, ai_detector: AIDetector) -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="VisionFlux",
        description="AI-Powered RTSP Camera Monitoring System",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store services in app state
    app.state.camera_manager = camera_manager
    app.state.ai_detector = ai_detector
    
    # Include API routes
    app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
    app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
    app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
    
    # Mount static files (make path configurable)
    import os
    static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Templates
    templates_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
    templates = Jinja2Templates(directory=templates_path)
    
    @app.get("/")
    async def root():
        """Root endpoint - serve the dashboard"""
        from fastapi.responses import FileResponse
        template_path = os.path.join(templates_path, "index.html")
        return FileResponse(template_path)
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup"""
        logger.info("🚀 VisionFlux starting up...")
        
        # Initialize AI detector
        await ai_detector.initialize()
        
        # Start cameras
        await camera_manager.start_all_cameras()
        
        logger.info("✅ VisionFlux startup complete")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown"""
        logger.info("🛑 VisionFlux shutting down...")
        
        # Stop all cameras
        camera_manager.stop_all_cameras()
        
        logger.info("✅ VisionFlux shutdown complete")
    
    # WebSocket for real-time updates
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        
        def alert_callback(alert):
            """Send alert via WebSocket"""
            try:
                asyncio.create_task(
                    websocket.send_json({
                        "type": "alert",
                        "data": alert.to_dict()
                    })
                )
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
        
        # Register alert callback
        camera_manager.add_alert_callback(alert_callback)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
    
    return app
