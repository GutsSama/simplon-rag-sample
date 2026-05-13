from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import make_asgi_app

from rag.api.logging import configure_logging
from rag.api.routers import chat, chaos, eval, health, ingestion
from rag.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    # Initialize logging
    configure_logging()

    app = FastAPI(
        title="Simplon RAG Sample API",
        description="Sample RAG support chatbot API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware for request ID
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(ingestion.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(eval.router, prefix="/api/v1")
    app.include_router(chaos.router, prefix="/api/v1")  # Chaos engineering endpoints

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app)
    
    @app.get("/test-endpoint")
    def test_endpoint():
        return {"status": "ok"}

    return app
