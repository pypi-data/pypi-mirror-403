from fastapi import APIRouter, HTTPException
from services.models import QueryAnalysis
from utils.notifier import notification_manager

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{alert_id}", response_model=QueryAnalysis)
async def get_analysis(alert_id: str):
    """Get detailed AI analysis for a specific alert"""
    # First check if alert exists
    alert = notification_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get analysis results
    analysis = notification_manager.get_analysis(alert_id)
    if not analysis:
        # Alert exists but analysis not ready yet
        raise HTTPException(
            status_code=202, 
            detail=f"Analysis in progress (status: {alert.status})"
        )
    
    return analysis
