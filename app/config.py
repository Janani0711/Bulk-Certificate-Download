from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./certificates.db"
    
    # File storage directory for certificates
    STORAGE_DIR: Path = Path("./generated_certificates")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
