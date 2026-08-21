#!/usr/bin/env bash
set -euo pipefail

ACE_DIR="/Users/oldowl/AI-Audio/ace-step"
PROJECT_DIR="/Users/oldowl/PycharmProjects/little_planet_wonders"
CHECKPOINTS_DIR="${ACE_DIR}/checkpoints"
PYTHON="${ACE_DIR}/.venv/bin/python"
INIT_LLM=true
DEVICE="auto"
while (( $# > 0 )); do
  case "$1" in
    --no-lm)
      INIT_LLM=false
      ;;
    --cpu)
      DEVICE="cpu"
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--no-lm] [--cpu]" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -x "${PYTHON}" ]] \
   || ! (cd "${ACE_DIR}" && "${PYTHON}" -c \
     'import acestep, huggingface_hub, loguru, mlx.core' >/dev/null 2>&1); then
  echo "ACE-Step runtime is missing or incomplete." >&2
  echo "Run /Users/oldowl/PycharmProjects/little_planet_wonders/scripts/ace-step-1.5/install-runtime.sh first." >&2
  exit 1
fi

missing=()
for relative_path in \
  "acestep-v15-turbo/model.safetensors" \
  "acestep-5Hz-lm-1.7B/model.safetensors" \
  "vae/diffusion_pytorch_model.safetensors" \
  "Qwen3-Embedding-0.6B/model.safetensors"; do
  if [[ ! -f "${CHECKPOINTS_DIR}/${relative_path}" ]]; then
    missing+=("${relative_path}")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Required ACE-Step weights are missing; no download was started." >&2
  printf '  %s\n' "${missing[@]}" >&2
  echo "Download later with: /Users/oldowl/PycharmProjects/little_planet_wonders/scripts/ace-step-1.5/download-model.sh" >&2
  exit 1
fi

cd "${ACE_DIR}"
export ACESTEP_CHECKPOINTS_DIR="${CHECKPOINTS_DIR}"
export ACESTEP_INIT_LLM="${INIT_LLM}"
export ACESTEP_DEVICE="${DEVICE}"
if [[ "${DEVICE}" == "cpu" ]]; then
  export ACESTEP_OFFLOAD_TO_CPU="false"
  export ACESTEP_OFFLOAD_DIT_TO_CPU="false"
  export ACESTEP_USE_FLASH_ATTENTION="false"
fi
if [[ "${INIT_LLM}" == "true" ]]; then
  export ACESTEP_LM_BACKEND="mlx"
  export ACESTEP_LM_MODEL_PATH="acestep-5Hz-lm-1.7B"
else
  unset ACESTEP_LM_BACKEND ACESTEP_LM_MODEL_PATH
fi
export HF_HUB_OFFLINE="1"
export TRANSFORMERS_OFFLINE="1"
export PYTHONPATH="${PROJECT_DIR}/src:${ACE_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

echo "Starting official ACE-Step API at http://127.0.0.1:8001 (init_lm=${INIT_LLM}, device=${DEVICE})"
echo "Model downloads are disabled for this server process. Stop with Ctrl-C."
command=("${PYTHON}" "${PROJECT_DIR}/src/lpw/music/ace_server.py" --host 127.0.0.1 --port 8001)
exec "${command[@]}"
