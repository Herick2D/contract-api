"""
Contract Generator API
======================

API REST para geração de documentos contratuais a partir de templates Word e dados Excel.

Desenvolvido para transformar uma aplicação desktop em serviço web.
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .api.endpoints import templates_router, contracts_router, prints_router
from .models.schemas import HealthResponse, ErrorResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    # Startup
    settings = get_settings()
    settings.setup_directories()
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} iniciando...")
    logger.info(f"📁 Storage: {settings.storage_dir}")
    logger.info(f"🖼️ Prints: {settings.prints_dir}")
    
    yield
    
    # Shutdown
    logger.info("👋 Aplicação encerrando...")


# Cria aplicação FastAPI
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="""
## API de Geração de Contratos

Esta API permite:

- 📝 **Gerenciar Templates**: Upload e gerenciamento de modelos Word (.docx)
- 🖼️ **Gerenciar Prints**: Upload de imagens das cláusulas contratuais
- 📊 **Processar Contratos**: Upload de planilhas Excel com dados dos contratos
- 📦 **Gerar Documentos**: Geração em lote de documentos preenchidos
- ⬇️ **Download**: Obter ZIP com todos os documentos gerados

### Fluxo de Uso

1. **Cadastrar Template**: Faça upload do modelo Word com os placeholders
2. **Enviar Prints**: Faça upload das imagens das cláusulas (opcional)
3. **Enviar Excel**: Faça upload da planilha com os dados dos contratos
4. **Processar**: A API preenche cada contrato no template
5. **Download**: Baixe o ZIP com todos os documentos gerados

### Autores

Transformação de aplicação desktop em API REST.
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Templates",
            "description": "Gerenciamento de templates Word"
        },
        {
            "name": "Prints",
            "description": "Gerenciamento de imagens das cláusulas contratuais"
        },
        {
            "name": "Contracts",
            "description": "Processamento de contratos e geração de documentos"
        },
        {
            "name": "Health",
            "description": "Verificação de saúde da API"
        }
    ]
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "Ocorreu um erro interno",
            "timestamp": datetime.now().isoformat()
        }
    )


# Routers
app.include_router(templates_router, prefix="/api/v1")
app.include_router(prints_router, prefix="/api/v1")
app.include_router(contracts_router, prefix="/api/v1")


# Health Check
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Verifica se a API está funcionando"
)
async def health_check():
    """Endpoint de health check"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version
    )


@app.get(
    "/",
    tags=["Health"],
    summary="Root",
    description="Informações básicas da API"
)
async def root():
    """Endpoint raiz"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Para rodar diretamente com: python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
