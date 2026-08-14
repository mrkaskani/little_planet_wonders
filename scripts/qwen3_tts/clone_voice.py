#!/usr/bin/env python3
"""Clone a reference voice with the local Qwen3-TTS Base checkpoint."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models" / "qwen3-tts" / "Qwen3-TTS-12Hz-1.7B-Base"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--ref-audio", type=Path, required=True, help="Reference audio file.")
    parser.add_argument("--ref-text", required=True, help="Exact reference transcript.")
    parser.add_argument("--language", default="Auto", help="Language or Auto.")
    parser.add_argument("--seed", type=int, default=0, help="Sampling seed.")
    parser.add_argument("--output", type=Path, required=True, help="Output WAV path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (MODEL_DIR / "model.safetensors").is_file():
        raise SystemExit("Model weights are missing; run scripts/qwen3_tts/download_base.sh")
    ref_audio = args.ref_audio.expanduser().resolve()
    if not ref_audio.is_file():
        raise SystemExit(f"Reference audio not found: {ref_audio}")

    random.seed(args.seed)
    np.random.seed(args.seed % (2**32))
    torch.manual_seed(args.seed)

    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    dtype = torch.float16 if use_mps else torch.float32
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL_DIR),
        device_map=device,
        dtype=dtype,
        attn_implementation="eager",
    )
    wavs, sample_rate = model.generate_voice_clone(
        text=args.text,
        language=args.language,
        ref_audio=str(ref_audio),
        ref_text=args.ref_text,
    )
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, wavs[0], sample_rate)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
