from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.api_key_service import ApiKeyService
from app.schemas.api_key import ApiKeyInDB

# Instancia o serviço de chaves de API uma vez
api_key_service = ApiKeyService()


async def get_valid_api_key(
    # FastAPI automaticamente mapeia 'x_api_key' para o cabeçalho 'X-API-Key'
    x_api_key: str = Header(
        ..., alias="X-API-Key", description="Sua chave de API para autenticação."
    ),
    db: Session = Depends(get_db),  # Injeta a sessão do banco de dados
) -> ApiKeyInDB:
    """
    Dependência que valida a chave de API fornecida no cabeçalho 'X-API-Key'.
    Se a chave for válida, ativa, não expirada e dentro do limite de chamadas,
    o contador de chamadas é incrementado e o objeto ApiKey é retornado.
    Caso contrário, uma exceção HTTPException 401 UNAUTHORIZED é levantada.
    """
    api_key_data = api_key_service.validate_and_use_api_key(db, x_api_key)

    if not api_key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida, inativa, expirada ou limite de chamadas excedido.",
            # O cabeçalho WWW-Authenticate indica o esquema de autenticação esperado
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return api_key_data
