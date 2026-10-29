"""GraphWeave Core Domain Models."""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.domain.ontology import EntityType, RelationType
from app.domain.provenance import ProvenanceRecord


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PARSED = "PARSED"
    EXTRACTING = "EXTRACTING"
    INDEXED = "INDEXED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClaimStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class Document(BaseModel):
    id: str = Field(..., description="Deterministic document ID")
    tenant_id: str
    corpus_id: str
    filename: str
    content_type: str = "text/markdown"
    version: str = "1.0"
    raw_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Chunk(BaseModel):
    id: str = Field(..., description="Deterministic chunk ID")
    document_id: str
    tenant_id: str
    corpus_id: str
    chunk_index: int
    text: str
    section_header: Optional[str] = None
    page_number: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Entity(BaseModel):
    canonical_id: str
    name: str
    entity_type: EntityType
    tenant_id: str
    corpus_id: str
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    confidence: float = 1.0


class CandidateClaim(BaseModel):
    """An extracted relationship treated as a candidate claim with explicit provenance."""
    id: str
    tenant_id: str
    corpus_id: str
    subject_entity: str
    subject_type: EntityType
    relation: RelationType
    object_entity: str
    object_type: EntityType
    confidence: float = Field(ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.CANDIDATE
    provenance: ProvenanceRecord
    evidence_text: str


class IngestionJob(BaseModel):
    id: str
    tenant_id: str
    corpus_id: str
    document_id: str
    filename: str
    status: JobStatus = JobStatus.PENDING
    chunk_count: int = 0
    extracted_entities_count: int = 0
    extracted_relations_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
