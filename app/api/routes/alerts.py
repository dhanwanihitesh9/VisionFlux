"""
Alerts API routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/")
async def get_alerts(request: Request, limit: int = 100):
    """Get recent alerts"""
    camera_manager = request.app.state.camera_manager
    alerts = camera_manager.get_recent_alerts(limit)
    return [alert.to_dict() for alert in alerts]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(request: Request, alert_id: str):
    """Acknowledge an alert"""
    camera_manager = request.app.state.camera_manager
    success = camera_manager.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged successfully"}
