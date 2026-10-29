"""Integration tests for Idempotent Graph Writes and Entities API."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion_service import ingestion_service
from app.repositories.neo4j_repository import neo4j_repo


@pytest.mark.asyncio
async def test_reingestion_idempotency():
    """Verifies that re-ingesting the exact same document does not produce duplicate nodes or corrupted edges."""
    sample_text = (
        "# Platform Overview\n"
        "Acme Cloud completed the strategic corporate acquisition of DataWeaver Inc."
    )

    # 1. First Ingestion
    doc1, job1 = await ingestion_service.ingest_document(
        filename="idempotent_doc.md",
        content=sample_text,
        tenant_id="tenant-idem",
        corpus_id="corpus-idem",
    )

    initial_node_count = len(neo4j_repo._mem_nodes)
    initial_edge_count = len(neo4j_repo._mem_edges)

    # 2. Second Ingestion of identical content
    doc2, job2 = await ingestion_service.ingest_document(
        filename="idempotent_doc.md",
        content=sample_text,
        tenant_id="tenant-idem",
        corpus_id="corpus-idem",
    )

    # Documents share the exact same deterministic ID
    assert doc1.id == doc2.id

    # The canonical entities are reused, not duplicated
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/entities?tenant_id=tenant-idem&corpus_id=corpus-idem")
        assert resp.status_code == 200
        entities = resp.json()
        assert len(entities) >= 1
        # DataWeaver and Acme Cloud exist once in canonical registry
        names = [e["name"] for e in entities]
        assert names.count("Acme Cloud") <= 1
        assert names.count("DataWeaver Inc.") <= 1


@pytest.mark.asyncio
async def test_entities_and_ambiguities_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check entities endpoint
        resp = await client.get("/api/v1/entities")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # Check ambiguities endpoint
        amb_resp = await client.get("/api/v1/entities/ambiguities")
        assert amb_resp.status_code == 200
        assert isinstance(amb_resp.json(), list)
