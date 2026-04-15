# GPU And Heterogeneous Pipeline Evidence

This page covers one of Boba’s sharpest wedges: multi-stage workloads that mix
CPU preprocess, GPU inference, different model stages, and heterogeneous node
groups.

These workloads are where “just set concurrency” stops being a credible
operating model.

## Why This Is A Distinct Problem Class

A heterogeneous pipeline can be locally reasonable and globally wrong.

Examples:

- the first GPU stage scales faster than downstream GPU stages can consume
- multiple stages each instantiate their own copy of a large model
- CPU or object-store pressure looks low, so backpressure does not trigger
- the autoscaler sees resources as “fully utilized” while the pipeline remains
  badly imbalanced

Boba needs to reason about the whole pipeline, not just isolated stages.

## Evidence From Real Users

### July 22, 2025: sharing one large model across pipeline steps is not straightforward

In [Can multiple Ray Data pipeline steps share the same large model instance for inference?](https://discuss.ray.io/t/can-multiple-ray-data-pipeline-steps-share-the-same-large-model-instance-for-inference/22876),
the user asks whether multiple Ray Data steps can share the same large
GPU-backed model instance.

The motivation is not academic:

- the inference stage is identical across steps
- separate stage-local model instances would duplicate GPU residency
- the user explicitly says they do not have enough GPUs to support that
  efficiently

This is the kind of question a control plane should not leave entirely to
application authors. Even when the right answer is “stage-local model residency
is still the practical assumption,” Boba should make that cost visible.

### August 5, 2025: Ray Data + vLLM can require more GPU than users expect

In [[Data] Ray Data + vLLM use unexpected (double) GPU resources #55247](https://github.com/ray-project/ray/issues/55247),
the reporter describes a one-GPU environment where a Ray Data + vLLM example
fails because:

- the `map_batches` side already occupies GPU resources
- the vLLM engine then tries to create its own placement group with GPU demand
- the placement group fails because the cluster effectively needs more GPU shape
  than the user expected

This is an especially useful issue for Boba because it shows that “one stage
needs one GPU” is not always the real requirement. The composition of Ray Data
and downstream engines can change the effective shape.

### August 14, 2025: multi-model batch inference can balance badly even when resources are fully used

In [Multi-model batch inference - problem with scaling of actors](https://discuss.ray.io/t/multi-model-batch-inference-problem-with-scaling-of-actors/22998),
the user describes a CPU/GPU pipeline on 4 nodes with 4 A100s each:

- `read_parquet`
- CPU preprocess
- GPU annotate
- preprocess
- annotate
- write

They set actor concurrency ranges like `(1, 16)` for each model stage.

The reported problem is not low utilization. It is the opposite:

- the first annotator consumes many GPUs early
- downstream annotators get fewer resources
- the first stage overproduces
- rows are small, so object-store pressure stays low enough that backpressure
  does not trigger
- the pipeline becomes imbalanced even though the scheduler believes utilization
  is acceptable

This is exactly a whole-pipeline resource-allocation problem.

## Evidence From Ray’s Own Issue Tracker

### December 15, 2023: actor-pool autoscaling policy was explicitly flagged as too sensitive

The GitHub issue [[data] Optimize actor pool autoscaling policy #41956](https://github.com/ray-project/ray/issues/41956)
says the current policy does not work well and is too sensitive because it looks
at transient usage instead of usage over a time interval.

That matters because transient usage is exactly what can mislead scaling in
heterogeneous pipelines with skewed stage runtimes.

### July 11, 2025: actor-based pipelines can underutilize CPUs and under-scale slow stages

In [[data] Ray Autoscaling - Suboptimal Performance with Actors #54540](https://github.com/ray-project/ray/issues/54540),
the user describes a skewed actor pipeline with:

- an I/O stage
- an iterate stage
- a very expensive extract stage
- a write stage

The key report is that with concurrency `(1,16)`, the workload still only uses
around 6 of 16 CPUs, and the slow stage never scales to the expected capacity.
They also report a roughly 2x runtime gap between task-based and actor-based
execution for the same broader pipeline.

That is strong evidence that actor autoscaling can remain suboptimal even when a
user has already provided what looks like the “right” concurrency envelope.

## What This Means For Boba

### 1. Pipeline balance should be a core analyzer, not a stretch goal

Boba should estimate:

- stage throughput ratios
- likely queue growth between stages
- whether upstream GPU allocation will starve or swamp downstream work

### 2. Model residency assumptions should be made explicit

Boba should warn when:

- multiple stages imply duplicate model residency
- GPU memory budgets assume model sharing that the pipeline does not actually
  achieve
- an external engine introduces hidden or secondary GPU shape requirements

### 3. Heterogeneous node planning should operate on bundles, not totals

It is not enough to say:

- 8 GPUs total
- 64 CPUs total

Boba should reason about:

- how many GPU bundles are needed at the same time
- whether those bundles need colocated CPU, memory, or disk headroom
- whether the shape of the cluster matches the shape of the pipeline

### 4. Benchmark coverage should include imbalanced multi-stage inference

The benchmark matrix should include:

- CPU preprocess plus GPU inference chains
- repeated GPU stages with unequal runtimes
- model-sharing and non-sharing assumptions
- small-row pipelines where backpressure does not trigger early enough

That is the only credible way to build a control plane for heterogeneous Ray
workloads.
