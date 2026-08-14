"""Synthesize JSON conversations using profile-locked Qwen Base clones."""

from __future__ import annotations

import gc
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

from conversion.profiles import resolve_locked_voice
from conversion.schema import ConversationSpec


DEFAULT_MODEL = Path("models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base")


def _seed_everything(seed: int, np: Any, torch: Any) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def generate_conversation(
    spec: ConversationSpec,
    *,
    workspace_root: Path,
    output_dir: Path,
    model_dir: Path | None = None,
) -> Path:
    """Generate immutable per-turn WAVs and one assembled conversation WAV."""

    # The application itself does not depend on this local ML stack. Import it
    # only when the conversion feature is actually invoked.
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    workspace_root = workspace_root.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    selected_model = (model_dir or workspace_root / DEFAULT_MODEL).expanduser().resolve()
    if not (selected_model / "model.safetensors").is_file():
        raise FileNotFoundError(
            f"Qwen Base model is missing: {selected_model}; "
            "run scripts/qwen3_tts/download_base.sh"
        )
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists and is immutable: {output_dir}")
    turns_dir = output_dir / "turns"
    turns_dir.mkdir(parents=True)

    speakers = sorted({turn.speaker for turn in spec.turns})
    references = {
        speaker: resolve_locked_voice(workspace_root, spec.project, speaker)
        for speaker in speakers
    }

    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    dtype = torch.float16 if use_mps else torch.float32
    print(
        f"Loading Base cloning model once on {device} for {len(spec.turns)} turns...",
        flush=True,
    )
    model = Qwen3TTSModel.from_pretrained(
        str(selected_model),
        device_map=device,
        dtype=dtype,
        attn_implementation="eager",
    )
    clone_prompts = {
        speaker: model.create_voice_clone_prompt(
            ref_audio=str(reference.audio_path),
            ref_text=reference.text,
            x_vector_only_mode=False,
        )
        for speaker, reference in references.items()
    }

    generated: list[dict[str, Any]] = []
    sample_rate: int | None = None
    for index, turn in enumerate(spec.turns, start=1):
        turn_seed = spec.seed + index * 101
        _seed_everything(turn_seed, np, torch)
        print(
            f"Generating turn {index}/{len(spec.turns)}: {turn.speaker}...",
            flush=True,
        )
        wavs, current_rate = model.generate_voice_clone(
            text=turn.text,
            language=spec.language,
            voice_clone_prompt=clone_prompts[turn.speaker],
            non_streaming_mode=True,
        )
        if sample_rate is None:
            sample_rate = current_rate
        elif current_rate != sample_rate:
            raise RuntimeError("generated turns use different sample rates")
        audio = np.asarray(wavs[0], dtype=np.float32).reshape(-1)
        turn_path = turns_dir / f"{index:03d}-{turn.speaker}.wav"
        sf.write(turn_path, audio, sample_rate)
        generated.append(
            {
                "index": index,
                "speaker": turn.speaker,
                "text": turn.text,
                "seed": turn_seed,
                "pause_after_seconds": turn.pause_after_seconds,
                "path": str(turn_path),
                "duration_seconds": len(audio) / sample_rate,
                "audio": audio,
            }
        )
        gc.collect()
        if use_mps:
            torch.mps.empty_cache()

    assert sample_rate is not None
    lead_seconds = 0.18
    trail_seconds = 0.25
    speech_seconds = sum(float(item["duration_seconds"]) for item in generated)
    unspecified_gaps = sum(
        item["pause_after_seconds"] is None for item in generated[:-1]
    )
    fixed_gap_seconds = sum(
        float(item["pause_after_seconds"] or 0.0) for item in generated[:-1]
    )
    remaining = spec.target_seconds - speech_seconds - lead_seconds - trail_seconds
    auto_gap_seconds = (
        min(max((remaining - fixed_gap_seconds) / unspecified_gaps, 0.12), 0.65)
        if unspecified_gaps
        else 0.0
    )

    pieces = [np.zeros(round(lead_seconds * sample_rate), dtype=np.float32)]
    for index, item in enumerate(generated):
        pieces.append(item["audio"])
        if index < len(generated) - 1:
            pause = item["pause_after_seconds"]
            pause_seconds = auto_gap_seconds if pause is None else float(pause)
            pieces.append(np.zeros(round(pause_seconds * sample_rate), dtype=np.float32))
    pieces.append(np.zeros(round(trail_seconds * sample_rate), dtype=np.float32))
    combined = np.concatenate(pieces)
    conversation_path = output_dir / "conversation.wav"
    sf.write(conversation_path, combined, sample_rate)

    transcript = [f"# {spec.title}", ""]
    transcript.extend(
        f"**{item['speaker'].title()}:** {item['text']}" for item in generated
    )
    (output_dir / "transcript.md").write_text("\n\n".join(transcript) + "\n")
    for item in generated:
        del item["audio"]
    manifest = {
        "spec": asdict(spec),
        "model": str(selected_model),
        "mode": "voice-clone-from-profile-neutral-reference",
        "references": {
            speaker: {
                "profile": str(reference.profile_path),
                "audio": str(reference.audio_path),
                "text": reference.text,
                "sha256": reference.sha256,
            }
            for speaker, reference in references.items()
        },
        "sample_rate": sample_rate,
        "target_seconds": spec.target_seconds,
        "speech_seconds": speech_seconds,
        "automatic_gap_seconds": auto_gap_seconds,
        "duration_seconds": len(combined) / sample_rate,
        "conversation": str(conversation_path),
        "turns": generated,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return conversation_path
