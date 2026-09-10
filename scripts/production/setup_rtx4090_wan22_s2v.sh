#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
RUNTIME_ROOT="${LPW_PRODUCTION_RUNTIME_ROOT:-${PROJECT_ROOT}/runtime/production/rtx4090-wan22-s2v}"
DIFFSYNTH_DIRECTORY="${LPW_DIFFSYNTH_DIR:-${RUNTIME_ROOT}/DiffSynth-Studio}"
VENV_DIRECTORY="${LPW_WAN_S2V_VENV:-${RUNTIME_ROOT}/venv}"
DIFFSYNTH_COMMIT="4dbf980d4d0eb34eda136300dd0d72014cff8965"

install_system_packages() {
  if ! command -v apt-get >/dev/null 2>&1; then
    return
  fi
  local prefix=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if ! command -v sudo >/dev/null 2>&1; then
      echo "apt-get is available but root/sudo is not; install git, ffmpeg, python3-venv manually" >&2
      exit 1
    fi
    prefix=(sudo)
  fi
  "${prefix[@]}" apt-get update
  "${prefix[@]}" apt-get install -y git ffmpeg python3-venv python3-dev build-essential
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
"${VENV_DIRECTORY}/bin/python" -m pip install -e "${DIFFSYNTH_DIRECTORY}[audio]" pyyaml psutil

"${VENV_DIRECTORY}/bin/python" - <<'PY'
import torch

if not torch.cuda.is_available():
    raise SystemExit("CUDA is unavailable inside the production virtual environment")
name = torch.cuda.get_device_name(0)
capability = torch.cuda.get_device_capability(0)
total_gib = torch.cuda.get_device_properties(0).total_memory / 1024**3
if capability < (8, 9):
    raise SystemExit(f"true FP8 path requires Ada compute capability 8.9+, got {capability}")
if not hasattr(torch, "float8_e4m3fn") or not hasattr(torch, "_scaled_mm"):
    raise SystemExit("this PyTorch build does not expose float8_e4m3fn and _scaled_mm")
print(f"CUDA ready: {name}; capability={capability}; VRAM={total_gib:.1f} GiB")
PY

printf 'Production environment ready.\nVenv: %s\nDiffSynth: %s\n' \
  "${VENV_DIRECTORY}" "${DIFFSYNTH_DIRECTORY}"
