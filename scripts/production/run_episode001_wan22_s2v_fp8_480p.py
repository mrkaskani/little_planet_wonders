#!/usr/bin/env python3
"""Render a manifest-defined episode with DiffSynth Wan 2.2 S2V FP8."""

from __future__ import annotations

import argparse
import gc
import json
import shutil
import subprocess
from pathlib import Path

import librosa
import torch
import yaml
from PIL import Image
from safetensors.torch import save_file

from diffsynth.pipelines.wan_video import ModelConfig, WanVideoPipeline, WanVideoUnit_S2V
from diffsynth.utils.data import save_video


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = PROJECT_ROOT / (
    "src/lpw/context/projects/riri-yoyo/generation-records/video-jobs/"
    "episode-001--moonlit-garden-greeting--wan22-s2v-fp8-480p--v002.yaml"
)
DEFAULT_MODEL_DIR = PROJECT_ROOT / "runtime/models/Wan2.2-S2V-14B"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / (
    "runtime/video/riri-yoyo/episodes/episode-001/s2v/fp8-480p-v002"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--vram-reserve-gib", type=float, default=2.5)
    parser.add_argument("--expected-gpu", default="RTX 4090")
    return parser.parse_args()


def require_file(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    return path


def require_model_files(model_dir: Path) -> dict[str, object]:
    model_dir = model_dir.expanduser().resolve()
    dit = sorted(model_dir.glob("diffusion_pytorch_model*.safetensors"))
    if not dit:
        raise FileNotFoundError(f"Wan DiT shards are missing from {model_dir}")
    return {
        "dit": [str(path) for path in dit],
        "t5": str(require_file(model_dir / "models_t5_umt5-xxl-enc-bf16.pth", "UMT5")),
        "audio": str(
            require_file(
                model_dir / "wav2vec2-large-xlsr-53-english/model.safetensors",
                "Wav2Vec2 audio encoder",
            )
        ),
        "vae": str(require_file(model_dir / "Wan2.1_VAE.pth", "Wan VAE")),
        "tokenizer": str((model_dir / "google/umt5-xxl").resolve()),
        "audio_processor": str((model_dir / "wav2vec2-large-xlsr-53-english").resolve()),
    }


def resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def run_command(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def save_motion_checkpoint(
    output_dir: Path,
    motion_video: torch.Tensor,
    window_index: int,
    frame_count: int,
) -> None:
    checkpoint = output_dir / "checkpoints" / f"motion-window-{window_index:02d}.safetensors"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    temporary = checkpoint.with_suffix(".partial.safetensors")
    save_file({"motion_video": motion_video.detach().cpu().contiguous()}, str(temporary))
    temporary.replace(checkpoint)
    metadata = {
        "completed_window": window_index,
        "saved_encoded_frames": frame_count,
        "motion_frames": int(motion_video.shape[2]),
        "checkpoint": str(checkpoint),
    }
    metadata_path = checkpoint.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def keep_s2v_audio_encoder_in_bfloat16(pipe: WanVideoPipeline) -> None:
    """Keep convolutional S2V audio conditioning off the FP8 linear path."""
    managed_encoder = pipe.dit.casual_audio_encoder
    raw_encoder = getattr(managed_encoder, "module", None)
    if raw_encoder is None or type(raw_encoder).__name__ != "CausalAudioEncoder":
        raise RuntimeError(
            "the pinned DiffSynth CausalAudioEncoder is not managed as expected"
        )

    # DiffSynth wraps both the parent encoder parameters and its nested Conv1d
    # layers independently. Conv1d does not use DiffSynth's scaled FP8 linear
    # implementation, so every convolution wrapper must be overridden.
    managed_modules = [managed_encoder]
    managed_convolutions = []
    for candidate in raw_encoder.modules():
        wrapped_module = getattr(candidate, "module", None)
        if isinstance(wrapped_module, torch.nn.Conv1d):
            managed_modules.append(candidate)
            managed_convolutions.append(candidate)
    if not managed_convolutions:
        raise RuntimeError("no managed Conv1d layers found in CausalAudioEncoder")

    for managed_module in managed_modules:
        managed_module.offload()
        managed_module.preparing_dtype = torch.bfloat16
        managed_module.computation_dtype = torch.bfloat16


def main() -> None:
    args = parse_args()
    manifest_path = require_file(args.manifest, "episode manifest")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")
    gpu_name = torch.cuda.get_device_name(0)
    if args.expected_gpu.lower() not in gpu_name.lower():
        raise RuntimeError(f"expected {args.expected_gpu}, detected {gpu_name}")
    if torch.cuda.get_device_capability(0) < (8, 9):
        raise RuntimeError("the selected true-FP8 path requires Ada capability 8.9+")
    if not hasattr(torch, "_scaled_mm"):
        raise RuntimeError("this PyTorch build lacks torch._scaled_mm")

    width = int(manifest["video"]["width"])
    height = int(manifest["video"]["height"])
    fps = int(manifest["video"]["fps"])
    infer_frames = int(manifest["video"]["infer_frames_per_window"])
    final_frames = int(manifest["execution_contract"]["final_encoded_frame_count"])
    steps = int(manifest["sampling"]["steps"])
    cfg = float(manifest["sampling"]["guide_scale"])
    shift = float(manifest["sampling"]["shift"])
    base_seed = int(manifest["sampling"]["base_seed"])
    solver = str(manifest["sampling"]["solver"]).lower()
    final_duration = float(manifest["execution_contract"]["final_duration_seconds"])
    expected_windows = len(manifest["execution_contract"]["internal_windows"])
    approved_profile = (width, height, fps, infer_frames, steps, solver, cfg, shift)
    if approved_profile != (832, 480, 16, 80, 20, "unipc", 5.0, 3.0):
        raise RuntimeError(
            "manifest no longer matches the approved RTX 4090 FP8 quality profile"
        )
    if final_frames != round(final_duration * fps):
        raise RuntimeError(
            f"final frame contract is inconsistent: {final_frames} frames for "
            f"{final_duration:g} seconds at {fps} fps"
        )
    if expected_windows < 1:
        raise RuntimeError("manifest must define at least one internal S2V window")

    image_path = require_file(
        resolve_project_path(manifest["inputs"]["reference_image"]["path"]),
        "reference image",
    )
    audio_path = require_file(
        resolve_project_path(manifest["inputs"]["conditioning_audio"]["path"]),
        "S2V conditioning audio",
    )
    final_audio_path = require_file(
        resolve_project_path(manifest["assembly"]["final_audio_authority"]),
        "approved final audio mix",
    )
    model_files = require_model_files(args.model_dir)

    output_dir = args.output_dir.expanduser().resolve()
    frame_dir = output_dir / "frames"
    window_dir = output_dir / "windows"
    frame_dir.mkdir(parents=True, exist_ok=True)
    window_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frame_dir.glob("frame-*.png"):
        old_frame.unlink()

    source_image = Image.open(image_path).convert("RGB")
    if source_image.size != (width, height):
        raise RuntimeError(
            f"reference must already be {width}x{height}; got {source_image.size}"
        )
    input_audio, audio_sample_rate = librosa.load(audio_path, sr=16000, mono=True)

    # DiffSynth's managed DiT linear layers use torch._scaled_mm when computation
    # dtype is float8. The text, audio, and VAE components remain BF16 and are
    # also disk-offloaded. Do not set clear_parameters=True here: disk-backed
    # wrappers need the registered parameter slots so they can materialize each
    # layer with load_state_dict(assign=True) when it is prepared.
    fp8_disk_config = {
        "offload_dtype": "disk",
        "offload_device": "disk",
        "onload_dtype": "disk",
        "onload_device": "disk",
        "preparing_dtype": torch.float8_e4m3fn,
        "preparing_device": "cuda",
        "computation_dtype": torch.float8_e4m3fn,
        "computation_device": "cuda",
    }
    bf16_disk_config = {
        "offload_dtype": "disk",
        "offload_device": "disk",
        "onload_dtype": "disk",
        "onload_device": "disk",
        "preparing_dtype": torch.bfloat16,
        "preparing_device": "cuda",
        "computation_dtype": torch.bfloat16,
        "computation_device": "cuda",
    }
    total_vram_gib = torch.cuda.get_device_properties(0).total_memory / 1024**3
    vram_limit = total_vram_gib - args.vram_reserve_gib
    if vram_limit < 19:
        raise RuntimeError(f"insufficient usable VRAM after reserve: {vram_limit:.1f} GiB")

    pipe = WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device="cuda",
        model_configs=[
            ModelConfig(path=model_files["dit"], **fp8_disk_config),
            ModelConfig(path=model_files["t5"], **bf16_disk_config),
            ModelConfig(path=model_files["audio"], **bf16_disk_config),
            ModelConfig(path=model_files["vae"], **bf16_disk_config),
        ],
        tokenizer_config=ModelConfig(path=model_files["tokenizer"], skip_download=True),
        audio_processor_config=ModelConfig(
            path=model_files["audio_processor"], skip_download=True
        ),
        vram_limit=vram_limit,
    )
    keep_s2v_audio_encoder_in_bfloat16(pipe)

    with torch.no_grad():
        audio_embeds, _, repeat_count = WanVideoUnit_S2V.pre_calculate_audio_pose(
            pipe=pipe,
            input_audio=input_audio,
            audio_sample_rate=audio_sample_rate,
            s2v_pose_video=None,
            num_frames=infer_frames + 1,
            height=height,
            width=width,
            fps=fps,
        )
    if repeat_count != expected_windows:
        raise RuntimeError(
            f"manifest defines {expected_windows} S2V windows, but the audio encoder "
            f"produced {repeat_count}"
        )

    prompt = manifest["positive_prompt"]
    window_prompts = manifest.get("window_prompts")
    if window_prompts is not None and len(window_prompts) != expected_windows:
        raise RuntimeError(
            f"manifest defines {len(window_prompts)} window prompts for "
            f"{expected_windows} S2V windows"
        )
    if window_prompts is not None:
        prompt_window_ids = [item["window_id"] for item in window_prompts]
        contract_window_ids = [
            item["window_id"]
            for item in manifest["execution_contract"]["internal_windows"]
        ]
        if prompt_window_ids != contract_window_ids:
            raise RuntimeError("window prompts do not match the execution window order")
    negative_prompt = manifest["negative_prompt"]
    motion_frames = int(manifest["memory"]["retained_motion_frames"])
    motion_video = None
    encoded_frame_count = 0

    for zero_based_window in range(repeat_count):
        window_number = zero_based_window + 1
        print(f"Generating window {window_number}/{repeat_count}", flush=True)
        current_prompt = prompt
        if window_prompts is not None:
            current_prompt = (
                f'{prompt}\n\n{window_prompts[zero_based_window]["positive_prompt"]}'
            )
        current_clip_tensor = pipe(
            prompt=current_prompt,
            input_image=source_image,
            negative_prompt=negative_prompt,
            seed=base_seed + zero_based_window,
            num_frames=infer_frames + 1,
            height=height,
            width=width,
            audio_embeds=audio_embeds[zero_based_window],
            s2v_pose_latents=None,
            motion_video=motion_video,
            num_inference_steps=steps,
            cfg_scale=cfg,
            sigma_shift=shift,
            tiled=True,
            tile_size=(30, 52),
            tile_stride=(15, 26),
            output_type="floatpoint",
        )
        current_clip_tensor = current_clip_tensor[:, :, -infer_frames:, :, :]
        if zero_based_window == 0:
            current_clip_tensor = current_clip_tensor[:, :, 3:, :, :]

        if motion_video is None:
            motion_video = current_clip_tensor[:, :, -motion_frames:, :, :].clone()
        else:
            overlap = min(motion_frames, current_clip_tensor.shape[2])
            motion_video = torch.cat(
                (
                    motion_video[:, :, overlap:, :, :],
                    current_clip_tensor[:, :, -overlap:, :, :],
                ),
                dim=2,
            )
        if motion_video.shape[2] != motion_frames:
            raise RuntimeError(f"motion context is {motion_video.shape[2]}, expected {motion_frames}")

        decoded_frames = pipe.vae_output_to_video(current_clip_tensor)
        save_video(
            decoded_frames,
            str(window_dir / f"window-{window_number:02d}.mp4"),
            fps=fps,
            quality=9,
        )
        for frame in decoded_frames:
            if encoded_frame_count >= final_frames:
                break
            frame.save(frame_dir / f"frame-{encoded_frame_count:06d}.png")
            encoded_frame_count += 1
        save_motion_checkpoint(output_dir, motion_video, window_number, encoded_frame_count)

        del current_clip_tensor, decoded_frames
        gc.collect()
        torch.cuda.empty_cache()

    if encoded_frame_count != final_frames:
        raise RuntimeError(f"saved {encoded_frame_count} final frames; expected {final_frames}")

    output_stem = manifest["assembly"].get(
        "output_stem", f'{manifest["scene"]["episode_id"]}--fp8-480p'
    )
    silent_video = output_dir / f"{output_stem}--silent.mp4"
    conditioning_video = output_dir / f"{output_stem}--conditioning-audio.mp4"
    final_mix_video = output_dir / f"{output_stem}--final-mix.mp4"
    run_command(
        [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(frame_dir / "frame-%06d.png"),
            "-frames:v", str(final_frames), "-c:v", "libx264", "-preset", "slow",
            "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(silent_video),
        ]
    )
    for selected_audio, destination in (
        (audio_path, conditioning_video),
        (final_audio_path, final_mix_video),
    ):
        run_command(
            [
                "ffmpeg", "-y", "-i", str(silent_video), "-i", str(selected_audio),
                "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                str(destination),
            ]
        )

    probe_path = output_dir / "ffprobe-final.json"
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-count_frames", "-show_streams",
            "-show_format", "-of", "json", str(final_mix_video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    probe_path.write_text(probe.stdout, encoding="utf-8")
    print(f"Production candidate: {final_mix_video}")
    print(f"Probe report: {probe_path}")


if __name__ == "__main__":
    main()
