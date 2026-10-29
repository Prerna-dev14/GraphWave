"""Unit tests for Phase 2 Extraction Pipeline."""
import pytest
from app.services.extraction_service import ExtractionService
from app.adapters.llm_adapter import BaseLLMAdapter
from typing import List, Dict, Any, Optional


class MockExtractionLLM(BaseLLMAdapter):
    """Custom mock LLM allowing injection of test claims with varied confidences and types."""
    def __init__(self, claims: List[Dict[str, Any]]):
        self.claims = claims
        self.model_name = "test-mock-llm"

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "mock completion"

    async def extract_claims(self, chunk_text: str, section_header: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.claims


@pytest.mark.asyncio
async def test_extraction_validation_success():
    test_claims = [
        {
            "subject": "Acme Cloud",
            "subject_type": "ORGANIZATION",
            "relation": "ACQUIRED",
            "object": "DataWeaver Inc.",
            "object_type": "ORGANIZATION",
            "confidence": 0.95,
            "evidence": "Acme Cloud completed the corporate acquisition of DataWeaver Inc.",
        }
    ]
    service = ExtractionService(llm_adapter=MockExtractionLLM(test_claims), confidence_threshold=0.65)
    claims, report = await service.extract_and_validate("sample chunk text")

    assert len(claims) == 1
    assert claims[0].subject_entity == "Acme Cloud"
    assert claims[0].relation.value == "ACQUIRED"
    assert report.validated_count == 1
    assert report.rejected_count == 0


@pytest.mark.asyncio
async def test_extraction_schema_rejection():
    # Invalid subject type for ACQUIRED: PERSON is not allowed
    test_claims = [
        {
            "subject": "John Doe",
            "subject_type": "PERSON",
            "relation": "ACQUIRED",
            "object": "DataWeaver Inc.",
            "object_type": "ORGANIZATION",
            "confidence": 0.95,
            "evidence": "John Doe acquired DataWeaver Inc.",
        }
    ]
    service = ExtractionService(llm_adapter=MockExtractionLLM(test_claims))
    claims, report = await service.extract_and_validate("sample chunk text")

    assert len(claims) == 0
    assert report.validated_count == 0
    assert report.rejected_count == 1
    assert report.rejected_claims[0].status == "REJECTED_SCHEMA"
    assert "Subject type 'PERSON' not permitted" in report.rejected_claims[0].reason


@pytest.mark.asyncio
async def test_extraction_confidence_threshold_rejection():
    test_claims = [
        {
            "subject": "Acme Cloud",
            "subject_type": "ORGANIZATION",
            "relation": "ACQUIRED",
            "object": "DataWeaver Inc.",
            "object_type": "ORGANIZATION",
            "confidence": 0.50,  # Below 0.65 threshold
            "evidence": "Rumors say Acme Cloud might acquire DataWeaver.",
        }
    ]
    service = ExtractionService(llm_adapter=MockExtractionLLM(test_claims), confidence_threshold=0.65)
    claims, report = await service.extract_and_validate("sample chunk text")

    assert len(claims) == 0
    assert report.validated_count == 0
    assert report.rejected_count == 1
    assert report.rejected_claims[0].status == "REJECTED_CONFIDENCE"
    assert "below threshold 0.65" in report.rejected_claims[0].reason


@pytest.mark.asyncio
async def test_extraction_confidence_threshold_override():
    test_claims = [
        {
            "subject": "Acme Cloud",
            "subject_type": "ORGANIZATION",
            "relation": "ACQUIRED",
            "object": "DataWeaver Inc.",
            "object_type": "ORGANIZATION",
            "confidence": 0.50,
            "evidence": "Acme Cloud acquired DataWeaver.",
        }
    ]
    service = ExtractionService(llm_adapter=MockExtractionLLM(test_claims), confidence_threshold=0.65)
    # Lower threshold to 0.40 via override
    claims, report = await service.extract_and_validate(
        "sample chunk text",
        confidence_threshold_override=0.40,
    )

    assert len(claims) == 1
    assert report.validated_count == 1
    assert report.rejected_count == 0
