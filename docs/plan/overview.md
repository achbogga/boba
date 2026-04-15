# Plan overview

## Workstreams

The v1 prototype advances in four parallel workstreams:

1. Repository and contributor foundations
2. Advisor-mode schemas and deterministic analyzers
3. Benchmark scenarios tied to Ray Data pain points
4. KubeRay demo environment and deployment assets

## Near-term milestones

### Milestone 1: Repo foundations

- GitHub-first workflow
- source-available licensing
- Trunk, hooks, CI/CD, and dev container
- contribution and governance docs

### Milestone 2: Advisor mode

- workload and cluster schemas
- deterministic schedulability and spill analyzers
- CLI and API parity
- explanation and decision-trace outputs

### Milestone 3: Validation harness

- scenario-backed benchmark runs
- machine-readable reports
- regression-style expected findings
- evidence register tied to real Ray Data pain

### Milestone 4: Demo environments

- local Kind + KubeRay smoke path
- heterogeneous GPU cluster manifest
- reproducible setup and teardown scripts

Each workstream should land in small, test-backed commits and keep public docs
updated as decisions change.
