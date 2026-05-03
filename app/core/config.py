from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "OBD-AI Diagnostics"
    DEBUG: bool = False
    GROQ_API_KEY: str = ""
    OBD_PORT: Optional[str] = None
    OBD_BAUDRATE: int = 38400
    DATABASE_URL: str = "sqlite+aiosqlite:///./diagnostics.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()