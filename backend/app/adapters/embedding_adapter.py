"""Replaceable Embedding Adapter Interface and Implementations.
Includes a Deterministic Mock Embedding Adapter producing normalized unit vectors.
"""
from abc import ABC, abstractmethod
from typing import List
import hashlib
import numpy as np

from app.core.config import settings


class BaseEmbeddingAdapter(ABC):
    """Abstract interface for text embedding generation."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single query or chunk into a floating-point vector."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text chunks into vectors."""
        pass


class DeterministicMockEmbeddingAdapter(BaseEmbeddingAdapter):
    """Generates deterministic pseudo-random unit vectors seeded by text hash.
    Preserves semantic pseudo-similarity for identical words while operating offline with 0 dependencies.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _generate_vector(self, text: str) -> List[float]:
        clean_text = text.strip().lower()
        # Seed NumPy PRNG deterministically from SHA256 of text
        digest = hashlib.sha256(clean_text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        rng = np.random.RandomState(seed)

        # Generate Gaussian vector and normalize to unit sphere
        vec = rng.randn(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class OpenAICompatibleEmbeddingAdapter(BaseEmbeddingAdapter):
    """Generates embeddings using an OpenAI or compatible HTTP endpoint."""

    def __init__(self, api_key: str, base_url: str, model_name: str, dimension: int = 1536):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.dimension = dimension

    async def embed_text(self, text: str) -> List[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        import httpx
        if not self.api_key:
            return await DeterministicMockEmbeddingAdapter(self.dimension).embed_batch(texts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


def get_embedding_adapter() -> BaseEmbeddingAdapter:
    """Factory selecting the configured embedding adapter."""
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAICompatibleEmbeddingAdapter(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model_name=settings.EMBEDDING_MODEL_NAME,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    return DeterministicMockEmbeddingAdapter(dimension=settings.EMBEDDING_DIMENSION)
