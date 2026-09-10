#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/wan22_s2v_local_env.sh"

cd "$PROJECT_ROOT"
exec .venv/bin/python -m lpw.generation.local_s2v_worker --width 832 --height 480
