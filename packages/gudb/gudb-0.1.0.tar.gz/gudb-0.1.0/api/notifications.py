from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.models import QueryAlert
from utils.notifier import notification_manager

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=List[QueryAlert])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = Query(None, regex="^(info|warning|critical)$")
):
    """Get recent query alerts, optionally filtered by severity"""
    alerts = notification_manager.get_alerts(limit=limit, severity=severity)
    return alerts


@router.get("/count")
async def get_notification_count():
    """Get count of unread notifications"""
    count = notification_manager.get_unread_count()
    return {"count": count}


@router.get("/{alert_id}", response_model=QueryAlert)
async def get_notification(alert_id: str):
    """Get a specific alert by ID"""
    alert = notification_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/clear")
async def clear_notifications():
    """Clear all notifications (for testing)"""
    notification_manager.clear_all()
    return {"message": "All notifications cleared"}
