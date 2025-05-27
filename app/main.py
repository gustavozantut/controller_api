from fastapi import FastAPI
from app.api.v1.endpoints import api_keys, plates  # Importe os routers

app = FastAPI(
    title="BRPlates API - Processamento de Placas",
    description="API para detecção de placas via YOLO e leitura via OCRs, com autenticação por chave de API e limite de chamadas.",
    version="1.0.0",
    # Adicione tags para organizar a documentação Swagger UI
    openapi_tags=[
        {"name": "API Keys", "description": "Operações para gerenciar chaves de API."},
        {
            "name": "Plates",
            "description": "Operações de processamento de imagens de placas.",
        },
    ],
)

# Inclua os routers de API
# As rotas de chaves de API estarão em /api/v1/keys
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])
# As rotas de processamento de placas estarão em /api/v1/processar-placa
app.include_router(plates.router, prefix="/api/v1", tags=["Plates"])


# Opcional: Rota raiz para verificar se a API está online
@app.get("/", tags=["Status"], summary="Verifica o status da API")
async def read_root():
    return {"message": "BRPlates API está online!"}
