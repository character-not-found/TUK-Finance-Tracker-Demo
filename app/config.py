# app/config.py
# This file defines application settings using pydantic-settings.

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # model_config provides configuration for how settings are loaded.
    # env_file: Specifies the .env file to load.
    #           By default, pydantic-settings looks for a file named '.env'.
    #           We'll use this for local development.
    # extra='ignore': Ignores any extra fields in the .env file not defined here.
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8')

    # --- Core Application Settings ---
    # DATABASE_URL: The connection string for your database.
    # This will be different for development, production, and demo.
    DATABASE_URL: str

    # APP_ENV: Identifies the current environment (e.g., "development", "production", "demo").
    # Default is "development" if not explicitly set.
    APP_ENV: str = "development"

    # SECRET_KEY: Used for security purposes like token signing (crucial for JWTs).
    # IMPORTANT: GENERATE A REAL, STRONG, RANDOM KEY FOR PRODUCTION!
    # You can generate one with: import secrets; print(secrets.token_urlsafe(32))
    SECRET_KEY: str = "SECRET KEY"

    # --- Demo Specific Settings (Optional, will be used later on 'demo' branch) ---
    # These settings are optional and will only be used when APP_ENV is "demo".
    # They are included here so the Settings class is consistent across branches,
    # but their values will only be set in the .env.demo file.
    DEMO_USERNAME: Optional[str] = None
    DEMO_PASSWORD: Optional[str] = None

# Create an instance of the Settings class.
# This instance will hold all your loaded configuration values.
settings = Settings()
