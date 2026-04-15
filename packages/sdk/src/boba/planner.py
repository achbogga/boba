"""Deterministic advisor-mode planning logic."""

from __future__ import annotations

from math import ceil

from boba.models import (
    Accelerator,
    AutoscalingSignal,
    ClusterInventory,
    ClusterShapeRecommendation,
    DecisionTraceEntry,
    EvidencePoint,
    ExecutionTuningRecommendation,
    Finding,
    FindingCategory,
    RecommendationPlan,
    Severity,
    StageSpec,
    ValidationResult,
    WorkloadSpec,
)
from boba.renderers import plan_to_markdown


def _stage_pool_candidates(stage: StageSpec, cluster: ClusterInventory) -> list[tuple[str, int]]:
    candidates: list[tuple[str, int]] = []
    for pool in cluster.node_pools:
        capacity = pool.capacity_for(stage)
        if capacity > 0:
            candidates.append((pool.name, capacity))
    return candidates


def _add_finding(
    findings: list[Finding],
    code: str,
    severity: Severity,
    category: FindingCategory,
    summary: str,
    detail: str,
    evidence: list[EvidencePoint],
    actions: list[str],
) -> None:
    findings.append(
        Finding(
            code=code,
            severity=severity,
            category=category,
            summary=summary,
            detail=detail,
            evidence=evidence,
            recommended_actions=actions,
        )
    )


def generate_plan(spec: WorkloadSpec, cluster: ClusterInventory) -> RecommendationPlan:
    findings: list[Finding] = []
    cluster_shape: list[ClusterShapeRecommendation] = []
    execution_tuning: list[ExecutionTuningRecommendation] = []
    autoscaling_signals: list[AutoscalingSignal] = []
    decision_trace: list[DecisionTraceEntry] = []
    confidence = 0.95

    total_working_set = 0.0
    block_size_mib = spec.dataset.block_size_mib
    recommended_block_size = max(64, min(256, int(cluster.object_store_memory_gib * 1024 * 0.12)))

    if block_size_mib > cluster.object_store_memory_gib * 1024 * 0.25:
        _add_finding(
            findings,
            code="spill.block_size_too_large",
            severity=Severity.WARNING,
            category=FindingCategory.SPILL_RISK,
            summary="Dataset block size is large relative to object store memory.",
            detail=(
                f"Configured block size is {block_size_mib} MiB while the object store has "
                f"{cluster.object_store_memory_gib:.1f} GiB."
            ),
            evidence=[
                EvidencePoint(
                    metric="dataset.block_size_mib",
                    observed=str(block_size_mib),
                    threshold=f"<= {cluster.object_store_memory_gib * 1024 * 0.25:.0f}",
                    rationale="Oversized blocks amplify object-store pressure and spill risk.",
                )
            ],
            actions=[
                f"Reduce dataset.block_size_mib to about {recommended_block_size} MiB.",
            ],
        )
        execution_tuning.append(
            ExecutionTuningRecommendation(
                stage="dataset",
                parameter="block_size_mib",
                current_value=str(block_size_mib),
                recommended_value=str(recommended_block_size),
                reason="Keep blocks small enough to fit safely in the object store.",
            )
        )
        decision_trace.append(
            DecisionTraceEntry(
                rule="dataset.block_size_guardrail",
                summary="Flagged large dataset blocks against object-store memory.",
                inputs={
                    "dataset_block_size_mib": block_size_mib,
                    "object_store_memory_gib": cluster.object_store_memory_gib,
                },
            )
        )

    for index, stage in enumerate(spec.stages):
        if stage.block_size_mib is None:
            confidence -= 0.02
        total_working_set += stage.effective_concurrency * stage.working_set_per_worker_gib
        candidates = _stage_pool_candidates(stage, cluster)
        if not candidates:
            _add_finding(
                findings,
                code=f"sched.{stage.name}.unschedulable",
                severity=Severity.ERROR,
                category=FindingCategory.SCHEDULABILITY,
                summary=f"Stage `{stage.name}` does not fit on any node pool.",
                detail=(
                    f"The stage needs {stage.cpu_per_worker} CPU, "
                    f"{stage.memory_gib_per_worker} GiB memory, and "
                    f"{stage.gpu_per_worker} GPU per worker."
                ),
                evidence=[
                    EvidencePoint(
                        metric="stage.resource_shape",
                        observed=(
                            f"cpu={stage.cpu_per_worker}, mem={stage.memory_gib_per_worker}, "
                            f"gpu={stage.gpu_per_worker}"
                        ),
                        threshold="fit within at least one node pool",
                        rationale="Unschedulable stages stall before useful work starts.",
                    )
                ],
                actions=[
                    "Reduce per-worker resources for "
                    f"`{stage.name}` or add a compatible node pool.",
                ],
            )
            decision_trace.append(
                DecisionTraceEntry(
                    rule="stage.shape_fits_pool",
                    summary=f"No node pool can host the `{stage.name}` worker shape.",
                    inputs={
                        "stage": stage.name,
                        "accelerator": stage.accelerator.value,
                    },
                )
            )
            continue

        selected_pool_name, workers_per_node = max(candidates, key=lambda item: item[1])
        selected_pool = next(pool for pool in cluster.node_pools if pool.name == selected_pool_name)
        desired_workers = max(stage.parallelism, stage.effective_concurrency)
        target_nodes = ceil(desired_workers / workers_per_node)
        if target_nodes > selected_pool.available_nodes:
            cluster_shape.append(
                ClusterShapeRecommendation(
                    node_pool=selected_pool.name,
                    current_nodes=selected_pool.available_nodes,
                    target_nodes=min(target_nodes, selected_pool.max_nodes),
                    reason=(
                        f"Stage `{stage.name}` needs about {desired_workers} workers on "
                        f"{selected_pool.name}."
                    ),
                )
            )
            if target_nodes > selected_pool.max_nodes:
                _add_finding(
                    findings,
                    code=f"sched.{stage.name}.capacity_exceeded",
                    severity=Severity.ERROR,
                    category=FindingCategory.CLUSTER_SHAPE,
                    summary=(
                        f"Stage `{stage.name}` exceeds the max size of "
                        f"`{selected_pool.name}`."
                    ),
                    detail=(
                        f"Estimated need is {target_nodes} nodes but the node pool caps at "
                        f"{selected_pool.max_nodes}."
                    ),
                    evidence=[
                        EvidencePoint(
                            metric="node_pool.max_nodes",
                            observed=str(target_nodes),
                            threshold=f"<= {selected_pool.max_nodes}",
                            rationale="The workload cannot autoscale into unavailable capacity.",
                        )
                    ],
                    actions=[
                        f"Increase `{selected_pool.name}` max_nodes or lower "
                        f"`{stage.name}` concurrency.",
                    ],
                )
            else:
                autoscaling_signals.append(
                    AutoscalingSignal(
                        node_pool=selected_pool.name,
                        requested_additional_nodes=target_nodes - selected_pool.available_nodes,
                        reason=f"Pre-scale `{selected_pool.name}` for stage `{stage.name}`.",
                    )
                )
        decision_trace.append(
            DecisionTraceEntry(
                rule="stage.worker_to_pool_mapping",
                summary=f"Mapped `{stage.name}` to `{selected_pool.name}`.",
                inputs={
                    "stage": stage.name,
                    "selected_pool": selected_pool.name,
                    "workers_per_node": workers_per_node,
                    "desired_workers": desired_workers,
                    "target_nodes": target_nodes,
                },
            )
        )

        if stage.accelerator == Accelerator.GPU and index > 0:
            previous_stage = spec.stages[index - 1]
            if previous_stage.parallelism > stage.effective_concurrency * 4:
                recommended_parallelism = stage.effective_concurrency * 2
                _add_finding(
                    findings,
                    code=f"balance.{previous_stage.name}_to_{stage.name}",
                    severity=Severity.WARNING,
                    category=FindingCategory.PIPELINE_BALANCE,
                    summary="Upstream CPU stage is likely to outrun the downstream GPU stage.",
                    detail=(
                        f"`{previous_stage.name}` runs at parallelism {previous_stage.parallelism} "
                        f"while `{stage.name}` has effective concurrency "
                        f"{stage.effective_concurrency}."
                    ),
                    evidence=[
                        EvidencePoint(
                            metric="upstream_parallelism_ratio",
                            observed=str(previous_stage.parallelism),
                            threshold=f"<= {stage.effective_concurrency * 4}",
                            rationale="Large producer-consumer gaps inflate object-store pressure.",
                        )
                    ],
                    actions=[
                        f"Lower `{previous_stage.name}` parallelism to about "
                        f"{recommended_parallelism}.",
                    ],
                )
                execution_tuning.append(
                    ExecutionTuningRecommendation(
                        stage=previous_stage.name,
                        parameter="parallelism",
                        current_value=str(previous_stage.parallelism),
                        recommended_value=str(recommended_parallelism),
                        reason="Reduce producer pressure ahead of the GPU stage.",
                    )
                )

    object_store_buffer = cluster.object_store_memory_gib * 0.7
    if total_working_set > object_store_buffer:
        overflow = max(0.0, total_working_set - cluster.object_store_memory_gib)
        severity = (
            Severity.ERROR
            if total_working_set > cluster.object_store_memory_gib
            else Severity.WARNING
        )
        _add_finding(
            findings,
            code="spill.total_working_set",
            severity=severity,
            category=FindingCategory.SPILL_RISK,
            summary="Estimated concurrent working set is high relative to object-store memory.",
            detail=(
                f"Estimated working set is {total_working_set:.1f} GiB with "
                f"{cluster.object_store_memory_gib:.1f} GiB object-store memory."
            ),
            evidence=[
                EvidencePoint(
                    metric="estimated_working_set_gib",
                    observed=f"{total_working_set:.1f}",
                    threshold=f"<= {object_store_buffer:.1f}",
                    rationale=(
                        "Working sets beyond safe object-store headroom trigger "
                        "spill or OOM."
                    ),
                )
            ],
            actions=[
                "Lower concurrency on the hottest stages or increase object-store memory.",
            ],
        )
        if overflow > 0 and cluster.spill_disk_gib < overflow * 1.5:
            _add_finding(
                findings,
                code="spill.disk_headroom",
                severity=Severity.ERROR,
                category=FindingCategory.SPILL_RISK,
                summary="Spill disk headroom is too small for the estimated overflow.",
                detail=(
                    f"Estimated overflow is {overflow:.1f} GiB while spill disk is "
                    f"{cluster.spill_disk_gib:.1f} GiB."
                ),
                evidence=[
                    EvidencePoint(
                        metric="spill_disk_gib",
                        observed=f"{cluster.spill_disk_gib:.1f}",
                        threshold=f">= {overflow * 1.5:.1f}",
                        rationale="Insufficient spill headroom turns pressure into hard failures.",
                    )
                ],
                actions=[
                    "Increase spill disk capacity or trim concurrent working set before execution.",
                ],
            )
        decision_trace.append(
            DecisionTraceEntry(
                rule="cluster.object_store_guardrail",
                summary="Compared estimated working set against object-store memory.",
                inputs={
                    "estimated_working_set_gib": round(total_working_set, 2),
                    "object_store_memory_gib": cluster.object_store_memory_gib,
                    "spill_disk_gib": cluster.spill_disk_gib,
                },
            )
        )

    if cluster.autoscaling_mode == "requested_resources":
        _add_finding(
            findings,
            code="autoscaling.requested_resources_mode",
            severity=Severity.INFO,
            category=FindingCategory.AUTOSCALING,
            summary="The cluster autoscaler reacts to requested resources, not utilization.",
            detail=(
                "Pre-scaling signals should be emitted before high-concurrency stages so the "
                "autoscaler has enough time to add nodes."
            ),
            evidence=[
                EvidencePoint(
                    metric="autoscaling_mode",
                    observed=cluster.autoscaling_mode,
                    threshold="planned prescale signal before burst stages",
                    rationale="Requested-resource autoscaling lags behind realized demand spikes.",
                )
            ],
            actions=[
                "Emit Boba pre-scale hints ahead of bursty stages and cold GPU pools.",
            ],
        )

    if not any(stage.accelerator == Accelerator.GPU for stage in spec.stages):
        confidence += 0.01

    confidence = max(0.5, min(confidence, 0.99))
    summary = (
        f"Plan generated for `{spec.name}` with {len(findings)} findings across "
        f"{len(spec.stages)} stages."
    )
    return RecommendationPlan(
        workload_name=spec.name,
        confidence=confidence,
        summary=summary,
        findings=findings,
        cluster_shape=cluster_shape,
        execution_tuning=execution_tuning,
        autoscaling_signals=autoscaling_signals,
        decision_trace=decision_trace,
    )


def validate_workload(spec: WorkloadSpec, cluster: ClusterInventory) -> ValidationResult:
    plan = generate_plan(spec, cluster)
    errors = [finding for finding in plan.findings if finding.severity == Severity.ERROR]
    warnings = [finding for finding in plan.findings if finding.severity == Severity.WARNING]
    return ValidationResult(ok=not errors, errors=errors, warnings=warnings, plan=plan)


def explain_plan(plan: RecommendationPlan) -> str:
    return plan_to_markdown(plan)
