from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.plate_service import PlateService
from app.schemas.plate import PlateProcessResponse
from app.core.dependencies import get_valid_api_key

# --> ADICIONE ESTA LINHA DE IMPORTAÇÃO:
from app.schemas.api_key import ApiKeyInDB  # Importe a classe ApiKeyInDB


router = APIRouter()
plate_service = PlateService()


@router.post(
    "/processar-placa",
    response_model=PlateProcessResponse,
    summary="Processar imagem de placa",
    description="Recebe uma imagem, detecta a placa via YOLO, e tenta ler a placa com múltiplos serviços OCR. Requer uma chave de API válida no cabeçalho 'X-API-Key'.",
)
async def processar_placa(
    file: UploadFile = File(
        ..., description="O arquivo de imagem da placa para processamento."
    ),
    api_key_data: ApiKeyInDB = Depends(get_valid_api_key),
):
    """
    Processa uma imagem de entrada para detectar a placa e realizar a leitura OCR.
    A autenticação é feita via cabeçalho X-API-Key.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo enviado não é uma imagem válida. Apenas formatos de imagem são aceitos.",
        )

    try:
        # Chama o serviço para processar a imagem
        raw_result = await plate_service.process_plate_image(file)

        if not raw_result.placa and not raw_result.results:
            # Se nenhuma placa foi detectada pelos OCRs
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma placa detectada ou lida na imagem fornecida.",
            )

        # Prepara a resposta com a placa principal e alternativas
        top_result = raw_result.results[0]
        placa = top_result.plate
        alternativas = []
        if hasattr(top_result, "candidates") and top_result.candidates:
            alternativas = [
                c.get("plate")
                for c in top_result.candidates
                if c.get("plate") and c.get("plate") != placa
            ]

        return {"placa": placa, "alternativas": alternativas}

    except RuntimeError as e:
        # Captura erros específicos de falha de comunicação com serviços externos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no pipeline de processamento: {str(e)}",
        )
    except Exception as e:
        # Captura quaisquer outros erros inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno inesperado: {str(e)}",
        )
