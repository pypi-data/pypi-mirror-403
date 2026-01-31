from typing import Optional

class GudbError(Exception):
    """Base exception for all gudb related errors."""
    pass

class ConfigurationError(GudbError):
    """Raised when the SDK is misconfigured."""
    pass

class InterceptionError(GudbError):
    """Raised when there is an issue intercepting a database query."""
    pass

class DisasterBlockedError(GudbError):
    """
    Raised when a query is blocked because it was identified as a 
    production-halting disaster.
    """
    def __init__(self, message: str, issue: str, impact: str, fix: Optional[str] = None):
        self.issue = issue
        self.impact = impact
        self.fix = fix
        
        # ANSI Colors for Hackathon "Wow" Factor
        RED = "\033[91m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        
        banner = f"\n{RED}{BOLD}🛑 [gudb] ACCESS DENIED - DATABASE SEATBELT ACTIVATED{RESET}"
        issue_line = f"   {BOLD}ISSUE:{RESET}  {YELLOW}{issue}{RESET}"
        impact_line = f"   {BOLD}IMPACT:{RESET} {RED}{impact}{RESET}"
        fix_line = f"   {BOLD}FIX:{RESET}    {CYAN}{fix}{RESET}" if fix else ""
        
        from gudb.config import settings
        recommendation = f"\n📈 {BOLD}For more recommendations, visit:{RESET} {CYAN}{settings.dashboard_url}{RESET}\n"
        
        full_message = f"{banner}\n{issue_line}\n{impact_line}\n{fix_line}{recommendation}"
        super().__init__(full_message)

class ProviderError(GudbError):
    """Raised when the AI provider (Remote/Local) fails or times out."""
    pass
