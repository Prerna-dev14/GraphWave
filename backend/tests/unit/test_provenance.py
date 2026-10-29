"""Unit tests for deterministic ID computation and provenance lineage."""
import pytest
from app.domain.provenance import (
    compute_document_id,
    compute_chunk_id,
    compute_canonical_entity_id,
    slugify_entity,
    ProvenanceRecord,
)


def test_compute_document_id_is_deterministic():
    id1 = compute_document_id("tenant-1", "corpus-1", "doc.md", "Sample Content")
    id2 = compute_document_id("tenant-1", "corpus-1", "doc.md", "Sample Content")
    assert id1 == id2
    assert len(id1) == 32

    # Different scope produces different ID
    id3 = compute_document_id("tenant-2", "corpus-1", "doc.md", "Sample Content")
    assert id1 != id3


def test_compute_chunk_id_is_deterministic():
    chunk_id1 = compute_chunk_id("abcdef1234567890", "1.0", 1, "First paragraph text")
    chunk_id2 = compute_chunk_id("abcdef1234567890", "1.0", 1, "First paragraph text")
    assert chunk_id1 == chunk_id2
    assert "chunk_0001" in chunk_id1
    assert "doc_abcdef123456" in chunk_id1


def test_canonical_entity_id():
    cid = compute_canonical_entity_id("ORGANIZATION", "Acme Cloud Platform, Inc.")
    assert cid == "org:acme_cloud_platform_inc"

    cid2 = compute_canonical_entity_id("PERSON", "Dr. Elena Vance")
    assert cid2 == "per:dr_elena_vance"


def test_provenance_record_validation():
    record = ProvenanceRecord(
        tenant_id="tenant-1",
        corpus_id="corpus-1",
        document_id="doc123",
        document_name="spec.md",
        document_version="1.0",
        chunk_id="chunk123",
        section_header="Executive Summary",
        confidence=0.95,
        extraction_model="mock",
    )
    assert record.confidence == 0.95
    assert record.tenant_id == "tenant-1"
