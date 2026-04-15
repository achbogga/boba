# How Contributors And Design Partners Can Help

This page turns the contributor call into something more operational.

If Boba is going to earn trust, it needs contributors who care about evidence,
reproducibility, and painful real-world workloads more than glossy claims.

## Who We Want

The best contributors for this repo usually fall into one of four groups:

- Ray power users who have already spent too much time hand-tuning data and
  inference pipelines
- platform engineers operating KubeRay or adjacent Kubernetes-based Ray
  infrastructure
- ML engineers running heterogeneous batch inference or ETL plus validation
  flows
- systems-minded contributors who care about schedulability, memory behavior,
  benchmarking, and control-plane design

## What Design Partners Should Bring

The fastest way to help Boba become useful is to bring hard cases, not generic
feature requests.

Strong design-partner inputs include:

- a simplified pipeline graph with stage names and rough resource needs
- cluster inventory by node group, including CPU, GPU, memory, and disk shape
- one or two concrete failure modes such as spill storms,
  `PENDING_NODE_ASSIGNMENT`, scale-down blockers, or GPU stage starvation
- logs, screenshots, metrics, or decision points that show where operators
  currently have to guess
- the manual tuning steps people have already tried

That material is more valuable than another abstract request for “better
autoscaling.”

## Where To Engage

Use the repo in the most direct way possible:

- start a discussion in
  [GitHub Discussions](https://github.com/achbogga/boba/discussions) for
  workload stories, design feedback, and architecture critique
- file an
  [issue](https://github.com/achbogga/boba/issues) for a missing analyzer,
  benchmark case, documentation gap, or concrete bug
- read the
  [evidence register](../evidence/ray-data-pain-points.md) before proposing a
  new rule family, so the problem statement stays grounded
- read the [validation matrix](../benchmarks/validation-matrix.md) before
  proposing a benchmark addition, so the scenario maps cleanly to a risk class
- read the [plan overview](../plan/overview.md) before opening large roadmap
  requests, so new asks line up with the current prototype sequence

## Good First High-Leverage Contributions

The most valuable early contributions are not random feature additions. They
are changes that improve Boba’s ability to make and explain decisions.

Good examples:

- add a benchmark scenario that reproduces a real Ray or KubeRay pain point
- improve a deterministic analyzer so it explains why a plan is unsafe
- add test-backed schema coverage for workload or cluster shapes that are
  currently under-modeled
- tighten the decision trace so recommendations map to evidence more directly
- improve docs where users are likely to mistrust or misunderstand the planner

## What Not To Contribute First

Early contributions should avoid widening scope before the foundation is solid.

Less helpful first contributions include:

- replacing Ray internals
- building a broad multi-engine abstraction layer
- adding dashboard-heavy surfaces before the planner is credible
- proposing opaque automation without replay, rationale, or test coverage

## The Standard For Core Contributors

Core contributors should expect a high bar:

- claims should map to real user pain or official platform constraints
- analyzer and policy changes should come with tests
- meaningful behavioral changes should be benchmarked or at least tied to a
  replayable scenario
- recommendations should explain tradeoffs, not just emit values

That is how Boba avoids becoming another vague “AI ops” wrapper.

## What Success Looks Like

The short-term success case is simple:

- a user points Boba at a real workload
- Boba flags likely failure modes before launch
- Boba recommends a better cluster and execution shape
- the recommendation is concrete enough that the user can trust or override it

If you want to help build that, start with the evidence pages, bring a real
failure case, and make the repo sharper.
