#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv-qwen3-tts"
MODEL_DIR="${PROJECT_ROOT}/models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base"

if [[ ! -x "${VENV_DIR}/bin/qwen-tts-demo" ]]; then
  echo "Run scripts/qwen3_tts/setup.sh first." >&2
  exit 1
fi

if [[ ! -f "${MODEL_DIR}/config.json" \
   || ! -f "${MODEL_DIR}/model.safetensors" \
   || ! -f "${MODEL_DIR}/speech_tokenizer/model.safetensors" ]]; then
  echo "Run scripts/qwen3_tts/download_base.sh first." >&2
  exit 1
fi

exec "${VENV_DIR}/bin/qwen-tts-demo" "${MODEL_DIR}" \
  --device mps \
  --dtype float16 \
  --no-flash-attn \
  --ip 127.0.0.1 \
  --port "${QWEN_TTS_PORT:-8001}"
