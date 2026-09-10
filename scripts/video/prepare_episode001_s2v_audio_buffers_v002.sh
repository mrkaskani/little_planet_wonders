#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_ROOT="${1:-$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/s2v-conditioning/v002}"

RIRI_001="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-001-riri/v001/episode-001_moonlit-garden-greeting_shot-001_riri_final.wav"
YOYO_002="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-002-yoyo/v001/episode-001_moonlit-garden-greeting_shot-002_yoyo_final.wav"
RIRI_003="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-003-riri/v001/episode-001_moonlit-garden-greeting_shot-003_riri_final.wav"

SEGMENT_001="$OUTPUT_ROOT/episode-001--segment-001--clean-speech--buffered-005s--v002.wav"
SEGMENT_002="$OUTPUT_ROOT/episode-001--segment-002--clean-speech--buffered-005s--v002.wav"
SEGMENT_003="$OUTPUT_ROOT/episode-001--segment-003--clean-speech--buffered-005s--v002.wav"

command -v sox >/dev/null 2>&1 || { echo "SoX is required" >&2; exit 2; }
mkdir -p "$OUTPUT_ROOT"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/lpw-s2v-buffer-v002.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

# The approved sources begin with 11,247, 7,200, and 15,949 digital-zero
# samples respectively. Align the first nonzero sample of every derived S2V
# file to sample 12,000 (exactly 0.25 seconds at 48 kHz). Adding/removing only
# digital-zero samples preserves every approved speech sample bit-for-bit.
sox "$RIRI_001" -r 48000 -c 1 -b 24 "$work_dir/segment-001-aligned.wav" pad 753s 0
sox "$YOYO_002" -r 48000 -c 1 -b 24 "$work_dir/segment-002-aligned.wav" pad 4800s 0
sox "$RIRI_003" -r 48000 -c 1 -b 24 "$work_dir/segment-003-aligned.wav" trim 3949s

# Append ample digital silence, then take exactly 240,000 samples (5 seconds).
sox "$work_dir/segment-001-aligned.wav" "$SEGMENT_001" pad 0 5 trim 0 240000s
sox "$work_dir/segment-002-aligned.wav" "$SEGMENT_002" pad 0 5 trim 0 240000s
sox "$work_dir/segment-003-aligned.wav" "$SEGMENT_003" pad 0 5 trim 0 240000s

for rendered_audio in "$SEGMENT_001" "$SEGMENT_002" "$SEGMENT_003"; do
  printf '%s  %s\n' "$(shasum -a 256 "$rendered_audio" | awk '{print $1}')" "$rendered_audio"
  soxi -D "$rendered_audio"
done
