# Validation matrix

The first benchmark tracks are:

- `etl-gpu-inference`
- `etl-training-validation-metrics`
- `spill-heavy-parquet`
- `pending-node-assignment`

Each scenario should emit:

- a machine-readable plan
- a human-readable explanation
- a decision trace
- workload and cluster metrics

## Scenario intent

| Scenario                          | Primary risk                                    | Expected Boba behavior                                               |
| --------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------- |
| `spill-heavy-parquet`             | spill, object-store pressure, oversized blocks  | downsize blocks, reduce concurrency, flag disk headroom              |
| `etl-gpu-inference`               | GPU imbalance, overscaled upstream CPU work     | prescale GPU nodes, lower producer parallelism                       |
| `etl-training-validation-metrics` | mixed ETL and GPU stages                        | validate heterogenous shape without touching training internals      |
| `pending-node-assignment`         | memory-heavy join shapes and delayed scheduling | fail preflight early and recommend bigger nodes or lower concurrency |
