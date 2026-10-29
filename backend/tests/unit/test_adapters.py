"""Unit tests for replaceable LLM and Embedding adapters."""
import pytest
import numpy as np
from app.adapters.llm_adapter import DeterministicMockLLMAdapter
from app.adapters.embedding_adapter import DeterministicMockEmbeddingAdapter


@pytest.mark.asyncio
async def test_deterministic_mock_llm():
    adapter = DeterministicMockLLMAdapter()
    
    # Test multi-hop answer completion
    ans = await adapter.complete("Who owns OmniMesh?")
    assert "Acme Cloud owns the OmniMesh" in ans
    assert "Citation:" in ans

    # Test extraction
    chunk_text = "Acme Cloud completed the strategic corporate acquisition of DataWeaver Inc. for an undisclosed sum."
    claims = await adapter.extract_claims(chunk_text)
    assert len(claims) >= 1
    assert claims[0]["subject"] == "Acme Cloud"
    assert claims[0]["relation"] == "ACQUIRED"
    assert claims[0]["object"] == "DataWeaver Inc."


@pytest.mark.asyncio
async def test_deterministic_mock_embedding():
    adapter = DeterministicMockEmbeddingAdapter(dimension=128)
    
    vec1 = await adapter.embed_text("Acme Cloud distributed storage")
    vec2 = await adapter.embed_text("Acme Cloud distributed storage")
    vec3 = await adapter.embed_text("Different query completely")

    # Identical texts produce identical vectors
    assert vec1 == vec2
    assert len(vec1) == 128

    # Vectors are normalized unit vectors (norm == 1.0)
    norm = np.linalg.norm(vec1)
    assert np.isclose(norm, 1.0, atol=1e-5)

    # Different texts produce different vectors
    assert vec1 != vec3
