# ADR-002: Provenance Tracking and Candidate Claim Semantics

## Status
Accepted

## Context
LLM information extraction is inherently probabilistic and prone to hallucinated relationships, faulty co-reference resolution, and misattributed facts. If extracted graph triples are treated as ground truth, the knowledge graph accumulates corrupted facts that poison multi-hop inference. Furthermore, users cannot verify why an answer was generated if citations cannot pinpoint exact source sentences.

## Decision
1. **Candidate Claims Model**:
   - All extracted entities and relationships are stored initially with status `CANDIDATE` and an explicit confidence score in `[0.0, 1.0]`.
   - Only claims exceeding the configurable threshold (default `0.65`) participate in active graph traversal, or they require validation against extraction rules.
2. **Mandatory Provenance Anchors**:
   - Every relationship stored in Neo4j and PostgreSQL must contain:
     - `source_chunk_ids`: List of deterministic chunk IDs supporting this relationship.
     - `doc_versions`: Document version string (e.g. `1.0`).
     - `tenant_id` & `corpus_id`: Strict isolation boundary.
     - `extraction_model`: Identifier of extraction LLM/model.
     - `confidence`: Confidence score assigned during extraction.
     - `created_at`: ISO timestamp.
3. **Deterministic Identification**:
   - `document_id`: SHA-256 of `(tenant_id, corpus_id, doc_name, content)`.
   - `chunk_id`: Formatted as `doc_{doc_id[:12]}_v{version}_chunk_{chunk_index:04d}`.
   - `canonical_id`: Slugified lowercase normalized entity name scoped by entity type (e.g., `org:acme_cloud`).
4. **Answer Grounding Rule**:
   - Answer synthesis prompts are forbidden from asserting relationships that do not exist in the evidence bundle. If evidence is missing, the synthesizer is mandated to return an explicit missing evidence disclaimer.

## Consequences
- Every answer can render exact interactive citation tags linking to original chunk text.
- Malformed or noisy extractions can be pruned or re-evaluated without database corruption.
