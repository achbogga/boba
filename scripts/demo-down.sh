#!/usr/bin/env bash

set -euo pipefail

PROFILE="${1:-kind}"

case "${PROFILE}" in
  kind)
    kubectl delete raycluster boba-cpu --ignore-not-found=true
    helm uninstall kuberay-operator --namespace boba-system || true
    kubectl delete namespace boba-system --ignore-not-found=true
    kind delete cluster --name boba || true
    ;;
  gpu)
    kubectl delete raycluster boba-heterogeneous --ignore-not-found=true
    ;;
  *)
    echo "Unsupported profile: ${PROFILE}" >&2
    exit 1
    ;;
esac

