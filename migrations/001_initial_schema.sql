-- GraphWeave Initial PostgreSQL Schema Migration
-- Enables pgvector, creates relational and provenance tables, and applies compound indexes.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(64) NOT NULL DEFAULT 'text/markdown',
    version VARCHAR(32) NOT NULL DEFAULT '1.0',
    raw_content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant_corpus ON documents (tenant_id, corpus_id);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents (tenant_id, corpus_id, filename);

-- 2. Chunks Table (with vector embeddings)
CREATE TABLE IF NOT EXISTS chunks (
    id VARCHAR(128) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    section_header VARCHAR(255),
    page_number INT DEFAULT 1,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_corpus ON chunks (tenant_id, corpus_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

-- 3. Ingestion Jobs Table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    document_id VARCHAR(64) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    chunk_count INT NOT NULL DEFAULT 0,
    extracted_entities_count INT NOT NULL DEFAULT 0,
    extracted_relations_count INT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_tenant_corpus ON ingestion_jobs (tenant_id, corpus_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON ingestion_jobs (status);

-- 4. Extraction Runs Table
CREATE TABLE IF NOT EXISTS extraction_runs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    document_id VARCHAR(64) NOT NULL,
    chunk_id VARCHAR(128) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    raw_claims JSONB NOT NULL,
    validated_claims_count INT NOT NULL DEFAULT 0,
    rejected_claims_count INT NOT NULL DEFAULT 0,
    execution_time_ms FLOAT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_extraction_runs_chunk ON extraction_runs (chunk_id);

-- 5. Entity Aliases Table
CREATE TABLE IF NOT EXISTS entity_aliases (
    canonical_id VARCHAR(128) NOT NULL,
    alias VARCHAR(255) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, corpus_id, canonical_id, alias)
);

-- 6. Evaluation Questions & Benchmark
CREATE TABLE IF NOT EXISTS evaluation_questions (
    id VARCHAR(64) PRIMARY KEY,
    category VARCHAR(64) NOT NULL,
    hops INT NOT NULL DEFAULT 1,
    question TEXT NOT NULL,
    expected_answer TEXT NOT NULL,
    expected_chunk_ids TEXT[] NOT NULL DEFAULT '{}',
    required_entities TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Evaluation Runs
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id VARCHAR(64) PRIMARY KEY,
    evaluation_dataset_version VARCHAR(32) NOT NULL,
    retrieval_mode VARCHAR(32) NOT NULL, -- 'vector_only', 'graph_only', 'hybrid'
    answer_correctness FLOAT,
    evidence_recall FLOAT,
    citation_precision FLOAT,
    latency_p50_ms FLOAT,
    latency_p95_ms FLOAT,
    token_cost_usd FLOAT,
    total_questions INT NOT NULL,
    metrics_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Request Traces and Telemetry
CREATE TABLE IF NOT EXISTS request_traces (
    request_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    corpus_id VARCHAR(64) NOT NULL,
    query_text TEXT,
    retrieval_mode VARCHAR(32),
    retrieved_chunk_count INT,
    traversed_graph_nodes_count INT,
    latency_total_ms FLOAT,
    latency_retrieval_ms FLOAT,
    latency_generation_ms FLOAT,
    tokens_prompt INT,
    tokens_completion INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_traces_tenant_corpus ON request_traces (tenant_id, corpus_id, created_at DESC);
