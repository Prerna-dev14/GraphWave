"""Schemas for schema-constrained Entity & Relation Extraction."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.ontology import EntityType, RelationType


class ExtractedEntitySchema(BaseModel):
    name: str = Field(..., min_length=1, description="Entity name or mention")
    entity_type: EntityType = Field(..., description="Ontology entity type")
    description: Optional[str] = Field(default=None, description="Brief contextual description")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class ExtractedRelationSchema(BaseModel):
    subject: str = Field(..., min_length=1, description="Subject entity name")
    subject_type: EntityType = Field(..., description="Subject entity type")
    relation: RelationType = Field(..., description="Typed directed relation from ontology")
    object: str = Field(..., min_length=1, description="Object entity name")
    object_type: EntityType = Field(..., description="Object entity type")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    evidence_quote: str = Field(..., description="Exact textual excerpt supporting this relation")


class RawExtractionPayload(BaseModel):
    """Raw structured extraction emitted by the LLM."""
    entities: List[ExtractedEntitySchema] = Field(default_factory=list)
    relations: List[ExtractedRelationSchema] = Field(default_factory=list)


class ClaimValidationReport(BaseModel):
    subject: str
    relation: str
    object: str
    confidence: float
    is_valid: bool
    status: str  # "VALIDATED", "REJECTED_SCHEMA", "REJECTED_CONFIDENCE"
    reason: Optional[str] = None
    evidence_quote: str


class ExtractionRunResponse(BaseModel):
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    model_name: str
    validated_claims: List[ClaimValidationReport]
    rejected_claims: List[ClaimValidationReport]
    total_extracted: int
    validated_count: int
    rejected_count: int
    execution_time_ms: float


class DirectExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text chunk to extract claims from")
    section_header: Optional[str] = Field(default=None, description="Section context")
    confidence_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
