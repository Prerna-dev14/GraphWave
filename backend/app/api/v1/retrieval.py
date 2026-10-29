"""API endpoints for Vector, Graph, and Hybrid Retrieval."""
from fastapi import APIRouter, status

from app.schemas.retrieval_schemas import RetrieveRequest, EvidenceBundleResponse
from app.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/api/v1", tags=["Retrieval"])


@router.post("/retrieve", response_model=EvidenceBundleResponse, status_code=status.HTTP_200_OK)
async def retrieve_evidence(req: RetrieveRequest):
    """Executes multi-hop retrieval and returns an evidence bundle with vector seeds, graph paths, and fused chunks."""
    bundle = await retrieval_service.retrieve(req)
    return bundle
