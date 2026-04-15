# Boba Agent Rules

Boba is a Ray/KubeRay control plane, not a generic agent harness repo.

## Product Stance

- keep the repo focused on advisory and autopilot logic for Ray batch data and ML workloads
- treat Latte as the external harness for context, memory, retrieval, and long-horizon orchestration
- preserve explainability: every recommendation must map back to evidence or a deterministic rule
- prefer benchmarkable changes over speculative control-plane complexity

## Working Rules

- read the roadmap, architecture docs, and evidence register before changing planner behavior
- when a recommendation policy changes, update the evidence or benchmark rationale alongside it
- keep CLI, SDK, and API outputs aligned
- never add repo-local memory or durable agent-loop code that belongs in Latte
