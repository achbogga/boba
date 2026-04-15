"""Benchmark helpers for file-backed scenario execution."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from boba.io import load_yaml_model, write_json, write_text, write_yaml
from boba.models import BenchmarkRun, BenchmarkScenario, ClusterInventory, WorkloadSpec
from boba.planner import explain_plan, generate_plan


def load_scenario(path: Path) -> BenchmarkScenario:
    return load_yaml_model(path, BenchmarkScenario)


def run_benchmark_scenario(scenario_path: Path, output_dir: Path) -> BenchmarkRun:
    scenario = load_scenario(scenario_path)
    base_dir = scenario_path.parent
    workload = load_yaml_model(base_dir / scenario.workload_file, WorkloadSpec)
    cluster = load_yaml_model(base_dir / scenario.cluster_file, ClusterInventory)
    return build_benchmark_run(scenario, workload, cluster, output_dir)


def build_benchmark_run(
    scenario: BenchmarkScenario,
    workload: WorkloadSpec,
    cluster: ClusterInventory,
    output_dir: Path | None = None,
) -> BenchmarkRun:
    plan = generate_plan(workload, cluster)
    findings = {finding.code for finding in plan.findings}
    matched = [code for code in scenario.expected_findings if code in findings]
    missing = [code for code in scenario.expected_findings if code not in findings]
    run = BenchmarkRun(
        id=uuid4().hex,
        scenario_name=scenario.name,
        plan=plan,
        matched_expected_findings=matched,
        missing_expected_findings=missing,
    )

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_json = output_dir / "plan.json"
        plan_yaml = output_dir / "plan.yaml"
        explanation = output_dir / "explanation.md"
        trace_json = output_dir / "decision-trace.json"
        summary_json = output_dir / "summary.json"

        write_json(plan_json, plan.model_dump(mode="json"))
        write_yaml(plan_yaml, plan.model_dump(mode="json"))
        write_text(explanation, explain_plan(plan))
        write_json(trace_json, [entry.model_dump(mode="json") for entry in plan.decision_trace])
        write_json(summary_json, run.model_dump(mode="json"))
        run.artifacts = {
            "plan_json": str(plan_json),
            "plan_yaml": str(plan_yaml),
            "explanation": str(explanation),
            "decision_trace": str(trace_json),
            "summary": str(summary_json),
        }

    return run

