"""Rendering helpers for plans and benchmark artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from boba.models import BenchmarkRun, RecommendationPlan


def plan_to_markdown(plan: RecommendationPlan) -> str:
    lines = [
        f"# Plan for {plan.workload_name}",
        "",
        f"- Confidence: {plan.confidence:.2f}",
        f"- Findings: {len(plan.findings)}",
        f"- Cluster changes: {len(plan.cluster_shape)}",
        f"- Execution tuning changes: {len(plan.execution_tuning)}",
        "",
        "## Summary",
        "",
        plan.summary,
        "",
        "## Findings",
        "",
    ]
    if not plan.findings:
        lines.append("- No critical findings.")
    for finding in plan.findings:
        lines.append(f"- `{finding.severity}` `{finding.code}`: {finding.summary}")
        lines.append(f"  - {finding.detail}")
        for action in finding.recommended_actions:
            lines.append(f"  - Action: {action}")

    lines.extend(["", "## Cluster shape", ""])
    if not plan.cluster_shape:
        lines.append("- No cluster shape changes recommended.")
    for shape_item in plan.cluster_shape:
        lines.append(
            f"- `{shape_item.node_pool}`: {shape_item.current_nodes} -> "
            f"{shape_item.target_nodes} nodes. {shape_item.reason}"
        )

    lines.extend(["", "## Execution tuning", ""])
    if not plan.execution_tuning:
        lines.append("- No execution tuning changes recommended.")
    for tuning_item in plan.execution_tuning:
        lines.append(
            f"- `{tuning_item.stage}` `{tuning_item.parameter}`: "
            f"{tuning_item.current_value} -> {tuning_item.recommended_value}. "
            f"{tuning_item.reason}"
        )

    lines.extend(["", "## Decision trace", ""])
    for trace_item in plan.decision_trace:
        lines.append(f"- `{trace_item.rule}`: {trace_item.summary}")
    return "\n".join(lines)


def print_plan_table(plan: RecommendationPlan, console: Console) -> None:
    summary = Table(title=f"Boba Plan: {plan.workload_name}")
    summary.add_column("Category")
    summary.add_column("Value")
    summary.add_row("Confidence", f"{plan.confidence:.2f}")
    summary.add_row("Findings", str(len(plan.findings)))
    summary.add_row("Cluster changes", str(len(plan.cluster_shape)))
    summary.add_row("Execution tuning", str(len(plan.execution_tuning)))
    console.print(summary)

    if plan.findings:
        findings = Table(title="Findings")
        findings.add_column("Severity")
        findings.add_column("Code")
        findings.add_column("Summary")
        for finding in plan.findings:
            findings.add_row(finding.severity.value, finding.code, finding.summary)
        console.print(findings)


def model_to_json(model: RecommendationPlan | BenchmarkRun) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True)


def model_to_yaml(model: RecommendationPlan | BenchmarkRun) -> str:
    return yaml.safe_dump(model.model_dump(mode="json"), sort_keys=False)


def write_plan_output(path: Path, plan: RecommendationPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".json":
        path.write_text(model_to_json(plan), encoding="utf-8")
        return
    path.write_text(model_to_yaml(plan), encoding="utf-8")
