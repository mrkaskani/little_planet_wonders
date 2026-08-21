#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
  exec /usr/bin/env bash "$0" "$@"
fi
set -euo pipefail

ACE_DIR="/Users/oldowl/AI-Audio/ace-step"
CHECKPOINTS_DIR="${ACE_DIR}/checkpoints"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${ACE_DIR}/.venv/bin/python"

runtime_ready() {
  [[ -x "${PYTHON}" ]] \
    && (cd "${ACE_DIR}" && "${PYTHON}" -c \
      'import acestep, huggingface_hub, loguru, mlx.core' >/dev/null 2>&1)
}

if ! runtime_ready; then
  echo "ACE-Step runtime is missing or incomplete; installing it first."
  "${SCRIPT_DIR}/install-runtime.sh"
fi

if ! runtime_ready; then
  echo "ACE-Step runtime verification failed after installation." >&2
  echo "Re-run ${SCRIPT_DIR}/install-runtime.sh and inspect its output." >&2
  exit 1
fi

echo "Downloading official ACE-Step/Ace-Step1.5 (~10.09 GB)."
echo "Includes: acestep-v15-turbo (2B), acestep-5Hz-lm-1.7B, VAE, and Qwen3-Embedding-0.6B."
echo "Excludes: XL models, 4B LM, and optional checkpoints."
echo "Authentication is read from the local Hugging Face login; never pass a token as an argument."

cd "${ACE_DIR}"
ACESTEP_CHECKPOINTS_DIR="${CHECKPOINTS_DIR}" \
  "${PYTHON}" -m acestep.model_downloader \
  --model main \
  --dir "${CHECKPOINTS_DIR}"
