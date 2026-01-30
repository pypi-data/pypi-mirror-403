from typing import TypedDict, Optional, List, Annotated
import operator


class SentinelState(TypedDict):
    # Alert tracking
    alert_id: str
    
    # The original slow query caught by the middleware
    raw_query: str 
    
    # Technical context gathered by the Detective Node
    explain_plan: Optional[str]
    schema_info: Optional[str]
    
    # The brain's output - Enhanced with comprehensive report
    suggested_fix: Optional[str]
    reasoning: Optional[str]
    business_impact: Optional[str]
    risk_assessment: Optional[str]
    cost_savings: Optional[str]
    rollback_command: Optional[str]
    
    # Verification data from the Tester Node
    performance_gain: Optional[float]
    is_verified: bool
    
    # Log of attempts (in case Gemini needs to retry)
    # Annotated with operator.add so it appends instead of overwrites
    history: Annotated[List[str], operator.add]