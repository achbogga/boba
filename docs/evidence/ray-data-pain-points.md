# Ray Data pain points

The initial prototype targets recurring pain reported by Ray Data users and by
Ray maintainers. This evidence register ties each pain point to a benchmark
scenario and a Boba rule family.

For the longer argument about why these pain points justify a separate control
plane, see:

- [Why Boba Matters: A Call For Core Contributors](../why-boba-matters/index.md)
- [Memory and spill evidence](../why-boba-matters/memory-and-spill.md)
- [Scheduling and autoscaling evidence](../why-boba-matters/scheduling-and-autoscaling.md)
- [GPU and heterogeneous pipeline evidence](../why-boba-matters/gpu-and-heterogeneity.md)
- [Fundamental platform limitations](../why-boba-matters/fundamental-limitations.md)

## Evidence register

| Pain point                                                                                  | Source                                                                                                                                                                                                           | Signal for Boba                                                                                       | Scenario                                   |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Datasets that do not fit memory still risk materialization pressure                         | [Can Ray Data be used on Datasets that don't fit in memory?](https://discuss.ray.io/t/can-ray-data-be-used-on-datasets-that-dont-fit-in-memory/13418)                                                            | Warn when working set or block sizes exceed safe object-store headroom                                | `spill-heavy-parquet`                      |
| Streaming execution can still pile up buffers and spill/OOM when operators are imbalanced   | [[Data] Streaming executor backpressure](https://github.com/ray-project/ray/issues/40754)                                                                                                                        | Flag producer-consumer imbalance and oversized tasks                                                  | `spill-heavy-parquet`, `etl-gpu-inference` |
| Join-heavy workloads can stall in `PENDING_NODE_ASSIGNMENT`                                 | [Join tasks getting stuck in PENDING_NODE_ASSIGNMENT](https://discuss.ray.io/t/join-tasks-getting-stuck-in-pending-node-assignment/22487)                                                                        | Reject unschedulable worker shapes and recommend prescale targets                                     | `pending-node-assignment`                  |
| KubeRay can stay above zero because dataset stats actors persist                            | [KubeRay Won't Scale to Zero: datasets_stats_actor Persists](https://discuss.ray.io/t/kuberay-wont-scale-to-zero-datasets-stats-actor-persists/23195)                                                            | Surface scale-down blockers in the decision trace                                                     | `pending-node-assignment`                  |
| Multi-stage inference pipelines over-allocate upstream GPU and actor pools                  | [Multi-model batch inference - problem with scaling of actors](https://discuss.ray.io/t/multi-model-batch-inference-problem-with-scaling-of-actors/22998)                                                        | Reduce upstream parallelism and emit GPU prescale hints                                               | `etl-gpu-inference`                        |
| Reusing a shared model instance across pipeline stages is hard, leading to extra GPU copies | [Can multiple Ray Data pipeline steps share the same large model instance for inference?](https://discuss.ray.io/t/can-multiple-ray-data-pipeline-steps-share-the-same-large-model-instance-for-inference/22876) | Model-stage capacity planning should assume stage-local GPU allocation unless explicitly externalized | `etl-gpu-inference`                        |
| Ray Data + vLLM can consume unexpected extra GPU resources                                  | [[Data] Ray Data + vLLM use unexpected (double) GPU resources #55247](https://github.com/ray-project/ray/issues/55247)                                                                                           | Flag one-GPU clusters as unsafe for certain LLM batch-inference shapes                                | `etl-gpu-inference`                        |
| Autoscaling relies on requested resources more than realized usage                          | [Ray cluster key concepts](https://docs.ray.io/en/latest/cluster/key-concepts.html) and [[Data] Streaming executor backpressure](https://github.com/ray-project/ray/issues/40754)                                | Emit prescale signals before burst stages instead of waiting for utilization                          | all scenarios                              |

## Implications for v1

- Keep the first policy engine deterministic and explainable.
- Prefer preflight and prescale recommendations before any closed-loop control.
- Benchmark imbalance, spill pressure, and heterogeneous resource shape before
  expanding into other workload classes.
