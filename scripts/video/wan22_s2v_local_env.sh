#!/usr/bin/env bash

# Source this file to bind the verified local Wan 2.2 S2V Q4_K_S package to the
# LPW worker. It intentionally does not select a backend implementation.
if [[ -n "${ZSH_VERSION:-}" ]]; then
  LPW_ENV_SOURCE="${(%):-%N}"
else
  LPW_ENV_SOURCE="${BASH_SOURCE[0]}"
fi
LPW_ENV_DIR="$(cd "$(dirname "$LPW_ENV_SOURCE")" && pwd)"
LPW_PROJECT_ROOT="$(cd "$LPW_ENV_DIR/../.." && pwd)"
MODEL_ROOT="${LPW_WAN_S2V_MODEL_DIR:-$LPW_PROJECT_ROOT/models/wan22-s2v-local-q4ks}"

export LPW_WAN_S2V_GGUF="$MODEL_ROOT/diffusion_models/Wan2.2-S2V-14B-Q4_K_S.gguf"
export LPW_WAN_S2V_VAE="$MODEL_ROOT/vae/wan_2.1_vae.safetensors"
export LPW_WAN_S2V_TEXT_ENCODER="$MODEL_ROOT/text_encoders/umt5-xxl-encoder-Q4_K_S.gguf"
export LPW_WAN_S2V_TOKENIZER="$MODEL_ROOT/text_encoders/umt5-tokenizer"
export LPW_WAN_S2V_AUDIO_ENCODER="$MODEL_ROOT/audio_encoders/wav2vec2_large_english_fp16.safetensors"
export LPW_WAN_S2V_BACKEND_MODULE="${LPW_WAN_S2V_BACKEND_MODULE:-lpw.generation.wan_s2v_backend}"
export LPW_FFMPEG="${LPW_FFMPEG:-/opt/homebrew/bin/ffmpeg}"
