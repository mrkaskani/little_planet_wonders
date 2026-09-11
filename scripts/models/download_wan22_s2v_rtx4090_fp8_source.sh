#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The non-Comfy DiffSynth production path reads the official Wan shards from
# disk and prepares the DiT in true E4M3 FP8 at runtime. Downloads are delegated
# to the hardware-neutral, resumable, checksum-aware model entry point.
exec "${SCRIPT_DIRECTORY}/download_wan22_s2v.sh"
