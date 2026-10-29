"""API endpoints for Answer Synthesis and Request Diagnostics."""
from fastapi import APIRouter, HTTPException, status

from app.schemas.query_schemas import QueryRequest, QueryResponse, RequestTraceResponse
from app.services.synthesis_service import synthesis_service
from app.repositories.postgres_repository import postgres_repo

router = APIRouter(prefix="/api/v1", tags=["Query & Synthesis"])


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def execute_query(req: QueryRequest):
    """Executes full end-to-end GraphRAG pipeline: retrieval, bounded graph expansion, answer synthesis, and citation grounding."""
    res = await synthesis_service.query(req)
    return res


@router.get("/requests/{request_id}", response_model=RequestTraceResponse, status_code=status.HTTP_200_OK)
async def get_request_trace(request_id: str):
    """Retrieve permitted request diagnostics and timing telemetry without exposing secrets or raw sensitive content."""
    trace = await postgres_repo.get_request_trace(request_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request trace '{request_id}' not found",
        )
    return RequestTraceResponse(**trace)
