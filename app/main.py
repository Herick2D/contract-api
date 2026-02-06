import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .api.endpoints import templates_router, contracts_router, prints_router
from .models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.setup_directories()
    logger.info(f"{settings.app_name} v{settings.app_version} iniciando...")
    logger.info(f"Storage: {settings.storage_dir}")
    logger.info(f"Prints: {settings.prints_dir}")

    yield

    logger.info("   Aplicação encerrando...")


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description="",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Templates", "description": "Gerenciamento de templates Word"},
        {
            "name": "Prints",
            "description": "Gerenciamento de imagens das cláusulas contratuais",
        },
        {
            "name": "Contracts",
            "description": "Processamento de contratos e geração de documentos",
        },
        {"name": "Health", "description": "Verificação de saúde da API"},
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "Ocorreu um erro interno",
            "timestamp": datetime.now().isoformat(),
        },
    )


app.include_router(templates_router, prefix="/api/v1")
app.include_router(prints_router, prefix="/api/v1")
app.include_router(contracts_router, prefix="/api/v1")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Verifica se a API está funcionando",
)
async def health_check():
    return HealthResponse(status="healthy", version=settings.app_version)


@app.get("/", tags=["Health"], summary="Root", description="Informações básicas da API")
async def root():

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
