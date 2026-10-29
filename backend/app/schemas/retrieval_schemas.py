"""Schemas for Vector, Graph, and Hybrid Retrieval Planner."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RetrievalMode(str, Enum):
    HYBRID = "hybrid"
    VECTOR_ONLY = "vector"
    GRAPH_ONLY = "graph"


class RetrievedChunkSchema(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    section_header: Optional[str] = None
    similarity_score: float
    source: str = "vector"  # "vector", "graph", or "fused"


class TraversedEdgeSchema(BaseModel):
    source_entity: str
    source_type: str
    relation: str
    target_entity: str
    target_type: str
    confidence: float
    hop: int
    source_chunk_ids: List[str]
    evidence_text: Optional[str] = None


class RetrievalMetricsSchema(BaseModel):
    latency_vector_ms: float
    latency_graph_ms: float
    latency_fusion_ms: float
    latency_total_ms: float
    seed_chunks_count: int
    graph_edges_count: int
    fused_chunks_count: int


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question or search query")
    mode: RetrievalMode = Field(default=RetrievalMode.HYBRID, description="Retrieval strategy")
    tenant_id: Optional[str] = Field(default=None)
    corpus_id: Optional[str] = Field(default=None)
    top_k_vector: int = Field(default=5, ge=1, le=20)
    max_depth: int = Field(default=2, ge=1, le=3)
    max_fan_out: int = Field(default=15, ge=1, le=50)


class EvidenceBundleResponse(BaseModel):
    query: str
    mode: RetrievalMode
    tenant_id: str
    corpus_id: str
    seed_chunks: List[RetrievedChunkSchema]
    graph_paths: List[TraversedEdgeSchema]
    fused_evidence_chunks: List[RetrievedChunkSchema]
    metrics: RetrievalMetricsSchema
