#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
exec "$SCRIPT_DIRECTORY/download_huggingface_wget.sh" \
  "Qwen/Qwen3-VL-32B-Instruct" \
  "0cfaf48183f594c314753d30a4c4974bc75f3ccb" \
  "${LPW_QWEN3_VL_PRODUCTION_DIR:-$PROJECT_ROOT/models/qwen3-vl-32b-instruct}" \
  '(^|/)(config\.json|generation_config\.json|chat_template\.json|preprocessor_config\.json|video_preprocessor_config\.json|tokenizer_config\.json|tokenizer\.json|merges\.txt|vocab\.json|model-[0-9]+-of-[0-9]+\.safetensors|model\.safetensors\.index\.json)$'
