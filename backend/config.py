"""
AICTE ONE Configuration Settings
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AICTE ONE - Unified Institutional Intelligence Platform"
    APP_VERSION: str = "2.4.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    default_db: str = "sqlite:////tmp/aicte_one.db" if os.getenv("VERCEL") == "1" else "sqlite:///./aicte_one.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", default_db)
    
    # External integrations & AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "simulated")  # "simulated", "tesseract", "easyocr"
    DIGILOCKER_SANDBOX_URL: str = os.getenv("DIGILOCKER_SANDBOX_URL", "https://sandbox.api.gov.in/digilocker/v1")
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Host & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
