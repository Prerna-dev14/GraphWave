"""Pydantic schemas for the Phase 6 evaluation benchmark and comparison harness."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TestCaseResult(BaseModel):
    """Evaluation result for a single benchmark test case question."""
    test_case_id: str
    category: str
    hops: int
    question: str
    retrieval_mode: str
    evidence_recall: float = Field(..., ge=0.0, le=1.0, description="Proportion of ground-truth evidence chunks retrieved")
    citation_precision: float = Field(..., ge=0.0, le=1.0, description="Proportion of citations that are grounded in valid evidence")
    answer_correctness: float = Field(..., ge=0.0, le=1.0, description="Semantic correctness score against expected criteria")
    latency_ms: float = Field(..., description="Total execution latency in milliseconds")
    token_cost_usd: float = Field(..., description="Estimated token cost in USD")
    retrieved_chunks_count: int
    traversed_paths_count: int
    generated_answer: str
    expected_answer: str
    passed: bool
    notes: Optional[str] = None


class EvaluationRunRequest(BaseModel):
    """Request parameters for triggering an evaluation run."""
    retrieval_mode: Optional[str] = Field(
        default=None,
        description="Retrieval mode to benchmark: 'vector_only', 'graph_only', 'hybrid', or null for comparative run",
    )
    max_depth: int = Field(default=2, ge=1, le=4, description="Max graph traversal depth")
    max_fan_out: int = Field(default=15, ge=1, le=50, description="Max neighbor expansion per entity")
    tenant_id: str = Field(default="tenant-default", description="Tenant isolation boundary")
    corpus_id: str = Field(default="corpus-primary", description="Corpus identifier")


class EvaluationRunResponse(BaseModel):
    """Summary and details of an evaluation run across the benchmark dataset."""
    id: str
    evaluation_dataset_version: str
    retrieval_mode: str
    answer_correctness: float
    evidence_recall: float
    citation_precision: float
    latency_p50_ms: float
    latency_p95_ms: float
    token_cost_usd: float
    total_questions: int
    metrics_detail: List[TestCaseResult] = Field(default_factory=list)
    created_at: str


class EvaluationComparisonResponse(BaseModel):
    """Comparative report contrasting vector-only, graph-only, and hybrid GraphRAG."""
    dataset_version: str
    timestamp: str
    runs: List[EvaluationRunResponse]
    recommended_mode: str
    analysis_summary: str
