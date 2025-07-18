import os
import json
import requests
from typing import Dict, Optional
from app.celery_app import celery


@celery.task(name="plate.process_plate_image_task")
def process_plate_image_task(
    original_bytes: bytes,
    filename: str,
    content_type: str,
    yolo_api_url: str,
    ocr_api_url: str,
    ezocr_api_url: str,
    yolo_output_dir: str,
) -> dict:
    """
    Task Celery que processa a imagem recebida:
    1. Detecta placa com YOLO
    2. Tenta OCR com ezOCR e OCR
    3. Retorna dict serializável com resultados
    """

    file_id = None
    classe_detectada = None
    crop_bytes = None

    # === Etapa 1: Envia imagem ao YOLO ===
    try:
        yolo_resp = requests.post(
            yolo_api_url,
            files={"file": (filename, original_bytes, content_type)},
            timeout=30,
        )
        if yolo_resp.status_code == 404:
            pass
        elif not yolo_resp.ok:
            yolo_resp.raise_for_status()

        yolo_json = yolo_resp.json()

        crop_path = None
        if "arquivo" in yolo_json:
            crop_path = yolo_json["arquivo"]
        elif "file_id" in yolo_json:
            crop_path = os.path.join(
                yolo_output_dir,
                yolo_json["file_id"],
                f"{yolo_json['file_id']}.jpg",
            )

        if not crop_path:
            raise ValueError("Resposta do YOLO não continha caminho válido.")

        file_id = yolo_json.get("file_id")
        classe_detectada = yolo_json.get("classe")

        if not os.path.exists(crop_path):
            raise FileNotFoundError(f"Imagem recortada não encontrada: {crop_path}")

        with open(crop_path, "rb") as f:
            crop_bytes = f.read()

    except Exception as e:
        return {"error": f"Erro no YOLO: {str(e)}"}

    # === Etapa 2: Tentativas OCR ===
    tentativa_urls = [
        (ezocr_api_url, classe_detectada),
        (ocr_api_url, classe_detectada),
        (ezocr_api_url, None),
        (ocr_api_url, None),
    ]

    def padronizar_resultado_ocr_bruto(resultado_ocr: Dict | str) -> dict:
        if isinstance(resultado_ocr, dict):
            if "resultado" in resultado_ocr:
                try:
                    parsed = json.loads(resultado_ocr["resultado"])
                    results = parsed.get("results", [])
                    return {
                        "placa": results[0]["plate"] if results else None,
                        "results": results,
                    }
                except json.JSONDecodeError:
                    return {"placa": None, "results": []}
            if "results" in resultado_ocr:
                results = resultado_ocr["results"]
                return {
                    "placa": results[0]["plate"] if results else None,
                    "results": results,
                }
        return {"placa": None, "results": []}

    def chamar_ocr(
        crop_bytes: bytes, categoria: Optional[str], anpr_api_url: str
    ) -> dict:
        data = {"categoria": categoria} if categoria else {}
        try:
            resp = requests.post(
                anpr_api_url,
                files={"file": ("input.jpg", crop_bytes, "image/jpeg")},
                data=data,
                timeout=30,
            )
            resp.raise_for_status()
            return padronizar_resultado_ocr_bruto(resp.json())
        except Exception:
            return {"placa": None, "results": []}

    raw_result = {"placa": None, "results": []}
    for url, categoria in tentativa_urls:
        raw_result = chamar_ocr(crop_bytes, categoria, url)
        if raw_result["placa"] or raw_result["results"]:
            break

    if not raw_result["placa"] and not raw_result["results"]:
        return {"placa": None, "results": []}

    # === Etapa 3: Salvar resultado em disco (opcional) ===
    try:
        if file_id and raw_result["placa"]:
            output_dir_for_file = os.path.join(yolo_output_dir, file_id)
            os.makedirs(output_dir_for_file, exist_ok=True)
            with open(
                os.path.join(output_dir_for_file, f"{file_id}.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(raw_result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ATENÇÃO: Erro ao salvar resultado em disco para {file_id}: {str(e)}")

    return raw_result
