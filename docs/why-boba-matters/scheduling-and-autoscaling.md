# Scheduling And Autoscaling Evidence

This page focuses on the gap between “the cluster can autoscale” and “the
workload gets the right shape at the right time.”

That gap is where Boba’s cluster-shaping and preflight schedulability work
belongs.

## The Core Problem

Ray and KubeRay expose autoscaling, but the autoscaler is not a workload-aware
planner.

The official docs say this clearly.

## Official Constraints

### Ray autoscaling reacts to requests, not real utilization

The [Ray cluster key concepts](https://docs.ray.io/en/latest/cluster/key-concepts.html)
page says:

- the autoscaler reacts to task and actor resource requests
- it does not react to application metrics
- it does not react to physical resource utilization

That means a cluster can be “correct” from the autoscaler’s perspective while
still being wrong for the workload.

### KubeRay autoscaling is driven by logical demand and can be tricky to configure

The [KubeRay autoscaling guide](https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/configuring-autoscaling.html)
repeats the same architectural boundary:

- scaling is based on logical resource requests
- insufficient resources result in queued requests
- autoscaling can reduce costs but adds launch overhead
- the docs explicitly say it can be tricky to configure

This is important because Boba should not pretend that autoscaling alone solves
cluster-shape selection.

## Real User Reports

### May 14, 2025: joins can stall in `PENDING_NODE_ASSIGNMENT`

In [Join tasks getting stuck in PENDING_NODE_ASSIGNMENT](https://discuss.ray.io/t/join-tasks-getting-stuck-in-pending-node-assignment/22487),
a user running Ray 2.46.0 on local Kubernetes reports that small replica counts
work, but larger joins leave `HashShuffleAggregator` tasks stuck in
`PENDING_NODE_ASSIGNMENT`.

The concrete cluster shape is modest:

- 1 head node with 1 CPU and 8 GiB memory
- 2 to 4 autoscaled workers with 1 CPU and 2 GiB each

The important point is not that the cluster is small. The important point is
that the user cannot easily predict the safe shape for the join, even on a test
environment.

That is exactly a preflight schedulability problem.

### September 29, 2025: scale-down to zero can be blocked by a Ray Data internal actor

In [KubeRay Won't Scale to Zero: datasets_stats_actor Persists](https://discuss.ray.io/t/kuberay-wont-scale-to-zero-datasets-stats-actor-persists/23195),
the user reports a KubeRay batch job that finishes but still leaves one worker
alive indefinitely.

The observed reason is operationally specific and useful:

- an internal `datasets_stats_actor` remains alive
- because that actor remains on the worker, the autoscaler does not consider the
  node idle
- the cluster therefore never completes its final scale-down to zero

This is exactly the kind of “works in principle, hurts in practice” gap that a
control plane can surface early in a decision trace.

## Why This Still Requires A Separate Control Plane

Autoscaling answers a narrower question than users need answered.

Autoscaling asks:

- what resource requests are pending?
- how many nodes do we need to satisfy those requests?

Users need answers to a broader set of questions:

- is this workload shape schedulable at all?
- is the join or shuffle likely to deadlock on the current worker shape?
- should the cluster be pre-scaled before a burst stage?
- is there a known scale-down blocker in this job shape?
- is the cluster logically “large enough” but still structurally wrong?

Boba should answer those questions before launch.

## What This Means For Boba

### 1. Preflight schedulability should be explicit

Boba should model:

- requested stage shapes
- per-stage minimum viable worker bundle
- whether current or planned node groups can satisfy those bundles
- whether the workload includes known bad combinations, such as large joins on
  undersized workers

### 2. Cluster-shape recommendations should be first-class outputs

Boba should recommend:

- worker groups by node type
- prescale targets by stage
- shape adjustments for joins, shuffles, and GPU bursts

### 3. Decision traces should include control-plane blockers

Boba should surface blockers such as:

- internal actors preventing idle detection
- placement and bundle mismatches
- resource requests that look satisfiable in aggregate but not in usable shapes

### 4. The benchmark harness should test scale-up and scale-down behavior

The validation matrix should include:

- `PENDING_NODE_ASSIGNMENT` reproduction cases
- prescale versus no-prescale startup comparisons
- scale-to-zero blocker cases on KubeRay
- join-heavy and hash-shuffle-heavy schedulability cases

Without those tests, Boba would miss one of the clearest parts of the real user
pain surface.
