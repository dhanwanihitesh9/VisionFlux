"""
Camera Manager Service for VisionFlux
Handles RTSP camera connections and frame processing
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

from app.models.schemas import CameraInfo, CameraStatus, DetectionResult, Alert, AlertType
from app.services.ai_detector import AIDetector
from app.config import settings

logger = logging.getLogger(__name__)


class CameraStream:
    """Manages a single RTSP camera stream"""
    
    def __init__(self, camera_info: CameraInfo, ai_detector: AIDetector):
        self.camera_info = camera_info
        self.ai_detector = ai_detector
        self.cap = None
        self.is_running = False
        self.frame_count = 0
        self.last_alert_time = {}
        self.current_frame = None
        self.lock = threading.Lock()
        
    async def connect(self) -> bool:
        """Connect to the RTSP stream"""
        try:
            # Disconnect any existing connection first
            if self.cap:
                self.cap.release()
                self.cap = None
            
            self.camera_info.status = CameraStatus.CONNECTING
            logger.info(f"Connecting to camera {self.camera_info.name}: {self.camera_info.rtsp_url}")
            
            # Create capture object with optimized settings for low latency
            self.cap = cv2.VideoCapture(self.camera_info.rtsp_url)
            
            # Optimize for low latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Limit FPS
            
            # Try to force specific codec (bypass HEVC issues)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            # Reduce frame size for faster processing (optional)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Test connection with timeout
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.camera_info.status = CameraStatus.CONNECTED
                self.camera_info.last_frame_time = datetime.now()
                self.camera_info.error_message = None
                logger.info(f"✅ Camera {self.camera_info.name} connected successfully")
                return True
            else:
                raise Exception("Failed to read frame from stream")
                
        except Exception as e:
            self.camera_info.status = CameraStatus.ERROR
            self.camera_info.error_message = str(e)
            logger.error(f"❌ Failed to connect to camera {self.camera_info.name}: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    def disconnect(self):
        """Disconnect from the RTSP stream"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.camera_info.status = CameraStatus.DISCONNECTED
        logger.info(f"Camera {self.camera_info.name} disconnected")
    
    async def start_processing(self, alert_callback: Callable[[Alert], None]):
        """Start processing frames from the camera"""
        if not self.cap or self.camera_info.status != CameraStatus.CONNECTED:
            logger.error(f"Camera {self.camera_info.name} not connected")
            return
        
        self.is_running = True
        logger.info(f"Starting frame processing for camera {self.camera_info.name}")
        
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        # Optimize frame skipping for real-time performance
        ai_process_interval = max(settings.frame_skip + 1, 3)  # Process every 3rd frame minimum
        
        try:
            while self.is_running:
                # Read frame in thread to avoid blocking
                future = loop.run_in_executor(executor, self._read_frame)
                frame = await future
                
                if frame is None:
                    logger.warning(f"No frame received from camera {self.camera_info.name}")
                    await asyncio.sleep(0.1)  # Shorter sleep for responsiveness
                    continue
                
                # Update camera info with current frame (for live streaming)
                with self.lock:
                    self.current_frame = frame.copy()
                    self.camera_info.last_frame_time = datetime.now()
                
                # Process frame for AI detection only periodically to reduce delay
                if (self.ai_detector.is_initialized() and 
                    self.frame_count % ai_process_interval == 0):
                    
                    # Process AI detection asynchronously without blocking
                    asyncio.create_task(self._process_ai_detection(frame, alert_callback))
                
                self.frame_count += 1
                
                # Minimal delay for real-time performance
                await asyncio.sleep(1.0 / 30)  # Target 30 FPS for smooth streaming
                
        except Exception as e:
            logger.error(f"Error processing frames for camera {self.camera_info.name}: {e}")
            self.camera_info.status = CameraStatus.ERROR
            self.camera_info.error_message = str(e)
        finally:
            executor.shutdown(wait=False)
    
    def _read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the camera (blocking operation)"""
        try:
            if not self.cap:
                return None
            
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return frame
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error reading frame from camera {self.camera_info.name}: {e}")
            return None
    
    async def _process_ai_detection(self, frame: np.ndarray, alert_callback: Callable[[Alert], None]):
        """Process AI detection asynchronously without blocking main stream"""
        try:
            detections = await self.ai_detector.analyze_frame(frame, self.camera_info.id)
            
            # Process detections and generate alerts
            for detection in detections:
                alert = self._create_alert(detection)
                if alert and self._should_send_alert(alert):
                    alert_callback(alert)
                    
        except Exception as e:
            logger.error(f"Error in AI detection for camera {self.camera_info.name}: {e}")
    
    def _create_alert(self, detection: DetectionResult) -> Optional[Alert]:
        """Create an alert from a detection result"""
        try:
            alert_id = str(uuid.uuid4())
            alert = Alert(
                id=alert_id,
                camera_id=self.camera_info.id,
                alert_type=AlertType.CUSTOM_PROMPT if "Custom prompt" in detection.description else AlertType.OBJECT_DETECTED,
                message=detection.description,
                confidence=detection.confidence,
                timestamp=detection.timestamp,
                metadata={
                    'bbox': detection.bbox,
                    'camera_name': self.camera_info.name
                }
            )
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def _should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent based on cooldown"""
        alert_key = f"{alert.alert_type}_{alert.message}"
        current_time = datetime.now()
        
        if alert_key in self.last_alert_time:
            time_diff = (current_time - self.last_alert_time[alert_key]).total_seconds()
            if time_diff < settings.alert_cooldown:
                return False
        
        self.last_alert_time[alert_key] = current_time
        return True
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame (thread-safe)"""
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None


class CameraManager:
    """Manages multiple camera streams"""
    
    def __init__(self, ai_detector: AIDetector):
        self.ai_detector = ai_detector
        self.cameras: Dict[str, CameraStream] = {}
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
    def add_camera(self, name: str, rtsp_url: str) -> str:
        """Add a new camera"""
        camera_id = str(uuid.uuid4())
        camera_info = CameraInfo(
            id=camera_id,
            name=name,
            rtsp_url=rtsp_url
        )
        
        camera_stream = CameraStream(camera_info, self.ai_detector)
        self.cameras[camera_id] = camera_stream
        
        logger.info(f"Added camera: {name} (ID: {camera_id})")
        return camera_id
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera"""
        if camera_id not in self.cameras:
            return False
        
        # Stop processing
        self.stop_camera(camera_id)
        
        # Remove camera
        camera = self.cameras[camera_id]
        camera.disconnect()
        del self.cameras[camera_id]
        
        logger.info(f"Removed camera: {camera.camera_info.name}")
        return True
    
    async def start_camera(self, camera_id: str) -> bool:
        """Start a camera stream"""
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        camera = self.cameras[camera_id]
        
        # Check if camera is already running
        if camera_id in self.processing_tasks and not self.processing_tasks[camera_id].done():
            logger.warning(f"Camera {camera_id} is already running")
            return True
        
        # Stop any existing task first
        if camera_id in self.processing_tasks:
            self.stop_camera(camera_id)
        
        # Connect to camera
        if not await camera.connect():
            return False
        
        # Start processing task
        task = asyncio.create_task(
            camera.start_processing(self._handle_alert)
        )
        self.processing_tasks[camera_id] = task
        
        return True
    
    def stop_camera(self, camera_id: str):
        """Stop a camera stream"""
        if camera_id in self.cameras:
            camera = self.cameras[camera_id]
            camera.disconnect()
        
        if camera_id in self.processing_tasks:
            task = self.processing_tasks[camera_id]
            if not task.done():
                try:
                    task.cancel()
                except Exception as e:
                    logger.warning(f"Error cancelling task for camera {camera_id}: {e}")
            del self.processing_tasks[camera_id]
    
    async def start_all_cameras(self):
        """Start all cameras"""
        logger.info("Starting all cameras...")
        
        # Load default cameras from config
        for i, rtsp_url in enumerate(settings.default_rtsp_urls):
            camera_id = self.add_camera(f"Camera {i+1}", rtsp_url)
            await self.start_camera(camera_id)
        
        # Ensure AI models are initialized
        if not self.ai_detector.is_initialized():
            await self.ai_detector.initialize()
    
    def stop_all_cameras(self):
        """Stop all cameras"""
        logger.info("Stopping all cameras...")
        for camera_id in list(self.cameras.keys()):
            self.stop_camera(camera_id)
    
    def get_cameras(self) -> List[CameraInfo]:
        """Get all camera information"""
        return [camera.camera_info for camera in self.cameras.values()]
    
    def get_camera(self, camera_id: str) -> Optional[CameraInfo]:
        """Get specific camera information"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].camera_info
        return None
    
    def get_camera_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get current frame from a camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_current_frame()
        return None
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add an alert callback function"""
        self.alert_callbacks.append(callback)
    
    def _handle_alert(self, alert: Alert):
        """Handle a new alert"""
        self.alerts.append(alert)
        logger.info(f"New alert: {alert.message} (confidence: {alert.confidence:.2f})")
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts"""
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
