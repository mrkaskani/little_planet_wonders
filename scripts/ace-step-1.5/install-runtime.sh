#!/usr/bin/env bash
set -euo pipefail

ACE_DIR="/Users/oldowl/AI-Audio/ace-step"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "ACE-Step MLX requires macOS on Apple Silicon (arm64)." >&2
  exit 1
fi
if [[ ! -d "${ACE_DIR}/.git" ]]; then
  echo "Missing official ACE-Step checkout: ${ACE_DIR}" >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
fi

cd "${ACE_DIR}"
uv sync
uv run python - <<'PY'
import mlx.core as mx
print(f"MLX version: {mx.__version__}")
print(f"MLX device: {mx.default_device()}")
PY

echo "ACE-Step runtime installed. Model weights were not downloaded by this script."

