"""GraphWeave FastAPI Main Application."""
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger, correlation_id_ctx
from app.core.errors import GraphWeaveException, ErrorResponse
from app.repositories.postgres_repository import postgres_repo
from app.repositories.neo4j_repository import neo4j_repo
from app.api.v1.health import router as health_router
from app.api.v1.documents import router as documents_router
from app.api.v1.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database connections and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    # Initialize repositories
    await postgres_repo.connect()
    await neo4j_repo.connect()
    await neo4j_repo.ensure_schema_constraints()
    yield
    # Shutdown
    logger.info("Shutting down GraphWeave services...")
    await neo4j_repo.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="GraphRAG system for multi-hop questions across documents with explicit provenance.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_timing_middleware(request: Request, call_next):
    """Attaches a unique correlation ID to every request and logs component-level latency."""
    correlation_id = request.headers.get("X-Correlation-ID") or f"trace_{uuid.uuid4().hex[:12]}"
    token = correlation_id_ctx.set(correlation_id)

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} in {duration_ms:.2f}ms")
        return response
    finally:
        correlation_id_ctx.reset(token)


@app.exception_handler(GraphWeaveException)
async def graphweave_exception_handler(request: Request, exc: GraphWeaveException):
    correlation_id = correlation_id_ctx.get()
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.code,
            message=exc.message,
            details=exc.details,
            trace_id=correlation_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = correlation_id_ctx.get()
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred processing your request.",
            trace_id=correlation_id,
        ).model_dump(),
    )


# Register Routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(jobs_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
