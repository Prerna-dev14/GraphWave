# GraphWeave Operations, Deployment & Runbook

**Version:** 1.0.0  
**Target Audience:** DevOps Engineers, Platform Engineers, Full-Stack AI Engineers  
**System Scope:** PostgreSQL 16 + pgvector, Neo4j 5 Enterprise/Community, FastAPI Backend, React/Vite Frontend

---

## 1. Local Development Quickstart

### Step 1: Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Default credentials:
- PostgreSQL: `postgres:postgres@localhost:5432/graphweave`
- Neo4j: `neo4j:graphweave_secret@localhost:7687` (HTTP Browser on `7474`)
- Provider Mode: `LLM_PROVIDER=mock`, `EMBEDDING_PROVIDER=mock` (Zero API keys required for offline testing)

### Step 2: Launch Databases with Docker Compose
```bash
docker compose -f infra/docker-compose.yml up postgres neo4j -d
```
Check health:
```bash
curl http://localhost:8000/health/ready
```

### Step 3: Run Database Migrations
Run the database migrations:
```bash
python migrations/run_migrations.py
```

### Step 4: Seed Demo Data and Run Benchmark
Ingest the 8 benchmark documents and run the comparative evaluation:
```bash
$env:PYTHONPATH="backend"
python scripts/seed_demo_data.py
```

### Step 5: Start Backend and Frontend
#### Backend:
```bash
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
#### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 2. Docker Compose Production Deployment

To run all four services (Postgres, Neo4j, FastAPI Backend, Nginx Frontend) in Docker:
```bash
docker compose -f infra/docker-compose.yml up --build -d
```
Service Endpoints:
- Frontend Application: `http://localhost:5173`
- Backend API & OpenAPI Docs: `http://localhost:8000/docs`
- Neo4j Browser Console: `http://localhost:7474`
- PostgreSQL Port: `localhost:5432`

---

## 3. Operational Troubleshooting

### A. Neo4j Constraints & Schema Initialization
If Neo4j starts up without indexes, constraints can be recreated idempotently:
```cypher
CREATE CONSTRAINT entity_canonical_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.canonical_id IS UNIQUE;

CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX edge_tenant_corpus_index IF NOT EXISTS
FOR ()-[r:RELATION]-() ON (r.tenant_id, r.corpus_id);
```
GraphWeave automatically invokes `await neo4j_repo.ensure_schema_constraints()` at FastAPI startup.

### B. Neo4j Memory Tuning
In high-volume corpora, adjust memory in `infra/docker-compose.yml`:
- `NEO4J_dbms_memory_heap_initial__size: 1G`
- `NEO4J_dbms_memory_heap_max__size: 2G`
- `NEO4J_dbms_memory_pagecache_size: 1G`

### C. Database Connection Loss & Recovery
- Both `PostgresRepository` and `Neo4jRepository` implement transparent fallback to in-memory mocks during unit testing or network partition.
- When live services recover, connection retries are automatically handled by asyncpg pool and the Neo4j Python async driver.

### D. Multi-Tenant Purge & Document Deletion
When a document is purged via `DELETE /api/v1/documents/{document_id}`:
1. All chunks in Postgres are deleted.
2. All candidate claims in Postgres are deleted.
3. All graph edges originating from that document are deleted in Neo4j within the tenant/corpus boundary.

---

## 4. Switching from Offline Mock to Live LLM & Embeddings

In `.env`, set:
```ini
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```
Restart backend. The architecture automatically switches adapters via factory pattern without modifying any business logic.
