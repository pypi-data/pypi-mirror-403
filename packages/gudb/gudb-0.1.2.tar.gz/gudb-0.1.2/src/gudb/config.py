from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GudbConfig(BaseSettings):
    """
    Global configuration for the gudb SDK.
    Values can be set via environment variables (e.g., GUDB_API_ENDPOINT).
    """
    model_config = SettingsConfigDict(
        env_prefix="GUDB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Settings
    api_endpoint: str = Field(
        default="https://ai-db-sentinel.onrender.com/api/sdk/evaluate",
        description="The URL of the gudb evaluation backend."
    )

    dashboard_url: str = Field(
        default="http://localhost:8000/dashboard",
        description="The URL of the gudb monitoring dashboard."
    )
    
    enabled: bool = Field(default=True, description="Master switch for the SDK.")
    fail_open: bool = Field(
        default=True, 
        description="If True, queries pass if the AI backend is unreachable."
    )
    
    # Thresholds
    timeout_seconds: float = Field(default=5.0, description="Timeout for AI evaluation.")
    max_execution_time_ms: int = Field(default=2000, description="Max allowed DB execution time before termination.")
    
    # Heuristics
    enable_local_heuristics: bool = Field(
        default=True, 
        description="Enable zero-latency local checks for DELETE/DROP."
    )
    
    # Security
    redact_pii: bool = Field(default=True, description="Scrub SQL literals before sending to AI.")
    
    # Enterprise
    environment: str = Field(default="development", description="Current environment (prod/stage/dev).")
    service_name: str = Field(default="unknown-service", description="Name of the protected service.")
    
    # Risky Keywords to trigger AI logic
    risky_keywords: List[str] = Field(
        default_factory=lambda: ["DELETE", "UPDATE", "DROP", "ALTER", "TRUNCATE"]
    )

# Singleton instance for internal SDK usage
settings = GudbConfig()
