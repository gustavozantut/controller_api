from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func  # Para funções do banco de dados como CURRENT_TIMESTAMP
from app.db.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"  # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True)  # ID único da chave
    key_hash = Column(
        String, unique=True, index=True, nullable=False
    )  # Hash da chave de API
    description = Column(String, nullable=True)  # Descrição para identificar a chave
    call_limit = Column(Integer, default=1000)  # Limite de chamadas permitidas
    calls_made = Column(Integer, default=0)  # Contador de chamadas realizadas
    is_active = Column(Boolean, default=True)  # Status da chave (ativa/inativa)
    created_at = Column(DateTime, server_default=func.now())  # Data de criação
