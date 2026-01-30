from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class NotificationLevel(str, Enum):
    """Severity levels for query alerts"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class QueryAlert(BaseModel):
    """Model for slow query alerts"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: str
    duration_ms: float
    endpoint: str
    method: str = "GET"
    severity: NotificationLevel
    status: str = "analyzing"  # analyzing, completed, failed
    
    class Config:
        use_enum_values = True


class QueryAnalysis(BaseModel):
    """Model for AI analysis results"""
    alert_id: str
    explain_plan: Optional[Dict[str, Any]] = None
    schema_info: Optional[str] = None
    bottleneck: Optional[str] = None
    suggested_fix: Optional[str] = None
    reasoning: Optional[str] = None
    performance_gain: Optional[float] = None
    is_verified: bool = False
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    class Config:
        use_enum_values = True


def determine_severity(duration_ms: float, warning_threshold: float = 500, critical_threshold: float = 2000) -> NotificationLevel:
    """Determine alert severity based on query duration"""
    if duration_ms >= critical_threshold:
        return NotificationLevel.CRITICAL
    elif duration_ms >= warning_threshold:
        return NotificationLevel.WARNING
    else:
        return NotificationLevel.INFO
