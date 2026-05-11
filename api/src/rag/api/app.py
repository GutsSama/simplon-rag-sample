from contextlib import asynccontextmanager

from fastapi import FastAPI

from rag.api.routers import chat, eval, explain, feedback, health, ingestion, predict
from rag.config.settings import get_settings
from rag.db.session import engine


import uuid
import time
import logging
from fastapi import Request
from rag.api.logging_config import setup_logging, request_id_var
from rag.api.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS, router as metrics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.app_log_level)
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title="MailGuard Observability API",
        description="Observable API for spam classification and RAG explanation",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Record metrics
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, 
            endpoint=request.url.path, 
            status=response.status_code
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method, 
            endpoint=request.url.path
        ).observe(process_time)
        
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            f"Request processed", 
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": process_time
            }
        )
        
        request_id_var.reset(token)
        return response

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(ingestion.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(eval.router, prefix="/api/v1")
    app.include_router(predict.router, prefix="/api/v1")
    app.include_router(explain.router, prefix="/api/v1")
    app.include_router(feedback.router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")

    return app
