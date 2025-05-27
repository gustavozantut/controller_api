import os

import json

import requests

from fastapi import FastAPI, File, UploadFile

from fastapi.responses import JSONResponse


app = FastAPI()


# === Configurações dos serviços ===

YOLO_API_URL = "http://yolo:8001/detectar-placa"

OCR_API_URL = "http://ocr:8002/ler-placa"

EZOCR_API_URL = "http://ezocr:8005/ler-placa"

YOLO_OUTPUT_DIR = os.getenv("YOLO_OUTPUT_DIR", "/brplates/runs")


# === Função para padronizar o retorno dos OCRs ===


def padronizar_resultado_ocr_bruto(resultado_ocr: dict | str) -> dict:
    """

    Padroniza o resultado vindo de OCR antigo (campo 'resultado') ou ezOCR (campo 'results').

    Retorna sempre:

    {

        "placa": str | None,

        "results": list[{"plate": str}]

    }

    """

    if isinstance(resultado_ocr, dict):

        # OCR antigo: {"resultado": "<json_string>"}

        if "resultado" in resultado_ocr:

            try:

                parsed = json.loads(resultado_ocr["resultado"])

                results = parsed.get("results", [])

                placa = results[0].get("plate") if results else None

                return {"placa": placa, "results": results}

            except json.JSONDecodeError:

                return {"placa": None, "results": []}

        # ezOCR: {"results": [...]}

        if "results" in resultado_ocr:

            results = resultado_ocr["results"]

            placa = results[0].get("plate") if results else None

            return {"placa": placa, "results": results}

    return {"placa": None, "results": []}


# === Função para chamar qualquer OCR padronizando resultado ===


def chamar_ocr(crop_bytes: bytes, categoria=None, ANPR_API_URL=None) -> dict:

    data = {"categoria": categoria} if categoria else {}

    try:

        resp = requests.post(
            ANPR_API_URL,
            files={"file": ("input.jpg", crop_bytes)},
            data=data,
        )

        if resp.status_code != 200:

            raise RuntimeError(resp.text)

        return padronizar_resultado_ocr_bruto(resp.json())

    except Exception as e:

        raise RuntimeError(f"OCR falhou: {str(e)}")


# === Rota principal ===


@app.post("/processar-placa")
async def processar_placa(file: UploadFile = File(...)):

    if not file.content_type.startswith("image/"):

        return JSONResponse(
            status_code=400,
            content={"erro": "Arquivo enviado não é uma imagem válida."},
        )

    original_bytes = await file.read()

    # === Etapa 1: Envia imagem ao YOLO ===

    try:

        yolo_resp = requests.post(
            YOLO_API_URL, files={"file": (file.filename, original_bytes)}
        )

        yolo_json = yolo_resp.json()

        if yolo_resp.status_code == 200:

            crop_path = yolo_json["arquivo"]

        elif yolo_resp.status_code == 404:

            crop_path = os.path.join(
                YOLO_OUTPUT_DIR, yolo_json["file_id"], f"{yolo_json['file_id']}.jpg"
            )

        else:

            return JSONResponse(
                status_code=500,
                content={"erro": "YOLO falhou", "detalhe": yolo_resp.text},
            )

        file_id = yolo_json["file_id"]

        classe_detectada = yolo_json.get("classe")

        with open(crop_path, "rb") as f:

            crop_bytes = f.read()

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"erro": "Falha ao obter imagem da placa", "detalhe": str(e)},
        )

    # === Etapa 2: Tentativas com ezOCR e OCR, com e sem categoria ===

    tentativa_urls = [
        (EZOCR_API_URL, classe_detectada),
        (OCR_API_URL, classe_detectada),
        (EZOCR_API_URL, None),
        (OCR_API_URL, None),
    ]

    raw_result = {"placa": None, "results": []}

    for url, categoria in tentativa_urls:

        try:

            raw_result = chamar_ocr(crop_bytes, categoria=categoria, ANPR_API_URL=url)

            if raw_result.get("placa") or raw_result.get("results"):

                break

        except RuntimeError:

            continue  # Tenta próxima

    if not raw_result["placa"] and not raw_result["results"]:

        return JSONResponse(
            status_code=404, content={"erro": "Nenhuma placa detectada"}
        )

    # === Etapa 3: Salva resultado em disco ===

    try:

        if file_id:

            with open(
                os.path.join(YOLO_OUTPUT_DIR, file_id, f"{file_id}.txt"),
                "w",
                encoding="utf-8",
            ) as f:

                json.dump(raw_result, f, ensure_ascii=False, indent=2)

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"erro": "Erro ao salvar resultado em disco", "detalhe": str(e)},
        )

    # === Etapa 4: Retorna resultado ao cliente ===

    try:

        top_result = raw_result["results"][0]

        placa = top_result["plate"]

        alternativas = []

        if "candidates" in top_result:

            alternativas = [
                c["plate"] for c in top_result["candidates"] if c["plate"] != placa
            ]

        return {"placa": placa, "alternativas": alternativas}

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={"erro": "Erro ao processar resultado", "detalhe": str(e)},
        )
