from pydantic import BaseModel, Field
from typing import List, Optional


class OCRResultItem(BaseModel):
    plate: str
    # Se seus OCRs retornam confiança, adicione aqui
    # confidence: Optional[float] = None
    # Se retornarem candidatos, adicione aqui
    candidates: Optional[List[dict]] = None


class PlateOCRRawResult(BaseModel):
    # Campo 'placa' para compatibilidade com o formato antigo, se necessário
    placa: Optional[str] = None
    results: List[OCRResultItem] = Field(default_factory=list)


class PlateProcessResponse(BaseModel):
    placa: str
    alternativas: List[str] = Field(default_factory=list)