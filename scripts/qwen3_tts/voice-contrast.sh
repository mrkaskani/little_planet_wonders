#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON="${PROJECT_ROOT}/.venv-qwen3-tts/bin/python"

case "${1:-}" in
  generate)
    shift
    exec "${PYTHON}" "${SCRIPT_DIR}/generate_contrast_candidates.py" "$@"
    ;;
  analyze)
    shift
    exec "${PYTHON}" "${SCRIPT_DIR}/analyze_voice_contrast.py" "$@"
    ;;
  download-analyzer)
    shift
    exec "${SCRIPT_DIR}/download-speaker-analyzer.sh" "$@"
    ;;
  *)
    echo "Usage: $0 {generate|analyze|download-analyzer} [options]" >&2
    exit 2
    ;;
esac
