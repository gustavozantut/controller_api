from sqlalchemy.orm import Session
from app.crud.api_key import (
    create_api_key_db,
    get_api_key_by_hash,
    increment_api_key_calls,
)
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyInDB
from app.core.security import generate_api_key, get_api_key_hash, verify_api_key
from app.core.config import settings
from datetime import datetime
from app.db.models import ApiKey


class ApiKeyService:
    def create_new_api_key(
        self, db: Session, api_key_data: ApiKeyCreate
    ) -> ApiKeyResponse:
        """
        Gera uma nova chave de API, armazena seu hash no DB e retorna a chave em texto puro.
        """
        plain_key = generate_api_key(settings.API_KEY_LENGTH)
        key_hash = get_api_key_hash(plain_key)
        db_api_key = create_api_key_db(db, key_hash, api_key_data)
        # Retorna a chave em texto puro APENAS NESTE PONTO.
        # Nunca armazene ou retorne a chave em texto puro em outros lugares.
        return ApiKeyResponse(key=plain_key, **db_api_key.__dict__)

    def validate_and_use_api_key(
        self, db: Session, client_api_key: str
    ) -> ApiKeyInDB | None:
        """
        Valida a chave de API fornecida pelo cliente, verifica limites e expiração,
        e incrementa o contador de chamadas.
        Retorna o objeto ApiKeyInDB se a chave for válida e autorizada, None caso contrário.
        """
        # Em cenários de alta performance com muitas chaves, um cache (Redis)
        # das chaves ativas ou um mecanismo de busca otimizado pode ser necessário.
        # A verificação iterativa de hash pode ser lenta com milhares de chaves.
        # No entanto, para começar, essa abordagem é clara e funcional.

        all_active_keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()

        found_key = None
        for db_key_model in all_active_keys:
            if verify_api_key(client_api_key, db_key_model.key_hash):
                found_key = db_key_model
                break

        if not found_key:
            return None  # Chave não encontrada ou hash não corresponde a nenhuma chave ativa

        # Verifica se a chave excedeu o limite de chamadas
        if found_key.calls_made >= found_key.call_limit:
            return None  # Limite de chamadas excedido

        # # Verifica se a chave expirou
        # if found_key.expires_at and found_key.expires_at < datetime.utcnow():
        #     # Opcional: Você pode querer desativar a chave aqui no DB se ela expirou
        #     # deactivate_api_key(db, found_key)
        #     return None  # Chave expirada

        # Incrementa o contador de chamadas APENAS SE a chave for válida e autorizada
        increment_api_key_calls(db, found_key)

        return found_key
