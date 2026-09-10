#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/../.." && pwd)"
exec "$SCRIPT_DIRECTORY/download_huggingface_wget.sh" \
  "ByteDance/LatentSync-1.6" \
  "c42c7e6c8e9c213626389fa7d9a3c444b8536353" \
  "${LPW_LATENTSYNC_PRODUCTION_DIR:-$PROJECT_ROOT/models/latentsync-1.6}" \
  '(^config\.json$|^latentsync_unet\.pt$|^stable_syncnet\.pt$|^whisper/tiny\.pt$|^auxiliary/(i3d_torchscript\.pt|koniq_pretrained\.pkl|sfd_face\.pth|syncnet_v2\.model|vgg16-397923af\.pth|vit_g_hybrid_pt_1200e_ssv2_ft\.pth)$)'
