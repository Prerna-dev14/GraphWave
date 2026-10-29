# ADR-003: Hybrid Retrieval Planner and Bounded Graph Traversal

## Status
Accepted

## Context
Unconstrained graph traversals across interconnected enterprise knowledge graphs lead to exponential combinatorial fan-out ("supernode problem" or dense graph explosion), long database locks, query timeouts, and out-of-memory failures. Conversely, purely vector retrieval lacks topological context.

## Decision
GraphWeave implements a multi-stage Bounded Hybrid Retrieval Planner:
1. **Seed Retrieval**:
   - Query embedding is computed and compared via cosine similarity against chunk embeddings in PostgreSQL (pgvector).
   - Top-K seed chunks (default `K=5`) are fetched.
   - Seed entities linked to these chunks are extracted.
2. **Bounded Graph Expansion**:
   - Cypher queries traverse outgoing and incoming relationships from seed entities up to a strictly bounded depth:
     - `MAX_TRAVERSAL_DEPTH`: 2 hops maximum.
     - `MAX_FAN_OUT`: 15 relationships per node maximum.
     - `QUERY_BUDGET_MAX_NODES`: 100 total nodes maximum.
     - `TRAVERSAL_TIMEOUT_SECONDS`: 5.0 seconds strict timeout.
     - `Scope Enforcement`: Every Cypher pattern is strictly scoped: `WHERE r.tenant_id = $tenant_id AND r.corpus_id = $corpus_id`.
3. **Evidence Deduplication & Fusion**:
   - Graph relationships and supporting chunks are merged with vector seed chunks.
   - Relevance scoring combines vector similarity with graph proximity (hop distance decay factor: `1.0 / (1 + hop)`).
   - Evidence bundle is formatted with explicit paths and source snippets.

## Consequences
- Predictable query latencies under 500ms on local environments.
- Protection against denial-of-service via dense cluster traversal.
