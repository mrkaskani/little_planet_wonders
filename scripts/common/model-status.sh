#!/usr/bin/env bash
set -euo pipefail

ACE_DIR="/Users/oldowl/AI-Audio/ace-step"
MLX_DIR="/Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Machine"
echo "  architecture: $(uname -m)"
echo "  chip: $(sysctl -n machdep.cpu.brand_string)"
echo "  free disk: $(df -h /Users/oldowl/AI-Audio | awk 'NR==2 {print $4}')"

echo "ACE-Step"
if [[ -x "${ACE_DIR}/.venv/bin/python" ]] \
   && (cd "${ACE_DIR}" && .venv/bin/python -c \
     'import acestep, huggingface_hub, loguru, mlx.core' >/dev/null 2>&1); then
  echo "  runtime: present"
else
  echo "  runtime: missing or incomplete"
fi
for relative_path in \
  "acestep-v15-turbo/model.safetensors" \
  "acestep-5Hz-lm-1.7B/model.safetensors" \
  "vae/diffusion_pytorch_model.safetensors" \
  "Qwen3-Embedding-0.6B/model.safetensors"; do
  if [[ -f "${ACE_DIR}/checkpoints/${relative_path}" ]]; then
    echo "  present: ${relative_path}"
  else
    echo "  missing: ${relative_path}"
  fi
done

echo "Stable Audio 3"
if [[ -x "${MLX_DIR}/.venv/bin/python" ]]; then
  (cd "${MLX_DIR}" && .venv/bin/python - <<'PY'
import mlx.core as mx
from scripts.weights import bundle_status
print(f"  MLX version: {mx.__version__}")
print(f"  MLX device: {mx.default_device()}")
for name in ("medium",):
    present, total = bundle_status(name)
    print(f"  {name}: {present}/{total} files")
PY
  )
else
  echo "  runtime: missing"
fi

echo "Qwen3-TTS and speaker analysis"
for model_spec in \
  "VoiceDesign|${PROJECT_ROOT}/models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-VoiceDesign|config.json model.safetensors speech_tokenizer/config.json speech_tokenizer/model.safetensors" \
  "Base|${PROJECT_ROOT}/models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base|config.json model.safetensors speech_tokenizer/config.json speech_tokenizer/model.safetensors" \
  "WavLM analyzer|${PROJECT_ROOT}/models/speaker-embeddings/wavlm-base-plus-sv|config.json preprocessor_config.json pytorch_model.bin"; do
  IFS='|' read -r label root required <<< "${model_spec}"
  present=0
  total=0
  for relative in ${required}; do
    total=$((total + 1))
    if [[ -s "${root}/${relative}" ]]; then
      present=$((present + 1))
    fi
  done
  echo "  ${label}: ${present}/${total} files"
done
