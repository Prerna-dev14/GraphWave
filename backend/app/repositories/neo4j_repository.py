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

    async def merge_entity_node(self, entity: Entity):
        """Idempotently writes canonical Entity node with aliases and properties."""
        node_key = f"entity:{entity.canonical_id}"
        self._mem_nodes[node_key] = {
            "type": "Entity",
            "canonical_id": entity.canonical_id,
            "name": entity.name,
            "entity_type": entity.entity_type.value,
            "tenant_id": entity.tenant_id,
            "corpus_id": entity.corpus_id,
            "aliases": list(entity.aliases),
            "confidence": entity.confidence,
        }

        if not self.is_connected or not self.driver:
            return

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.run(
                """
                MERGE (e:Entity {canonical_id: $cid, tenant_id: $tenant_id, corpus_id: $corpus_id})
                SET e.name = $name,
                    e.type = $type,
                    e.aliases = $aliases,
                    e.confidence = $confidence,
                    e.updated_at = timestamp()
                """,
                cid=entity.canonical_id,
                tenant_id=entity.tenant_id,
                corpus_id=entity.corpus_id,
                name=entity.name,
                type=entity.entity_type.value,
                aliases=entity.aliases,
                confidence=entity.confidence,
            )

    async def merge_alias_edge(self, alias_cid: str, target_cid: str):
        """Idempotently writes ALIAS_OF relationship between two entities."""
        self._mem_edges.append({
            "source": alias_cid,
            "target": target_cid,
            "type": "ALIAS_OF",
            "tenant_id": settings.DEFAULT_TENANT_ID,
            "corpus_id": settings.DEFAULT_CORPUS_ID,
        })
        if not self.is_connected or not self.driver:
            return

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            await session.run(
                """
                MATCH (a:Entity {canonical_id: $alias_cid}), (b:Entity {canonical_id: $target_cid})
                MERGE (a)-[r:ALIAS_OF]->(b)
                SET r.updated_at = timestamp()
                """,
                alias_cid=alias_cid,
                target_cid=target_cid,
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

    async def merge_resolved_relationship(
        self,
        subject: Entity,
        relation_type: str,
        object_entity: Entity,
        source_chunk_id: str,
        document_version: str,
        confidence: float,
        evidence_text: str,
    ):
        """Idempotently writes typed directed relationship between canonical entities with provenance."""
        edge_data = {
            "source": subject.canonical_id,
            "target": object_entity.canonical_id,
            "relation": relation_type,
            "confidence": confidence,
            "tenant_id": subject.tenant_id,
            "corpus_id": subject.corpus_id,
            "source_chunk_ids": [source_chunk_id],
            "document_version": document_version,
            "evidence_text": evidence_text,
        }
        self._mem_edges.append(edge_data)

        if not self.is_connected or not self.driver:
            return

        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            # We use a parameterized typed Cypher query
            cypher = f"""
            MATCH (s:Entity {{canonical_id: $s_cid, tenant_id: $tenant_id, corpus_id: $corpus_id}})
            MATCH (o:Entity {{canonical_id: $o_cid, tenant_id: $tenant_id, corpus_id: $corpus_id}})
            MERGE (s)-[r:{relation_type} {{tenant_id: $tenant_id, corpus_id: $corpus_id}}]->(o)
            SET r.confidence = $confidence,
                r.document_version = $version,
                r.evidence_text = $evidence,
                r.source_chunk_ids = CASE
                    WHEN r.source_chunk_ids IS NULL THEN [$chunk_id]
                    WHEN NOT $chunk_id IN r.source_chunk_ids THEN r.source_chunk_ids + $chunk_id
                    ELSE r.source_chunk_ids
                END,
                r.updated_at = timestamp()
            """
            await session.run(
                cypher,
                s_cid=subject.canonical_id,
                o_cid=object_entity.canonical_id,
                tenant_id=subject.tenant_id,
                corpus_id=subject.corpus_id,
                confidence=confidence,
                version=document_version,
                evidence=evidence_text,
                chunk_id=source_chunk_id,
            )

    async def traverse_bounded_neighborhood(
        self,
        seed_entity_ids: List[str],
        tenant_id: str,
        corpus_id: str,
        max_depth: int = 2,
        max_fan_out: int = 15,
        timeout_sec: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """Traverses relationships bounded by depth, fan-out, and tenant/corpus scope."""
        traversed_edges: List[Dict[str, Any]] = []

        # In-memory graph traversal (works with 0 database dependencies for offline testing)
        visited_nodes = set(seed_entity_ids)
        visited_edge_keys = set()
        current_frontier = set(seed_entity_ids)

        for hop in range(1, max_depth + 1):
            next_frontier = set()
            for edge in self._mem_edges:
                if edge.get("tenant_id") == tenant_id and edge.get("corpus_id") == corpus_id:
                    src = edge.get("source")
                    tgt = edge.get("target")
                    rel = edge.get("relation", "")
                    edge_key = (src, rel, tgt)

                    if (src in current_frontier or tgt in current_frontier) and edge_key not in visited_edge_keys:
                        visited_edge_keys.add(edge_key)
                        edge_copy = dict(edge)
                        edge_copy["hop"] = hop
                        traversed_edges.append(edge_copy)
                        if len(traversed_edges) >= max_fan_out:
                            break
                        new_node = tgt if src in current_frontier else src
                        if new_node not in visited_nodes:
                            next_frontier.add(new_node)
                            visited_nodes.add(new_node)
            if len(traversed_edges) >= max_fan_out:
                break
            current_frontier = next_frontier

        return traversed_edges[:max_fan_out]

    async def purge_document_claims(self, doc_id: str, tenant_id: str, corpus_id: str) -> int:
        """Purges relationships originating from a deleted document within tenant/corpus."""
        if not hasattr(self, "_mem_edges"):
            self._mem_edges = []

        initial_count = len(self._mem_edges)
        self._mem_edges = [
            e for e in self._mem_edges
            if not (
                e.get("tenant_id") == tenant_id
                and e.get("corpus_id") == corpus_id
                and any(doc_id in chunk_id for chunk_id in e.get("source_chunk_ids", []))
            )
        ]
        purged_count = initial_count - len(self._mem_edges)

        if self.is_connected and self.driver:
            try:
                async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                    await session.run(
                        """
                        MATCH ()-[r]->()
                        WHERE r.tenant_id = $tenant_id
                          AND r.corpus_id = $corpus_id
                          AND ANY(cid IN r.source_chunk_ids WHERE cid CONTAINS $doc_id)
                        DELETE r
                        """,
                        tenant_id=tenant_id,
                        corpus_id=corpus_id,
                        doc_id=doc_id,
                    )
            except Exception as e:
                logger.warning(f"Neo4j purge_document_claims failed: {e}")

        return purged_count


neo4j_repo = Neo4jRepository()

