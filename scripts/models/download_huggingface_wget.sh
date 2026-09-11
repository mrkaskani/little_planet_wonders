#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 4 ]]; then
  echo "Usage: $0 REPOSITORY REVISION OUTPUT_DIRECTORY INCLUDE_REGEX" >&2
  exit 2
fi

REPOSITORY="$1"
REVISION="$2"
OUTPUT_DIRECTORY="$3"
INCLUDE_REGEX="$4"
PYTHON_BIN="${LPW_PYTHON:-python3}"
WGET_BIN="${LPW_WGET:-wget}"

if ! command -v "$WGET_BIN" >/dev/null 2>&1; then
  echo "wget is required. Install GNU wget before downloading model weights." >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python is required to validate Hugging Face repository metadata." >&2
  exit 2
fi

mkdir -p "$OUTPUT_DIRECTORY"
METADATA_FILE="$OUTPUT_DIRECTORY/.repository-metadata-${REVISION}.json"
MANIFEST_FILE="$OUTPUT_DIRECTORY/.wget-manifest-${REVISION}.tsv"
API_URL="https://huggingface.co/api/models/${REPOSITORY}/revision/${REVISION}?blobs=true"
run_wget() {
  if [[ -n "${HF_TOKEN:-}" ]]; then
    "$WGET_BIN" --header="Authorization: Bearer ${HF_TOKEN}" "$@"
  else
    "$WGET_BIN" "$@"
  fi
}

file_size() {
  "$PYTHON_BIN" -c 'import os, sys; print(os.path.getsize(sys.argv[1]))' "$1"
}

run_wget -q --https-only --tries=5 --timeout=30 \
  -O "${METADATA_FILE}.part" "$API_URL"
mv "${METADATA_FILE}.part" "$METADATA_FILE"

"$PYTHON_BIN" - "$METADATA_FILE" "$REVISION" "$INCLUDE_REGEX" > "${MANIFEST_FILE}.part" <<'PY'
import json
import pathlib
import re
import sys

metadata_path, revision, include_pattern = sys.argv[1:]
metadata = json.loads(pathlib.Path(metadata_path).read_text(encoding="utf-8"))
if metadata.get("sha") != revision:
    raise SystemExit(
        f"Pinned revision mismatch: requested {revision}, API returned {metadata.get('sha')}"
    )
pattern = re.compile(include_pattern)
selected = 0
for sibling in metadata.get("siblings", []):
    relative = sibling["rfilename"]
    path = pathlib.PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not pattern.search(relative):
        continue
    size = (sibling.get("lfs") or {}).get("size", sibling.get("size"))
    if not isinstance(size, int) or size < 0:
        raise SystemExit(f"No trustworthy size metadata for {relative}")
    print(f"{size}\t{relative}")
    selected += 1
if selected == 0:
    raise SystemExit("Include expression selected no repository files")
PY
mv "${MANIFEST_FILE}.part" "$MANIFEST_FILE"

read -r REQUIRED_BYTES FILE_COUNT < <(
  "$PYTHON_BIN" - "$MANIFEST_FILE" "$OUTPUT_DIRECTORY" <<'PY'
import pathlib
import sys

manifest = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
required = 0
count = 0
for line in manifest.read_text(encoding="utf-8").splitlines():
    size_text, relative = line.split("\t", 1)
    size = int(size_text)
    destination = root / relative
    partial = destination.with_name(destination.name + ".part")
    present = destination.stat().st_size if destination.is_file() else 0
    partial_present = partial.stat().st_size if partial.is_file() else 0
    required += max(0, size - max(present, partial_present))
    count += 1
print(required, count)
PY
)

AVAILABLE_BYTES="$(df -Pk "$OUTPUT_DIRECTORY" | awk 'NR==2 {print $4 * 1024}')"
SAFETY_BYTES=$((5 * 1024 * 1024 * 1024))
if (( AVAILABLE_BYTES < REQUIRED_BYTES + SAFETY_BYTES )); then
  "$PYTHON_BIN" - "$REPOSITORY" "$REQUIRED_BYTES" "$AVAILABLE_BYTES" <<'PY'
import sys

repository, required, available = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
gib = 1024 ** 3
print(
    f"BLOCKED: {repository} needs {required / gib:.2f} GiB remaining plus a 5 GiB "
    f"safety margin; only {available / gib:.2f} GiB is available.",
    file=sys.stderr,
)
PY
  exit 3
fi

echo "Downloading $FILE_COUNT pinned file(s) for $REPOSITORY@$REVISION"
while IFS=$'\t' read -r EXPECTED_SIZE RELATIVE_PATH; do
  DESTINATION="$OUTPUT_DIRECTORY/$RELATIVE_PATH"
  PARTIAL="${DESTINATION}.part"
  mkdir -p "$(dirname "$DESTINATION")"
  if [[ -f "$DESTINATION" ]] && [[ "$(file_size "$DESTINATION")" == "$EXPECTED_SIZE" ]]; then
    echo "READY  $RELATIVE_PATH"
    continue
  fi
  URL="https://huggingface.co/${REPOSITORY}/resolve/${REVISION}/${RELATIVE_PATH}?download=true"
  echo "FETCH  $RELATIVE_PATH"
  run_wget --continue --https-only --tries=20 --timeout=60 \
    --retry-connrefused --waitretry=5 --progress=bar:force:noscroll \
    -O "$PARTIAL" "$URL"
  ACTUAL_SIZE="$(file_size "$PARTIAL")"
  if [[ "$ACTUAL_SIZE" != "$EXPECTED_SIZE" ]]; then
    echo "BAD-SIZE $RELATIVE_PATH expected=$EXPECTED_SIZE actual=$ACTUAL_SIZE" >&2
    exit 4
  fi
  mv "$PARTIAL" "$DESTINATION"
done < "$MANIFEST_FILE"

echo "READY: $REPOSITORY@$REVISION in $OUTPUT_DIRECTORY"
