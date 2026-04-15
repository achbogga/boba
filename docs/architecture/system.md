# System architecture

Boba is split into four top-level surfaces:

- SDK and CLI for local planning and validation
- API service for remote plan generation
- benchmark harness for replayable scenario execution
- deployment assets for KubeRay demo environments

The prototype stays advisory-first. It produces plans, explanations, and
machine-readable reports before any automated control loop is introduced.

