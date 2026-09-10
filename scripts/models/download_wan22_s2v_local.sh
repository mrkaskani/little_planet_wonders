#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="${LPW_WAN_S2V_MANIFEST:-$SCRIPT_DIR/wan22_s2v_q4ks_manifest.tsv}"
MODEL_ROOT="${1:-${LPW_WAN_S2V_MODEL_DIR:-$PROJECT_ROOT/models/wan22-s2v-local-q4ks}}"
VERIFY_SCRIPT="$SCRIPT_DIR/verify_wan22_s2v_local.sh"

if ! command -v wget >/dev/null 2>&1; then
  echo "GNU wget is required. On macOS, install it with: brew install wget" >&2
  exit 2
fi

mkdir -p "$MODEL_ROOT"

while IFS=$'\t' read -r role repository revision remote_path local_path expected_size expected_sha; do
  [[ -z "${role:-}" || "$role" == \#* ]] && continue
  destination="$MODEL_ROOT/$local_path"

  if [[ -f "$destination" ]]; then
    printf 'EXISTS   %-26s %s\n' "$role" "$destination"
    continue
  fi

  partial="$destination.part"
  mkdir -p "$(dirname "$destination")"
  artifact_url="https://huggingface.co/$repository/resolve/$revision/$remote_path"

  printf 'DOWNLOAD %-26s %s@%s:%s\n' "$role" "$repository" "$revision" "$remote_path"
  printf 'RESUME   %-26s %s\n' "$role" "$partial"
  wget \
    --continue \
    --tries=0 \
    --timeout=30 \
    --waitretry=5 \
    --retry-connrefused \
    --progress=bar:force:noscroll \
    --output-document="$partial" \
    "$artifact_url"

  actual_size="$(stat -f '%z' "$partial" 2>/dev/null || stat -c '%s' "$partial")"
  if [[ "$actual_size" != "$expected_size" ]]; then
    printf 'Incomplete size for %s: expected=%s actual=%s\n' \
      "$role" "$expected_size" "$actual_size" >&2
    exit 1
  fi

  if [[ "$expected_sha" != "-" ]]; then
    actual_sha="$(shasum -a 256 "$partial" | awk '{print $1}')"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      printf 'SHA-256 mismatch for %s; partial preserved at %s\n' "$role" "$partial" >&2
      exit 1
    fi
  fi

  mv "$partial" "$destination"
done < "$MANIFEST"

echo "Downloads completed. Running offline size and SHA-256 verification..."
"$VERIFY_SCRIPT" "$MODEL_ROOT"

cat <<EOF

Wan 2.2 S2V Q4_K_S package is ready at:
  $MODEL_ROOT

No LightX2V I2V/T2V LoRAs were downloaded because they are not S2V weights.
EOF
