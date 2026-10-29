# GraphWeave (GWeave)

> **GraphRAG for Multi-Hop Cross-Document Retrieval with Verifiable Provenance**

GraphWeave combines vector similarity retrieval (PostgreSQL + pgvector) with bounded knowledge graph traversal (Neo4j) to answer multi-hop questions whose evidence is distributed across multiple corporate documents. Every relationship used in an answer links to deterministic source chunk IDs and document versions.

---

## Architecture Overview

```
                      +-----------------------------+
                      |       GraphWeave UI         |
                      |   (React + Vite + Tailwind) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |     FastAPI Backend API     |
                      |  (Pydantic, Async, Tracing) |
                      +-------+--------------+------+
                              |              |
                +-------------+              +-------------+
                v                                          v
+-------------------------------+          +-------------------------------+
|     PostgreSQL + pgvector     |          |       Neo4j Graph Store       |
|  - Raw Documents & Metadata   |          |  - Canonical Entity Nodes     |
|  - Boundary-Aware Chunks      |          |  - Typed Directed Relations   |
|  - Chunk Vector Embeddings    |          |  - Chunk & Document Nodes     |
|  - Ingestion & Audit Traces   |          |  - Complete Provenance Anchor |
+-------------------------------+          +-------------------------------+
```

---

## Repository Structure

```
GraphWeave/
├── backend/
│   ├── app/
│   │   ├── adapters/          # Replaceable LLM & Embedding adapters (Mock + OpenAI)
│   │   ├── api/v1/            # Health, Document Ingestion, and Job routes
│   │   ├── core/              # Config, structured logging, custom error envelopes
│   │   ├── domain/            # Knowledge graph ontology, provenance models, core entities
│   │   ├── repositories/      # PostgreSQL & Neo4j clients with resilient test fallbacks
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Boundary-aware parser, deterministic chunker, ingestion
│   ├── tests/
│   │   ├── unit/              # Ontology, provenance, chunking, and adapter tests
│   │   └── integration/       # API contract and ingestion pipeline tests
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── evaluation/            # Multi-hop benchmark dataset v1 with 5 test cases
│   └── sample/                # Curated markdown benchmark documents + injection test
├── docs/                      # Master specification, implementation guide, ADRs, threat model
│   ├── architecture/          # ADR-001, ADR-002, ADR-003
│   └── threat-model/          # Indirect prompt injection, DoS, and scope isolation controls
├── frontend/
│   ├── src/                   # React + TypeScript + Vite + Tailwind frontend shell
│   └── Dockerfile
├── infra/
│   └── docker-compose.yml     # PostgreSQL 16 + pgvector, Neo4j 5, Backend, Frontend
├── migrations/                # 001_initial_schema.sql and migration runner
├── .env.example
├── .gitignore
└── README.md
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 20+ and npm
- Docker & Docker Compose (optional for fully containerized run)

### 2. Environment Configuration
```bash
cp .env.example .env
```

### 3. Running with Docker Compose
```bash
docker compose -f infra/docker-compose.yml up --build -d
```
- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

### 4. Running Locally for Development
#### Backend:
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## Automated Tests

Run the full backend test suite:
```bash
$env:PYTHONPATH="backend"; .\.venv\Scripts\pytest.exe backend\tests -v
```

Build the frontend bundle:
```bash
cd frontend
npm run build
```

---

## Phase Status and Next Steps

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Ontology, Provenance Model, Multi-Hop Benchmark Dataset, ADRs | **COMPLETED** |
| **Phase 1** | Repo Setup, Postgres/pgvector & Neo4j Config, Health Checks, Ingestion Skeleton, Frontend Shell | **COMPLETED** |
| **Phase 2** | Extraction Pipeline: Schema Constraints, Confidence Thresholding, Prompt Injection Defense, Audit Logs | **COMPLETED** |
| **Phase 3** | Entity Resolution & Graph Writes: Normalization, Aliases, Ambiguity Queue, Idempotent Writes | **COMPLETED** |
| **Phase 4** | Hybrid Retrieval Planner: Vector Seed + Bounded Cypher Expansion & Evidence Fusion | **COMPLETED** |
| **Phase 5** | Answer Synthesis with Exact Citations & Interactive Graph Visualizer UI | **READY FOR APPROVAL** |
| **Phase 6** | Automated Multi-Hop Evaluation Benchmark Execution (Vector vs Graph vs Hybrid) | Planned |
| **Phase 7** | System Hardening, Tenant Scoping, Rate Limiting, Release Candidate | Planned |
