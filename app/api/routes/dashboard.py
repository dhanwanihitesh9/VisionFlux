"""
Dashboard API routes
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/status")
async def get_system_status(request: Request):
    """Get system status overview"""
    camera_manager = request.app.state.camera_manager
    ai_detector = request.app.state.ai_detector
    
    cameras = camera_manager.get_cameras()
    recent_alerts = camera_manager.get_recent_alerts(10)
    
    # Count cameras by status
    status_counts = {}
    for camera in cameras:
        status = camera.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "system": {
            "ai_models_loaded": ai_detector.is_initialized(),
            "total_cameras": len(cameras),
            "camera_status_counts": status_counts
        },
        "cameras": [camera.to_dict() for camera in cameras],
        "recent_alerts": [alert.to_dict() for alert in recent_alerts],
        "custom_prompts": [prompt.to_dict() for prompt in ai_detector.get_custom_prompts()]
    }
