from sqlalchemy.orm import Session
from app.db.models import ApiKey
from app.schemas.api_key import ApiKeyCreate
from app.core.config import settings


def get_api_key_by_hash(db: Session, key_hash: str) -> ApiKey | None:
    """Retorna uma chave de API pelo seu hash."""
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()


def get_api_key_by_id(db: Session, api_key_id: int) -> ApiKey | None:
    """Retorna uma chave de API pelo seu ID."""
    return db.query(ApiKey).filter(ApiKey.id == api_key_id).first()


def create_api_key_db(db: Session, key_hash: str, api_key_data: ApiKeyCreate) -> ApiKey:
    """Cria uma nova chave de API no banco de dados."""
    # Define o limite de chamadas: usa o valor fornecido ou o padrão do sistema
    call_limit_val = (
        api_key_data.call_limit
        if api_key_data.call_limit is not None
        else settings.DEFAULT_CALL_LIMIT
    )

    db_api_key = ApiKey(
        key_hash=key_hash,
        description=api_key_data.description,
        call_limit=call_limit_val,
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)  # Atualiza o objeto para incluir o ID gerado pelo DB
    return db_api_key


def increment_api_key_calls(db: Session, api_key: ApiKey) -> ApiKey:
    """Incrementa o contador de chamadas de uma chave de API."""
    api_key.calls_made += 1
    db.add(api_key)  # Adiciona ao controle da sessão (caso já não esteja)
    db.commit()  # Salva a alteração no banco de dados
    db.refresh(api_key)  # Atualiza o objeto com os dados mais recentes do DB
    return api_key


def deactivate_api_key(db: Session, api_key: ApiKey) -> ApiKey:
    """Desativa uma chave de API."""
    api_key.is_active = False
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key
