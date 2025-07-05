import os
import json
import requests
from typing import Dict, Union, List, Optional
from fastapi import UploadFile

from app.core.config import settings
from app.schemas.plate import PlateOCRRawResult, OCRResultItem  # Importe os schemas


class PlateService:
    def __init__(self):
        self.YOLO_API_URL = settings.YOLO_API_URL
        self.OCR_API_URL = settings.OCR_API_URL
        self.EZOCR_API_URL = settings.EZOCR_API_URL
        self.YOLO_OUTPUT_DIR = settings.YOLO_OUTPUT_DIR

    def _padronizar_resultado_ocr_bruto(
        self, resultado_ocr: Dict | str
    ) -> PlateOCRRawResult:
        """
        Função auxiliar para padronizar o resultado vindo dos OCRs.
        """
        if isinstance(resultado_ocr, dict):
            # OCR antigo: {"resultado": "<json_string>"}
            if "resultado" in resultado_ocr:
                try:
                    parsed = json.loads(resultado_ocr["resultado"])
                    results = parsed.get("results", [])
                    # Mapeia resultados para o schema OCRResultItem
                    parsed_results = [OCRResultItem(**item) for item in results]
                    placa = parsed_results[0].plate if parsed_results else None
                    return PlateOCRRawResult(placa=placa, results=parsed_results)
                except json.JSONDecodeError:
                    return PlateOCRRawResult(placa=None, results=[])

            # ezOCR: {"results": [...]}
            if "results" in resultado_ocr:
                results = resultado_ocr["results"]
                # Mapeia resultados para o schema OCRResultItem
                parsed_results = [OCRResultItem(**item) for item in results]
                placa = parsed_results[0].plate if parsed_results else None
                return PlateOCRRawResult(placa=placa, results=parsed_results)

        return PlateOCRRawResult(placa=None, results=[])

    def _chamar_ocr(
        self,
        crop_bytes: bytes,
        categoria: Optional[str] = None,
        anpr_api_url: str = None,
    ) -> PlateOCRRawResult:
        """
        Função auxiliar para fazer a chamada a um serviço OCR.
        """
        data = {"categoria": categoria} if categoria else {}
        try:
            resp = requests.post(
                anpr_api_url,
                files={
                    "file": ("input.jpg", crop_bytes, "image/jpeg")
                },  # Adicione o mimetype
                data=data,
                timeout=30,  # Adicione timeout para evitar requisições presas
            )
            resp.raise_for_status()  # Lança HTTPError para respostas 4xx/5xx
            return self._padronizar_resultado_ocr_bruto(resp.json())
        except requests.exceptions.RequestException as e:
            # Captura erros de requisição (conexão, timeout, HTTPError)
            raise RuntimeError(f"OCR falhou: {anpr_api_url} - {str(e)}")
        except Exception as e:
            # Captura outros erros inesperados
            raise RuntimeError(f"Erro inesperado no OCR: {str(e)}")

    async def process_plate_image(self, file: UploadFile) -> PlateOCRRawResult:
        """
        Processa uma imagem para detectar e ler a placa.
        """
        original_bytes = await file.read()
        file_id = None
        classe_detectada = None
        crop_bytes = None
        yolo_result_bytes = original_bytes  # Inicializa com a imagem original
        yolo_detected = False  # Flag para saber se o YOLO detectou algo

        # === Etapa 1: Envia imagem ao YOLO ===
        try:
            yolo_resp = requests.post(
                self.YOLO_API_URL,
                files={"file": (file.filename, original_bytes, file.content_type)},
                timeout=30,  # Adicione timeout
            )
            if yolo_resp.status_code == 404:
                pass
            elif not yolo_resp.ok:  # Verifica se o status code NÃO é 2xx
                yolo_resp.raise_for_status()

            yolo_json = yolo_resp.json()

            crop_path = None
            if "arquivo" in yolo_json:
                crop_path = yolo_json["arquivo"]
            elif "file_id" in yolo_json:
                crop_path = os.path.join(
                    self.YOLO_OUTPUT_DIR,
                    yolo_json["file_id"],
                    f"{yolo_json['file_id']}.jpg",
                )

            if not crop_path:
                raise ValueError(
                    "Resposta do YOLO não continha um caminho de recorte válido."
                )

            file_id = yolo_json.get("file_id")
            classe_detectada = yolo_json.get("classe")

            # Abre o arquivo de imagem recortado (assumindo que YOLO salva no disco compartilhado)
            if not os.path.exists(crop_path):
                raise FileNotFoundError(f"Imagem recortada não encontrada: {crop_path}")

            with open(crop_path, "rb") as f:
                crop_bytes = f.read()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"YOLO falhou na comunicação: {str(e)}")
        except FileNotFoundError as e:
            raise RuntimeError(f"Erro ao ler recorte do YOLO: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Falha inesperada ao processar YOLO: {str(e)}")

        # === Etapa 2: Tentativas com ezOCR e OCR, com e sem categoria ===
        tentativa_urls = [
            (self.EZOCR_API_URL, classe_detectada),
            (self.OCR_API_URL, classe_detectada),
            (self.EZOCR_API_URL, None),
            (self.OCR_API_URL, None),
        ]

        raw_result = PlateOCRRawResult(
            placa=None, results=[]
        )  # Inicializa com valor padrão
        for url, categoria in tentativa_urls:
            try:
                raw_result = self._chamar_ocr(
                    crop_bytes, categoria=categoria, anpr_api_url=url
                )
                if (
                    raw_result.placa or raw_result.results
                ):  # Se encontrou alguma placa ou resultados
                    break
            except RuntimeError as e:
                print(
                    f"Tentativa OCR falhou com {url} (categoria: {categoria}): {e}"
                )  # Logar o erro
                continue  # Tenta a próxima opção

        if not raw_result.placa and not raw_result.results:
            # Se nenhuma das tentativas de OCR retornou resultados válidos
            return PlateOCRRawResult(placa=None, results=[])

        # === Etapa 3: Salva resultado em disco (opcional, pode ser movido para outro serviço) ===
        try:
            if (
                file_id and raw_result.placa
            ):  # Salva apenas se houver um file_id e uma placa detectada
                output_dir_for_file = os.path.join(self.YOLO_OUTPUT_DIR, file_id)
                os.makedirs(
                    output_dir_for_file, exist_ok=True
                )  # Garante que o diretório exista
                with open(
                    os.path.join(output_dir_for_file, f"{file_id}.txt"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    # Use .model_dump() para Pydantic v2
                    json.dump(
                        raw_result.model_dump(mode="json"),
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
        except Exception as e:
            print(
                f"ATENÇÃO: Erro ao salvar resultado em disco para {file_id}: {str(e)}"
            )
            # Não lança exceção fatal, apenas registra o erro

        return raw_result
