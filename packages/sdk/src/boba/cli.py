"""Typer CLI for the Boba prototype."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from boba.benchmark import run_benchmark_scenario
from boba.io import load_plan, load_yaml_model
from boba.models import BenchmarkRun, ClusterInventory, RecommendationPlan, WorkloadSpec
from boba.planner import explain_plan, generate_plan, validate_workload
from boba.renderers import model_to_json, model_to_yaml, print_plan_table, write_plan_output

app = typer.Typer(help="Boba advisor-mode CLI.")
benchmark_app = typer.Typer(help="Run file-backed benchmark scenarios.")
demo_app = typer.Typer(help="Manage the local KubeRay demo environment.")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(demo_app, name="demo")

console = Console()


def _render_plan(plan: RecommendationPlan, output_format: str) -> None:
    if output_format == "json":
        console.print(model_to_json(plan))
        return
    if output_format == "yaml":
        console.print(model_to_yaml(plan))
        return
    print_plan_table(plan, console)


@app.command()
def plan(
    spec: Annotated[Path, typer.Option(help="Path to a workload YAML file.")],
    cluster: Annotated[Path, typer.Option(help="Path to a cluster inventory YAML file.")],
    output: Annotated[Path | None, typer.Option(help="Optional output path.")] = None,
    output_format: Annotated[str, typer.Option("--format", help="table, json, or yaml.")] = "table",
) -> None:
    workload = load_yaml_model(spec, WorkloadSpec)
    inventory = load_yaml_model(cluster, ClusterInventory)
    plan_payload = generate_plan(workload, inventory)
    _render_plan(plan_payload, output_format)
    if output is not None:
        write_plan_output(output, plan_payload)


@app.command()
def validate(
    spec: Annotated[Path, typer.Option(help="Path to a workload YAML file.")],
    cluster: Annotated[Path, typer.Option(help="Path to a cluster inventory YAML file.")],
    output_format: Annotated[str, typer.Option("--format", help="table, json, or yaml.")] = "table",
) -> None:
    workload = load_yaml_model(spec, WorkloadSpec)
    inventory = load_yaml_model(cluster, ClusterInventory)
    result = validate_workload(workload, inventory)
    _render_plan(result.plan, output_format)
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def explain(
    plan_file: Annotated[Path, typer.Option(help="Path to a plan JSON or YAML file.")],
    output: Annotated[Path | None, typer.Option(help="Optional markdown output file.")] = None,
) -> None:
    plan_payload = load_plan(plan_file, RecommendationPlan)
    markdown = explain_plan(plan_payload)
    console.print(markdown)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")


@benchmark_app.command("run")
def benchmark_run(
    scenario: Annotated[Path, typer.Option(help="Path to a benchmark scenario YAML file.")],
    output_dir: Annotated[
        Path | None,
        typer.Option(help="Directory for generated artifacts."),
    ] = None,
) -> None:
    resolved_output = output_dir or Path("benchmarks/output") / scenario.stem
    run = run_benchmark_scenario(scenario, resolved_output)
    console.print(model_to_json(run))


@benchmark_app.command("report")
def benchmark_report(
    summary_file: Annotated[Path, typer.Option(help="Path to a benchmark summary JSON file.")],
) -> None:
    run = load_plan(summary_file, BenchmarkRun)
    console.print(model_to_json(run))


def _run_demo_script(script_name: str, profile: str) -> None:
    repo_root = Path(__file__).resolve().parents[4]
    script = repo_root / "scripts" / script_name
    result = subprocess.run([str(script), profile], check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@demo_app.command("up")
def demo_up(
    profile: Annotated[str, typer.Option(help="Demo profile to reference.")] = "kind",
) -> None:
    _run_demo_script("demo-up.sh", profile)


@demo_app.command("down")
def demo_down(
    profile: Annotated[str, typer.Option(help="Demo profile to reference.")] = "kind",
) -> None:
    _run_demo_script("demo-down.sh", profile)


@demo_app.command("status")
def demo_status(
    profile: Annotated[str, typer.Option(help="Demo profile to reference.")] = "kind",
) -> None:
    _run_demo_script("demo-status.sh", profile)
