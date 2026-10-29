"""Document Ingestion and Retrieval endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.core.errors import DocumentNotFoundError
from app.schemas.document_schemas import (
    DocumentIngestRequest,
    DocumentResponse,
    DocumentListResponse,
    ChunkResponse,
    IngestionJobResponse,
)
from app.services.ingestion_service import ingestion_service
from app.repositories.postgres_repository import postgres_repo

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("", response_model=IngestionJobResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(req: DocumentIngestRequest):
    """Ingest a new document with parsing, deterministic chunking, and candidate claim extraction."""
    tenant_id = req.tenant_id or settings.DEFAULT_TENANT_ID
    corpus_id = req.corpus_id or settings.DEFAULT_CORPUS_ID

    document, job = await ingestion_service.ingest_document(
        filename=req.filename,
        content=req.content,
        version=req.version,
        content_type=req.content_type,
        tenant_id=tenant_id,
        corpus_id=corpus_id,
        metadata=req.metadata,
    )

    return IngestionJobResponse(
        job_id=job.id,
        document_id=document.id,
        filename=document.filename,
        status=job.status,
        chunk_count=job.chunk_count,
        extracted_entities_count=job.extracted_entities_count,
        extracted_relations_count=job.extracted_relations_count,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents(
    tenant_id: str = Query(default=settings.DEFAULT_TENANT_ID),
    corpus_id: str = Query(default=settings.DEFAULT_CORPUS_ID),
):
    """List documents visible within the authorized tenant and corpus scope."""
    docs = await postgres_repo.list_documents(tenant_id, corpus_id)
    doc_responses = []
    for d in docs:
        chunks = await postgres_repo.get_chunks_for_document(d.id)
        doc_responses.append(
            DocumentResponse(
                id=d.id,
                tenant_id=d.tenant_id,
                corpus_id=d.corpus_id,
                filename=d.filename,
                content_type=d.content_type,
                version=d.version,
                chunk_count=len(chunks),
                metadata=d.metadata,
                created_at=d.created_at,
            )
        )

    return DocumentListResponse(
        documents=doc_responses,
        total_count=len(doc_responses),
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    tenant_id: str = Query(default=settings.DEFAULT_TENANT_ID),
    corpus_id: str = Query(default=settings.DEFAULT_CORPUS_ID),
):
    """Retrieve document metadata by document ID within scope."""
    doc = await postgres_repo.get_document(document_id, tenant_id, corpus_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found within scope {tenant_id}/{corpus_id}",
        )
    chunks = await postgres_repo.get_chunks_for_document(doc.id)
    return DocumentResponse(
        id=doc.id,
        tenant_id=doc.tenant_id,
        corpus_id=doc.corpus_id,
        filename=doc.filename,
        content_type=doc.content_type,
        version=doc.version,
        chunk_count=len(chunks),
        metadata=doc.metadata,
        created_at=doc.created_at,
    )


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse], status_code=status.HTTP_200_OK)
async def get_document_chunks(
    document_id: str,
    tenant_id: str = Query(default=settings.DEFAULT_TENANT_ID),
    corpus_id: str = Query(default=settings.DEFAULT_CORPUS_ID),
):
    """Inspect deterministic chunks and section metadata for a document."""
    doc = await postgres_repo.get_document(document_id, tenant_id, corpus_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    chunks = await postgres_repo.get_chunks_for_document(doc.id)
    return [
        ChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            text=c.text,
            section_header=c.section_header,
            page_number=c.page_number,
            created_at=c.created_at,
        )
        for c in chunks
    ]
