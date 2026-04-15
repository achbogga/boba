#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ensure_trunk() {
  if command -v trunk >/dev/null 2>&1; then
    return
  fi

  mkdir -p "${HOME}/.local/bin"
  curl -fsSL https://trunk.io/releases/trunk -o "${HOME}/.local/bin/trunk"
  chmod +x "${HOME}/.local/bin/trunk"
  export PATH="${HOME}/.local/bin:${PATH}"
}

cd "${ROOT_DIR}"
ensure_trunk
uv sync --dev
npm install
export PATH="${ROOT_DIR}/.venv/bin:${ROOT_DIR}/node_modules/.bin:${HOME}/.local/bin:${PATH}"
trunk install
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

echo "Development environment bootstrapped."
