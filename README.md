# Boba

[![CI](https://github.com/achbogga/boba/actions/workflows/ci.yml/badge.svg)](https://github.com/achbogga/boba/actions/workflows/ci.yml)
[![Docs](https://github.com/achbogga/boba/actions/workflows/docs.yml/badge.svg)](https://github.com/achbogga/boba/actions/workflows/docs.yml)
[![Images](https://github.com/achbogga/boba/actions/workflows/images.yml/badge.svg)](https://github.com/achbogga/boba/actions/workflows/images.yml)
![License](https://img.shields.io/badge/license-BSL%201.1-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)

*Self-driving Ray clusters, powered by Boba.*

Boba is a source-available control plane for Ray workloads running on
heterogeneous Kubernetes-backed infrastructure. It helps teams plan, validate,
shape, and tune Ray batch data and ML workloads before they fail expensively.

## License model

Boba is source-available under BSL 1.1 today, with an Apache-2.0 change
license. Commercial use is free for organizations with up to two named human
users of Boba. Larger commercial use requires a separate commercial license.

## What exists today

- a modern monorepo foundation with `uv`, Trunk, `pre-commit`, GitHub Actions,
  and a dev container
- hierarchical docs for plan, architecture, evidence, benchmarks, and
  contributing
- the initial SDK, CLI, API, and benchmark scaffolding for advisor mode

## Quick start

```bash
git clone git@github.com:achbogga/boba.git
cd boba
./scripts/bootstrap-dev.sh
uv run boba plan --spec examples/workloads/etl-gpu-inference.workload.yaml \
  --cluster examples/workloads/local-kind.cluster.yaml
```

## Repository map

- `packages/sdk`: Python SDK, planner, schemas, and CLI
- `services/api`: FastAPI service
- `benchmarks`: scenario definitions and output conventions
- `deploy/kuberay`: demo manifests and scripts
- `docs`: plan, architecture, evidence, benchmark, and contributor docs

## Contribution

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Use test-driven development for
behavior changes and keep commits atomic.

