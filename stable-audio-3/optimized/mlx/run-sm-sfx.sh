#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIRED=(
  "models/mlx/dit_sm-sfx_f16.npz"
  "models/mlx/same_s_decoder_f32.npz"
  "models/mlx/same_s_encoder_f32.npz"
  "models/mlx/t5gemma_f16.npz"
)

missing=()
for relative_path in "${REQUIRED[@]}"; do
  [[ -e "${SCRIPT_DIR}/${relative_path}" ]] || missing+=("${relative_path}")
done

if (( ${#missing[@]} )); then
  echo "Small-SFX is not downloaded; refusing to trigger an implicit download." >&2
  printf '  missing: %s\n' "${missing[@]}" >&2
  echo "Run ./download-sm-sfx.sh when you are ready." >&2
  exit 1
fi

exec "${SCRIPT_DIR}/sa3" \
  --dit sm-sfx \
  --decoder same-s \
  "$@"

