#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
RUNTIME_ROOT="${LPW_PRODUCTION_RUNTIME_ROOT:-${PROJECT_ROOT}/runtime/production/rtx3090-wan22-s2v}"
DIFFSYNTH_DIRECTORY="${LPW_DIFFSYNTH_DIR:-${RUNTIME_ROOT}/DiffSynth-Studio}"
VENV_DIRECTORY="${LPW_WAN_S2V_VENV:-${RUNTIME_ROOT}/venv}"
MODEL_DIRECTORY="${LPW_WAN_S2V_MODEL_DIR:-${PROJECT_ROOT}/runtime/models/Wan2.2-S2V-14B}"
DIFFSYNTH_COMMIT="4dbf980d4d0eb34eda136300dd0d72014cff8965"

install_system_packages() {
  if ! command -v apt-get >/dev/null 2>&1; then
    for command in git ffmpeg python3 wget; do
      if ! command -v "${command}" >/dev/null 2>&1; then
        echo "Missing ${command}; install it with the host package manager." >&2
        exit 1
      fi
    done
    return
  fi

  local prefix=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if ! command -v sudo >/dev/null 2>&1; then
      echo "apt-get is available but root/sudo is not; install the required packages manually." >&2
      exit 1
    fi
    prefix=(sudo)
  fi
  "${prefix[@]}" apt-get update
  "${prefix[@]}" apt-get install -y \
    build-essential ca-certificates ffmpeg git python3-dev python3-venv wget
}

install_system_packages
mkdir -p "${RUNTIME_ROOT}"

if [[ ! -d "${DIFFSYNTH_DIRECTORY}/.git" ]]; then
  git clone https://github.com/modelscope/DiffSynth-Studio.git "${DIFFSYNTH_DIRECTORY}"
fi
git -C "${DIFFSYNTH_DIRECTORY}" fetch --depth 1 origin "${DIFFSYNTH_COMMIT}"
git -C "${DIFFSYNTH_DIRECTORY}" checkout --detach "${DIFFSYNTH_COMMIT}"

if [[ ! -x "${VENV_DIRECTORY}/bin/python" ]]; then
  python3 -m venv --system-site-packages "${VENV_DIRECTORY}"
fi

"${VENV_DIRECTORY}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIRECTORY}/bin/python" -m pip install -e "${PROJECT_ROOT}"
"${VENV_DIRECTORY}/bin/python" -m pip install \
  -e "${DIFFSYNTH_DIRECTORY}[audio]" pyyaml psutil

"${VENV_DIRECTORY}/bin/python" - <<'PY'
import torch

if not torch.cuda.is_available():
    raise SystemExit("CUDA is unavailable inside the production virtual environment")
name = torch.cuda.get_device_name(0)
capability = torch.cuda.get_device_capability(0)
total_gib = torch.cuda.get_device_properties(0).total_memory / 1024**3
if "RTX 3090" not in name.upper():
    raise SystemExit(f"expected an RTX 3090, detected {name}")
if capability < (8, 0):
    raise SystemExit(f"BF16 execution requires Ampere capability 8.0+, got {capability}")
if total_gib < 23:
    raise SystemExit(f"expected approximately 24 GiB VRAM, detected {total_gib:.1f} GiB")
if not torch.cuda.is_bf16_supported():
    raise SystemExit("this CUDA/PyTorch build does not report BF16 support")
print(f"CUDA BF16 ready: {name}; capability={capability}; VRAM={total_gib:.1f} GiB")
PY

if [[ "${LPW_SKIP_MODEL_DOWNLOAD:-0}" != "1" ]]; then
  LPW_PYTHON="${VENV_DIRECTORY}/bin/python" \
  LPW_WAN_S2V_MODEL_DIR="${MODEL_DIRECTORY}" \
    "${PROJECT_ROOT}/scripts/models/download_wan22_s2v.sh"
fi

printf 'RTX 3090 Wan S2V environment ready.\nVenv: %s\nDiffSynth: %s\nModel: %s\n' \
  "${VENV_DIRECTORY}" "${DIFFSYNTH_DIRECTORY}" "${MODEL_DIRECTORY}"
