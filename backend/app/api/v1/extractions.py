"""API endpoints for Entity & Relation Extraction and audit logs."""
from typing import List
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.schemas.extraction_schemas import DirectExtractRequest, ExtractionRunResponse
from app.services.extraction_service import extraction_service
from app.repositories.postgres_repository import postgres_repo

router = APIRouter(prefix="/api/v1", tags=["Extraction"])


@router.post("/extract", response_model=ExtractionRunResponse, status_code=status.HTTP_200_OK)
async def direct_extract_claims(req: DirectExtractRequest):
    """Run schema-constrained entity and relation extraction directly on raw text with validation reporting."""
    _, run_response = await extraction_service.extract_and_validate(
        chunk_text=req.text,
        section_header=req.section_header,
        confidence_threshold_override=req.confidence_threshold,
    )
    return run_response


@router.get("/documents/{document_id}/extractions", response_model=List[ExtractionRunResponse], status_code=status.HTTP_200_OK)
async def get_document_extractions(document_id: str):
    """Fetch extraction audit history for a document."""
    runs = await postgres_repo.get_extraction_runs_for_document(document_id)
    responses = []
    for r in runs:
        responses.append(
            ExtractionRunResponse(
                document_id=r.document_id,
                chunk_id=r.chunk_id,
                model_name=r.model_name,
                validated_claims=[],
                rejected_claims=[],
                total_extracted=r.validated_claims_count + r.rejected_claims_count,
                validated_count=r.validated_claims_count,
                rejected_count=r.rejected_claims_count,
                execution_time_ms=r.execution_time_ms,
            )
        )
    return responses


@router.get("/documents/{document_id}/claims", status_code=status.HTTP_200_OK)
async def get_document_candidate_claims(document_id: str):
    """Fetch all validated candidate claims and provenance anchors for an ingested document."""
    claims = await postgres_repo.get_candidate_claims_for_document(document_id)
    return [
        {
            "id": c.id,
            "subject": c.subject_entity,
            "subject_type": c.subject_type.value,
            "relation": c.relation.value,
            "object": c.object_entity,
            "object_type": c.object_type.value,
            "confidence": c.confidence,
            "status": c.status.value,
            "chunk_id": c.provenance.chunk_id,
            "section_header": c.provenance.section_header,
            "evidence_text": c.evidence_text,
        }
        for c in claims
    ]
