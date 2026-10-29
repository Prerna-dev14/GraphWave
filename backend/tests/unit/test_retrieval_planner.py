"""Unit tests for Vector, Graph, and Hybrid Retrieval Planner."""
import pytest
from app.services.retrieval_service import RetrievalService
from app.schemas.retrieval_schemas import RetrieveRequest, RetrievalMode
from app.domain.models import Document, Chunk, Entity
from app.domain.ontology import EntityType
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.neo4j_repository import Neo4jRepository
from app.services.entity_resolution_service import EntityResolutionService


@pytest.mark.asyncio
async def test_vector_only_retrieval():
    pg_repo = PostgresRepository()
    graph_repo = Neo4jRepository()
    res_service = EntityResolutionService(pg_repo, graph_repo)
    service = RetrievalService(pg_repo, graph_repo, res_service)

    # Ingest mock chunks
    chunk1 = Chunk(
        id="c1",
        document_id="doc1",
        tenant_id="tenant-test",
        corpus_id="corpus-test",
        chunk_index=1,
        text="Acme Cloud Platform Overview",
        embedding=[1.0] + [0.0] * 1535,
    )
    await pg_repo.save_chunks([chunk1])

    req = RetrieveRequest(
        query="Acme Cloud Platform",
        mode=RetrievalMode.VECTOR_ONLY,
        tenant_id="tenant-test",
        corpus_id="corpus-test",
    )
    bundle = await service.retrieve(req)

    assert bundle.mode == RetrievalMode.VECTOR_ONLY
    assert len(bundle.seed_chunks) >= 1
    assert bundle.seed_chunks[0].chunk_id == "c1"
    assert len(bundle.graph_paths) == 0  # No graph expansion in vector-only


@pytest.mark.asyncio
async def test_bounded_graph_traversal_limits():
    pg_repo = PostgresRepository()
    graph_repo = Neo4jRepository()
    res_service = EntityResolutionService(pg_repo, graph_repo)
    service = RetrievalService(pg_repo, graph_repo, res_service)

    # Register entities and chained edges: E1 -> E2 -> E3 -> E4 (depth 3)
    e1 = await res_service.resolve_entity("E1", EntityType.ORGANIZATION, "tenant-test", "corpus-test")
    e2 = await res_service.resolve_entity("E2", EntityType.ORGANIZATION, "tenant-test", "corpus-test")
    e3 = await res_service.resolve_entity("E3", EntityType.ORGANIZATION, "tenant-test", "corpus-test")
    e4 = await res_service.resolve_entity("E4", EntityType.ORGANIZATION, "tenant-test", "corpus-test")

    await graph_repo.merge_resolved_relationship(e1, "RELATES", e2, "c1", "1.0", 0.9, "e1 to e2")
    await graph_repo.merge_resolved_relationship(e2, "RELATES", e3, "c2", "1.0", 0.9, "e2 to e3")
    await graph_repo.merge_resolved_relationship(e3, "RELATES", e4, "c3", "1.0", 0.9, "e3 to e4")

    # Traversal bounded at depth = 2
    req = RetrieveRequest(
        query="Tell me about E1",
        mode=RetrievalMode.GRAPH_ONLY,
        tenant_id="tenant-test",
        corpus_id="corpus-test",
        max_depth=2,
        max_fan_out=15,
    )
    bundle = await service.retrieve(req)

    assert bundle.mode == RetrievalMode.GRAPH_ONLY
    assert len(bundle.graph_paths) == 2  # E1->E2 (hop 1) and E2->E3 (hop 2); E3->E4 (hop 3) is excluded!
    hops = [p.hop for p in bundle.graph_paths]
    assert max(hops) <= 2
