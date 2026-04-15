# Why Boba Matters: A Call For Core Contributors

Boba exists because too much of the operational intelligence for large Ray Data
workloads still lives in human heads.

That is not a branding claim. It is visible in the combination of:

- official Ray and KubeRay documentation
- open Ray GitHub issues
- multi-year Ray forum threads from users trying to run larger or more
  heterogeneous workloads

The common pattern is consistent: once a workload is large enough, multi-stage
enough, or heterogeneous enough, the user often becomes the de facto:

- scheduler
- autoscaler
- memory planner
- spill-risk analyst
- cluster shaper
- concurrency tuner

That is the gap Boba is trying to close.

## This Is A Real Problem, Not A Narrative

Between June 17, 2022 and September 29, 2025, users kept reporting the same
classes of operational pain:

- memory pressure and spill behavior that become workload-shaping problems, not
  just tuning problems
- joins and multi-stage jobs that become schedulability problems on KubeRay
- autoscaling decisions that reflect logical resource requests, not actual stage
  bottlenecks or physical utilization
- GPU pipelines where actor concurrency, placement, and model reuse interact
  badly with heterogeneous CPU/GPU clusters
- scale-down blockers and long-tail control-plane friction that leave users
  debugging internals instead of shipping workloads

This repo is our attempt to build an open-source control plane that makes those
problems more automatic, more explainable, and more replayable.

## If This Sounds Familiar, Boba Is Probably For You

You are in Boba’s target zone if your team has already experienced one or more
of these failure signatures:

- Ray Data pipelines that spill hard enough to turn into disk-pressure or
  non-responsiveness incidents
- joins, shuffles, or actor-heavy stages that become
  `PENDING_NODE_ASSIGNMENT` problems on KubeRay
- GPU pipelines where the first stage takes most of the cluster and starves the
  rest of the workflow
- scale-down behavior that looks correct on paper but leaves expensive workers
  alive after the useful work is done
- a constant operational loop of changing `override_num_blocks`, concurrency,
  worker shape, or resource bundles by hand

That is the operator reality Boba is targeting.

## The Hard-Evidence Summary

If you want the deep dive, read the child pages:

- [Memory and spill evidence](memory-and-spill.md)
- [Scheduling and autoscaling evidence](scheduling-and-autoscaling.md)
- [GPU and heterogeneous pipeline evidence](gpu-and-heterogeneity.md)
- [Fundamental platform limitations](fundamental-limitations.md)
- [How contributors and design partners can help](how-to-help.md)

If you want the fastest path through the repo after this page, continue with:

- the [evidence register](../evidence/ray-data-pain-points.md)
- the [validation matrix](../benchmarks/validation-matrix.md)
- the [plan overview](../plan/overview.md)

The short version is:

### 1. Ray Data still exposes real memory and materialization edges

Users have reported object-store spill storms, disk exhaustion, and OOMs when
datasets or blocks get too large or operators become imbalanced. Ray’s own docs
still describe heap memory reduction and spilling avoidance as active areas of
development, and they explicitly note that some operations materialize data in
memory or act as all-to-all barriers.

That means Boba should not pretend memory behavior is solved upstream. It
should estimate working set risk before the job starts.

### 2. KubeRay autoscaling is useful, but not workload-aware enough

The official docs state that the autoscaler reacts to logical resource requests,
not application metrics or physical utilization. On real workloads, users still
hit `PENDING_NODE_ASSIGNMENT`, scale-down blockers, and under- or over-scaling
across stages.

That means Boba should treat cluster shape as a first-class planning output, not
as something the user guesses and hopes the autoscaler figures out later.

### 3. Heterogeneous GPU pipelines create balancing problems that are larger than any single operator

Users running CPU preprocess plus GPU inference plus downstream GPU or CPU
stages repeatedly report actor-pool imbalance, duplicated model residency, and
surprising GPU allocation behavior. These are not just “set a different
concurrency value” problems. They are whole-pipeline shape problems.

That means Boba should reason about pipelines across stages, node types, and
resource bundles instead of validating each stage in isolation.

### 4. Some limitations are fundamental, not incidental

Ray Data stores blocks in the object store. Large rows cannot always be split.
Global shuffle and some repartitioning paths materialize or synchronize the
whole dataset. Autoscaling reasons from requested shapes, not workload intent or
cost-performance goals.

That means Boba should not try to hide the platform’s real constraints. It
should make them legible and actionable.

## Why Boba, Specifically

Boba is not trying to replace Ray or Kubernetes scheduling.

Boba’s job is narrower and more practical:

- inspect the workload before launch
- inspect the cluster before launch
- infer whether the planned run is schedulable and safe enough
- recommend a better cluster shape when it is not
- recommend safer execution settings when memory, spill, or imbalance risk is
  high
- record a decision trace so users can understand and override the result

That is why Boba is advisor-first.

The first win is not “full autonomy.” The first win is that a developer can
point Boba at a real Ray workload and get a better answer than a generic
sequence of tuning guesses around `override_num_blocks`, concurrency, block
size, and autoscaling.

## What Contributors Can Help Build

We want contributors who care about evidence, reproducibility, and operator
reality.

The highest-leverage areas are:

- workload modeling for Ray Data and multi-stage pipelines
- preflight analyzers for schedulability, spill risk, and heterogeneous resource
  fit
- benchmark scenario design rooted in real reported failure modes
- recommendation rendering that explains tradeoffs instead of hiding them
- replay and regression infrastructure so policy changes are measurable
- KubeRay integration points for cluster-shape translation and autoscaling hints

We also want design partners who are already operating:

- large ETL or batch ML jobs on Ray
- heterogeneous CPU/GPU clusters
- KubeRay with autoscaling
- spill-sensitive or shuffle-heavy pipelines
- multi-stage batch inference pipelines

The most helpful design partners can bring concrete evidence such as:

- a workload graph or simplified pipeline outline
- cluster shape and node-group details
- failure symptoms, logs, or screenshots
- metrics showing where the workload stalls, spills, or over-allocates
- examples of the knobs people have already tried without confidence

## What We Are Not Looking For

We do not want to turn Boba into:

- another metrics dashboard with weak opinions
- a vague “AI ops” wrapper with no benchmark discipline
- a replacement scheduler
- an abstraction layer that hides Ray so thoroughly that users lose control

The standard here is stricter:

- every meaningful claim should map to a real pain point
- every policy should have a rationale
- every recommendation should be explainable
- every change should be benchmarkable or replayable

## Why This Is The Right Time

Ray is stronger than it used to be, but that does not eliminate the control
plane gap. In some ways it makes the gap sharper.

As Ray Data, KubeRay, LLM batch inference, and heterogeneous cluster patterns
grow more capable, users gain more knobs, more interactions, and more failure
modes. The missing layer is not more primitives. The missing layer is better
decision-making over those primitives.

That is the product thesis behind Boba.

If that thesis matches the problems you are seeing in production or in serious
experimentation, the best next steps are practical:

- open a discussion at
  [github.com/achbogga/boba/discussions](https://github.com/achbogga/boba/discussions)
  if you want to share a workload, failure mode, or design critique
- open an issue at
  [github.com/achbogga/boba/issues](https://github.com/achbogga/boba/issues)
  if you have a specific bug, missing benchmark case, or doc gap
- read [How contributors and design partners can help](how-to-help.md) if you
  want a more concrete map of where to plug in

The repo needs contributors who want to build a real control plane, not just a
nicer wrapper.
