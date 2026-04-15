from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from boba.cli import app

runner = CliRunner()


def test_plan_command_writes_json_output() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    output_file = repo_root / "tmp" / "plan.json"
    result = runner.invoke(
        app,
        [
            "plan",
            "--spec",
            str(repo_root / "examples/workloads/spill-heavy.workload.yaml"),
            "--cluster",
            str(repo_root / "examples/workloads/local-kind.cluster.yaml"),
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["workload_name"] == "spill-heavy-parquet"


def test_benchmark_run_writes_artifacts() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = repo_root / "tmp" / "benchmark-run"
    result = runner.invoke(
        app,
        [
            "benchmark",
            "run",
            "--scenario",
            str(repo_root / "benchmarks/scenarios/spill-heavy-parquet.yaml"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "plan.json").exists()
    assert (output_dir / "explanation.md").exists()

