#!/usr/bin/env bash
set -euo pipefail

MLX_DIR="/Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx"
PYTHON="${MLX_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Run /Users/oldowl/PycharmProjects/little_planet_wonders/scripts/stable-audio-3/install-runtime.sh first." >&2
  exit 1
fi

echo "Downloading only Stable Audio 3 Medium with SAME-L and shared T5Gemma (~6.88 GB)."
echo "Authentication is read from the local Hugging Face login or HF_TOKEN."
cd "${MLX_DIR}"
INSTALL_SKIP_PIP=1 "${PYTHON}" scripts/install.py --download medium
