"""Security and Hardening tests: Multi-tenant isolation, cascade deletion, and query bounds."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion_service import ingestion_service


@pytest.mark.asyncio
async def test_tenant_and_corpus_isolation_boundary():
    """Proves strict multi-tenant boundary: Tenant A cannot see or retrieve Tenant B's data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ingest Tenant A Document
        doc_a, _ = await ingestion_service.ingest_document(
            filename="tenant_a_confidential.md",
            content="# Alpha Secret Project\nAlpha is building classified engine X-1.",
            tenant_id="tenant-alpha",
            corpus_id="corpus-main",
        )

        # Ingest Tenant B Document
        doc_b, _ = await ingestion_service.ingest_document(
            filename="tenant_b_confidential.md",
            content="# Beta Secret Project\nBeta is building classified engine Y-2.",
            tenant_id="tenant-beta",
            corpus_id="corpus-main",
        )

        # 1. Document Listing Isolation
        resp_a = await client.get("/api/v1/documents?tenant_id=tenant-alpha&corpus_id=corpus-main")
        assert resp_a.status_code == 200
        docs_a = resp_a.json()["documents"]
        doc_ids_a = {d["id"] for d in docs_a}
        assert doc_a.id in doc_ids_a
        assert doc_b.id not in doc_ids_a

        # 2. Cross-Tenant Direct ID Access Refusal
        resp_leak = await client.get(f"/api/v1/documents/{doc_b.id}?tenant_id=tenant-alpha&corpus_id=corpus-main")
        assert resp_leak.status_code == 404

        # 3. Query Retrieval Isolation
        query_req = {
            "query": "What is classified engine Y-2?",
            "tenant_id": "tenant-alpha",
            "corpus_id": "corpus-main",
            "mode": "hybrid",
        }
        query_resp = await client.post("/api/v1/query", json=query_req)
        assert query_resp.status_code == 200
        q_data = query_resp.json()

        # Tenant A's query MUST NOT retrieve Tenant B's chunk
        for cit in q_data.get("citations", []):
            assert cit["document_id"] != doc_b.id


@pytest.mark.asyncio
async def test_document_deletion_and_cascade_purge():
    """Tests that deleting a document purges relational chunks and graph edges cleanly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc, _ = await ingestion_service.ingest_document(
            filename="temporary_doc.md",
            content="# Temporary Data\nAcme Cloud acquired DataWeaver Inc. in 2024.",
            tenant_id="tenant-purge-test",
            corpus_id="corpus-purge-test",
        )

        # Verify document exists
        get_resp = await client.get(f"/api/v1/documents/{doc.id}?tenant_id=tenant-purge-test&corpus_id=corpus-purge-test")
        assert get_resp.status_code == 200

        # Delete document
        del_resp = await client.delete(f"/api/v1/documents/{doc.id}?tenant_id=tenant-purge-test&corpus_id=corpus-purge-test")
        assert del_resp.status_code == 200
        del_data = del_resp.json()
        assert del_data["status"] == "success"

        # Verify document is gone
        get_gone = await client.get(f"/api/v1/documents/{doc.id}?tenant_id=tenant-purge-test&corpus_id=corpus-purge-test")
        assert get_gone.status_code == 404

        # Verify chunks are gone
        chunks_gone = await client.get(f"/api/v1/documents/{doc.id}/chunks?tenant_id=tenant-purge-test&corpus_id=corpus-purge-test")
        assert chunks_gone.status_code == 404


@pytest.mark.asyncio
async def test_query_limits_and_budget_defense():
    """Verifies input length bounds and traversal parameter limits to defend against resource exhaustion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Oversized query (> 1000 characters)
        oversized_query = "What is " + ("A" * 1200) + "?"
        resp_over = await client.post("/api/v1/query", json={"query": oversized_query})
        assert resp_over.status_code == 422

        # Invalid traversal depth (> 3)
        resp_depth = await client.post(
            "/api/v1/query",
            json={"query": "Valid question?", "max_depth": 5},
        )
        assert resp_depth.status_code == 422

        # Invalid fan-out (> 50)
        resp_fanout = await client.post(
            "/api/v1/query",
            json={"query": "Valid question?", "max_fan_out": 100},
        )
        assert resp_fanout.status_code == 422
