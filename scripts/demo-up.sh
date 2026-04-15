#!/usr/bin/env bash

set -euo pipefail

PROFILE="${1:-kind}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

helm_setup() {
  helm repo add kuberay https://ray-project.github.io/kuberay-helm/ >/dev/null 2>&1 || true
  helm repo update >/dev/null
}

install_operator() {
  kubectl create namespace boba-system --dry-run=client -o yaml | kubectl apply -f -
  helm upgrade --install kuberay-operator kuberay/kuberay-operator \
    --namespace boba-system \
    --version 1.5.1
}

case "${PROFILE}" in
  kind)
    require_cmd docker
    require_cmd kind
    require_cmd kubectl
    require_cmd helm
    if ! kind get clusters | grep -qx "boba"; then
      kind create cluster --config "${ROOT_DIR}/deploy/kuberay/kind-config.yaml"
    fi
    helm_setup
    install_operator
    kubectl apply -f "${ROOT_DIR}/deploy/kuberay/raycluster-cpu.yaml"
    echo "Kind demo is up."
    ;;
  gpu)
    require_cmd kubectl
    require_cmd helm
    helm_setup
    install_operator
    kubectl apply -f "${ROOT_DIR}/deploy/kuberay/raycluster-heterogeneous.yaml"
    echo "GPU demo manifest applied."
    ;;
  *)
    echo "Unsupported profile: ${PROFILE}" >&2
    exit 1
    ;;
esac

