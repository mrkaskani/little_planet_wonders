#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
OUTPUT_DIRECTORY="${LPW_RIFE_PRODUCTION_DIR:-$PROJECT_ROOT/models/practical-rife}"
ARCHIVE="$OUTPUT_DIRECTORY/rife-v4.25.zip"
PARTIAL="${ARCHIVE}.part"
WGET_BIN="${LPW_WGET:-wget}"
mkdir -p "$OUTPUT_DIRECTORY"

if [[ -f "$OUTPUT_DIRECTORY/train_log/flownet.pkl" ]]; then
  echo "READY: Practical-RIFE v4.25 weights in $OUTPUT_DIRECTORY/train_log"
  exit 0
fi

# v4.25 is the latest complete model archive linked by the official Practical-RIFE README.
URL="https://drive.usercontent.google.com/download?id=1_l4OgBp3GrrHOcQB87xXCI7OtTzyeXZL&export=download&confirm=t"
"$WGET_BIN" --continue --tries=20 --timeout=60 --retry-connrefused \
  --waitretry=5 --progress=bar:force:noscroll -O "$PARTIAL" "$URL"
unzip -tq "$PARTIAL" >/dev/null
mv "$PARTIAL" "$ARCHIVE"
STAGING_DIRECTORY="$(mktemp -d "$OUTPUT_DIRECTORY/.rife-extract.XXXXXX")"
trap 'rm -rf "$STAGING_DIRECTORY"' EXIT
unzip -q "$ARCHIVE" -d "$STAGING_DIRECTORY"
FLOWNET="$(find "$STAGING_DIRECTORY" -type f -name flownet.pkl -print -quit)"
if [[ -z "$FLOWNET" ]]; then
  echo "The official v4.25 archive did not contain flownet.pkl." >&2
  exit 4
fi
mkdir -p "$OUTPUT_DIRECTORY/train_log"
cp -R "$(dirname "$FLOWNET")/." "$OUTPUT_DIRECTORY/train_log/"
echo "READY: Practical-RIFE v4.25 weights in $OUTPUT_DIRECTORY/train_log"
