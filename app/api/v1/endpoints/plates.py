from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.plate_service import PlateService, process_plate_image_task
from app.schemas.plate import TaskStatusInit, TaskStatusResponse
from app.core.dependencies import get_valid_api_key
from app.schemas.api_key import ApiKeyInDB  # Importe a classe ApiKeyInDB

from app.celery_app import celery


router = APIRouter()
plate_service = PlateService()


@router.post(
    "/processar-placa",
    summary="Processar imagem de placa",
    description="Envia a imagem para processamento assíncrono via Celery e retorna o task_id.",
    response_model=TaskStatusResponse,
)
async def processar_placa(
    file: UploadFile = File(..., description="Imagem da placa"),
    api_key_data: ApiKeyInDB = Depends(get_valid_api_key),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Arquivo enviado não é uma imagem válida.",
        )

    # Dispara a task Celery e retorna o id da task
    original_bytes = await file.read()
    task = process_plate_image_task.delay(
        original_bytes,
        file.filename,
        file.content_type,
        plate_service.YOLO_API_URL,
        plate_service.OCR_API_URL,
        plate_service.EZOCR_API_URL,
        plate_service.YOLO_OUTPUT_DIR,
    )

    return TaskStatusInit(task_id=task.id, status="processing")


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="Consulta status e resultado da task de processamento de placa",
)
async def get_task_status(task_id: str):
    async_result = celery.AsyncResult(task_id)
    if async_result.state == "PENDING":
        return TaskStatusResponse(task_id=task_id, status="pending")
    elif async_result.state == "STARTED":
        return TaskStatusResponse(task_id=task_id, status="started")
    elif async_result.state == "FAILURE":
        # Pode retornar a exceção ou mensagem de erro
        return TaskStatusResponse(task_id=task_id, status="failure")
    elif async_result.state == "SUCCESS":
        result = async_result.result  # deve ser dict com placa e alternativas
        placa = None
        alternativas = []
        if result:
            placa = result.get("placa")
            if result.get("results") and len(result["results"]) > 0:
                top_result = result["results"][0]
                alternativas = [
                    c.get("plate")
                    for c in top_result.get("candidates", [])
                    if c.get("plate") and c.get("plate") != placa
                ]
        return TaskStatusResponse(
            task_id=task_id,
            status="success",
            placa=placa,
            alternativas=alternativas,
        )
    else:
        return TaskStatusResponse(task_id=task_id, status=async_result.state.lower())
