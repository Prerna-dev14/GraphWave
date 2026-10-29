"""GraphWeave Ingestion Service.
Coordinates parsing, deterministic chunking, provenance attribution, embedding, and job tracking.
"""
import uuid
import re
from typing import List, Tuple, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.domain.models import Document, Chunk, IngestionJob, JobStatus, CandidateClaim, ClaimStatus
from app.domain.provenance import compute_document_id, compute_chunk_id, ProvenanceRecord
from app.domain.ontology import validate_relation, EntityType, RelationType
from app.adapters.embedding_adapter import get_embedding_adapter
from app.adapters.llm_adapter import get_llm_adapter
from app.repositories.postgres_repository import postgres_repo, PostgresRepository
from app.repositories.neo4j_repository import neo4j_repo, Neo4jRepository


class IngestionService:
    def __init__(
        self,
        pg_repo: Optional[PostgresRepository] = None,
        graph_repo: Optional[Neo4jRepository] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ):
        self.pg_repo = pg_repo or postgres_repo
        self.graph_repo = graph_repo or neo4j_repo
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_adapter = get_embedding_adapter()
        self.llm_adapter = get_llm_adapter()

    def parse_and_chunk(
        self,
        content: str,
        doc_id: str,
        version: str,
        tenant_id: str,
        corpus_id: str,
    ) -> List[Chunk]:
        """Splits document content into boundary-aware chunks with deterministic identifiers."""
        chunks: List[Chunk] = []
        lines = content.splitlines()

        current_section = "Introduction"
        current_buffer: List[str] = []
        current_len = 0
        chunk_idx = 1

        for line in lines:
            line_stripped = line.strip()
            is_header = line_stripped.startswith("#")
            line_len = len(line) + 1

            # If line is a header and buffer is not empty, flush previous section chunk first
            if is_header and current_buffer:
                chunk_text = "\n".join(current_buffer).strip()
                if chunk_text:
                    cid = compute_chunk_id(doc_id, version, chunk_idx, chunk_text)
                    chunks.append(
                        Chunk(
                            id=cid,
                            document_id=doc_id,
                            tenant_id=tenant_id,
                            corpus_id=corpus_id,
                            chunk_index=chunk_idx,
                            text=chunk_text,
                            section_header=current_section,
                            page_number=1,
                        )
                    )
                    chunk_idx += 1
                current_buffer = []
                current_len = 0

            if is_header:
                current_section = line_stripped.lstrip("#").strip()

            if current_len + line_len > self.chunk_size and current_buffer:
                chunk_text = "\n".join(current_buffer).strip()
                if chunk_text:
                    cid = compute_chunk_id(doc_id, version, chunk_idx, chunk_text)
                    chunks.append(
                        Chunk(
                            id=cid,
                            document_id=doc_id,
                            tenant_id=tenant_id,
                            corpus_id=corpus_id,
                            chunk_index=chunk_idx,
                            text=chunk_text,
                            section_header=current_section,
                            page_number=1,
                        )
                    )
                    chunk_idx += 1

                overlap_text = "\n".join(current_buffer[-2:]) if len(current_buffer) >= 2 else ""
                current_buffer = [overlap_text, line] if overlap_text else [line]
                current_len = sum(len(l) + 1 for l in current_buffer)
            else:
                current_buffer.append(line)
                current_len += line_len

        # Flush trailing content
        if current_buffer:
            chunk_text = "\n".join(current_buffer).strip()
            if chunk_text:
                cid = compute_chunk_id(doc_id, version, chunk_idx, chunk_text)
                chunks.append(
                    Chunk(
                        id=cid,
                        document_id=doc_id,
                        tenant_id=tenant_id,
                        corpus_id=corpus_id,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        section_header=current_section,
                        page_number=1,
                    )
                )

        return chunks

    async def ingest_document(
        self,
        filename: str,
        content: str,
        version: str = "1.0",
        content_type: str = "text/markdown",
        tenant_id: Optional[str] = None,
        corpus_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Tuple[Document, IngestionJob]:
        """Executes the full ingestion pipeline: job creation, chunking, embedding, extraction, and graph indexing."""
        tenant_id = tenant_id or settings.DEFAULT_TENANT_ID
        corpus_id = corpus_id or settings.DEFAULT_CORPUS_ID
        metadata = metadata or {}

        # 1. Deterministic document ID
        doc_id = compute_document_id(tenant_id, corpus_id, filename, content)

        # 2. Ingestion Job initialization
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = IngestionJob(
            id=job_id,
            tenant_id=tenant_id,
            corpus_id=corpus_id,
            document_id=doc_id,
            filename=filename,
            status=JobStatus.PROCESSING,
        )
        await self.pg_repo.save_job(job)

        try:
            document = Document(
                id=doc_id,
                tenant_id=tenant_id,
                corpus_id=corpus_id,
                filename=filename,
                content_type=content_type,
                version=version,
                raw_content=content,
                metadata=metadata,
            )
            await self.pg_repo.save_document(document)

            # 3. Chunking with deterministic IDs
            chunks = self.parse_and_chunk(content, doc_id, version, tenant_id, corpus_id)

            # 4. Generate Embeddings for chunks
            chunk_texts = [c.text for c in chunks]
            embeddings = await self.embedding_adapter.embed_batch(chunk_texts)
            for c, emb in zip(chunks, embeddings):
                c.embedding = emb

            await self.pg_repo.save_chunks(chunks)

            # 5. Graph writes (Document and Chunks)
            await self.graph_repo.merge_document_and_chunks(document, chunks)

            # 6. Candidate claim extraction & validation via ExtractionService (Phase 2)
            extracted_claims_count = 0
            from app.services.extraction_service import extraction_service

            for chunk in chunks:
                claims, run_resp = await extraction_service.extract_and_validate(
                    chunk_text=chunk.text,
                    document_id=doc_id,
                    document_name=filename,
                    document_version=version,
                    chunk_id=chunk.id,
                    section_header=chunk.section_header,
                    tenant_id=tenant_id,
                    corpus_id=corpus_id,
                )
                for claim in claims:
                    await self.graph_repo.merge_candidate_claim(claim)
                    extracted_claims_count += 1

            # 7. Update Job Status to COMPLETED
            await self.pg_repo.update_job_status(
                job_id,
                status=JobStatus.COMPLETED,
                chunk_count=len(chunks),
                extracted_entities=extracted_claims_count * 2,
                extracted_relations=extracted_claims_count,
            )
            job.status = JobStatus.COMPLETED
            job.chunk_count = len(chunks)
            job.extracted_relations_count = extracted_claims_count
            logger.info(f"Ingestion successful for {filename} (doc_id={doc_id}, chunks={len(chunks)})")
            return document, job

        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
            await self.pg_repo.update_job_status(job_id, status=JobStatus.FAILED, error_message=str(e))
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            return document, job


ingestion_service = IngestionService()
