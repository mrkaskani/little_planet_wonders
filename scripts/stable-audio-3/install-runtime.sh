#!/usr/bin/env bash
set -euo pipefail

MLX_DIR="/Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "Stable Audio MLX requires macOS on Apple Silicon (arm64)." >&2
  exit 1
fi
if [[ ! -x "${MLX_DIR}/install.sh" ]]; then
  echo "Missing official Stable Audio MLX checkout: ${MLX_DIR}" >&2
  exit 1
fi

cd "${MLX_DIR}"
./install.sh
echo "Stable Audio runtime installed. No --download bundle was requested."

