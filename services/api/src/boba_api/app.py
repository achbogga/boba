"""FastAPI application for Boba."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from boba.benchmark import build_benchmark_run
from boba.models import (
    BenchmarkRun,
    BenchmarkRunRequest,
    BenchmarkScenario,
    ExplainRequest,
    ExplainResponse,
    PlanRequest,
    RecommendationPlan,
    ValidationResult,
)
from boba.planner import explain_plan, generate_plan, validate_workload


def create_app() -> FastAPI:
    app = FastAPI(title="Boba API", version="0.1.0")
    runs: dict[str, BenchmarkRun] = {}

    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/plans", response_model=RecommendationPlan)
    def create_plan(request: PlanRequest) -> RecommendationPlan:
        return generate_plan(request.workload, request.cluster)

    @app.post("/v1/validations", response_model=ValidationResult)
    def create_validation(request: PlanRequest) -> ValidationResult:
        return validate_workload(request.workload, request.cluster)

    @app.post("/v1/explanations", response_model=ExplainResponse)
    def create_explanation(request: ExplainRequest) -> ExplainResponse:
        return ExplainResponse(markdown=explain_plan(request.plan))

    @app.post("/v1/benchmarks/runs", response_model=BenchmarkRun)
    def create_benchmark_run(request: BenchmarkRunRequest) -> BenchmarkRun:
        scenario = BenchmarkScenario(
            name=request.name,
            description=request.description,
            workload_file="inline",
            cluster_file="inline",
            expected_findings=request.expected_findings,
            notes=request.notes,
        )
        run = build_benchmark_run(scenario, request.workload, request.cluster, output_dir=None)
        runs[run.id] = run
        return run

    @app.get("/v1/benchmarks/runs/{run_id}", response_model=BenchmarkRun)
    def get_benchmark_run(run_id: str) -> BenchmarkRun:
        run = runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Benchmark run not found.")
        return run

    return app


app = create_app()

