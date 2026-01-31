from typing import Any
from gudb.core.guardian import Guardian
from gudb.core.interceptor import GudbConnectionWrapper
from gudb.config import settings

__version__ = "0.1.1"

class Gudb:
    """The main entry point for gudb."""
    def __init__(self, provider=None):
        self._guardian = Guardian(provider=provider)

    def monitor(self, conn: Any) -> Any:
        """
        Wraps a database connection to provide real-time guarding.
        
        Args:
            conn: A PEP 249 compliant connection object (e.g., psycopg2).
            
        Returns:
            A wrapped connection object.
        """
        return GudbConnectionWrapper(conn, self._guardian)

# Singleton for easy access
gudb = Gudb()

def monitor(conn: Any) -> Any:
    """Convenience function for gudb.monitor(conn)."""
    return gudb.monitor(conn)

__all__ = ["gudb", "monitor", "Gudb", "settings"]
