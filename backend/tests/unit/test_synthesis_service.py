"""Unit tests for Answer Synthesis and Citation Extraction."""
import pytest
from app.services.synthesis_service import SynthesisService
from app.schemas.retrieval_schemas import RetrievedChunkSchema, EvidenceBundleResponse, RetrievalMetricsSchema, RetrievalMode
from app.schemas.query_schemas import QueryRequest


def test_extract_citations_regex():
    service = SynthesisService()
    fused_chunks = [
        RetrievedChunkSchema(
            chunk_id="chunk_acme_001",
            document_id="doc_acme",
            chunk_index=1,
            text="Acme Cloud completed the acquisition of DataWeaver Inc.",
            section_header="Mergers",
            similarity_score=0.95,
            source="fused",
        ),
        RetrievedChunkSchema(
            chunk_id="chunk_dw_002",
            document_id="doc_dw",
            chunk_index=1,
            text="DataWeaver developed OmniMesh in-memory cache.",
            section_header="Products",
            similarity_score=0.92,
            source="fused",
        ),
    ]

    # LLM completion with citation tags
    answer = "Acme Cloud owns OmniMesh because it acquired DataWeaver. [Citation: chunk_acme_001, chunk_dw_002]"
    citations = service.extract_citations(answer, fused_chunks)

    assert len(citations) == 2
    c_ids = [c.chunk_id for c in citations]
    assert "chunk_acme_001" in c_ids
    assert "chunk_dw_002" in c_ids
    assert citations[0].snippet is not None


@pytest.mark.asyncio
async def test_synthesis_missing_evidence_refusal():
    service = SynthesisService()
    req = QueryRequest(
        query="Who founded QuantaCore Systems and in what year was their processor released?",
        mode=RetrievalMode.HYBRID,
    )
    res = await service.query(req)

    # Must indicate missing evidence rather than fabricating
    assert "do not contain evidence" in res.answer.lower() or "missing" in res.answer.lower()
    assert res.trace_id.startswith("trace_")
