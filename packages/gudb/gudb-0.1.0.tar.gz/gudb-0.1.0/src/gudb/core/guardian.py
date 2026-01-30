import hashlib
import threading
from typing import Dict, Any, Optional
from gudb.config import settings
from gudb.providers.base import BaseProvider
from gudb.providers.remote import RemoteGudbProvider
from gudb.utils.logging import get_logger
from gudb.core.redactor import SQLRedactor
from gudb.utils.context import ContextCollector

logger = get_logger("guardian")

class Guardian:
    """
    The brain of the SDK. Manages the evaluation lifecycle:
    Heuristics -> Caching -> AI Evaluation.
    """
    
    def __init__(self, provider: Optional[BaseProvider] = None):
        self.provider = provider or RemoteGudbProvider()
        self.query_cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.redactor = SQLRedactor()
        self.context = ContextCollector()

    def evaluate(self, query: str) -> Dict[str, Any]:
        """Runs the full safety check on a query (Seatbelt Mode)."""
        if not settings.enabled:
            return {"verdict": "GO"}

        # 1. ZERO LATENCY LOCAL HEURISTICS (The Core Seatbelt)
        if settings.enable_local_heuristics:
            heuristic_result = self._check_heuristics(query)
            if heuristic_result:
                # We stop immediately! No AI needed for blatant disasters.
                return heuristic_result

        # 2. FAST-PATH: Only redact and AI-check if risky
        if not self._is_risky(query):
            return {"verdict": "GO"}

        # 3. Redaction & Caching (Advisory Level)
        processed_query = self.redactor.redact(query) if settings.redact_pii else query
        query_hash = hashlib.sha256(processed_query.encode()).hexdigest()
        
        with self._lock:
            if query_hash in self.query_cache:
                return self.query_cache[query_hash]

        # 4. AI Advisory (Consulting the Senior DRE)
        logger.info(f"🛡️ [Advisor] Consulting AI for pattern: {processed_query[:40]}...")
        context = self.context.collect_all()
        result = self.provider.evaluate(processed_query, context)
        
        # 5. Caching & Result
        with self._lock:
            self.query_cache[query_hash] = result
            
        return result

    def _check_heuristics(self, query: str) -> Optional[Dict[str, Any]]:
        """Hardcoded safety rules that MUST NEVER be violated."""
        upper_sql = query.upper().strip()
        
        # Rule 1: No unconstrained DELETE/UPDATE (The Career-Saver)
        if (upper_sql.startswith("DELETE") or upper_sql.startswith("UPDATE")) and " WHERE " not in upper_sql:
             return {
                 "verdict": "STOP",
                 "issue": "UNCONSTRAINED DATA MODIFICATION",
                 "impact": "This query will wipe or corrupt EVERY ROW in the table.",
                 "fix": "Add a WHERE clause to target specific records.",
                 "reasoning_short": "Seatbelt: Blocked because a WHERE clause is missing."
             }
        
        # Rule 2: No accidental DROPs
        if "DROP TABLE" in upper_sql or "DROP DATABASE" in upper_sql:
            return {
                "verdict": "STOP",
                "issue": "SCHEMA DESTRUCTION DETECTED",
                "impact": "This will PERMANENTLY delete your data structure.",
                "fix": "Schema changes should go through a migration pipeline, not direct execution.",
                "reasoning_short": "Seatbelt: DROP statements are restricted."
            }
            
        # Rule 3: No TRUNCATE without safety
        if "TRUNCATE" in upper_sql:
            return {
                "verdict": "STOP",
                "issue": "BLITZ-WIPE DETECTED",
                "impact": "TRUNCATE is irreversible and ignores triggers.",
                "fix": "Use DELETE with WHERE if you only want to remove specific data.",
                "reasoning_short": "Seatbelt: TRUNCATE is considered too dangerous for direct SDK use."
            }

        return None

    def _is_risky(self, query: str) -> bool:
        upper_sql = query.upper()
        return any(kw in upper_sql for kw in settings.risky_keywords)
