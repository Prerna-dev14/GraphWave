"""Unit tests for Ingestion Service parsing and state flow."""
import pytest
from app.services.ingestion_service import IngestionService
from app.domain.models import JobStatus


@pytest.mark.asyncio
async def test_parse_and_chunk_with_headers():
    service = IngestionService(chunk_size=150, chunk_overlap=30)
    sample_content = (
        "# Acme Cloud Overview\n"
        "Acme Cloud provides distributed computing across global data centers.\n\n"
        "## Mergers and Acquisitions\n"
        "In June 2024, Acme Cloud acquired DataWeaver Inc.\n"
        "DataWeaver created OmniMesh for low-latency memory caching.\n"
    )

    chunks = service.parse_and_chunk(
        content=sample_content,
        doc_id="testdoc123",
        version="1.0",
        tenant_id="tenant-1",
        corpus_id="corpus-1",
    )

    assert len(chunks) >= 2
    assert chunks[0].section_header in ("Acme Cloud Overview", "Introduction")
    assert any(c.section_header == "Mergers and Acquisitions" for c in chunks)
    assert all(c.id.startswith("doc_testdoc123_v1_0_chunk_") for c in chunks)


@pytest.mark.asyncio
async def test_full_ingestion_pipeline():
    service = IngestionService()
    sample_text = (
        "# Platform Spec\n"
        "Acme Cloud completed the strategic corporate acquisition of DataWeaver Inc."
    )

    doc, job = await service.ingest_document(
        filename="acme_spec.md",
        content=sample_text,
        tenant_id="tenant-test",
        corpus_id="corpus-test",
    )

    assert doc.id is not None
    assert doc.filename == "acme_spec.md"
    assert job.status == JobStatus.COMPLETED
    assert job.chunk_count >= 1
    assert job.extracted_relations_count >= 1
