# app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Odoo AI Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Odoo
    ODOO_URL: str
    ODOO_DB: str = "produccion"
    ODOO_USER: str = "admin"
    ODOO_PASSWORD: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Groq
    GROQ_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
