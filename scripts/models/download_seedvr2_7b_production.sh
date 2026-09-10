#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
exec "$SCRIPT_DIRECTORY/download_huggingface_wget.sh" \
  "ByteDance-Seed/SeedVR2-7B" \
  "eb0c4281d41ba3767d4f14370f0e37e9e9180c16" \
  "${LPW_SEEDVR2_PRODUCTION_DIR:-$PROJECT_ROOT/models/seedvr2-7b}" \
  '^(ema_vae\.pth|seedvr2_ema_7b\.pth|seedvr2_ema_7b_sharp\.pth)$'
