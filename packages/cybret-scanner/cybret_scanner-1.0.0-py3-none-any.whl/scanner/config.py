"""
Configuration management for CYBRET AI Scanner
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "cybretai2024"
    neo4j_database: str = "neo4j"

    # Scanner Configuration
    scan_timeout: int = 3600
    max_file_size: int = 10485760  # 10MB
    max_concurrent_scans: int = 5
    supported_languages: List[str] = ["python", "javascript", "java", "go"]

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    log_level: str = "INFO"
    enable_cors: bool = True
    allowed_origins: List[str] = ["http://localhost:3000"]

    # Security
    secret_key: str = "change-this-secret-key-in-production"
    access_token_expire_minutes: int = 30

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Git Repository Scanning
    clone_dir: str = "/tmp/cybret-scans"
    max_repo_size: int = 524288000  # 500MB

    # Detection Configuration
    idor_detection_enabled: bool = True
    auth_bypass_detection_enabled: bool = True
    priv_esc_detection_enabled: bool = True
    sql_injection_detection_enabled: bool = True

    # Monitoring
    enable_prometheus: bool = True
    prometheus_port: int = 9090

    # LLM Configuration
    # Supports: OpenAI, Anthropic, OpenRouter, Ollama (local)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Default LLM models
    llm_model: str = "anthropic/claude-3.5-sonnet"  # For OpenRouter
    openai_model: str = "gpt-4"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    # Feature Flags
    enable_multi_language: bool = True
    enable_incremental_scan: bool = False
    enable_ai_analysis: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Make .env file optional
        env_ignore_empty = True
        extra = "ignore"


# Global settings instance
# Use try-except to handle missing .env file gracefully
try:
    settings = Settings()
except Exception as e:
    # If .env parsing fails, create settings with defaults only
    import os
    if os.path.exists(".env"):
        print(f"Warning: Error parsing .env file: {e}")
        print("Using default configuration values")
    settings = Settings(_env_file=None)
