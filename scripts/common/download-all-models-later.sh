#!/usr/bin/env bash
set -uo pipefail

SCRIPTS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "${SCRIPTS_ROOT}/.." && pwd)"
ACE_CHECKPOINTS="/Users/oldowl/AI-Audio/ace-step/checkpoints"
SA3_MODELS="/Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx/models/mlx"
QWEN_MODELS="${PROJECT_ROOT}/models/qwen3-tts"
SPEAKER_MODELS="${PROJECT_ROOT}/models/speaker-embeddings"

MAX_RETRIES="${MODEL_DOWNLOAD_RETRIES:-3}"
RETRY_DELAY_SECONDS="${MODEL_DOWNLOAD_RETRY_DELAY:-15}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: download-all-models-later.sh [--dry-run]

Downloads only incomplete configured model bundles. Complete bundles are
skipped. Failed downloads are retried and do not prevent later jobs running.

Environment overrides:
  MODEL_DOWNLOAD_RETRIES=N       attempts per incomplete bundle (default: 3)
  MODEL_DOWNLOAD_RETRY_DELAY=N   seconds between attempts (default: 15)
EOF
}

case "${1:-}" in
  "") ;;
  --dry-run) DRY_RUN=1 ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

if ! [[ "${MAX_RETRIES}" =~ ^[1-9][0-9]*$ ]]; then
  echo "MODEL_DOWNLOAD_RETRIES must be a positive integer." >&2
  exit 2
fi
if ! [[ "${RETRY_DELAY_SECONDS}" =~ ^[0-9]+$ ]]; then
  echo "MODEL_DOWNLOAD_RETRY_DELAY must be a non-negative integer." >&2
  exit 2
fi

files_present() {
  local root="$1"
  shift
  local relative
  for relative in "$@"; do
    [[ -s "${root}/${relative}" ]] || return 1
  done
}

ace_complete() {
  files_present "${ACE_CHECKPOINTS}" \
    "acestep-v15-turbo/model.safetensors" \
    "acestep-5Hz-lm-1.7B/model.safetensors" \
    "vae/diffusion_pytorch_model.safetensors" \
    "Qwen3-Embedding-0.6B/model.safetensors"
}

sa3_medium_complete() {
  files_present "${SA3_MODELS}" \
    "dit_medium_f16.npz" \
    "same_l_decoder_f32.npz" \
    "same_l_encoder_f32.npz" \
    "t5gemma_f16.npz"
}

qwen_voice_design_complete() {
  files_present "${QWEN_MODELS}/Qwen3-TTS-12Hz-1.7B-VoiceDesign" \
    "config.json" \
    "model.safetensors" \
    "speech_tokenizer/config.json" \
    "speech_tokenizer/model.safetensors"
}

qwen_base_complete() {
  files_present "${QWEN_MODELS}/Qwen3-TTS-12Hz-1.7B-Base" \
    "config.json" \
    "model.safetensors" \
    "speech_tokenizer/config.json" \
    "speech_tokenizer/model.safetensors"
}

speaker_analyzer_complete() {
  files_present "${SPEAKER_MODELS}/wavlm-base-plus-sv" \
    "config.json" \
    "preprocessor_config.json" \
    "pytorch_model.bin"
}

declare -a RESULTS=()
FAILURES=0

run_job() {
  local label="$1"
  local check_function="$2"
  local command="$3"
  local attempt

  echo
  echo "==> ${label}"
  if "${check_function}"; then
    echo "SKIP: all required files already exist."
    RESULTS+=("SKIPPED  ${label}")
    return 0
  fi

  if (( DRY_RUN )); then
    echo "PENDING: required files are incomplete."
    echo "Would run: ${command}"
    RESULTS+=("PENDING  ${label}")
    return 0
  fi

  for (( attempt=1; attempt<=MAX_RETRIES; attempt++ )); do
    echo "Attempt ${attempt}/${MAX_RETRIES}: ${command}"
    if "${command}"; then
      echo "Download command finished; verifying required files..."
    else
      echo "Attempt ${attempt} exited with an error; checking for completed files..." >&2
    fi

    if "${check_function}"; then
      echo "COMPLETE: all required files verified."
      RESULTS+=("COMPLETE ${label}")
      return 0
    fi

    if (( attempt < MAX_RETRIES )); then
      echo "Still incomplete. Retrying in ${RETRY_DELAY_SECONDS}s..." >&2
      sleep "${RETRY_DELAY_SECONDS}"
    fi
  done

  echo "FAILED: ${label} remains incomplete after ${MAX_RETRIES} attempts." >&2
  echo "Continuing to the next model bundle." >&2
  RESULTS+=("FAILED   ${label}")
  FAILURES=$((FAILURES + 1))
  return 0
}

echo "Resumable local model downloader"
echo "Free disk: $(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')"
echo "Retries per incomplete bundle: ${MAX_RETRIES}"
echo "Retry delay: ${RETRY_DELAY_SECONDS}s"
if (( DRY_RUN )); then
  echo "Mode: dry run (no downloads)"
fi

run_job "Qwen3-TTS 1.7B VoiceDesign" \
  qwen_voice_design_complete \
  "${SCRIPTS_ROOT}/qwen3_tts/download.sh"
run_job "Qwen3-TTS 1.7B Base" \
  qwen_base_complete \
  "${SCRIPTS_ROOT}/qwen3_tts/download_base.sh"
run_job "WavLM speaker analyzer" \
  speaker_analyzer_complete \
  "${SCRIPTS_ROOT}/qwen3_tts/download-speaker-analyzer.sh"
run_job "ACE-Step 1.5 main bundle" \
  ace_complete \
  "${SCRIPTS_ROOT}/ace-step-1.5/download-model.sh"
run_job "Stable Audio 3 Medium + SAME-L" \
  sa3_medium_complete \
  "${SCRIPTS_ROOT}/stable-audio-3-medium/download-model.sh"
echo
echo "Download summary"
printf '  %s\n' "${RESULTS[@]}"

if (( FAILURES > 0 )); then
  echo "${FAILURES} bundle(s) remain incomplete. Re-run this command to resume them." >&2
  exit 1
fi

if (( DRY_RUN )); then
  echo "Dry run complete; no downloads were started."
else
  echo "All configured model bundles are complete."
fi
