#!/usr/bin/env bash

set -euo pipefail

branch_name="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
if [[ -z "${branch_name}" ]] || ! git show-ref --verify --quiet "refs/heads/${branch_name}"; then
  echo "Skipping Trunk on the initial commit; no HEAD exists yet."
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${ROOT_DIR}/.venv/bin:${ROOT_DIR}/node_modules/.bin:${HOME}/.local/bin:${PATH}"
trunk check --all --ci --no-progress
