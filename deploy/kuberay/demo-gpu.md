# GPU cluster demo

This profile assumes an existing Kubernetes cluster with:

- GPU nodes
- the NVIDIA device plugin
- `kubectl` and `helm` configured against the cluster

Apply the demo assets with:

```bash
./scripts/demo-up.sh gpu
```

Boba does not provision the GPU node pool itself in the prototype. It applies
the RayCluster manifest and relies on the underlying cluster autoscaler.
