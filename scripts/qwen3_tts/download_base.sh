#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv-qwen3-tts"
MODEL_DIR="${PROJECT_ROOT}/models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base"

if [[ ! -x "${VENV_DIR}/bin/hf" ]]; then
  echo "Run scripts/qwen3_tts/setup.sh first." >&2
  exit 1
fi

mkdir -p "${MODEL_DIR}"
HF_HUB_DISABLE_XET=1 HF_HUB_DOWNLOAD_TIMEOUT=120 \
  "${VENV_DIR}/bin/hf" download \
  Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --max-workers 1 \
  --local-dir "${MODEL_DIR}"

echo "Base model downloaded to ${MODEL_DIR}"
