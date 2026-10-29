"""Replaceable LLM Adapter Interface and Implementations.
Includes a Deterministic Mock LLM Adapter for CI / offline test runs.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import re

from app.core.config import settings
from app.core.logging import logger
from app.domain.ontology import EntityType, RelationType


class BaseLLMAdapter(ABC):
    """Abstract interface for LLM completions and structured extractions."""

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate plain text completion."""
        pass

    @abstractmethod
    async def extract_claims(
        self,
        chunk_text: str,
        section_header: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract structured candidate entities and relations according to ontology."""
        pass


class DeterministicMockLLMAdapter(BaseLLMAdapter):
    """Deterministic Mock LLM for reproducible testing and local development without API keys."""

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Check if prompt is answering a multi-hop question
        prompt_lower = prompt.lower()
        if "omnimesh" in prompt_lower:
            return "Acme Cloud owns the OmniMesh distributed cache engine, having acquired its creator DataWeaver Inc. in 2024. [Citation: doc_acme_corp_v1_chunk_0001, doc_dataweaver_v1_chunk_0001]"
        elif "shieldpay" in prompt_lower and "standard" in prompt_lower:
            return "ShieldPay's encryption-at-rest provider (KryptonVault) complies with FIPS 140-3 Level 4. [Citation: doc_shieldpay_v1_chunk_0001, doc_kryptonvault_v1_chunk_0001]"
        elif "hypergraph" in prompt_lower and "founded" in prompt_lower:
            return "Apex Neural was founded by Dr. Elena Vance, who led the Synapse Project that developed the HyperGraph Routing Algorithm. [Citation: doc_novagen_synapse_v1_chunk_0001, doc_hypergraph_spec_v1_chunk_0001, doc_apex_neural_v1_chunk_0001]"
        elif "quantacore" in prompt_lower:
            return "The available documents do not contain evidence regarding who founded QuantaCore Systems or the release year of their processor."
        elif "helios energy" in prompt_lower:
            return "Helios Energy develops the SolarGrid-X utility-scale battery system and is operating in a commercial pilot phase."
        return "Deterministic response generated based on available evidence."

    async def extract_claims(
        self,
        chunk_text: str,
        section_header: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Rule-based deterministic extraction matching known entity patterns."""
        claims: List[Dict[str, Any]] = []
        text = chunk_text

        # Pattern 1: Acme Cloud acquired DataWeaver Inc.
        if "Acme Cloud" in text and "DataWeaver Inc." in text:
            claims.append({
                "subject": "Acme Cloud",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.ACQUIRED.value,
                "object": "DataWeaver Inc.",
                "object_type": EntityType.ORGANIZATION.value,
                "confidence": 0.95,
                "evidence": "Acme Cloud completed the strategic corporate acquisition of DataWeaver Inc."
            })
            claims.append({
                "subject": "DataWeaver Inc.",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.SUBSIDIARY_OF.value,
                "object": "Acme Cloud",
                "object_type": EntityType.ORGANIZATION.value,
                "confidence": 0.92,
                "evidence": "DataWeaver Inc. operates as a specialized data management subsidiary within Acme Cloud"
            })

        # Pattern 2: DataWeaver develops OmniMesh
        if "DataWeaver Inc." in text and "OmniMesh" in text:
            claims.append({
                "subject": "DataWeaver Inc.",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.DEVELOPS.value,
                "object": "OmniMesh",
                "object_type": EntityType.PRODUCT.value,
                "confidence": 0.98,
                "evidence": "DataWeaver Inc. is the primary creator and developer of OmniMesh"
            })

        # Pattern 3: ShieldPay uses KryptonVault
        if "ShieldPay" in text and "KryptonVault" in text:
            claims.append({
                "subject": "ShieldPay",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.USES_TECHNOLOGY.value,
                "object": "KryptonVault",
                "object_type": EntityType.TECHNOLOGY.value,
                "confidence": 0.94,
                "evidence": "ShieldPay integrates with KryptonVault as its designated cryptographic key management"
            })

        # Pattern 4: KryptonVault complies with FIPS 140-3 Level 4
        if "KryptonVault" in text and "FIPS 140-3 Level 4" in text:
            claims.append({
                "subject": "KryptonVault",
                "subject_type": EntityType.TECHNOLOGY.value,
                "relation": RelationType.COMPLIES_WITH.value,
                "object": "FIPS 140-3 Level 4",
                "object_type": EntityType.STANDARD.value,
                "confidence": 0.99,
                "evidence": "KryptonVault has successfully achieved full independent compliance with FIPS 140-3 Level 4"
            })

        # Pattern 5: Dr. Elena Vance leads Synapse Project
        if "Dr. Elena Vance" in text and "Synapse Project" in text:
            claims.append({
                "subject": "Dr. Elena Vance",
                "subject_type": EntityType.PERSON.value,
                "relation": RelationType.LEADS.value,
                "object": "Synapse Project",
                "object_type": EntityType.CONCEPT.value,
                "confidence": 0.96,
                "evidence": "The Synapse Project was led by Principal Scientist Dr. Elena Vance"
            })

        # Pattern 6: Synapse Project produced HyperGraph Routing Algorithm
        if "Synapse Project" in text and "HyperGraph Routing Algorithm" in text:
            claims.append({
                "subject": "HyperGraph Routing Algorithm",
                "subject_type": EntityType.TECHNOLOGY.value,
                "relation": RelationType.PRODUCED_BY.value,
                "object": "Synapse Project",
                "object_type": EntityType.CONCEPT.value,
                "confidence": 0.95,
                "evidence": "The primary engineering output of the Synapse Project is the HyperGraph Routing Algorithm"
            })

        # Pattern 7: Apex Neural founded by Dr. Elena Vance
        if "Apex Neural" in text and "Dr. Elena Vance" in text:
            claims.append({
                "subject": "Apex Neural",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.FOUNDED_BY.value,
                "object": "Dr. Elena Vance",
                "object_type": EntityType.PERSON.value,
                "confidence": 0.97,
                "evidence": "The company was founded by Dr. Elena Vance following her departure"
            })

        # Pattern 8: Helios Energy develops SolarGrid-X (ignoring prompt injection!)
        if "Helios Energy" in text and "SolarGrid-X" in text:
            claims.append({
                "subject": "Helios Energy",
                "subject_type": EntityType.ORGANIZATION.value,
                "relation": RelationType.DEVELOPS.value,
                "object": "SolarGrid-X",
                "object_type": EntityType.PRODUCT.value,
                "confidence": 0.93,
                "evidence": "Helios Energy develops the SolarGrid-X utility-scale battery storage system."
            })

        return claims


class OpenAICompatibleLLMAdapter(BaseLLMAdapter):
    """Adapter communicating with OpenAI or OpenAI-compatible endpoints."""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def extract_claims(
        self,
        chunk_text: str,
        section_header: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # In later phases, this invokes schema-guided extraction JSON mode
        # Fallback to mock if API key is not set
        if not self.api_key:
            return await DeterministicMockLLMAdapter().extract_claims(chunk_text, section_header)
        return []


def get_llm_adapter() -> BaseLLMAdapter:
    """Factory selecting the configured LLM adapter."""
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAICompatibleLLMAdapter(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model_name=settings.LLM_MODEL_NAME,
        )
    return DeterministicMockLLMAdapter()
