"""FastAPI Router for Evaluation Benchmark and Mode Tuning (Phase 6)."""
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.evaluation_schemas import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationComparisonResponse,
)
from app.schemas.retrieval_schemas import RetrievalMode
from app.services.evaluation_service import evaluation_service, EvaluationService
from app.repositories.postgres_repository import postgres_repo, PostgresRepository

router = APIRouter(prefix="/api/v1/evaluations", tags=["Evaluations"])


def get_eval_service() -> EvaluationService:
    return evaluation_service


def get_pg_repo() -> PostgresRepository:
    return postgres_repo


@router.post(
    "/run",
    response_model=Union[EvaluationComparisonResponse, EvaluationRunResponse],
    summary="Trigger Benchmark Evaluation Run",
    description="Executes automated multi-hop evaluation benchmark for a specific retrieval mode or across all modes.",
)
async def run_evaluation(
    req: EvaluationRunRequest,
    eval_svc: EvaluationService = Depends(get_eval_service),
):
    try:
        if req.retrieval_mode is None or req.retrieval_mode.lower() == "all":
            # Comparative run across all three modes
            return await eval_svc.run_benchmark_comparison(
                max_depth=req.max_depth,
                max_fan_out=req.max_fan_out,
                tenant_id=req.tenant_id,
                corpus_id=req.corpus_id,
            )
        else:
            mode = RetrievalMode(req.retrieval_mode.lower())
            return await eval_svc.run_evaluation_mode(
                mode=mode,
                max_depth=req.max_depth,
                max_fan_out=req.max_fan_out,
                tenant_id=req.tenant_id,
                corpus_id=req.corpus_id,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}",
        )


@router.get(
    "/compare",
    response_model=EvaluationComparisonResponse,
    summary="Get Comparative Evaluation Benchmark",
    description="Executes and returns a side-by-side benchmark comparing Vector-Only, Graph-Only, and Hybrid GraphRAG.",
)
async def get_comparative_benchmark(
    max_depth: int = Query(default=2, ge=1, le=4),
    max_fan_out: int = Query(default=15, ge=1, le=50),
    tenant_id: str = Query(default="tenant-default"),
    corpus_id: str = Query(default="corpus-primary"),
    eval_svc: EvaluationService = Depends(get_eval_service),
):
    try:
        return await eval_svc.run_benchmark_comparison(
            max_depth=max_depth,
            max_fan_out=max_fan_out,
            tenant_id=tenant_id,
            corpus_id=corpus_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparative evaluation failed: {str(e)}",
        )


@router.get(
    "/runs",
    response_model=List[EvaluationRunResponse],
    summary="List Evaluation Runs",
    description="Returns list of historical evaluation runs with aggregate quality and latency metrics.",
)
async def list_evaluation_runs(
    limit: int = Query(default=20, ge=1, le=100),
    pg_repo: PostgresRepository = Depends(get_pg_repo),
):
    try:
        runs = await pg_repo.list_evaluation_runs(limit=limit)
        return runs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evaluation runs: {str(e)}",
        )


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get Evaluation Run Details",
    description="Retrieves a specific evaluation run with individual test case results.",
)
async def get_evaluation_run(
    run_id: str,
    pg_repo: PostgresRepository = Depends(get_pg_repo),
):
    run = await pg_repo.get_evaluation_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found",
        )
    return run
