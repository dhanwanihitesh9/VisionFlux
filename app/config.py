"""
Configuration settings for VisionFlux application
"""

import os
from typing import List, Optional
try:
    from pydantic import BaseSettings, validator
except ImportError:
    # Fallback for older pydantic versions or if not installed
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def validator(field, pre=False):
        def decorator(func):
            return func
        return decorator


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # RTSP Camera settings
    default_rtsp_urls: List[str] = []
    camera_timeout: int = 30
    frame_rate: int = 30
    
    # AI Model settings
    ai_model_name: str = "openai/clip-vit-base-patch32"
    detection_confidence: float = 0.7
    yolo_model: str = "yolov8n.pt"
    
    # Alert settings
    email_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    webhook_url: Optional[str] = None
    alert_cooldown: int = 60  # seconds
    
    # Storage settings
    save_detected_frames: bool = True
    frames_directory: str = "detected_frames"
    max_stored_frames: int = 1000
    
    # Processing settings
    max_concurrent_cameras: int = 4
    frame_skip: int = 5  # Process every 5th frame for AI (reduces CPU load)
    stream_frame_rate: int = 30  # Live stream FPS (separate from AI processing)
    
    def __init__(self, **kwargs):
        # Load from environment variables
        env_vars = {
            'host': os.getenv('HOST', self.host),
            'port': int(os.getenv('PORT', str(self.port))),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'default_rtsp_urls': self._parse_rtsp_urls(os.getenv('DEFAULT_RTSP_URLS', '')),
            'camera_timeout': int(os.getenv('CAMERA_TIMEOUT', str(self.camera_timeout))),
            'frame_rate': int(os.getenv('FRAME_RATE', str(self.frame_rate))),
            'ai_model_name': os.getenv('AI_MODEL_NAME', self.ai_model_name),
            'detection_confidence': float(os.getenv('DETECTION_CONFIDENCE', str(self.detection_confidence))),
            'yolo_model': os.getenv('YOLO_MODEL', self.yolo_model),
            'email_enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', str(self.smtp_port))),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'webhook_url': os.getenv('WEBHOOK_URL'),
            'alert_cooldown': int(os.getenv('ALERT_COOLDOWN', str(self.alert_cooldown))),
            'save_detected_frames': os.getenv('SAVE_DETECTED_FRAMES', 'true').lower() == 'true',
            'frames_directory': os.getenv('FRAMES_DIRECTORY', self.frames_directory),
            'max_stored_frames': int(os.getenv('MAX_STORED_FRAMES', str(self.max_stored_frames))),
            'max_concurrent_cameras': int(os.getenv('MAX_CONCURRENT_CAMERAS', str(self.max_concurrent_cameras))),
            'frame_skip': int(os.getenv('FRAME_SKIP', str(self.frame_skip))),
            'stream_frame_rate': int(os.getenv('STREAM_FRAME_RATE', str(self.stream_frame_rate))),
        }
        
        # Update with provided kwargs
        env_vars.update(kwargs)
        
        # Set attributes
        for key, value in env_vars.items():
            setattr(self, key, value)
    
    def _parse_rtsp_urls(self, urls_str: str) -> List[str]:
        """Parse comma-separated RTSP URLs"""
        if not urls_str:
            return []
        return [url.strip() for url in urls_str.split(',') if url.strip()]


# Global settings instance
settings = Settings()
