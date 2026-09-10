#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/wan22_s2v_local_env.sh"

REPORT_PATH="${1:-${PROJECT_ROOT}/runtime/diagnostics/wan22-s2v-gguf-mps-block-0.json}"

exec "${PROJECT_ROOT}/.venv/bin/python" -m lpw.generation.wan_gguf_mps \
  --model "${LPW_WAN_S2V_GGUF}" \
  --config "${PROJECT_ROOT}/models/wan22-s2v-local-q4ks/config/config.json" \
  --block 0 \
  --report "${REPORT_PATH}"
