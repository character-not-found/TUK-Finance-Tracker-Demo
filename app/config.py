# app/config.py
# Defines application settings using pydantic-settings for robust configuration management.

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Configuration for loading settings, particularly from .env files.
    # 'env_file': Specifies the .env file to load for environment variables.
    # 'extra='ignore'': Allows additional variables in the .env file not explicitly defined here.
    # 'env_file_encoding='utf-8'': Ensures proper character encoding for the .env file.
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8')

    # Core Application Settings (Values typically loaded from .env)
    DATABASE_URL: str = Field(..., description="The connection string for the database (e.g., 'sqlite:///./sql_app.db' or 'postgresql://user:password@host:port/dbname').")

    APP_ENV: str = Field("development", description="Identifies the current environment (e.g., 'development', 'production', 'demo'). Default is 'development' if not set in .env.")

    # SECRET_KEY: Essential for security, used for tasks like token signing (e.g., JWTs).
    # IMPORTANT: Always ensure this is set to a strong, random key in your .env file for any deployment.
    # A placeholder is provided for local development, but it MUST be overridden for production.
    SECRET_KEY: str = "your-super-secret-key-replace-me-in-production"

    # Demo-Specific Credentials (Optional, loaded from .env if present for demo functionality)
    DEMO_USERNAME: Optional[str] = Field(None, description="Optional username for demo mode, loaded from .env.")
    DEMO_PASSWORD: Optional[str] = Field(None, description="Optional password for demo mode, loaded from .env.")

settings = Settings()