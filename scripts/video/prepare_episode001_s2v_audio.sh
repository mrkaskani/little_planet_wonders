#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_ROOT="${1:-$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/s2v-conditioning/v001}"

RIRI_001="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-001-riri/v001/episode-001_moonlit-garden-greeting_shot-001_riri_final.wav"
YOYO_002="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-002-yoyo/v001/episode-001_moonlit-garden-greeting_shot-002_yoyo_final.wav"
RIRI_003="$PROJECT_ROOT/runtime/audio/riri-yoyo/episodes/episode-001/dialogue/moonlit-garden-greeting/shot-003-riri/v001/episode-001_moonlit-garden-greeting_shot-003_riri_final.wav"

MASTER="$OUTPUT_ROOT/episode-001--moonlit-garden-greeting--clean-conversation--000s-012s--v001.wav"
SEGMENT_001="$OUTPUT_ROOT/episode-001--segment-001--clean-speech--000s-005s--v001.wav"
SEGMENT_002="$OUTPUT_ROOT/episode-001--segment-002--clean-speech--005s-010s--v001.wav"
SEGMENT_003="$OUTPUT_ROOT/episode-001--segment-003--clean-speech--010s-012s-padded-to-015s--v001.wav"

if ! command -v sox >/dev/null 2>&1; then
  echo "SoX is required. On macOS, install it with: brew install sox" >&2
  exit 2
fi

for source_audio in "$RIRI_001" "$YOYO_002" "$RIRI_003"; do
  if [[ ! -f "$source_audio" ]]; then
    echo "Missing locked dialogue source: $source_audio" >&2
    exit 1
  fi
done

mkdir -p "$OUTPUT_ROOT"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/lpw-s2v-audio.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

# Preserve the approved editorial timing exactly. The padding values make each
# temporary stem exactly 12 seconds before the three stems are mixed together.
sox "$RIRI_001" -r 48000 -c 1 -b 24 "$work_dir/riri-001-padded.wav" pad 0.8 7.92
sox "$YOYO_002" -r 48000 -c 1 -b 24 "$work_dir/yoyo-002-padded.wav" pad 4.75 5.41
sox "$RIRI_003" -r 48000 -c 1 -b 24 "$work_dir/riri-003-padded.wav" pad 7.1 1.22
sox -m \
  "$work_dir/riri-001-padded.wav" \
  "$work_dir/yoyo-002-padded.wav" \
  "$work_dir/riri-003-padded.wav" \
  -r 48000 -c 1 -b 24 "$MASTER"

# These are sample-exact timeline slices. Do not add fades at 5s or 10s: the
# pieces must reconstruct the approved conversation without rearranging speech.
sox "$MASTER" -r 48000 -c 1 -b 24 "$SEGMENT_001" trim 0 5
sox "$MASTER" -r 48000 -c 1 -b 24 "$SEGMENT_002" trim 5 5
sox "$MASTER" -r 48000 -c 1 -b 24 "$SEGMENT_003" trim 10 2 pad 0 3

for rendered_audio in "$MASTER" "$SEGMENT_001" "$SEGMENT_002" "$SEGMENT_003"; do
  printf '%s  %s\n' "$(shasum -a 256 "$rendered_audio" | awk '{print $1}')" "$rendered_audio"
  soxi -D "$rendered_audio"
done
