#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=wan22_s2v_local_env.sh
source "$SCRIPT_DIR/wan22_s2v_local_env.sh"

cd "$PROJECT_ROOT"
exec .venv/bin/python -m lpw.generation.local_s2v_worker \
  --validate-only \
  --allow-non-macos-validation \
  --backend-module "${LPW_WAN_S2V_BACKEND_MODULE:-backend-not-installed}" \
  --model-gguf "$LPW_WAN_S2V_GGUF" \
  --vae "$LPW_WAN_S2V_VAE" \
  --text-encoder "$LPW_WAN_S2V_TEXT_ENCODER" \
  --tokenizer "$LPW_WAN_S2V_TOKENIZER" \
  --audio-encoder "$LPW_WAN_S2V_AUDIO_ENCODER" \
  --ffmpeg "$LPW_FFMPEG" \
  --width 832 \
  --height 480
