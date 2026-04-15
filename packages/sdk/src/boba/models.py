"""Shared data models for the Boba prototype."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StageKind(StrEnum):
    INGEST = "ingest"
    TRANSFORM = "transform"
    SHUFFLE = "shuffle"
    JOIN = "join"
    INFERENCE = "inference"
    TRAINING = "training"
    VALIDATION = "validation"
    METRICS = "metrics"


class Accelerator(StrEnum):
    CPU = "cpu"
    GPU = "gpu"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FindingCategory(StrEnum):
    SCHEDULABILITY = "schedulability"
    SPILL_RISK = "spill-risk"
    PIPELINE_BALANCE = "pipeline-balance"
    CLUSTER_SHAPE = "cluster-shape"
    AUTOSCALING = "autoscaling"


class DatasetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str = "parquet"
    input_gib: float = Field(gt=0)
    average_row_kib: float | None = Field(default=None, gt=0)
    file_count: int | None = Field(default=None, gt=0)
    block_size_mib: int = Field(default=128, gt=0)


class WorkloadObjectives(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prioritize_throughput: bool = True
    minimize_cost: bool = True
    max_startup_latency_minutes: int | None = Field(default=None, gt=0)


class StageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: StageKind
    accelerator: Accelerator = Accelerator.CPU
    parallelism: int = Field(default=1, ge=1)
    concurrency: int | None = Field(default=None, ge=1)
    cpu_per_worker: float = Field(default=1.0, gt=0)
    memory_gib_per_worker: float = Field(default=1.0, gt=0)
    gpu_per_worker: float = Field(default=0.0, ge=0)
    working_set_per_worker_gib: float = Field(default=1.0, gt=0)
    ephemeral_disk_per_worker_gib: float = Field(default=0.0, ge=0)
    block_size_mib: int | None = Field(default=None, gt=0)
    expected_output_ratio: float = Field(default=1.0, gt=0)

    @property
    def effective_concurrency(self) -> int:
        return self.concurrency or self.parallelism

    @model_validator(mode="after")
    def validate_accelerator_shape(self) -> StageSpec:
        if self.accelerator == Accelerator.GPU and self.gpu_per_worker <= 0:
            raise ValueError("GPU stages must request gpu_per_worker > 0.")
        if self.accelerator == Accelerator.CPU and self.gpu_per_worker > 0:
            raise ValueError("CPU stages cannot request gpu_per_worker > 0.")
        return self


class WorkloadSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    workload_class: str = "generic"
    execution_mode: str = "advisor"
    dataset: DatasetProfile
    stages: list[StageSpec]
    objectives: WorkloadObjectives = Field(default_factory=WorkloadObjectives)


class NodePool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    instance_family: str
    available_nodes: int = Field(default=0, ge=0)
    min_nodes: int = Field(default=0, ge=0)
    max_nodes: int = Field(ge=0)
    cpu_per_node: float = Field(gt=0)
    memory_gib_per_node: float = Field(gt=0)
    gpu_per_node: float = Field(default=0.0, ge=0)
    disk_gib_per_node: float = Field(default=50.0, gt=0)
    cost_per_hour_usd: float | None = Field(default=None, ge=0)
    labels: dict[str, str] = Field(default_factory=dict)

    def capacity_for(self, stage: StageSpec) -> int:
        ratios = [
            int(self.cpu_per_node // stage.cpu_per_worker),
            int(self.memory_gib_per_node // stage.memory_gib_per_worker),
        ]
        if stage.gpu_per_worker > 0:
            ratios.append(int(self.gpu_per_node // stage.gpu_per_worker))
        if any(ratio <= 0 for ratio in ratios):
            return 0
        return min(ratios)


class ClusterInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ray_version: str
    kuberay_version: str | None = None
    autoscaling_mode: str = "requested_resources"
    object_store_memory_gib: float = Field(gt=0)
    spill_disk_gib: float = Field(gt=0)
    node_pools: list[NodePool]


class EvidencePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    observed: str
    threshold: str
    rationale: str


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Severity
    category: FindingCategory
    summary: str
    detail: str
    evidence: list[EvidencePoint] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class ClusterShapeRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_pool: str
    current_nodes: int
    target_nodes: int
    reason: str


class ExecutionTuningRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str
    parameter: str
    current_value: str
    recommended_value: str
    reason: str


class AutoscalingSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_pool: str
    requested_additional_nodes: int
    reason: str


class DecisionTraceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: str
    summary: str
    inputs: dict[str, Any] = Field(default_factory=dict)


class RecommendationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_name: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confidence: float = Field(ge=0, le=1)
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    cluster_shape: list[ClusterShapeRecommendation] = Field(default_factory=list)
    execution_tuning: list[ExecutionTuningRecommendation] = Field(default_factory=list)
    autoscaling_signals: list[AutoscalingSignal] = Field(default_factory=list)
    decision_trace: list[DecisionTraceEntry] = Field(default_factory=list)


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[Finding] = Field(default_factory=list)
    warnings: list[Finding] = Field(default_factory=list)
    plan: RecommendationPlan


class BenchmarkScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    workload_file: str
    cluster_file: str
    expected_findings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scenario_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "completed"
    plan: RecommendationPlan
    matched_expected_findings: list[str] = Field(default_factory=list)
    missing_expected_findings: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload: WorkloadSpec
    cluster: ClusterInventory


class ExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: RecommendationPlan


class ExplainResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str


class BenchmarkRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    workload: WorkloadSpec
    cluster: ClusterInventory
    expected_findings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
