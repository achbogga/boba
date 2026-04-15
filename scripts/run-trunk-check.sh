#!/usr/bin/env bash

set -euo pipefail

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Skipping Trunk on the initial commit; no HEAD exists yet."
  exit 0
fi

export PATH="${HOME}/.local/bin:${PATH}"
trunk check --all --ci

