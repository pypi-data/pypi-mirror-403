import time
from typing import Any
from gudb.core.guardian import Guardian
from gudb.config import settings
from gudb.exceptions import DisasterBlockedError, GudbError
from gudb.utils.logging import get_logger

logger = get_logger("core.interceptor")

class PerformanceLimitError(GudbError):
    """Raised when a query is terminated due to performance risks."""
    def __init__(self, elapsed: float, limit: int, query_type: str):
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        
        banner = f"\n{RED}{BOLD}🛑 [gudb] QUERY TERMINATED - PERFORMANCE RISK DETECTED{RESET}"
        stats = f"   {BOLD}Execution Time:{RESET} {RED}{elapsed:.2f}s{RESET} (Limit: {limit/1000:.2f}s)"
        risk = f"   {BOLD}Risk:{RESET}           {YELLOW}Database Stall / Lock Contention{RESET}"
        advice = f"\n💡 {CYAN}{BOLD}AI ADVICE:{RESET}\n   • Add missing indexes\n   • Avoid SELECT *\n   • Break query into paginated batches"
        outcome = f"\n   {BOLD}Outcome:{RESET}        {RED}❌ TERMINATED{RESET}"
        
        recommendation = f"\n📈 {BOLD}For more recommendations, visit:{RESET} {CYAN}{settings.dashboard_url}{RESET}\n"
        
        super().__init__(f"{banner}\n{stats}\n{risk}\n{advice}\n{outcome}\n{recommendation}")

class GudbCursorWrapper:
    """Wraps a database cursor to intercept execution."""
    def __init__(self, cursor: Any, guardian: Guardian):
        self._cursor = cursor
        self._guardian = guardian
        self._set_session_safety()

    def _set_session_safety(self):
        """Injects hard authoritative timeouts into the session (Tier 2)."""
        try:
            # For Postgres
            self._cursor.execute(f"SET statement_timeout = {settings.max_execution_time_ms};")
        except:
            # Fallback/Ignore for non-postgres drivers in demo
            pass

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)

    def execute(self, query: str, vars: Any = None) -> Any:
        # Tier 1: AI/Heuristic Evaluation (Pre-Execution)
        try:
            decision = self._guardian.evaluate(query)
            
            if decision.get("verdict") == "STOP":
                raise DisasterBlockedError(
                    message="[gudb] Query Blocked!",
                    issue=decision.get("issue", "Critical risk"),
                    impact=decision.get("impact", "Potential downtime"),
                    fix=decision.get("fix")
                )
        except DisasterBlockedError:
            raise
        except Exception as e:
            logger.error(f"Interception failed (Failing Open): {e}")

        # Tier 2: Performance Guard (Runtime)
        start_time = time.perf_counter()
        try:
            result = self._cursor.execute(query, vars)
            elapsed = time.perf_counter() - start_time
            
            # If DB timeout didn't kill it but it was slow
            if (elapsed * 1000) > settings.max_execution_time_ms:
                logger.warning(f"Performance Seatbelt: Query took {elapsed:.2f}s (Limit: {settings.max_execution_time_ms/1000}s)")
            
            return result
        except Exception as e:
            # Check if this was a timeout exception (driver specific)
            if "query_wait_timeout" in str(e).lower() or "statement_timeout" in str(e).lower():
                elapsed = time.perf_counter() - start_time
                raise PerformanceLimitError(
                    elapsed=elapsed,
                    limit=settings.max_execution_time_ms,
                    query_type="SELECT" # Simplified for demo
                )
            raise e

class GudbConnectionWrapper:
    """Wraps a database connection."""
    def __init__(self, conn: Any, guardian: Guardian):
        self._conn = conn
        self._guardian = guardian

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        cursor = self._conn.cursor(*args, **kwargs)
        return GudbCursorWrapper(cursor, self._guardian)
