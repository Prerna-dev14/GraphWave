"""GraphWeave Demo Data Seeder and Benchmark Pre-loader (Phase 7).

Ingests all 8 sample multi-hop documents into the primary corpus, triggers candidate
claim extraction, resolves canonical entities, and executes the comparative benchmark.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import settings
from app.core.logging import logger
from app.services.ingestion_service import ingestion_service
from app.services.evaluation_service import evaluation_service
from app.repositories.postgres_repository import postgres_repo
from app.repositories.neo4j_repository import neo4j_repo


async def seed_data():
    print("=" * 60)
    print("  GraphWeave (GWeave) — Demo Corpus & Benchmark Seeder")
    print("=" * 60)

    # Initialize repositories
    await postgres_repo.connect()
    await neo4j_repo.connect()
    await neo4j_repo.ensure_schema_constraints()

    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    if not sample_dir.exists():
        print(f"Error: Sample data directory not found at {sample_dir}")
        return

    md_files = sorted(sample_dir.glob("*.md"))
    print(f"\n[1/3] Found {len(md_files)} sample documents in {sample_dir.name}/")

    tenant_id = settings.DEFAULT_TENANT_ID
    corpus_id = settings.DEFAULT_CORPUS_ID

    for f in md_files:
        content = f.read_text(encoding="utf-8")
        doc, job = await ingestion_service.ingest_document(
            filename=f.name,
            content=content,
            tenant_id=tenant_id,
            corpus_id=corpus_id,
        )
        print(f"  [OK] Ingested: {f.name:<35} -> Chunks: {job.chunk_count}, Status: {job.status.value}")

    print(f"\n[2/3] Verified Entity Registry and Knowledge Graph edges:")
    from app.services.entity_resolution_service import entity_resolution_service
    entities = entity_resolution_service.list_canonical_entities(tenant_id, corpus_id)
    edges_count = len(getattr(neo4j_repo, "_mem_edges", []))
    print(f"  [OK] Canonical Entities: {len(entities)}")
    print(f"  [OK] Knowledge Graph Edges: {edges_count}")

    print(f"\n[3/3] Running Comparative Multi-Hop Benchmark (Vector vs Graph vs Hybrid)...")
    comparison = await evaluation_service.run_benchmark_comparison(
        max_depth=2,
        max_fan_out=15,
        tenant_id=tenant_id,
        corpus_id=corpus_id,
    )

    print("\nBenchmark Summary Results:")
    print("-" * 60)
    for run in comparison.runs:
        print(
            f"  Mode: {run.retrieval_mode.upper():<10} | "
            f"Recall: {(run.evidence_recall * 100):.0f}% | "
            f"Correctness: {(run.answer_correctness * 100):.0f}% | "
            f"Latency p50: {run.latency_p50_ms:.1f}ms"
        )
    print("-" * 60)
    print(f"Recommended Strategy: {comparison.recommended_mode.upper()} GraphRAG")
    print("=" * 60)
    print("Seeding complete. GraphWeave is ready for demo queries!\n")


if __name__ == "__main__":
    asyncio.run(seed_data())
