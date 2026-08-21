#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

exec "${PROJECT_ROOT}/.venv-qwen3-tts/bin/python" \
  "${SCRIPT_DIR}/generate_profile_references.py" \
  --profile "${PROJECT_ROOT}/src/lpw/context/projects/riri-yoyo/characters/riri/voice-profile.yaml" \
  --seed-base "${RIRI_VOICE_SEED:-314159}" \
  "$@"
