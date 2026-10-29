"""Integration test for full Ingestion-to-Answer Vertical Slice via /api/v1/query."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion_service import ingestion_service


@pytest.mark.asyncio
async def test_full_query_pipeline_vertical_slice():
    """Validates the complete vertical slice:
    Ingestion -> Extraction -> Resolution -> Hybrid Retrieval -> Answer Synthesis + Citations + Telemetry Trace.
    """
    tenant_id = "tenant-e2e"
    corpus_id = "corpus-e2e"

    # 1. Ingest Acme document
    doc1, job1 = await ingestion_service.ingest_document(
        filename="acme.md",
        content="# Overview\nAcme Cloud completed the strategic corporate acquisition of DataWeaver Inc.",
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )
    assert job1.status.value == "COMPLETED"

    # 2. Ingest DataWeaver document
    doc2, job2 = await ingestion_service.ingest_document(
        filename="dataweaver.md",
        content="# Products\nDataWeaver Inc. is the primary creator and developer of OmniMesh.",
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )
    assert job2.status.value == "COMPLETED"

    # 3. Query the system end-to-end
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        query_payload = {
            "query": "Which parent corporation currently owns the OmniMesh distributed cache engine?",
            "mode": "hybrid",
            "tenant_id": tenant_id,
            "corpus_id": corpus_id,
            "max_depth": 2,
            "max_fan_out": 15,
        }
        resp = await client.post("/api/v1/query", json=query_payload)
        assert resp.status_code == 200
        data = resp.json()

        # Verify answer
        assert "Acme Cloud owns the OmniMesh" in data["answer"]
        assert data["mode"] == "hybrid"
        assert len(data["citations"]) >= 1

        # Verify graph paths
        assert len(data["graph_paths"]) >= 1

        # Verify telemetry metrics
        assert data["metrics"]["latency_total_ms"] > 0
        assert data["metrics"]["latency_generation_ms"] >= 0
        assert data["trace_id"] is not None
        trace_id = data["trace_id"]

        # 4. Fetch request trace diagnostic endpoint
        trace_resp = await client.get(f"/api/v1/requests/{trace_id}")
        assert trace_resp.status_code == 200
        trace_data = trace_resp.json()
        assert trace_data["request_id"] == trace_id
        assert trace_data["retrieval_mode"] == "hybrid"
