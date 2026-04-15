# System architecture

## Surfaces

Boba is split into four top-level surfaces:

- SDK and CLI for local planning and validation
- API service for remote plan generation
- benchmark harness for replayable scenario execution
- deployment assets for KubeRay demo environments

## Control flow

1. A workload spec describes the dataset, stage graph, and execution shape.
2. A cluster inventory describes node pools, object store memory, and spill
   capacity.
3. The planner applies deterministic rules for:
   - schedulability
   - spill risk
   - pipeline balance
   - cluster shaping
   - autoscaling signals
4. Boba returns a recommendation plan, decision trace, and explanation.

## Boundaries

- Ray remains the execution engine.
- Kubernetes and KubeRay remain the substrate and reconciler.
- Boba does not replace scheduling; it recommends and prepares the right shape.
- Training internals remain out of scope for the prototype.

## Prototype internals

- `packages/sdk`: shared models, planner rules, CLI, and benchmark helpers
- `services/api`: FastAPI wrapper over shared planner logic
- `benchmarks/scenarios`: scenario inputs and expected findings
- `deploy/kuberay`: local demo assets and cluster manifests
