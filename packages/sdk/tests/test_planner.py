from __future__ import annotations

from boba.models import (
    ClusterInventory,
    DatasetProfile,
    NodePool,
    StageKind,
    StageSpec,
    WorkloadSpec,
)
from boba.planner import generate_plan, validate_workload


def build_gpu_workload() -> WorkloadSpec:
    return WorkloadSpec(
        name="etl-gpu-inference",
        workload_class="etl-gpu-inference",
        dataset=DatasetProfile(format="parquet", input_gib=240, block_size_mib=512),
        stages=[
            StageSpec(
                name="ingest",
                kind=StageKind.INGEST,
                parallelism=48,
                concurrency=24,
                cpu_per_worker=2,
                memory_gib_per_worker=4,
                working_set_per_worker_gib=3,
            ),
            StageSpec(
                name="embed",
                kind=StageKind.INFERENCE,
                accelerator="gpu",
                parallelism=8,
                concurrency=8,
                cpu_per_worker=6,
                memory_gib_per_worker=12,
                gpu_per_worker=1,
                working_set_per_worker_gib=10,
            ),
        ],
    )


def build_cluster(*, with_gpu: bool) -> ClusterInventory:
    pools = [
        NodePool(
            name="cpu-general",
            instance_family="m6i",
            available_nodes=2,
            min_nodes=0,
            max_nodes=10,
            cpu_per_node=16,
            memory_gib_per_node=64,
            disk_gib_per_node=200,
        )
    ]
    if with_gpu:
        pools.append(
            NodePool(
                name="gpu-l4",
                instance_family="g6",
                available_nodes=0,
                min_nodes=0,
                max_nodes=4,
                cpu_per_node=32,
                memory_gib_per_node=128,
                gpu_per_node=1,
                disk_gib_per_node=500,
            )
        )
    return ClusterInventory(
        name="kind-demo",
        ray_version="2.54.0",
        kuberay_version="1.5.1",
        autoscaling_mode="requested_resources",
        object_store_memory_gib=24,
        spill_disk_gib=80,
        node_pools=pools,
    )


def test_generate_plan_flags_unschedulable_gpu_stage() -> None:
    plan = generate_plan(build_gpu_workload(), build_cluster(with_gpu=False))
    finding_codes = {finding.code for finding in plan.findings}

    assert "sched.embed.unschedulable" in finding_codes
    assert "spill.total_working_set" in finding_codes


def test_generate_plan_recommends_gpu_scale_out_when_pool_exists() -> None:
    plan = generate_plan(build_gpu_workload(), build_cluster(with_gpu=True))

    assert any(shape.node_pool == "gpu-l4" for shape in plan.cluster_shape)
    assert any(signal.node_pool == "gpu-l4" for signal in plan.autoscaling_signals)


def test_validate_workload_fails_on_error_findings() -> None:
    result = validate_workload(build_gpu_workload(), build_cluster(with_gpu=False))

    assert result.ok is False
    assert result.errors
