# app/config.py
# Defines application settings using pydantic-settings for robust configuration management.

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, ClassVar

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8')

    DATABASE_URL: str = Field(..., description="The connection string for the database (e.g., 'sqlite:///./sql_app.db' or 'postgresql://user:password@host:port/dbname').")

    APP_ENV: str = Field("development", description="Identifies the current environment (e.g., 'development', 'production', 'demo'). Default is 'development' if not set in .env.")

    SECRET_KEY: str = Field(..., description="The secret key for signing JWTs, loaded from .env.")

    DEMO_USERNAME: Optional[str] = Field(None, description="Optional username for demo mode, loaded from .env.")
    DEMO_PASSWORD: Optional[str] = Field(None, description="Optional password for demo mode, loaded from .env.")
    
    ALGORITHM: ClassVar[str] = "HS256"
    
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[int] = 30

settings = Settings()