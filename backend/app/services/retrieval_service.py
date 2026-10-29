"""GraphWeave Hybrid Retrieval Planner Service.

Coordinates vector similarity search (pgvector), bounded graph traversal (Neo4j),
and multi-hop evidence fusion with latency telemetry and tenant/corpus scoping.
"""
import time
from typing import List, Dict, Any, Set, Tuple, Optional

from app.core.config import settings
from app.core.logging import logger
from app.schemas.retrieval_schemas import (
    RetrievalMode,
    RetrieveRequest,
    RetrievedChunkSchema,
    TraversedEdgeSchema,
    RetrievalMetricsSchema,
    EvidenceBundleResponse,
)
from app.domain.models import Chunk
from app.adapters.embedding_adapter import get_embedding_adapter, BaseEmbeddingAdapter
from app.repositories.postgres_repository import postgres_repo, PostgresRepository
from app.repositories.neo4j_repository import neo4j_repo, Neo4jRepository
from app.services.entity_resolution_service import entity_resolution_service, EntityResolutionService


class RetrievalService:
    def __init__(
        self,
        pg_repo: Optional[PostgresRepository] = None,
        graph_repo: Optional[Neo4jRepository] = None,
        resolution_service: Optional[EntityResolutionService] = None,
        embedding_adapter: Optional[BaseEmbeddingAdapter] = None,
    ):
        self.pg_repo = pg_repo or postgres_repo
        self.graph_repo = graph_repo or neo4j_repo
        self.resolution_service = resolution_service or entity_resolution_service
        self.embedding_adapter = embedding_adapter or get_embedding_adapter()

    def _extract_query_entities(
        self, query: str, tenant_id: str, corpus_id: str
    ) -> List[str]:
        """Finds entities in query text matching canonical entity names or aliases."""
        matched_cids: Set[str] = set()
        query_lower = query.lower()

        # Check against canonical entities
        entities_with_counts = self.resolution_service.list_canonical_entities(tenant_id, corpus_id)
        for entity, _ in entities_with_counts:
            # Check canonical name
            if entity.name.lower() in query_lower:
                matched_cids.add(entity.canonical_id)
                continue
            # Check aliases
            for alias in entity.aliases:
                if alias.lower() in query_lower:
                    matched_cids.add(entity.canonical_id)
                    break

        return list(matched_cids)

    async def retrieve(self, req: RetrieveRequest) -> EvidenceBundleResponse:
        """Executes the requested retrieval strategy (Vector, Graph, or Hybrid) and builds an evidence bundle."""
        start_total = time.perf_counter()
        tenant_id = req.tenant_id or settings.DEFAULT_TENANT_ID
        corpus_id = req.corpus_id or settings.DEFAULT_CORPUS_ID

        seed_chunks_schema: List[RetrievedChunkSchema] = []
        traversed_edges_schema: List[TraversedEdgeSchema] = []
        fused_chunks_schema: List[RetrievedChunkSchema] = []

        latency_vector = 0.0
        latency_graph = 0.0
        latency_fusion = 0.0

        seed_entity_ids: Set[str] = set()

        # ==========================================================
        # STAGE 1: VECTOR SEED RETRIEVAL (for Vector-Only and Hybrid)
        # ==========================================================
        if req.mode in (RetrievalMode.VECTOR_ONLY, RetrievalMode.HYBRID):
            start_vec = time.perf_counter()
            query_embedding = await self.embedding_adapter.embed_text(req.query)
            scored_chunks = await self.pg_repo.search_chunks_by_vector(
                query_embedding=query_embedding,
                tenant_id=tenant_id,
                corpus_id=corpus_id,
                top_k=req.top_k_vector,
            )
            latency_vector = (time.perf_counter() - start_vec) * 1000.0

            for chunk, sim in scored_chunks:
                seed_chunks_schema.append(
                    RetrievedChunkSchema(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        section_header=chunk.section_header,
                        similarity_score=round(sim, 4),
                        source="vector",
                    )
                )

        # Discover seed entities from query and seed chunk contents
        query_entity_cids = self._extract_query_entities(req.query, tenant_id, corpus_id)
        seed_entity_ids.update(query_entity_cids)

        # If in hybrid mode, also check entities in seed chunks
        if req.mode == RetrievalMode.HYBRID:
            for sc in seed_chunks_schema:
                chunk_entities = self._extract_query_entities(sc.text, tenant_id, corpus_id)
                seed_entity_ids.update(chunk_entities)

        # ==========================================================
        # STAGE 2: BOUNDED GRAPH EXPANSION (for Graph-Only and Hybrid)
        # ==========================================================
        if req.mode in (RetrievalMode.GRAPH_ONLY, RetrievalMode.HYBRID) and seed_entity_ids:
            start_graph = time.perf_counter()
            raw_edges = await self.graph_repo.traverse_bounded_neighborhood(
                seed_entity_ids=list(seed_entity_ids),
                tenant_id=tenant_id,
                corpus_id=corpus_id,
                max_depth=req.max_depth,
                max_fan_out=req.max_fan_out,
                timeout_sec=settings.TRAVERSAL_TIMEOUT_SECONDS,
            )
            latency_graph = (time.perf_counter() - start_graph) * 1000.0

            for edge in raw_edges:
                traversed_edges_schema.append(
                    TraversedEdgeSchema(
                        source_entity=edge.get("source", ""),
                        source_type="ENTITY",
                        relation=edge.get("relation", edge.get("type", "RELATES_TO")),
                        target_entity=edge.get("target", ""),
                        target_type="ENTITY",
                        confidence=edge.get("confidence", 0.9),
                        hop=edge.get("hop", 1),
                        source_chunk_ids=edge.get("source_chunk_ids", []),
                        evidence_text=edge.get("evidence_text"),
                    )
                )

        # ==========================================================
        # STAGE 3: EVIDENCE FUSION & DEDUPLICATION
        # ==========================================================
        start_fusion = time.perf_counter()
        fused_chunks_map: Dict[str, Tuple[Chunk, float, str]] = {}

        # Add vector chunks
        for sc in seed_chunks_schema:
            chunk_obj = await self.pg_repo.get_chunk_by_id(sc.chunk_id)
            if chunk_obj:
                fused_chunks_map[sc.chunk_id] = (chunk_obj, sc.similarity_score, "vector")

        # Add chunks supporting traversed graph edges
        for edge_item in traversed_edges_schema:
            hop_decay = 1.0 / (1.0 + edge_item.hop)
            edge_boost = edge_item.confidence * hop_decay
            for chunk_id in edge_item.source_chunk_ids:
                if chunk_id in fused_chunks_map:
                    # Boost existing chunk score with graph confirmation
                    chunk_obj, prev_score, _ = fused_chunks_map[chunk_id]
                    fused_chunks_map[chunk_id] = (chunk_obj, prev_score + edge_boost, "fused")
                else:
                    # New chunk discovered purely through graph hop
                    chunk_obj = await self.pg_repo.get_chunk_by_id(chunk_id)
                    if chunk_obj:
                        fused_chunks_map[chunk_id] = (chunk_obj, edge_boost, "graph")

        # Sort fused chunks by final relevance score
        sorted_fused = sorted(fused_chunks_map.values(), key=lambda x: x[1], reverse=True)
        for chunk_obj, score, source_label in sorted_fused:
            fused_chunks_schema.append(
                RetrievedChunkSchema(
                    chunk_id=chunk_obj.id,
                    document_id=chunk_obj.document_id,
                    chunk_index=chunk_obj.chunk_index,
                    text=chunk_obj.text,
                    section_header=chunk_obj.section_header,
                    similarity_score=round(score, 4),
                    source=source_label,
                )
            )

        latency_fusion = (time.perf_counter() - start_fusion) * 1000.0
        latency_total = (time.perf_counter() - start_total) * 1000.0

        metrics = RetrievalMetricsSchema(
            latency_vector_ms=round(latency_vector, 2),
            latency_graph_ms=round(latency_graph, 2),
            latency_fusion_ms=round(latency_fusion, 2),
            latency_total_ms=round(latency_total, 2),
            seed_chunks_count=len(seed_chunks_schema),
            graph_edges_count=len(traversed_edges_schema),
            fused_chunks_count=len(fused_chunks_schema),
        )

        logger.info(
            f"Retrieval complete (mode={req.mode.value}): {metrics.fused_chunks_count} chunks, "
            f"{metrics.graph_edges_count} edges in {metrics.latency_total_ms:.2f}ms"
        )

        return EvidenceBundleResponse(
            query=req.query,
            mode=req.mode,
            tenant_id=tenant_id,
            corpus_id=corpus_id,
            seed_chunks=seed_chunks_schema,
            graph_paths=traversed_edges_schema,
            fused_evidence_chunks=fused_chunks_schema,
            metrics=metrics,
        )


retrieval_service = RetrievalService()
