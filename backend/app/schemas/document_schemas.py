"""Pydantic schemas for Document Ingestion and Job status API."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.models import JobStatus


class DocumentIngestRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    content: str = Field(..., min_length=1, description="Raw text or markdown document content")
    version: str = Field(default="1.0", max_length=32, description="Semantic document version")
    content_type: str = Field(default="text/markdown", description="MIME content type")
    tenant_id: Optional[str] = Field(default=None, description="Tenant override")
    corpus_id: Optional[str] = Field(default=None, description="Corpus override")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    text: str
    section_header: Optional[str] = None
    page_number: Optional[int] = None
    created_at: datetime


class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    corpus_id: str
    filename: str
    content_type: str
    version: str
    chunk_count: int
    metadata: Dict[str, Any]
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    tenant_id: str
    corpus_id: str


class IngestionJobResponse(BaseModel):
    job_id: str
    document_id: str
    filename: str
    status: JobStatus
    chunk_count: int
    extracted_entities_count: int
    extracted_relations_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
