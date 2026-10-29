"""Health endpoints for process liveness and dependency readiness."""
from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.schemas.health_schemas import LiveHealthResponse, ReadyHealthResponse, ServiceDependencyStatus
from app.repositories.postgres_repository import postgres_repo
from app.repositories.neo4j_repository import neo4j_repo

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=LiveHealthResponse, status_code=status.HTTP_200_OK)
async def check_liveness():
    """Returns process liveness."""
    return LiveHealthResponse(
        status="live",
        service="GraphWeave",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health/ready", response_model=ReadyHealthResponse, status_code=status.HTTP_200_OK)
async def check_readiness():
    """Checks PostgreSQL and Neo4j dependency readiness."""
    pg_health = await postgres_repo.check_health()
    neo_health = await neo4j_repo.check_health()

    dependencies = {
        "postgresql": ServiceDependencyStatus(
            status=pg_health.get("status", "unhealthy"),
            latency_ms=pg_health.get("latency_ms"),
            details=pg_health.get("details") or pg_health.get("mode"),
        ),
        "neo4j": ServiceDependencyStatus(
            status=neo_health.get("status", "unhealthy"),
            latency_ms=neo_health.get("latency_ms"),
            details=neo_health.get("details") or neo_health.get("mode"),
        ),
    }

    is_ready = all(d.status in ("healthy", "degraded") for d in dependencies.values())

    return ReadyHealthResponse(
        status="ready" if is_ready else "not_ready",
        service="GraphWeave",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        dependencies=dependencies,
    )
