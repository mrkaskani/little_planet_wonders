#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv-qwen3-tts"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.local.txt"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  uv venv --python 3.12 "${VENV_DIR}"
fi

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
  echo "Missing local requirements file: ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

uv pip install --python "${VENV_DIR}/bin/python" --upgrade \
  --requirements "${REQUIREMENTS_FILE}"

# FlashAttention 2 requires Linux plus a CUDA or ROCm toolkit. Install it only
# when this environment has a working CUDA runtime; Apple MPS uses eager
# attention instead.
if [[ "$(uname -s)" == "Linux" ]] && "${VENV_DIR}/bin/python" - <<'PY'
import torch
raise SystemExit(0 if torch.cuda.is_available() else 1)
PY
then
  uv pip install --python "${VENV_DIR}/bin/python" --upgrade ninja packaging psutil
  MAX_JOBS="${MAX_JOBS:-4}" uv pip install \
    --python "${VENV_DIR}/bin/python" \
    --no-build-isolation \
    --upgrade flash-attn
else
  echo "FlashAttention skipped: it requires Linux with a supported CUDA/ROCm GPU."
fi

"${VENV_DIR}/bin/python" - <<'PY'
from importlib.metadata import version
from qwen_tts import Qwen3TTSModel

print(f"qwen-tts: {version('qwen-tts')}")
print(f"Qwen3TTSModel: {Qwen3TTSModel.__name__}")
PY
