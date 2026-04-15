# Fundamental Platform Limitations

This page is deliberately blunt.

Boba does not need Ray or KubeRay to be “bad” in order to justify itself. It is
enough that some important boundaries are fundamental to how the platform works.

Those boundaries are real, documented, and user-visible.

## 1. Ray Data Is Built Around Blocks In The Object Store

The [Ray Data internals page](https://docs.ray.io/en/latest/data/data-internals.html)
says:

- Ray Data stores blocks in Ray’s shared-memory object store
- blocks are the basic unit of parallel transfer and execution
- input and output blocks consume both heap and object-store memory
- if blocks cannot fit, they spill to disk

That architecture is powerful, but it means users are always operating inside a
memory hierarchy:

- worker heap
- object store
- local spill disk

Boba should treat that as the ground truth.

## 2. Block Sizing Is Heuristic, Not Perfect

The same docs say Ray Data aims for blocks in the 1 MiB to 128 MiB range and
can dynamically split oversized blocks.

But there is a hard boundary:

- Ray Data cannot split rows

That means a dataset with very large rows, large images, or large binary
payloads can violate the “safe block” heuristic even if the general system is
behaving as designed.

Boba should not promise to tune around that invisibly. It should detect and
explain it.

## 3. Some Operations Still Materialize Or Synchronize The Whole Dataset

The [performance tips](https://docs.ray.io/en/latest/data/performance-tips.html)
and [shuffling guide](https://docs.ray.io/en/latest/data/shuffling-data.html)
make this explicit:

- global shuffle is expensive
- it acts as a synchronization barrier
- block-order randomization can materialize all blocks in memory
- repartitioning and shuffle-heavy paths can require all-to-all movement
- the docs warn that these costs can be prohibitive on very large datasets

This matters because a user can have a “streaming” mental model of the pipeline
while one operator quietly invalidates that mental model.

Boba should call those boundaries out before launch.

## 4. The Autoscaler Does Not Understand Workload Intent

The [Ray cluster key concepts](https://docs.ray.io/en/latest/cluster/key-concepts.html)
and [KubeRay autoscaling guide](https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/configuring-autoscaling.html)
say the autoscaler reasons from logical resource requests, not physical
utilization or higher-level workload intent.

That means there is no built-in component whose job is to answer questions like:

- is this the right shape for the next stage?
- should we prescale before a burst?
- is the cluster technically feasible but economically bad?
- are we safe from spill, join deadlock, or downstream starvation?

That is not a bug. It is simply outside the autoscaler’s contract.

Boba exists to fill that contract gap.

## 5. Operational Workarounds Are Still Knob-Centric

The docs and issue threads repeatedly point users toward knobs such as:

- `override_num_blocks`
- `batch_size`
- `num_cpus` or `num_gpus`
- `object_store_memory`
- repartitioning strategy
- manual prescaling via resource requests

Those knobs are valuable, but they are not a planning system.

A planning system should answer:

- which knob should move?
- by how much?
- because of which evidence?
- with what expected tradeoff?

Boba should convert low-level tuning knobs into explainable decisions.

## 6. Some Failures Are Systemic Enough To Deserve Their Own Control Plane

When users repeatedly encounter:

- spill storms
- disk exhaustion
- `PENDING_NODE_ASSIGNMENT`
- scale-down blockers
- skewed multi-stage actor pipelines
- duplicate GPU residency

the right response is not merely “read the tuning guide more carefully.”

The right response is to build a system that:

- sees the workload shape ahead of time
- sees the cluster shape ahead of time
- knows the common failure signatures
- recommends a safer plan before the run burns time and money

That system is what Boba is trying to become.
