"""
Configuration module for the A2A Audit & Compliance Agent Network.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    app_name: str = "A2A Audit & Compliance Agent Network"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database Configuration (for future use)
    database_url: Optional[str] = None
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # A2A Framework Configuration
    a2a_framework_version: str = "0.2.2"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
