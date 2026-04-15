#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ensure_trunk() {
  if command -v trunk >/dev/null 2>&1; then
    return
  fi

  curl https://get.trunk.io -fsSL | bash
  export PATH="${HOME}/.local/bin:${PATH}"
}

cd "${ROOT_DIR}"
ensure_trunk
uv sync --dev
npm install
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

echo "Development environment bootstrapped."

