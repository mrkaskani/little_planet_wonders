#!/usr/bin/env python3
"""Route local audio jobs to the official ACE-Step and Stable Audio 3 tools."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


ROOT = Path("/Users/oldowl/AI-Audio")
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
ACE_DIR = ROOT / "ace-step"
SA3_DIR = ROOT / "stable-audio-3" / "optimized" / "mlx"
SA3 = SA3_DIR / "sa3"

SA3_WEIGHTS = {
    "soundtrack": (
        "models/mlx/dit_medium_f16.npz",
        "models/mlx/same_l_decoder_f32.npz",
        "models/mlx/same_l_encoder_f32.npz",
        "models/mlx/t5gemma_f16.npz",
    ),
    "sfx": (
        "models/mlx/dit_medium_f16.npz",
        "models/mlx/same_l_decoder_f32.npz",
        "models/mlx/same_l_encoder_f32.npz",
        "models/mlx/t5gemma_f16.npz",
    ),
}


def fail(message: str) -> "None":
    raise SystemExit(f"error: {message}")


def default_output(kind: str, suffix: str) -> Path:
    folders = {
        "song": "children-songs",
        "soundtrack": "soundtracks",
        "sfx": "sfx",
    }
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return ROOT / "generated" / folders[kind] / f"{kind}-{stamp}.{suffix}"


def resolve_output(kind: str, requested: str | None, suffix: str) -> Path:
    output = Path(requested).expanduser() if requested else default_output(kind, suffix)
    if not output.is_absolute():
        output = ROOT / "generated" / {
            "song": "children-songs",
            "soundtrack": "soundtracks",
            "sfx": "sfx",
        }[kind] / output
    output.parent.mkdir(parents=True, exist_ok=True)
    return output.resolve()


def check_sa3(kind: str) -> None:
    python = SA3_DIR / ".venv" / "bin" / "python"
    if not python.is_file():
        fail(
            "Stable Audio runtime is missing. Run "
            f"{SCRIPTS_DIR}/stable-audio-3/install-runtime.sh"
        )
    if not SA3.is_file():
        fail(f"official Stable Audio launcher not found: {SA3}")
    missing = [relative for relative in SA3_WEIGHTS[kind] if not (SA3_DIR / relative).exists()]
    if missing:
        downloader = (
            f"{SCRIPTS_DIR}/stable-audio-3-medium/download-model.sh"
            if kind == "soundtrack"
            else f"{SCRIPTS_DIR}/stable-audio-3-medium/download-model.sh"
        )
        fail(
            "required local weights are missing; no download was started.\n"
            + "Missing:\n  "
            + "\n  ".join(missing)
            + f"\nDownload later with: {downloader}"
        )


def run_sa3(args: argparse.Namespace) -> None:
    check_sa3(args.command)
    output = resolve_output(args.command, args.output, "wav")
    if output.exists() and not args.overwrite:
        fail(f"output already exists (use --overwrite): {output}")

    dit, decoder = "medium", "same-l"

    command = [
        str(SA3),
        "--prompt", args.prompt,
        "--dit", dit,
        "--decoder", decoder,
        "--seconds", str(args.seconds),
        "--steps", str(args.steps),
        "--cfg", str(args.cfg),
        "--out", str(output),
    ]
    if args.seed is not None:
        command += ["--seed", str(args.seed)]
    if args.negative_prompt:
        command += ["--negative-prompt", args.negative_prompt]
    if args.init_audio:
        init_audio = Path(args.init_audio).expanduser().resolve()
        if not init_audio.is_file():
            fail(f"init audio does not exist: {init_audio}")
        command += [
            "--init-audio", str(init_audio),
            "--init-noise-level", str(args.init_noise_level),
        ]
    if args.inpaint_range:
        if not args.init_audio:
            fail("--inpaint-range requires --init-audio")
        command += ["--inpaint-range", args.inpaint_range]
    if args.play:
        command.append("--play")

    print(f"Routing {args.command} to Stable Audio 3 ({dit} + {decoder}).")
    subprocess.run(command, cwd=SA3_DIR, check=True)
    print(f"Output: {output}")


def api_request(
    url: str,
    payload: dict | None = None,
    api_key: str | None = None,
    timeout: float = 30,
) -> bytes:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"ACE-Step API returned HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(
            f"ACE-Step API is not reachable at {url}: {exc.reason}\n"
            "Start it in another terminal with: "
            f"{SCRIPTS_DIR}/orchestrator/start-song-server.sh"
        )


def api_multipart_request(
    url: str,
    fields: dict[str, object],
    file_field: str,
    file_path: Path,
    api_key: str | None = None,
    timeout: float = 60,
) -> bytes:
    """Upload source audio because ACE-Step rejects absolute JSON paths."""
    boundary = f"lpw-{uuid.uuid4().hex}"
    body = bytearray()

    def append_line(value: str = "") -> None:
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    for name, value in fields.items():
        append_line(f"--{boundary}")
        append_line(f'Content-Disposition: form-data; name="{name}"')
        append_line()
        if isinstance(value, bool):
            append_line("true" if value else "false")
        else:
            append_line(str(value))

    append_line(f"--{boundary}")
    append_line(
        f'Content-Disposition: form-data; name="{file_field}"; '
        f'filename="{file_path.name}"'
    )
    append_line("Content-Type: audio/wav")
    append_line()
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    append_line(f"--{boundary}--")

    headers = {
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=bytes(body), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"ACE-Step API returned HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(
            f"ACE-Step API is not reachable at {url}: {exc.reason}\n"
            "Start it in another terminal with: "
            f"{SCRIPTS_DIR}/orchestrator/start-song-server.sh"
        )


def unwrap(payload: bytes) -> object:
    try:
        response = json.loads(payload)
    except json.JSONDecodeError as exc:
        fail(f"ACE-Step returned invalid JSON: {exc}")
    if not isinstance(response, dict) or response.get("code") != 200:
        fail(f"ACE-Step request failed: {response}")
    return response.get("data")


def run_song(args: argparse.Namespace) -> None:
    base_url = args.server_url.rstrip("/")
    unwrap(api_request(f"{base_url}/health", api_key=args.api_key))

    payload: dict[str, object] = {
        "thinking": args.thinking,
        "model": "acestep-v15-turbo",
        "audio_duration": args.seconds,
        "audio_format": args.format,
        "inference_steps": args.steps,
        "batch_size": 1,
    }
    if args.bpm is not None:
        payload["bpm"] = args.bpm
    if args.time_signature:
        payload["time_signature"] = args.time_signature
    if args.key_scale:
        payload["key_scale"] = args.key_scale
    if args.vocal_language:
        payload["vocal_language"] = args.vocal_language
    if args.thinking:
        payload.update(
            {
                "lm_model_path": "acestep-5Hz-lm-1.7B",
                "lm_backend": "mlx",
            }
        )
    if args.lyrics:
        payload.update({"prompt": args.prompt, "lyrics": args.lyrics})
    else:
        payload["sample_query"] = args.prompt
    if args.seed is not None:
        payload.update({"use_random_seed": False, "seed": args.seed})
    source_audio: Path | None = None
    reference_audio: Path | None = None
    if args.source_audio:
        source_audio = Path(args.source_audio).expanduser().resolve()
        if not source_audio.is_file():
            fail(f"ACE-Step source audio does not exist: {source_audio}")
        payload.update(
            {
                "task_type": args.task_type,
                "audio_cover_strength": args.audio_cover_strength,
                "cover_noise_strength": args.cover_noise_strength,
            }
        )
        if args.task_type == "repaint":
            payload.update(
                {
                    "repainting_start": args.repainting_start,
                    "repainting_end": args.repainting_end,
                    "repaint_mode": args.repaint_mode,
                    "repaint_strength": args.repaint_strength,
                    "repaint_latent_crossfade_frames": args.repaint_crossfade_frames,
                    "repaint_wav_crossfade_sec": args.repaint_wav_crossfade_seconds,
                }
            )
    if args.reference_audio:
        reference_audio = Path(args.reference_audio).expanduser().resolve()
        if not reference_audio.is_file():
            fail(f"ACE-Step reference audio does not exist: {reference_audio}")
        if source_audio is not None:
            fail("use either --source-audio or --reference-audio, not both")
        payload["audio_cover_strength"] = args.audio_cover_strength

    if source_audio is not None:
        response = api_multipart_request(
            f"{base_url}/release_task",
            fields=payload,
            file_field="ctx_audio",
            file_path=source_audio,
            api_key=args.api_key,
            timeout=60,
        )
    elif reference_audio is not None:
        response = api_multipart_request(
            f"{base_url}/release_task",
            fields=payload,
            file_field="ref_audio",
            file_path=reference_audio,
            api_key=args.api_key,
            timeout=60,
        )
    else:
        response = api_request(
            f"{base_url}/release_task",
            payload=payload,
            api_key=args.api_key,
            timeout=60,
        )
    result = unwrap(response)
    if not isinstance(result, dict) or not result.get("task_id"):
        fail(f"ACE-Step did not return a task ID: {result}")
    task_id = str(result["task_id"])
    print(f"ACE-Step task queued: {task_id}")

    deadline = time.monotonic() + args.timeout
    last_progress = ""
    audio_url = ""
    while time.monotonic() < deadline:
        data = unwrap(
            api_request(
                f"{base_url}/query_result",
                payload={"task_id_list": [task_id]},
                api_key=args.api_key,
                # ACE-Step can block this first poll while lazily loading several
                # gigabytes of local MLX weights. Keep the request alive instead
                # of treating model initialization as a failed generation.
                timeout=min(float(args.timeout), 300.0),
            )
        )
        if not isinstance(data, list) or not data:
            fail(f"ACE-Step returned no status for task {task_id}")
        item = data[0]
        status = int(item.get("status", 0))
        progress = str(item.get("progress_text") or "working")
        if progress != last_progress:
            print(f"ACE-Step: {progress}")
            last_progress = progress
        if status == 2:
            details = item.get("result", "unknown failure")
            fail(f"ACE-Step generation failed: {details}")
        if status == 1:
            try:
                generated = json.loads(item.get("result", "[]"))
                audio_url = str(generated[0]["file"])
            except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
                fail(f"ACE-Step result did not include an audio file: {exc}")
            break
        time.sleep(args.poll_interval)
    else:
        fail(f"timed out waiting for ACE-Step task {task_id}")

    if not audio_url:
        fail("ACE-Step completed without an audio URL")
    download_url = urllib.parse.urljoin(f"{base_url}/", audio_url)
    output = resolve_output("song", args.output, args.format)
    if output.exists() and not args.overwrite:
        fail(f"output already exists (use --overwrite): {output}")
    audio = api_request(download_url, api_key=args.api_key, timeout=120)
    output.write_bytes(audio)
    print(f"Output: {output}")


def add_common_audio_arguments(parser: argparse.ArgumentParser, default_seconds: float) -> None:
    parser.add_argument("prompt", help="description of the audio to generate")
    parser.add_argument("--seconds", type=float, default=default_seconds)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", "-o")
    parser.add_argument("--overwrite", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local Apple-Silicon audio orchestrator (never downloads model weights)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    song = subparsers.add_parser("song", help="generate a song through ACE-Step 1.5")
    add_common_audio_arguments(song, 30.0)
    song.add_argument("--lyrics", help="explicit lyrics; otherwise ACE-Step designs the song")
    song.add_argument("--bpm", type=int, choices=range(30, 301))
    song.add_argument("--time-signature", choices=("2/4", "3/4", "4/4", "6/8"))
    song.add_argument("--key-scale", help="musical key, for example 'C Major'")
    song.add_argument("--vocal-language", default="en", help="vocal language code")
    song.add_argument(
        "--thinking",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use the optional 5 Hz language-model planner",
    )
    song.add_argument("--format", choices=("mp3", "wav", "flac", "opus", "aac"), default="mp3")
    song.add_argument("--server-url", default="http://127.0.0.1:8001")
    song.add_argument("--api-key")
    song.add_argument("--timeout", type=float, default=3600)
    song.add_argument("--poll-interval", type=float, default=3)
    song.add_argument(
        "--source-audio",
        help="WAV used as ACE-Step cover/remix conditioning",
    )
    song.add_argument(
        "--reference-audio",
        help="WAV used only for global timbre/style conditioning in text-to-music mode",
    )
    song.add_argument(
        "--task-type",
        choices=("text2music", "cover", "cover-nofsq", "repaint"),
        default="cover",
    )
    song.add_argument("--audio-cover-strength", type=float, default=1.0)
    song.add_argument(
        "--cover-noise-strength",
        type=float,
        default=0.6,
        help="melody retention: 0 is a new composition, 1 is closest to source",
    )
    song.add_argument("--repainting-start", type=float, default=0.0)
    song.add_argument("--repainting-end", type=float)
    song.add_argument(
        "--repaint-mode",
        choices=("conservative", "balanced", "aggressive"),
        default="balanced",
    )
    song.add_argument("--repaint-strength", type=float, default=0.5)
    song.add_argument("--repaint-crossfade-frames", type=int, default=10)
    song.add_argument("--repaint-wav-crossfade-seconds", type=float, default=0.25)
    song.set_defaults(handler=run_song)

    for command, help_text, seconds in (
        ("soundtrack", "generate instrumental music through Stable Audio 3 Medium", 15.0),
        ("sfx", "generate a sound effect through Stable Audio 3 Medium", 4.0),
    ):
        child = subparsers.add_parser(command, help=help_text)
        add_common_audio_arguments(child, seconds)
        child.add_argument("--cfg", type=float, default=1.0)
        child.add_argument("--negative-prompt")
        child.add_argument(
            "--init-audio",
            help="44.1 kHz, 16-bit WAV used as audio-to-audio context",
        )
        child.add_argument(
            "--init-noise-level",
            type=float,
            default=0.6,
            help="reference variation strength; lower preserves more of init audio",
        )
        child.add_argument(
            "--inpaint-range",
            help="time range START,END to regenerate while preserving init audio outside it",
        )
        child.add_argument("--play", action="store_true")
        child.set_defaults(handler=run_sa3)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except subprocess.CalledProcessError as exc:
        fail(f"official generator exited with status {exc.returncode}")
    except KeyboardInterrupt:
        fail("interrupted")


if __name__ == "__main__":
    main()
