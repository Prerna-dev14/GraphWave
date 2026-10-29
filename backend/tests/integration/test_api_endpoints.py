"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_live():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "live"
        assert data["service"] == "GraphWeave"


@pytest.mark.asyncio
async def test_health_ready():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready", "not_ready")
        assert "postgresql" in data["dependencies"]
        assert "neo4j" in data["dependencies"]


@pytest.mark.asyncio
async def test_document_ingestion_and_retrieval_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingest Document
        payload = {
            "filename": "integration_test_doc.md",
            "content": "# Test Header\nAcme Cloud acquired DataWeaver Inc. in June 2024.",
            "version": "1.0",
            "tenant_id": "tenant-test",
            "corpus_id": "corpus-test",
        }
        ingest_resp = await client.post("/api/v1/documents", json=payload)
        assert ingest_resp.status_code == 201
        job_data = ingest_resp.json()
        assert job_data["status"] == "COMPLETED"
        assert job_data["document_id"] is not None
        doc_id = job_data["document_id"]

        # 2. List Documents
        list_resp = await client.get("/api/v1/documents?tenant_id=tenant-test&corpus_id=corpus-test")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total_count"] >= 1
        assert any(d["id"] == doc_id for d in list_data["documents"])

        # 3. Inspect Chunks
        chunk_resp = await client.get(f"/api/v1/documents/{doc_id}/chunks?tenant_id=tenant-test&corpus_id=corpus-test")
        assert chunk_resp.status_code == 200
        chunks = chunk_resp.json()
        assert len(chunks) >= 1
        assert "Acme Cloud" in chunks[0]["text"]

        # 4. Check Ingestion Job endpoint
        job_resp = await client.get(f"/api/v1/ingestion-jobs/{job_data['job_id']}")
        assert job_resp.status_code == 200
        assert job_resp.json()["job_id"] == job_data["job_id"]
