"""Ingestion job tracking endpoints."""
from fastapi import APIRouter, HTTPException, status
from app.schemas.document_schemas import IngestionJobResponse
from app.repositories.postgres_repository import postgres_repo

router = APIRouter(prefix="/api/v1/ingestion-jobs", tags=["Ingestion Jobs"])


@router.get("/{job_id}", response_model=IngestionJobResponse, status_code=status.HTTP_200_OK)
async def get_ingestion_job(job_id: str):
    """Fetch status and statistics for an ingestion job."""
    job = await postgres_repo.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found",
        )
    return IngestionJobResponse(
        job_id=job.id,
        document_id=job.document_id,
        filename=job.filename,
        status=job.status,
        chunk_count=job.chunk_count,
        extracted_entities_count=job.extracted_entities_count,
        extracted_relations_count=job.extracted_relations_count,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
