#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
MODEL_DIRECTORY="${LPW_WAN_S2V_MODEL_DIR:-${PROJECT_ROOT}/runtime/models/Wan2.2-S2V-14B}"

# Download the official pinned BF16 source bundle required by Wan 2.2 S2V.
# Runtime precision is selected by the renderer, so these same source files
# support the RTX 3090 BF16/offload path and the RTX 4090 FP8 execution path.
LPW_WAN_S2V_PRODUCTION_DIR="${MODEL_DIRECTORY}" \
  exec "${SCRIPT_DIRECTORY}/download_wan22_s2v_bf16_production.sh"
