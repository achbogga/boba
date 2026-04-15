# Memory And Spill Evidence

This page collects concrete evidence that memory planning and spill management
are still active operational problems for Ray Data users.

## Why This Matters To Boba

If memory and spill behavior were already predictable from Ray defaults, Boba
would not need to exist.

But the evidence shows something more uncomfortable:

- users still hit OOMs on seemingly simple workloads
- users still fill object stores and disks on real pipelines
- Ray’s own docs still describe important parts of memory behavior as active
  areas of development

That is exactly the kind of gap a control plane should close.

## Evidence Timeline

### June 17, 2022: Parquet ingestion can trigger disk-pressure incidents

In [Data loading of parquet files is very memory consuming](https://discuss.ray.io/t/data-loading-of-parquet-files-is-very-memory-consuming/6535),
the user describes a TensorFlow ingestion flow where the Ray Dataset path
behaves very differently from the TFRecord path:

- the TF path starts feeding training quickly with modest memory usage
- the Ray Dataset path appears to load aggressively into memory and object store
- once the object store fills, the system spills to disk
- once disk fills, the pipeline becomes non-responsive

The user gives a concrete scale marker: roughly 300 files at 100 MB each,
where the pipeline starts becoming unstable once the input set grows past a
small subset.

This matters because it is not a synthetic benchmark. It is a normal
data-loading complaint from someone trying to train a model.

### January 14, 2024: Basic aggregations can still materialize all data in memory

In [Can Ray Data be used on Datasets that don't fit in memory?](https://discuss.ray.io/t/can-ray-data-be-used-on-datasets-that-dont-fit-in-memory/13418),
a user reports OOMs even for a simple column sum when the uncompressed dataset
size exceeds available memory.

The maintainer response is unusually important because it is not merely a
workaround:

- Ray Data is described as designed for ML training and inference
- it is explicitly said to not be a replacement for generic ETL pipelines
- summation-style operations are described as materializing all data in memory

That is a product-boundary statement, not just a tuning note.

Boba should take this seriously. Some workloads need a warning before launch
that the requested operation class is likely to force materialization.

### October 27, 2023 onward: Streaming execution still has known backpressure gaps

The GitHub issue [[Data] Streaming executor backpressure #40754](https://github.com/ray-project/ray/issues/40754)
is one of the clearest pieces of maintainer-authored evidence in this space.

The issue explicitly states that even with the streaming execution backend,
several cases can still cause:

- OOM
- disk spilling
- out-of-disk errors

It then names specific failure modes:

- upstream operators consuming all resources and starving downstream stages
- tasks that are too large for backpressure to protect effectively
- slow consumers not triggering backpressure correctly
- resource-based backpressure not considering real resource usage

This is exactly the kind of evidence Boba should design around. A planner can
flag these patterns before the job reaches the cluster.

### June 17, 2025: Users still report `read_text` reading ahead, hogging memory, and spilling

In [Ray data read_text calls read all of input hogging memory and spilling](https://discuss.ray.io/t/ray-data-read-text-calls-read-all-of-input-hogging-memory-and-spilling/22667),
the user describes a slower downstream pipeline where `read_text` appears to
read ahead without respecting the desired backpressure boundary.

The reported symptoms are operationally serious:

- the whole dataset is read without waiting for later stages
- data spills heavily
- the spill worker continues consuming memory long after the original pipeline
  code goes out of scope

Whether the exact root cause is user code, operator composition, or runtime
behavior, Boba should care because the user-facing symptom is the same:
memory and spill become control-plane problems.

## Official Documentation That Confirms The Boundary

Ray’s current docs reinforce that these are not fully-solved problems.

### Ray Data stores blocks in the object store

The [Ray Data internals page](https://docs.ray.io/en/latest/data/data-internals.html)
states that the dataset is held by the driver-side process and that blocks are
stored as objects in Ray’s shared-memory object store.

That is architecturally important because it means:

- object-store pressure is a normal part of Ray Data execution
- spill behavior is part of the steady-state runtime model
- users cannot reason only about worker heap memory

### Block sizing is heuristic, and large rows break the heuristic

The same internals page says Ray Data attempts to bound block sizes between
1 MiB and 128 MiB, and dynamically splits blocks once they exceed the safe
factor threshold.

But it also says Ray Data cannot split rows.

That means large rows or large binary payloads are fundamental adversarial
cases for the default heuristics.

### The performance guide still calls memory reduction an active area of development

The [performance tips guide](https://docs.ray.io/en/latest/data/performance-tips.html)
states directly that improving heap memory usage is an active area of
development. It also says:

- intermediate and output blocks live in the object store
- working sets can still exceed object-store capacity
- spilling can significantly slow execution or lead to out-of-disk conditions
- if spilling happens and the cause is unclear, users should file a Ray Data
  GitHub issue

The guide also notes that several operations still materialize or synchronize
the dataset:

- `ds.materialize()`
- shuffle-heavy paths
- repartitioning paths that require all-to-all movement

The [shuffling guide](https://docs.ray.io/en/latest/data/shuffling-data.html)
goes further:

- block-order randomization can require materializing all blocks in memory
- global shuffle is described as expensive and a synchronization barrier
- the docs explicitly say this can be prohibitive on very large datasets

## What This Means For Boba

Boba should assume that memory safety requires explicit planning.

That implies at least four product requirements:

### 1. Working-set estimation before launch

Boba should estimate:

- likely block counts and block sizes
- whether large rows or large binary payloads make split heuristics ineffective
- whether planned shuffle or materialization steps can fit object-store headroom

### 2. Spill-risk classification, not just memory warnings

Users do not only care about OOM.

They care about:

- slowdowns from spill
- disk exhaustion
- worker churn
- non-responsive jobs after spill storms

Boba should model spill as a first-class failure mode.

### 3. Explainable tuning recommendations

If the likely safe move is:

- increasing `override_num_blocks`
- reducing batch size
- reducing concurrency
- changing object-store limits
- avoiding a shuffle path

then Boba should say exactly why.

### 4. Benchmark coverage that mirrors real complaints

The benchmark corpus should include:

- compressed parquet that expands heavily in memory
- large-file binary ingestion
- slow downstream consumers with fast readers
- shuffle-heavy workloads that cross object-store capacity

Those scenarios are not optional. They are directly grounded in reported user
pain.
