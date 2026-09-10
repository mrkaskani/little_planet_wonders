#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
exec "$SCRIPT_DIRECTORY/download_huggingface_wget.sh" \
  "Wan-AI/Wan2.2-S2V-14B" \
  "dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b" \
  "${LPW_WAN_S2V_PRODUCTION_DIR:-$PROJECT_ROOT/models/wan22-s2v-production-bf16}" \
  '(^config\.json$|^configuration\.json$|^Wan2\.1_VAE\.pth$|^diffusion_pytorch_model.*\.safetensors(\.index\.json)?$|^models_t5_umt5-xxl-enc-bf16\.pth$|^google/umt5-xxl/(special_tokens_map\.json|spiece\.model|tokenizer\.json|tokenizer_config\.json)$|^wav2vec2-large-xlsr-53-english/(config\.json|configuration\.json|model\.safetensors|preprocessor_config\.json|special_tokens_map\.json|vocab\.json)$)'
