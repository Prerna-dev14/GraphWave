"""Integration tests for Phase 6 evaluation benchmark runner and comparative reporting."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_evaluation_run_single_mode_api():
    """Runs the benchmark suite for HYBRID mode via API and verifies metrics schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_data = {
            "retrieval_mode": "hybrid",
            "max_depth": 2,
            "max_fan_out": 15,
            "tenant_id": "tenant-eval-test",
            "corpus_id": "corpus-eval-test",
        }
        response = await client.post("/api/v1/evaluations/run", json=req_data)
        assert response.status_code == 200
        data = response.json()

        assert data["id"].startswith("eval_run_hybrid")
        assert data["retrieval_mode"] == "hybrid"
        assert data["total_questions"] == 5
        assert data["answer_correctness"] >= 0.70
        assert data["evidence_recall"] >= 0.70
        assert data["citation_precision"] >= 0.50
        assert data["latency_p50_ms"] >= 0.0
        assert data["token_cost_usd"] >= 0.0
        assert len(data["metrics_detail"]) == 5


@pytest.mark.asyncio
async def test_evaluation_comparison_api():
    """Executes side-by-side benchmark comparison and proves GraphRAG superiority over vector-only."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/evaluations/compare?tenant_id=tenant-compare&corpus_id=corpus-compare")
        assert response.status_code == 200
        data = response.json()

        assert data["dataset_version"] == "1.0.0"
        assert data["recommended_mode"] == "hybrid"
        assert len(data["runs"]) == 3

        runs_by_mode = {r["retrieval_mode"]: r for r in data["runs"]}
        assert "vector" in runs_by_mode
        assert "graph" in runs_by_mode
        assert "hybrid" in runs_by_mode

        hybrid_run = runs_by_mode["hybrid"]
        vector_run = runs_by_mode["vector"]

        # Empirical proof: Hybrid GraphRAG achieves higher evidence recall than Vector-Only
        assert hybrid_run["evidence_recall"] > vector_run["evidence_recall"]
        assert hybrid_run["answer_correctness"] >= vector_run["answer_correctness"]


@pytest.mark.asyncio
async def test_list_and_get_evaluation_runs_api():
    """Tests listing past runs and retrieving single run detail by ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First ensure at least one run exists
        run_req = {
            "retrieval_mode": "hybrid",
            "tenant_id": "tenant-test",
            "corpus_id": "corpus-test",
        }
        create_resp = await client.post("/api/v1/evaluations/run", json=run_req)
        assert create_resp.status_code == 200
        created_id = create_resp.json()["id"]

        # List runs
        list_resp = await client.get("/api/v1/evaluations/runs?limit=10")
        assert list_resp.status_code == 200
        runs = list_resp.json()
        assert len(runs) >= 1
        assert any(r["id"] == created_id for r in runs)

        # Get specific run
        get_resp = await client.get(f"/api/v1/evaluations/runs/{created_id}")
        assert get_resp.status_code == 200
        run_detail = get_resp.json()
        assert run_detail["id"] == created_id
        assert run_detail["total_questions"] == 5
