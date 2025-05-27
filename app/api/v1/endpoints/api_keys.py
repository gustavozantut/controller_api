from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.api_key_service import ApiKeyService

router = APIRouter()
api_key_service = ApiKeyService()


@router.post(
    "/keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar uma nova chave de API (APENAS PARA ADMINS!)",
)
def create_new_api_key_endpoint(
    api_key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    # TODO: Em produção, adicione uma dependência de autenticação/autorização aqui,
    #       como 'current_admin_user: User = Depends(get_current_admin_user)'
):
    """
    Cria uma nova chave de API com descrição e limite de chamadas opcionais.
    A chave gerada (texto puro) é retornada APENAS uma vez na resposta.
    É CRÍTICO que você salve essa chave, pois ela não pode ser recuperada depois.
    """
    try:
        new_key = api_key_service.create_new_api_key(db, api_key_data)
        return new_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar chave de API: {str(e)}",
        )
