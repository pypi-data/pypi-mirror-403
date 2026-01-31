from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    """
    Interface for AI Evaluation Providers.
    Enterprise users can implement this to use their own LLMs.
    """
    
    @abstractmethod
    def evaluate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a query and return a verdict.
        
        Args:
            query: The SQL query string.
            context: Forensic metadata (stack trace, git info, etc.).
            
        Returns:
            A dict containing: verdict (STOP|WARNING|GO), issue, impact, etc.
        """
        pass
