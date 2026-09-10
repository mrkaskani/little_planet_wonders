#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="${LPW_WAN_S2V_MANIFEST:-$SCRIPT_DIR/wan22_s2v_q4ks_manifest.tsv}"
MODEL_ROOT="${1:-${LPW_WAN_S2V_MODEL_DIR:-$PROJECT_ROOT/models/wan22-s2v-local-q4ks}}"

file_size() {
  if stat -f '%z' "$1" >/dev/null 2>&1; then
    stat -f '%z' "$1"
  else
    stat -c '%s' "$1"
  fi
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "Neither shasum nor sha256sum is installed." >&2
    return 2
  fi
}

failures=0
checked=0
while IFS=$'\t' read -r role repository revision remote_path local_path expected_size expected_sha; do
  [[ -z "${role:-}" || "$role" == \#* ]] && continue
  artifact="$MODEL_ROOT/$local_path"
  checked=$((checked + 1))

  if [[ ! -f "$artifact" ]]; then
    printf 'MISSING  %-26s %s\n' "$role" "$artifact" >&2
    failures=$((failures + 1))
    continue
  fi

  actual_size="$(file_size "$artifact")"
  if [[ "$actual_size" != "$expected_size" ]]; then
    printf 'BAD-SIZE %-26s expected=%s actual=%s %s\n' \
      "$role" "$expected_size" "$actual_size" "$artifact" >&2
    failures=$((failures + 1))
    continue
  fi

  if [[ "$expected_sha" != "-" ]]; then
    actual_sha="$(sha256_file "$artifact")"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      printf 'BAD-HASH %-26s %s\n' "$role" "$artifact" >&2
      failures=$((failures + 1))
      continue
    fi
  fi

  printf 'OK       %-26s %s\n' "$role" "$artifact"
done < "$MANIFEST"

if [[ "$checked" -eq 0 ]]; then
  echo "Manifest contained no artifacts: $MANIFEST" >&2
  exit 2
fi

if [[ "$failures" -ne 0 ]]; then
  printf 'Verification failed: %d of %d artifact(s) invalid or missing.\n' "$failures" "$checked" >&2
  exit 1
fi

printf 'Verified %d Wan 2.2 S2V Q4_K_S artifact(s) in %s\n' "$checked" "$MODEL_ROOT"
