"""API endpoints for Canonical Entities, Aliases, and Ambiguity Review."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.schemas.resolution_schemas import CanonicalEntityResponse, AmbiguousMatch, ManualResolveRequest
from app.services.entity_resolution_service import entity_resolution_service

router = APIRouter(prefix="/api/v1/entities", tags=["Entities & Resolution"])


@router.get("", response_model=List[CanonicalEntityResponse], status_code=status.HTTP_200_OK)
async def list_canonical_entities(
    tenant_id: str = Query(default=settings.DEFAULT_TENANT_ID),
    corpus_id: str = Query(default=settings.DEFAULT_CORPUS_ID),
):
    """List canonical entities with their alias mappings and mention frequencies in scope."""
    from datetime import datetime, timezone
    entities_with_counts = entity_resolution_service.list_canonical_entities(tenant_id, corpus_id)
    return [
        CanonicalEntityResponse(
            canonical_id=e.canonical_id,
            name=e.name,
            entity_type=e.entity_type,
            tenant_id=e.tenant_id,
            corpus_id=e.corpus_id,
            aliases=e.aliases,
            mention_count=cnt,
            created_at=datetime.now(timezone.utc),
        )
        for e, cnt in entities_with_counts
    ]


@router.get("/ambiguities", response_model=List[AmbiguousMatch], status_code=status.HTTP_200_OK)
async def list_ambiguous_matches(
    status_filter: Optional[str] = Query(default="PENDING_REVIEW")
):
    """Fetch queued ambiguous entity matches awaiting human review."""
    return entity_resolution_service.list_ambiguities(status=status_filter)


@router.post("/resolve", response_model=AmbiguousMatch, status_code=status.HTTP_200_OK)
async def resolve_ambiguous_match(req: ManualResolveRequest):
    """Manually approve or reject an ambiguous entity merge."""
    updated = await entity_resolution_service.resolve_ambiguity(req.match_id, req.action)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ambiguity match '{req.match_id}' not found",
        )
    return updated
