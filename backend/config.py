"""
AICTE ONE Configuration Settings
"""
import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "AICTE ONE - Unified Institutional Intelligence Platform"
    APP_VERSION: str = "2.4.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security & Tokens
    SECRET_KEY: str = os.getenv("SECRET_KEY", "aicte-one-super-secret-governance-key-2026-production-grade")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Database
    default_db: str = "sqlite:////tmp/aicte_one.db" if os.getenv("VERCEL") == "1" else "sqlite:///./aicte_one.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", default_db)
    
    # External integrations & AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "simulated")  # "simulated", "tesseract", "easyocr"
    DIGILOCKER_SANDBOX_URL: str = os.getenv("DIGILOCKER_SANDBOX_URL", "https://sandbox.api.gov.in/digilocker/v1")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "https://*.vercel.app"
    ]
    
    # Host & Port
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

settings = Settings()
