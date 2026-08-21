#!/usr/bin/env bash
set -euo pipefail

echo "Create a read-only token locally at: https://huggingface.co/settings/tokens"
echo "Do not paste the token into chat or save it in these scripts."

if [[ -x "/Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx/.venv/bin/hf" ]]; then
  exec /Users/oldowl/AI-Audio/stable-audio-3/optimized/mlx/.venv/bin/hf auth login
elif command -v hf >/dev/null 2>&1; then
  exec hf auth login
else
  echo "The Hugging Face CLI is not installed yet; install either runtime first." >&2
  exit 1
fi
