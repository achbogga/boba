#!/usr/bin/env bash

set -euo pipefail

PROFILE="${1:-kind}"

case "${PROFILE}" in
  kind)
    kubectl get namespaces
    kubectl get pods -A
    kubectl get rayclusters -A
    ;;
  gpu)
    kubectl get pods -A
    kubectl get rayclusters -A
    ;;
  *)
    echo "Unsupported profile: ${PROFILE}" >&2
    exit 1
    ;;
esac

