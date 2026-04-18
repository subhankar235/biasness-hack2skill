import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FairLens"
    API_VERSION: str = "v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/fairlens")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    S3_BUCKET: str = os.getenv("S3_BUCKET", "fairlens-data")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()