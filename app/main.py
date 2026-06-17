import time
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.models.config import get_config
from app.models.database import create_tables
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers.auth_router import router as auth_router
from app.routers.agent_router import router as chat_router, ingest_router
from app.routers.eval_router import router as eval_router

config = get_config()
START_TIME = time.time()

# ─── Logging Setup ───────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
    level=config.log_level,
    serialize=config.app_env == "production",
)
logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🍷 Wine Sommelier API starting (env={config.app_env})")
    create_tables()
    logger.info("Database tables ready.")
    yield
    logger.info("🍷 Wine Sommelier API shutting down.")


# ─── App Factory ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="🍷 Wine Sommelier AI",
    description="Agentic RAG-powered personal wine sommelier with JWT auth, conversation memory, and LLM-as-judge evaluation.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

# Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(eval_router)


# ─── Health & Metrics ────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
def health():
    from app.utils.ocr_utils import ocr_is_available
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "database": "ok",
            "ocr": "ok" if ocr_is_available() else "unavailable",
        },
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/", tags=["System"], summary="Root")
def root():
    return {
        "message": "🍷 Wine Sommelier AI v2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
