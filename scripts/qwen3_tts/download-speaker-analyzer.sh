#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv-qwen3-tts"
MODEL_DIR="${PROJECT_ROOT}/models/speaker-embeddings/wavlm-base-plus-sv"

if [[ ! -x "${VENV_DIR}/bin/hf" ]]; then
  echo "Run ${SCRIPT_DIR}/setup.sh first." >&2
  exit 1
fi

mkdir -p "${MODEL_DIR}"
HF_HUB_DISABLE_XET=1 HF_HUB_DOWNLOAD_TIMEOUT=120 \
  "${VENV_DIR}/bin/hf" download \
  microsoft/wavlm-base-plus-sv \
  --max-workers 1 \
  --local-dir "${MODEL_DIR}"

echo "Speaker analyzer downloaded to ${MODEL_DIR}"
