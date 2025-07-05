# app/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Novas variáveis para o PostgreSQL (lidas do .env)
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "db"  # Valor padrão para o nome do serviço Docker Compose
    POSTGRES_PORT: int = 5432  # Valor padrão para a porta do PostgreSQL

    # Propriedade para construir a DATABASE_URL
    @property
    def DATABASE_URL(self) -> str:
        # Importante: usar f-string para construir a URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Suas outras variáveis de configuração
    API_KEY_LENGTH: int
    DEFAULT_CALL_LIMIT: int
    YOLO_API_URL: str
    OCR_API_URL: str
    EZOCR_API_URL: str
    YOLO_OUTPUT_DIR: str
    MAX_TOTAL_API_KEYS: int = 20


settings = Settings()
