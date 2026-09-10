#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
job_dir="${1:-${project_root}/runtime/video/riri-yoyo/episodes/episode-002/jobs}"
output="${2:-${project_root}/runtime/video/riri-yoyo/episodes/episode-002/sharing-shapes-episode-002-832x480.mp4}"
song="${project_root}/src/lpw/context/projects/riri-yoyo/assets/music/songs/sharing-shapes/candidates/sharing-shapes-v007-seed-950053.wav"

jobs=(s01-a s01-b s01-c s02-a s02-b s03-a s03-b s04-a s05-a s06-a)
for job in "${jobs[@]}"; do
  clip="${job_dir}/${job}.mp4"
  if [[ ! -f "${clip}" ]]; then
    echo "Missing rendered job: ${clip}" >&2
    exit 2
  fi
done
if [[ ! -f "${song}" ]]; then
  echo "Missing final song authority: ${song}" >&2
  exit 2
fi

mkdir -p "$(dirname "${output}")"
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/lpw-episode002-concat.XXXXXX")"
trap 'rm -rf "${work_dir}"' EXIT
list_file="${work_dir}/clips.txt"
for job in "${jobs[@]}"; do
  printf "file '%s'\n" "${job_dir}/${job}.mp4" >> "${list_file}"
done

# Re-encode once so every independently generated Wan job has identical stream
# parameters. Ignore embedded job audio; the approved 34-second song is muxed as
# the single timeline authority after concatenation.
ffmpeg -hide_banner -y \
  -f concat -safe 0 -i "${list_file}" \
  -i "${song}" \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=832:480:force_original_aspect_ratio=increase,crop=832:480,fps=16,format=yuv420p" \
  -t 34.0 \
  -c:v libx264 -preset slow -crf 16 \
  -c:a aac -b:a 256k \
  -movflags +faststart \
  "${output}"

ffprobe -v error \
  -show_entries format=duration:stream=codec_name,width,height,r_frame_rate \
  -of json "${output}"
echo "Created ${output}"
