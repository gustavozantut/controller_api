from fastapi import UploadFile
from app.schemas.plate import TaskStatusInit
from app.services.task import process_plate_image_task
from app.core.config import settings


class PlateService:
    def __init__(self):
        self.YOLO_API_URL = settings.YOLO_API_URL
        self.OCR_API_URL = settings.OCR_API_URL
        self.EZOCR_API_URL = settings.EZOCR_API_URL
        self.YOLO_OUTPUT_DIR = settings.YOLO_OUTPUT_DIR

    async def process_plate_image(self, file: UploadFile) -> TaskStatusInit:
        original_bytes = await file.read()

        task = process_plate_image_task.delay(
            original_bytes,
            file.filename,
            file.content_type,
            self.YOLO_API_URL,
            self.OCR_API_URL,
            self.EZOCR_API_URL,
            self.YOLO_OUTPUT_DIR,
        )

        return TaskStatusInit(
            task_id=task.id,
            status="processing",
        )
