"""Schemas for Entity Resolution, Aliases, and Ambiguity Review."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.ontology import EntityType


class CanonicalEntityResponse(BaseModel):
    canonical_id: str
    name: str
    entity_type: EntityType
    tenant_id: str
    corpus_id: str
    aliases: List[str]
    mention_count: int
    created_at: datetime


class AmbiguousMatch(BaseModel):
    id: str
    mention_a: str
    type_a: EntityType
    canonical_id_a: str
    mention_b: str
    type_b: EntityType
    canonical_id_b: str
    similarity_score: float
    status: str = "PENDING_REVIEW"  # PENDING_REVIEW, APPROVED, REJECTED
    reason: str
    created_at: datetime


class ManualResolveRequest(BaseModel):
    match_id: str
    action: str = Field(..., description="'APPROVE_MERGE' or 'REJECT_MERGE'")
    target_canonical_id: Optional[str] = None
