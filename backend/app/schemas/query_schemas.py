"""Schemas for End-to-End Query and Answer Synthesis API."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.retrieval_schemas import RetrievalMode, TraversedEdgeSchema


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    section_header: Optional[str] = None
    snippet: str
    document_version: str = "1.0"


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language question")
    mode: RetrievalMode = Field(default=RetrievalMode.HYBRID, description="Retrieval strategy: hybrid, vector, or graph")
    tenant_id: Optional[str] = Field(default=None)
    corpus_id: Optional[str] = Field(default=None)
    max_depth: int = Field(default=2, ge=1, le=3)
    max_fan_out: int = Field(default=15, ge=1, le=50)


class QueryMetrics(BaseModel):
    latency_vector_ms: float
    latency_graph_ms: float
    latency_fusion_ms: float
    latency_generation_ms: float
    latency_total_ms: float
    fused_chunks_count: int
    graph_edges_count: int
    citations_count: int
    estimated_cost_usd: float = 0.0


class QueryResponse(BaseModel):
    query: str
    answer: str
    mode: RetrievalMode
    tenant_id: str
    corpus_id: str
    trace_id: str
    citations: List[Citation]
    graph_paths: List[TraversedEdgeSchema]
    metrics: QueryMetrics
    created_at: str


class RequestTraceResponse(BaseModel):
    request_id: str
    tenant_id: str
    corpus_id: str
    query_text: str
    retrieval_mode: str
    retrieved_chunk_count: int
    traversed_graph_nodes_count: int
    latency_total_ms: float
    latency_retrieval_ms: float
    latency_generation_ms: float
    created_at: str
