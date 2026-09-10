#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
MODEL_DIRECTORY="${LPW_WAN_S2V_MODEL_DIR:-${PROJECT_ROOT}/runtime/models/Wan2.2-S2V-14B}"

# The non-Comfy DiffSynth production path reads the official Wan shards from
# disk and prepares the DiT in true E4M3 FP8 at runtime. Downloads are delegated
# to the existing wget-based, resumable, checksum-aware Hugging Face helper.
LPW_WAN_S2V_PRODUCTION_DIR="${MODEL_DIRECTORY}" \
  exec "${SCRIPT_DIRECTORY}/download_wan22_s2v_bf16_production.sh"
