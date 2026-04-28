import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FairLens"
    API_VERSION: str = "v1"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./fairlens.db"
    
    CORS_ORIGINS: list = ["*"]
    
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

settings = Settings()