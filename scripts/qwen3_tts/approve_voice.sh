#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--force] {yoyo|riri} [REFERENCE] CANDIDATE.wav" >&2
  echo "REFERENCE defaults to neutral-friendly." >&2
  exit 2
}

force=0
if [[ "${1:-}" == "--force" ]]; then
  force=1
  shift
fi
[[ $# -eq 2 || $# -eq 3 ]] || usage

character="$1"
if [[ $# -eq 2 ]]; then
  reference="neutral-friendly"
  candidate_arg="$2"
else
  reference="$2"
  candidate_arg="$3"
fi
candidate="$(cd "$(dirname "${candidate_arg}")" 2>/dev/null && pwd)/$(basename "${candidate_arg}")"
case "${character}" in
  yoyo|riri) ;;
  *) usage ;;
esac
case "${reference}" in
  neutral-friendly|happy-gentle|curious|mild-concern|reassuring) ;;
  *) usage ;;
esac

[[ -f "${candidate}" ]] || { echo "Candidate not found: ${candidate}" >&2; exit 1; }
[[ "${candidate##*.}" == "wav" ]] || { echo "Candidate must be a WAV file." >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
target="${PROJECT_ROOT}/src/lpw/context/projects/classroom/audio-assets/voice-references/${character}/${reference}.wav"
mkdir -p "$(dirname "${target}")"

if [[ -e "${target}" && ${force} -ne 1 ]]; then
  echo "Approved reference already exists: ${target}" >&2
  echo "Use --force only after listening and explicitly approving the replacement." >&2
  exit 1
fi

cp "${candidate}" "${target}"
echo "Approved ${character}/${reference} voice reference: ${target}"
echo "Future dialogue should use the Base-model clone script, not VoiceDesign."
