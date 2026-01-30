import requests
from typing import Dict, Any
from gudb.providers.base import BaseProvider
from gudb.config import settings
from gudb.utils.logging import get_logger

logger = get_logger("provider.remote")

class RemoteGudbProvider(BaseProvider):
    """
    Standard provider that calls the gudb Backend API.
    """
    
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or settings.api_endpoint

    def evaluate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            payload = {
                "query": query,
                "stack_trace": context.get("stack_trace"),
                "git_info": context.get("git_info"),
                "env": settings.environment
            }
            
            response = requests.post(
                self.endpoint, 
                json=payload, 
                timeout=settings.timeout_seconds
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Backend returned status {response.status_code}")
                return {"verdict": "GO", "reason": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to reach gudb backend: {e}")
            return {"verdict": "GO", "error": "Backend unreachable"}
