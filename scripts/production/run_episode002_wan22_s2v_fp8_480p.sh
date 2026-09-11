#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIRECTORY}/../.." && pwd)"
RUNTIME_ROOT="${LPW_PRODUCTION_RUNTIME_ROOT:-${PROJECT_ROOT}/runtime/production/rtx4090-wan22-s2v}"
VENV_DIRECTORY="${LPW_WAN_S2V_VENV:-${RUNTIME_ROOT}/venv}"
MODEL_DIRECTORY="${LPW_WAN_S2V_MODEL_DIR:-${PROJECT_ROOT}/runtime/models/Wan2.2-S2V-14B}"
MANIFEST="${LPW_EPISODE002_MANIFEST:-${PROJECT_ROOT}/src/lpw/context/projects/riri-yoyo/generation-records/video-jobs/episode-002--sharing-shapes--wan22-s2v-fp8-480p--v001.yaml}"
OUTPUT_DIRECTORY="${LPW_EPISODE002_OUTPUT_DIR:-${PROJECT_ROOT}/runtime/video/riri-yoyo/episodes/episode-002/s2v/fp8-480p-v001}"

if [[ ! -x "${VENV_DIRECTORY}/bin/python" ]]; then
  echo "Missing production environment. Run scripts/production/setup_rtx4090_wan22_s2v.sh first." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"
exec "${VENV_DIRECTORY}/bin/python" \
  "${SCRIPT_DIRECTORY}/run_episode001_wan22_s2v_fp8_480p.py" \
  --manifest "${MANIFEST}" \
  --model-dir "${MODEL_DIRECTORY}" \
  --output-dir "${OUTPUT_DIRECTORY}" \
  "$@"
