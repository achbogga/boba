# Ray Data pain points

The initial prototype targets recurring pain reported by Ray Data users:

- memory pressure and object-store spill on large reads and transforms
- scheduling stalls such as `PENDING_NODE_ASSIGNMENT`
- autoscaling behavior driven by requested resources rather than realized usage
- GPU actor pool imbalance in multi-stage inference pipelines

This document should track the public evidence source, the benchmark scenario,
and the Boba rule that addresses each problem.

