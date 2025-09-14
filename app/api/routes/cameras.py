"""
Camera management API routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Response, Form
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import io
import base64

from app.models.schemas import CameraInfo

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_cameras(request: Request):
    """Get all cameras"""
    camera_manager = request.app.state.camera_manager
    cameras = camera_manager.get_cameras()
    return [camera.to_dict() for camera in cameras]


@router.post("/")
async def add_camera(request: Request, name: str = Form(...), rtsp_url: str = Form(...)):
    """Add a new camera"""
    camera_manager = request.app.state.camera_manager
    camera_id = camera_manager.add_camera(name, rtsp_url)
    return {"camera_id": camera_id, "message": "Camera added successfully"}


@router.delete("/{camera_id}")
async def remove_camera(request: Request, camera_id: str):
    """Remove a camera"""
    camera_manager = request.app.state.camera_manager
    success = camera_manager.remove_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera removed successfully"}


@router.post("/{camera_id}/start")
async def start_camera(request: Request, camera_id: str):
    """Start a camera stream"""
    camera_manager = request.app.state.camera_manager
    success = await camera_manager.start_camera(camera_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start camera")
    return {"message": "Camera started successfully"}


@router.post("/{camera_id}/stop")
async def stop_camera(request: Request, camera_id: str):
    """Stop a camera stream"""
    camera_manager = request.app.state.camera_manager
    camera_manager.stop_camera(camera_id)
    return {"message": "Camera stopped successfully"}


@router.get("/{camera_id}")
async def get_camera(request: Request, camera_id: str):
    """Get camera information"""
    camera_manager = request.app.state.camera_manager
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera.to_dict()


@router.get("/{camera_id}/frame")
async def get_camera_frame(request: Request, camera_id: str):
    """Get current frame from camera as base64 encoded image"""
    camera_manager = request.app.state.camera_manager
    frame = camera_manager.get_camera_frame(camera_id)
    
    if frame is None:
        raise HTTPException(status_code=404, detail="No frame available")
    
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "camera_id": camera_id,
        "frame": frame_base64,
        "format": "jpeg"
    }


@router.get("/{camera_id}/stream")
async def stream_camera(request: Request, camera_id: str):
    """Stream camera feed as MJPEG"""
    camera_manager = request.app.state.camera_manager
    
    def generate_frames():
        while True:
            frame = camera_manager.get_camera_frame(camera_id)
            if frame is not None:
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                # Return a placeholder image if no frame available
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "No Signal", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', placeholder)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
