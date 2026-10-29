# ADR-001: GraphRAG Dual-Store Architecture (PostgreSQL + Neo4j)

## Status
Accepted

## Context
Standard Vector RAG embeds text chunks into a vector database and performs cosine similarity search. While this performs well for direct semantic lookup within single passages, it routinely fails on multi-hop questions where evidence is fragmented across multiple documents and linked through entity relationships (e.g., Company A acquired Company B, which developed Technology C; query: "Who owns Technology C?").

Pure Knowledge Graphs, on the other hand, can traverse structural relationships, but suffer from high extraction costs, schema brittleness, loss of unstructured nuances, and inability to handle exploratory or fuzzy semantic search.

## Decision
GraphWeave adopts a dual-store hybrid architecture:
1. **Relational & Vector Store (PostgreSQL with pgvector)**:
   - Stores documents, raw text chunks, ingestion jobs, extraction logs, entity alias tables, and chunk embedding vectors (1536-dim or configurable).
   - Responsible for lexical filtering, vector similarity retrieval (seed finding), and request/audit traces.
2. **Graph Store (Neo4j)**:
   - Stores extracted canonical entities (`Entity`), document nodes (`Document`), chunk nodes (`Chunk`), and typed directed edges (`RELATES_TO`, `MENTIONS`, `ALIAS_OF`).
   - Responsible for bounded neighborhood expansion (1 to 2 hops), shortest-path discovery, and relationship path retrieval.
3. **Evidence Fusion Layer**:
   - Fuses seed vector hits with graph-expanded nodes and paths.
   - Preserves complete document and chunk provenance for all traversed edges.
   - Synthesizes answers strictly backed by cited chunks and edge proofs.

## Consequences
- Requires synchronizing data ingestion between PostgreSQL and Neo4j.
- Ingestion is executed with idempotent operations: documents and chunks write to PostgreSQL first, followed by atomic and idempotent Cypher `MERGE` operations in Neo4j.
- Re-indexing or re-ingestion wipes and recreates the scoped graph subgraph deterministically using `tenant_id` and `corpus_id`.
