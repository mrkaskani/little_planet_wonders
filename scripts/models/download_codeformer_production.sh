#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
OUTPUT_DIRECTORY="${LPW_CODEFORMER_PRODUCTION_DIR:-$PROJECT_ROOT/models/codeformer}"
WGET_BIN="${LPW_WGET:-wget}"
mkdir -p "$OUTPUT_DIRECTORY/facelib"

download() {
  local url="$1"
  local destination="$2"
  local partial="${destination}.part"
  if [[ -s "$destination" ]]; then
    echo "READY  $destination"
    return
  fi
  "$WGET_BIN" --continue --https-only --tries=20 --timeout=60 \
    --retry-connrefused --waitretry=5 --progress=bar:force:noscroll \
    -O "$partial" "$url"
  test -s "$partial"
  mv "$partial" "$destination"
}

RELEASE="https://github.com/sczhou/CodeFormer/releases/download/v0.1.0"
download "$RELEASE/codeformer.pth" "$OUTPUT_DIRECTORY/codeformer.pth"
download "$RELEASE/detection_Resnet50_Final.pth" "$OUTPUT_DIRECTORY/facelib/detection_Resnet50_Final.pth"
download "$RELEASE/parsing_parsenet.pth" "$OUTPUT_DIRECTORY/facelib/parsing_parsenet.pth"
download "$RELEASE/RealESRGAN_x2plus.pth" "$OUTPUT_DIRECTORY/facelib/RealESRGAN_x2plus.pth"
echo "READY: CodeFormer v0.1.0 production weights in $OUTPUT_DIRECTORY"
