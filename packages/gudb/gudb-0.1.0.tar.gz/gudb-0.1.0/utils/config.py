from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # Database Configuration
    db_url: str = "postgresql://user:password@localhost:5432/dbname"
    
    # Gemini API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Query Monitoring Thresholds (in milliseconds)
    slow_query_threshold_ms: float = 500.0
    critical_threshold_ms: float = 2000.0
    
    # Safety Thresholds
    max_safe_cost_threshold: float = 100000.0  # Max estimated cost to allow EXPLAIN ANALYZE
    
    # Feature Flags
    enable_auto_analysis: bool = True
    enable_notifications: bool = True
    
    # Notification Settings
    max_stored_alerts: int = 100
    
    # Git Integration
    enable_git_tracking: bool = True
    git_repo_path: str = "."
    track_migration_files: bool = True
    git_lookback_hours: int = 48  # How far back to look for commits
    
    # Schema Evolution
    enable_schema_tracking: bool = True
    schema_snapshot_interval_hours: int = 24
    auto_capture_schema: bool = False  # Auto-capture schema on startup
    
    # Preventive Analysis
    enable_preventive_mode: bool = True
    migration_risk_threshold: str = "medium"  # low, medium, high
    
    # AI Response Style
    ai_response_style: str = "senior_engineer"  # Options: standard, senior_engineer
    include_alternative_fixes: bool = True
    max_fix_options: int = 3
    include_git_context: bool = True  # Include git info in AI analysis
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
