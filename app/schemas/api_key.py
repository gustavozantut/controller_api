from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKeyCreate(BaseModel):
    description: Optional[str] = Field(
        None, description="Descrição da chave de API (ex: 'App Cliente X')"
    )
    call_limit: Optional[int] = Field(
        None,
        ge=0,
        description="Limite de chamadas para esta chave. Se nulo, usa o padrão do sistema.",
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
