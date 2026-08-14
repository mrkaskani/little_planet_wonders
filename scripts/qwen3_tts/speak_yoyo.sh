#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 'dialogue text' OUTPUT.wav" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REFERENCE="${PROJECT_ROOT}/src/lpw/context/projects/classroom/audio-assets/voice-references/yoyo/neutral-friendly.wav"

exec "${PROJECT_ROOT}/.venv-qwen3-tts/bin/python" "${SCRIPT_DIR}/clone_voice.py" \
  --text "$1" \
  --ref-audio "${REFERENCE}" \
  --ref-text "Hello! I'm happy to see you. It's a lovely day. Shall we look around together?" \
  --language English \
  --seed 271828 \
  --output "$2"
