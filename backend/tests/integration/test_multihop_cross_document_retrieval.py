"""Integration test proving cross-document multi-hop retrieval."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion_service import ingestion_service
from app.schemas.retrieval_schemas import RetrieveRequest, RetrievalMode


@pytest.mark.asyncio
async def test_cross_document_multihop_retrieval_slice():
    """Ingests two connected documents and proves that Hybrid retrieval discovers
    the multi-hop reasoning path spanning across both documents.
    """
    tenant_id = "tenant-multihop"
    corpus_id = "corpus-multihop"

    # Document 1: Corporate Acquisition
    doc1_content = (
        "# Acme Cloud Platform Overview\n\n"
        "## Strategic Mergers & Acquisitions\n"
        "In June 2024, Acme Cloud completed the strategic corporate acquisition of DataWeaver Inc. for an undisclosed sum."
    )
    doc1, job1 = await ingestion_service.ingest_document(
        filename="doc_01_acme_corp.md",
        content=doc1_content,
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )
    assert job1.status.value == "COMPLETED"

    # Document 2: Product Lineage
    doc2_content = (
        "# DataWeaver Engineering Architecture Brief\n\n"
        "## Product Portfolio\n"
        "DataWeaver Inc. is the primary creator and developer of OmniMesh, an ultra-low latency in-memory distributed cache engine."
    )
    doc2, job2 = await ingestion_service.ingest_document(
        filename="doc_02_dataweaver.md",
        content=doc2_content,
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )
    assert job2.status.value == "COMPLETED"

    # Multi-hop question: Asking about the owner of OmniMesh (requires Doc 2 -> Doc 1 traversal)
    question = "Which parent corporation currently owns the OmniMesh distributed cache engine?"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Execute HYBRID Retrieval
        hybrid_req = {
            "query": question,
            "mode": "hybrid",
            "tenant_id": tenant_id,
            "corpus_id": corpus_id,
            "max_depth": 2,
            "max_fan_out": 15,
        }
        hybrid_resp = await client.post("/api/v1/retrieve", json=hybrid_req)
        assert hybrid_resp.status_code == 200
        bundle = hybrid_resp.json()

        assert bundle["mode"] == "hybrid"
        # Traversed graph paths found the connection
        assert len(bundle["graph_paths"]) >= 1

        # Check traversed relations
        relations = [p["relation"] for p in bundle["graph_paths"]]
        assert any("DEVELOPS" in r or "ACQUIRED" in r for r in relations)

        # Fused evidence chunks must span BOTH documents!
        doc_ids_in_evidence = {c["document_id"] for c in bundle["fused_evidence_chunks"]}
        assert doc1.id in doc_ids_in_evidence
        assert doc2.id in doc_ids_in_evidence

        # Check telemetry latency metrics
        assert bundle["metrics"]["latency_total_ms"] > 0
        assert bundle["metrics"]["fused_chunks_count"] >= 2
