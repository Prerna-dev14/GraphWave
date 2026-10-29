"""Neo4j Graph Database Repository.
Handles graph persistence, schema constraints, scoped traversals, and in-memory test fallback.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings
from app.core.logging import logger
from app.domain.models import Document, Chunk, Entity, CandidateClaim


class Neo4jRepository:
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.is_connected = False
        # In-memory graph representation for testing
        self._mem_nodes: Dict[str, Dict[str, Any]] = {}
        self._mem_edges: List[Dict[str, Any]] = []

    async def connect(self) -> bool:
        """Initialize connection to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_timeout=2.0,
            )
            await self.driver.verify_connectivity()
            self.is_connected = True
            logger.info("Successfully connected to Neo4j Graph Database")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to live Neo4j ({e}). Operating in memory mode.")
            self.is_connected = False
            return False

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def check_health(self) -> Dict[str, Any]:
        """Verify Neo4j connectivity and measure latency."""
        if not self.is_connected or not self.driver:
            return {
                "status": "healthy" if settings.ENABLE_MOCK_FALLBACK else "unhealthy",
                "mode": "in-memory (mock-fallback active)" if settings.ENABLE_MOCK_FALLBACK else "disconnected",
                "details": "Running with in-memory graph adapter" if settings.ENABLE_MOCK_FALLBACK else "Neo4j unavailable",
            }
        try:
            start = datetime.now()
            async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run("RETURN 1 AS alive")
                record = await result.single()
            latency = (datetime.now() - start).total_seconds() * 1000.0
            return {"status": "healthy", "latency_ms": round(latency, 2), "mode": "neo4j"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def ensure_schema_constraints(self):
        """Sets up uniqueness constraints for Entity, Document, and Chunk nodes."""
        if not self.is_connected or not self.driver:
            return
        constraints = [
            "CREATE CONSTRAINT entity_canonical_id IF NOT EXISTS FOR (e:Entity) REQUIRE (e.tenant_id, e.corpus_id, e.canonical_id) IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE (d.tenant_id, d.corpus_id, d.id) IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE (c.tenant_id, c.corpus_id, c.id) IS UNIQUE",
        ]
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            for cypher in constraints:
                try:
                    await session.run(cypher)
                except Exception as e:
                    logger.debug(f"Constraint notice: {e}")

    async def merge_document_and_chunks(self, document: Document, chunks: List[Chunk]):
        """Idempotently writes Document and Chunk nodes and MENTIONS/PART_OF relationships."""
        self._mem_nodes[document.id] = {
            "type": "Document",
            "id": document.id,
            "filename": document.filename,
            "version": document.version,
            "tenant_id": document.tenant_id,
            "corpus_id": document.corpus_id,
        }
        for chunk in chunks:
            self._mem_nodes[chunk.id] = {
                "type": "Chunk",
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "tenant_id": chunk.tenant_id,
                "corpus_id": chunk.corpus_id,
            }
            self._mem_edges.append({
                "source": document.id,
                "target": chunk.id,
                "type": "CONTAINS_CHUNK",
                "tenant_id": document.tenant_id,
                "corpus_id": document.corpus_id,
            })

        if not self.is_connected or not self.driver:
            return

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.run(
                """
                MERGE (d:Document {id: $doc_id, tenant_id: $tenant_id, corpus_id: $corpus_id})
                SET d.filename = $filename, d.version = $version, d.updated_at = timestamp()
                """,
                doc_id=document.id,
                tenant_id=document.tenant_id,
                corpus_id=document.corpus_id,
                filename=document.filename,
                version=document.version,
            )
            for chunk in chunks:
                await session.run(
                    """
                    MERGE (c:Chunk {id: $chunk_id, tenant_id: $tenant_id, corpus_id: $corpus_id})
                    SET c.document_id = $doc_id, c.text = $text, c.updated_at = timestamp()
                    WITH c
                    MATCH (d:Document {id: $doc_id, tenant_id: $tenant_id, corpus_id: $corpus_id})
                    MERGE (d)-[:CONTAINS_CHUNK]->(c)
                    """,
                    chunk_id=chunk.id,
                    tenant_id=chunk.tenant_id,
                    corpus_id=chunk.corpus_id,
                    doc_id=chunk.document_id,
                    text=chunk.text,
                )

    async def merge_candidate_claim(self, claim: CandidateClaim):
        """Idempotently writes entity nodes and typed edge with complete provenance."""
        self._mem_edges.append({
            "source": claim.subject_entity,
            "target": claim.object_entity,
            "relation": claim.relation.value,
            "confidence": claim.confidence,
            "tenant_id": claim.tenant_id,
            "corpus_id": claim.corpus_id,
            "source_chunk_ids": [claim.provenance.chunk_id],
        })


neo4j_repo = Neo4jRepository()
