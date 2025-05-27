import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configura o Pydantic para ler de .env e ignorar chaves não mapeadas
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    API_KEY_LENGTH: int
    DEFAULT_CALL_LIMIT: int

    YOLO_API_URL: str
    OCR_API_URL: str
    EZOCR_API_URL: str
    YOLO_OUTPUT_DIR: str


settings = Settings()
