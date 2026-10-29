"""Deterministic Provenance Tracking and Identification for GraphWeave."""
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


def slugify_entity(text: str) -> str:
    """Normalize entity name into an identifier slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text)


def compute_document_id(tenant_id: str, corpus_id: str, filename: str, content: str) -> str:
    """Generates a stable SHA-256 identifier for a document based on its scope, name, and content."""
    payload = f"{tenant_id}:{corpus_id}:{filename}:{content}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


def compute_chunk_id(doc_id: str, version: str, chunk_index: int, chunk_text: str) -> str:
    """Generates a deterministic chunk ID preserving document version and sequence."""
    chunk_hash = hashlib.sha256(chunk_text.strip().encode("utf-8")).hexdigest()[:8]
    clean_version = re.sub(r"[^\w]", "_", version)
    return f"doc_{doc_id[:12]}_v{clean_version}_chunk_{chunk_index:04d}_{chunk_hash}"


def compute_canonical_entity_id(entity_type: str, name: str) -> str:
    """Computes a canonical entity ID scoped by entity type."""
    type_prefix = entity_type.lower()[:3]
    return f"{type_prefix}:{slugify_entity(name)}"


class ProvenanceRecord(BaseModel):
    """Complete lineage and provenance for any extracted claim, chunk, or relationship."""
    tenant_id: str = Field(..., description="Multi-tenant isolation boundary")
    corpus_id: str = Field(..., description="Document collection/corpus scope")
    document_id: str = Field(..., description="Deterministic source document ID")
    document_name: str = Field(..., description="Source document filename or title")
    document_version: str = Field(default="1.0", description="Version string of source document")
    chunk_id: str = Field(..., description="Deterministic source chunk ID")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    section_header: Optional[str] = Field(default=None, description="Enclosing Markdown/Document section")
    char_span: Optional[List[int]] = Field(default=None, description="[start, end] char offsets in source chunk")
    extraction_model: str = Field(default="mock", description="LLM/pipeline model that extracted this fact")
    extraction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of extraction",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
