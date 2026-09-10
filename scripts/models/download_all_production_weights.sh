#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
MINIMUM_FREE_GIB="${LPW_PRODUCTION_DOWNLOAD_MINIMUM_FREE_GIB:-230}"
AVAILABLE_KIB="$(df -Pk "$PROJECT_ROOT/models" | awk 'NR==2 {print $4}')"
REQUIRED_KIB=$((MINIMUM_FREE_GIB * 1024 * 1024))
if (( AVAILABLE_KIB < REQUIRED_KIB )); then
  echo "BLOCKED: all production weights require at least ${MINIMUM_FREE_GIB} GiB free before starting." >&2
  echo "Current free space: $((AVAILABLE_KIB / 1024 / 1024)) GiB." >&2
  exit 3
fi

for script in \
  download_qwen3_vl_32b_production.sh \
  download_wan22_s2v_bf16_production.sh \
  download_seedvr2_7b_production.sh \
  download_latentsync_1_6_production.sh \
  download_codeformer_production.sh \
  download_practical_rife_production.sh; do
  "$SCRIPT_DIRECTORY/$script"
done

"$PROJECT_ROOT/.venv/bin/python" -m lpw.pipeline_cli check --environment production
