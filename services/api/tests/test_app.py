from __future__ import annotations

from fastapi.testclient import TestClient

from boba_api.app import create_app

client = TestClient(create_app())


def test_plan_endpoint_returns_findings() -> None:
    payload = {
        "workload": {
            "name": "api-spill-case",
            "dataset": {
                "format": "parquet",
                "input_gib": 120,
                "block_size_mib": 512,
            },
            "stages": [
                {
                    "name": "read",
                    "kind": "ingest",
                    "parallelism": 24,
                    "cpu_per_worker": 2,
                    "memory_gib_per_worker": 4,
                    "working_set_per_worker_gib": 2,
                }
            ],
        },
        "cluster": {
            "name": "test-cluster",
            "ray_version": "2.54.0",
            "kuberay_version": "1.5.1",
            "autoscaling_mode": "requested_resources",
            "object_store_memory_gib": 16,
            "spill_disk_gib": 40,
            "node_pools": [
                {
                    "name": "cpu-general",
                    "instance_family": "m6i",
                    "available_nodes": 1,
                    "min_nodes": 0,
                    "max_nodes": 2,
                    "cpu_per_node": 16,
                    "memory_gib_per_node": 64,
                    "disk_gib_per_node": 200,
                    "gpu_per_node": 0
                }
            ]
        }
    }

    response = client.post("/v1/plans", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["workload_name"] == "api-spill-case"
    assert body["findings"]


def test_benchmark_run_is_retrievable() -> None:
    payload = {
        "name": "inline-benchmark",
        "description": "API benchmark request",
        "expected_findings": ["spill.block_size_too_large"],
        "workload": {
            "name": "api-benchmark",
            "dataset": {
                "format": "parquet",
                "input_gib": 90,
                "block_size_mib": 512,
            },
            "stages": [
                {
                    "name": "read",
                    "kind": "ingest",
                    "parallelism": 12,
                    "cpu_per_worker": 2,
                    "memory_gib_per_worker": 2,
                    "working_set_per_worker_gib": 1.5,
                }
            ],
        },
        "cluster": {
            "name": "inline-cluster",
            "ray_version": "2.54.0",
            "kuberay_version": "1.5.1",
            "autoscaling_mode": "requested_resources",
            "object_store_memory_gib": 8,
            "spill_disk_gib": 60,
            "node_pools": [
                {
                    "name": "cpu-general",
                    "instance_family": "m6i",
                    "available_nodes": 1,
                    "min_nodes": 0,
                    "max_nodes": 3,
                    "cpu_per_node": 8,
                    "memory_gib_per_node": 32,
                    "disk_gib_per_node": 200,
                    "gpu_per_node": 0
                }
            ]
        }
    }

    create_response = client.post("/v1/benchmarks/runs", json=payload)
    assert create_response.status_code == 200
    run_id = create_response.json()["id"]

    get_response = client.get(f"/v1/benchmarks/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == run_id

