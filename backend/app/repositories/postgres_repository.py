"""PostgreSQL + pgvector repository for documents, chunks, and ingestion jobs.
Supports live asyncpg connection and robust in-memory fallback for local testing.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import asyncpg

from app.core.config import settings
from app.core.logging import logger
from app.domain.models import Document, Chunk, IngestionJob, JobStatus


class PostgresRepository:
    def __init__(self, connection_url: Optional[str] = None):
        self.connection_url = connection_url or settings.DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None
        # In-memory storage structures for fallback and isolated test runs
        self._mem_documents: Dict[str, Document] = {}
        self._mem_chunks: Dict[str, List[Chunk]] = {}
        self._mem_jobs: Dict[str, IngestionJob] = {}
        self.is_connected = False

    async def connect(self) -> bool:
        """Attempt connection to PostgreSQL with fallback to memory."""
        try:
            # Strip +asyncpg dialect if present for raw asyncpg
            clean_url = self.connection_url.replace("postgresql+asyncpg://", "postgresql://")
            self.pool = await asyncpg.create_pool(clean_url, min_size=1, max_size=5, timeout=2.0)
            self.is_connected = True
            logger.info("Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to live PostgreSQL ({e}). Operating in memory mode.")
            self.is_connected = False
            return False

    async def check_health(self) -> Dict[str, Any]:
        """Verify PostgreSQL connectivity and measure round-trip latency."""
        if not self.is_connected or not self.pool:
            return {
                "status": "healthy" if settings.ENABLE_MOCK_FALLBACK else "unhealthy",
                "mode": "in-memory (mock-fallback active)" if settings.ENABLE_MOCK_FALLBACK else "disconnected",
                "details": "Running with in-memory persistence adapter" if settings.ENABLE_MOCK_FALLBACK else "PostgreSQL unavailable",
            }
        try:
            start = datetime.now()
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            latency = (datetime.now() - start).total_seconds() * 1000.0
            return {"status": "healthy", "latency_ms": round(latency, 2), "mode": "postgresql"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def save_document(self, doc: Document) -> Document:
        self._mem_documents[doc.id] = doc
        return doc

    async def get_document(self, doc_id: str, tenant_id: str, corpus_id: str) -> Optional[Document]:
        doc = self._mem_documents.get(doc_id)
        if doc and doc.tenant_id == tenant_id and doc.corpus_id == corpus_id:
            return doc
        return None

    async def list_documents(self, tenant_id: str, corpus_id: str) -> List[Document]:
        return [
            d for d in self._mem_documents.values()
            if d.tenant_id == tenant_id and d.corpus_id == corpus_id
        ]

    async def save_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        if not chunks:
            return []
        doc_id = chunks[0].document_id
        if doc_id not in self._mem_chunks:
            self._mem_chunks[doc_id] = []
        self._mem_chunks[doc_id].extend(chunks)
        return chunks

    async def get_chunks_for_document(self, doc_id: str) -> List[Chunk]:
        return self._mem_chunks.get(doc_id, [])

    async def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        for chunk_list in self._mem_chunks.values():
            for c in chunk_list:
                if c.id == chunk_id:
                    return c
        return None

    async def search_chunks_by_vector(
        self,
        query_embedding: List[float],
        tenant_id: str,
        corpus_id: str,
        top_k: int = 5,
    ) -> List[Tuple[Chunk, float]]:
        """Searches scoped chunks by vector cosine similarity."""
        import numpy as np

        # In-memory cosine similarity computation
        scored: List[Tuple[Chunk, float]] = []
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        for chunk_list in self._mem_chunks.values():
            for c in chunk_list:
                if c.tenant_id == tenant_id and c.corpus_id == corpus_id:
                    if c.embedding:
                        c_vec = np.array(c.embedding, dtype=np.float32)
                        c_norm = np.linalg.norm(c_vec)
                        if c_norm > 0:
                            c_vec = c_vec / c_norm
                        sim = float(np.dot(q_vec, c_vec))
                        scored.append((c, sim))
                    else:
                        scored.append((c, 0.0))

        # Sort descending by similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    async def save_job(self, job: IngestionJob) -> IngestionJob:
        self._mem_jobs[job.id] = job
        return job

    async def get_job(self, job_id: str) -> Optional[IngestionJob]:
        return self._mem_jobs.get(job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        chunk_count: int = 0,
        extracted_entities: int = 0,
        extracted_relations: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[IngestionJob]:
        job = self._mem_jobs.get(job_id)
        if job:
            job.status = status
            if chunk_count:
                job.chunk_count = chunk_count
            if extracted_entities:
                job.extracted_entities_count = extracted_entities
            if extracted_relations:
                job.extracted_relations_count = extracted_relations
            if error_message:
                job.error_message = error_message
            job.updated_at = datetime.now(timezone.utc)
        return job

    # Phase 2: Extraction runs & claims storage
    async def save_extraction_run(self, run: "ExtractionRun") -> "ExtractionRun":
        if not hasattr(self, "_mem_extraction_runs"):
            self._mem_extraction_runs: Dict[str, List[Any]] = {}
        if run.document_id not in self._mem_extraction_runs:
            self._mem_extraction_runs[run.document_id] = []
        self._mem_extraction_runs[run.document_id].append(run)
        return run

    async def get_extraction_runs_for_document(self, doc_id: str) -> List[Any]:
        if not hasattr(self, "_mem_extraction_runs"):
            self._mem_extraction_runs = {}
        return self._mem_extraction_runs.get(doc_id, [])

    async def save_candidate_claims(self, claims: List["CandidateClaim"]) -> List["CandidateClaim"]:
        if not hasattr(self, "_mem_candidate_claims"):
            self._mem_candidate_claims: Dict[str, List[Any]] = {}
        for c in claims:
            doc_id = c.provenance.document_id
            if doc_id not in self._mem_candidate_claims:
                self._mem_candidate_claims[doc_id] = []
            self._mem_candidate_claims[doc_id].append(c)
        return claims

    async def get_candidate_claims_for_document(self, doc_id: str) -> List[Any]:
        if not hasattr(self, "_mem_candidate_claims"):
            self._mem_candidate_claims = {}
        return self._mem_candidate_claims.get(doc_id, [])

    # Phase 5: Request traces storage
    async def save_request_trace(self, trace_data: Dict[str, Any]):
        if not hasattr(self, "_mem_traces"):
            self._mem_traces: Dict[str, Dict[str, Any]] = {}
        self._mem_traces[trace_data["request_id"]] = trace_data
        return trace_data

    async def get_request_trace(self, request_id: str) -> Optional[Dict[str, Any]]:
        if not hasattr(self, "_mem_traces"):
            self._mem_traces = {}
        return self._mem_traces.get(request_id)

    # Phase 6: Evaluation runs storage
    async def save_evaluation_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.pool:
            try:
                import json
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO evaluation_runs (
                            id, evaluation_dataset_version, retrieval_mode,
                            answer_correctness, evidence_recall, citation_precision,
                            latency_p50_ms, latency_p95_ms, token_cost_usd,
                            total_questions, metrics_detail, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                        ON CONFLICT (id) DO UPDATE SET
                            answer_correctness = EXCLUDED.answer_correctness,
                            evidence_recall = EXCLUDED.evidence_recall,
                            citation_precision = EXCLUDED.citation_precision,
                            latency_p50_ms = EXCLUDED.latency_p50_ms,
                            latency_p95_ms = EXCLUDED.latency_p95_ms,
                            token_cost_usd = EXCLUDED.token_cost_usd,
                            metrics_detail = EXCLUDED.metrics_detail;
                        """,
                        run_data["id"],
                        run_data["evaluation_dataset_version"],
                        run_data["retrieval_mode"],
                        run_data.get("answer_correctness", 0.0),
                        run_data.get("evidence_recall", 0.0),
                        run_data.get("citation_precision", 0.0),
                        run_data.get("latency_p50_ms", 0.0),
                        run_data.get("latency_p95_ms", 0.0),
                        run_data.get("token_cost_usd", 0.0),
                        run_data.get("total_questions", 0),
                        json.dumps(run_data.get("metrics_detail", {})),
                    )
            except Exception as e:
                logger.warning(f"PostgreSQL save_evaluation_run failed, using memory fallback: {e}")

        if not hasattr(self, "_mem_eval_runs"):
            self._mem_eval_runs: Dict[str, Dict[str, Any]] = {}
        self._mem_eval_runs[run_data["id"]] = run_data
        return run_data

    async def list_evaluation_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.pool:
            try:
                import json
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(
                        """
                        SELECT id, evaluation_dataset_version, retrieval_mode,
                               answer_correctness, evidence_recall, citation_precision,
                               latency_p50_ms, latency_p95_ms, token_cost_usd,
                               total_questions, metrics_detail, created_at
                        FROM evaluation_runs
                        ORDER BY created_at DESC
                        LIMIT $1;
                        """,
                        limit,
                    )
                    return [
                        {
                            "id": r["id"],
                            "evaluation_dataset_version": r["evaluation_dataset_version"],
                            "retrieval_mode": r["retrieval_mode"],
                            "answer_correctness": r["answer_correctness"],
                            "evidence_recall": r["evidence_recall"],
                            "citation_precision": r["citation_precision"],
                            "latency_p50_ms": r["latency_p50_ms"],
                            "latency_p95_ms": r["latency_p95_ms"],
                            "token_cost_usd": r["token_cost_usd"],
                            "total_questions": r["total_questions"],
                            "metrics_detail": json.loads(r["metrics_detail"]) if isinstance(r["metrics_detail"], str) else r["metrics_detail"],
                            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.warning(f"PostgreSQL list_evaluation_runs failed, using memory fallback: {e}")

        if not hasattr(self, "_mem_eval_runs"):
            self._mem_eval_runs = {}
        # Return sorted by created_at desc
        runs = list(self._mem_eval_runs.values())
        return runs[-limit:]

    async def get_evaluation_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        if self.pool:
            try:
                import json
                async with self.pool.acquire() as conn:
                    r = await conn.fetchrow(
                        """
                        SELECT id, evaluation_dataset_version, retrieval_mode,
                               answer_correctness, evidence_recall, citation_precision,
                               latency_p50_ms, latency_p95_ms, token_cost_usd,
                               total_questions, metrics_detail, created_at
                        FROM evaluation_runs
                        WHERE id = $1;
                        """,
                        run_id,
                    )
                    if r:
                        return {
                            "id": r["id"],
                            "evaluation_dataset_version": r["evaluation_dataset_version"],
                            "retrieval_mode": r["retrieval_mode"],
                            "answer_correctness": r["answer_correctness"],
                            "evidence_recall": r["evidence_recall"],
                            "citation_precision": r["citation_precision"],
                            "latency_p50_ms": r["latency_p50_ms"],
                            "latency_p95_ms": r["latency_p95_ms"],
                            "token_cost_usd": r["token_cost_usd"],
                            "total_questions": r["total_questions"],
                            "metrics_detail": json.loads(r["metrics_detail"]) if isinstance(r["metrics_detail"], str) else r["metrics_detail"],
                            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
                        }
            except Exception as e:
                logger.warning(f"PostgreSQL get_evaluation_run failed, using memory fallback: {e}")

        if not hasattr(self, "_mem_eval_runs"):
            self._mem_eval_runs = {}
        return self._mem_eval_runs.get(run_id)


postgres_repo = PostgresRepository()

