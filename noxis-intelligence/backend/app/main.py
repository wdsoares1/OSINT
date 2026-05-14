"""
NOXIS Intelligence - Main Application Entry Point
Aplicação FastAPI com configuração completa.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.logging_config import logger
from app.middleware.audit_logging import AuditLoggingMiddleware
from app.routers.search import router as search_router

# Importa modelos para criar tabelas
from app.models.schemas import AuditLog, Entity, Finding, InvestigationCase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    
    # Startup
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Cria tabelas no banco de dados (em produção, usar migrations)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas do banco de dados criadas/atualizadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info(f"Encerrando {settings.APP_NAME}")


# Cria aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## NOXIS Intelligence Platform

Plataforma automatizada de OSINT e investigação tática para órgãos de controle e corregedoria.

### Funcionalidades Principais:

- **Busca Multi-Fonte**: Consulta simultânea em Google Dorks, Portal da Transparência, BNMP/CNJ e Redes Sociais
- **Scraping Ético**: Utiliza Playwright e BeautifulSoup com rotação de User-Agents
- **Auditoria Completa**: Logs detalhados de todas as consultas com identificação do operador
- **Classificação de Risco**: Score automático baseado nos resultados encontrados
- **Persistência**: Armazenamento de entidades e descobertas no PostgreSQL

### Endpoints Principais:

- **POST /api/v1/search**: Realiza busca OSINT completa
    """,
    lifespan=lifespan,
)

# Configura CORS para permitir frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona middleware de auditoria
app.add_middleware(AuditLoggingMiddleware, db_session_factory=get_db)

# Registra routers
app.include_router(search_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificação de saúde da API"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": f"Bem-vindo ao {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
