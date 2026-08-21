#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Runtime missing. Run ./install.sh without --download first." >&2
  exit 1
fi

echo "Downloading only Stable Audio 3 Small-SFX and its required shared weights."
echo "Bundle: sm-sfx; decoder: SAME-S; medium and sm-music are excluded."
echo "Hugging Face tokens are read from the local login or HF_TOKEN; never pass a token as an argument."

INSTALL_SKIP_PIP=1 "${PYTHON}" "${SCRIPT_DIR}/scripts/install.py" \
  --download sm-sfx

