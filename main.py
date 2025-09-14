#!/usr/bin/env python3
"""
VisionFlux - AI-Powered RTSP Camera Monitoring
Main application entry point
"""

import asyncio
import uvicorn
from app.config import Settings
from app.api.main import create_app
from app.services.camera_manager import CameraManager
from app.services.ai_detector import AIDetector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    settings = Settings()
    
    logger.info("🚀 Starting VisionFlux - AI-Powered Camera Monitoring")
    logger.info(f"Server will run on http://{settings.host}:{settings.port}")
    
    # Initialize services
    ai_detector = AIDetector()
    camera_manager = CameraManager(ai_detector)
    
    # Create FastAPI app
    app = create_app(camera_manager, ai_detector)
    
    # Start the server
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        reload=settings.debug
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        raise
