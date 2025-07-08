from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.config import settings

MAX_CALL_LIMIT_PER_KEY = settings.DEFAULT_CALL_LIMIT


class ApiKeyCreate(BaseModel):
    description: Optional[str] = Field(
        None, description="Descrição da chave de API (ex: 'App Cliente X')"
    )
    call_limit: Optional[int] = Field(
        None,
        ge=1,  # Garante que seja maior ou igual a zero
        le=MAX_CALL_LIMIT_PER_KEY,  # <--- AQUI: Limite máximo
        description=f"Limite de chamadas para esta chave (máx: {MAX_CALL_LIMIT_PER_KEY}). Se nulo, usa o padrão do sistema.",
    )


class ApiKeyResponse(BaseModel):
    id: int
    key: str = Field(
        ..., description="A chave de API em texto puro (exibida apenas na criação)."
    )
    description: Optional[str] = None
    call_limit: int
    calls_made: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Permite mapeamento de ORM (SQLAlchemy) para Pydantic


class ApiKeyInDB(BaseModel):
    id: int
    key_hash: str  # Aqui armazenamos o hash da chave, não a chave em texto puro
    description: Optional[str] = None
    call_limit: int
    calls_made: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
