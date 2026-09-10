"""Persistent local Wan 2.2 S2V worker for constrained Apple Silicon hosts.

The worker intentionally does not pretend that llama.cpp can execute Wan video
diffusion. A separately installed backend module must implement the protocol in
this file and explicitly support Wan 2.2 S2V GGUF weights on MPS.
"""

from __future__ import annotations

import argparse
import gc
import importlib
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import wave
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, TextIO

# This must be set before a backend imports torch. A zero value disables the
# normal MPS allocation ceiling, so this worker serializes jobs and aggressively
# synchronizes cache releases. The runtime profile documents the associated risk.
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"


FRAME_COUNT = 81
FPS = 16
STEPS = 20
CFG = 6.0
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 480
MIN_LEADING_SILENCE_SECONDS = 0.2
MAX_LEADING_SILENCE_SECONDS = 0.5
MAX_JSON_LINE_BYTES = 1_048_576
FORBIDDEN_BACKENDS = {"llama_cpp", "llama_cpp_python", "llama-cpp-python"}


class WorkerError(RuntimeError):
    """Base error for deterministic worker failures."""


class ConfigurationError(WorkerError):
    """Raised when the local runtime cannot safely start."""


class JobValidationError(WorkerError):
    """Raised when an MCP job violates the S2V contract."""


class BackendProtocolError(WorkerError):
    """Raised when a backend does not implement the required contract."""


class JsonLogger:
    """Emit one compact JSON object per stdout line."""

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        self._stream = stream

    def emit(
        self,
        status: str,
        phase: str,
        message: str,
        *,
        job_id: str | None = None,
        **fields: Any,
    ) -> None:
        payload = {
            "timestamp_unix": round(time.time(), 3),
            "status": status,
            "phase": phase,
            "message": message,
        }
        if job_id is not None:
            payload["job_id"] = job_id
        payload.update(fields)
        self._stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self._stream.flush()


@dataclass(frozen=True)
class WorkerConfig:
    """Resolved local model and execution configuration."""

    backend_module: str
    model_gguf: Path
    vae_path: Path
    text_encoder_path: Path
    tokenizer_path: Path
    audio_encoder_path: Path
    output_root: Path
    ffmpeg: str = "ffmpeg"
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    frame_count: int = FRAME_COUNT
    fps: int = FPS
    steps: int = STEPS
    cfg: float = CFG
    allow_non_macos_validation: bool = False

    def backend_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, Path):
                payload[key] = str(value)
        payload.update(
            {
                "device": "mps",
                "model_format": "gguf",
                "quantization": "q4-k-s",
                "text_encoder_device": "cpu",
                "text_encoder_format": "gguf",
                "text_encoder_quantization": "q4-k-s",
                "audio_encoder_device": "cpu",
                "audio_encoder_dtype": "float16",
                "lora_enabled": False,
            }
        )
        return payload


@dataclass(frozen=True)
class GenerationJob:
    """One validated MCP generation request."""

    job_id: str
    prompt: str
    negative_prompt: str
    reference_image: Path
    audio_path: Path
    output_path: Path
    seed: int


class S2VBackend(Protocol):
    """Protocol implemented by a verified external Wan S2V GGUF backend."""

    def generate_to_directory(
        self,
        job: dict[str, Any],
        frame_directory: str,
        emit: Callable[..., None],
    ) -> int:
        """Stream numbered PNG frames to ``frame_directory`` and return count."""


def mps_release(logger: JsonLogger, phase: str, job_id: str | None = None) -> None:
    """Force Python and MPS cleanup without importing torch until runtime."""
    gc.collect()
    try:
        torch = importlib.import_module("torch")
    except ModuleNotFoundError:
        logger.emit("warning", phase, "torch is unavailable; skipped MPS cache release", job_id=job_id)
        return
    mps = getattr(torch, "mps", None)
    if mps is None or not bool(torch.backends.mps.is_available()):
        logger.emit("warning", phase, "MPS is unavailable; skipped cache release", job_id=job_id)
        return
    mps.empty_cache()
    mps.synchronize()
    logger.emit("ok", phase, "completed gc.collect, MPS empty_cache, and synchronize", job_id=job_id)


def _require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ConfigurationError(f"{label} does not exist: {resolved}")
    return resolved


def _require_directory(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise ConfigurationError(f"{label} does not exist: {resolved}")
    return resolved


def _validate_gguf(path: Path) -> None:
    with path.open("rb") as handle:
        if handle.read(4) != b"GGUF":
            raise ConfigurationError(f"model is not a GGUF file: {path}")


def _validate_dimensions(width: int, height: int) -> None:
    if width < 384 or height < 384:
        raise ConfigurationError("local S2V dimensions must be at least 384x384")
    if width % 16 or height % 16:
        raise ConfigurationError("width and height must both be divisible by 16")


def validate_config(config: WorkerConfig, *, require_runtime: bool = True) -> None:
    """Validate files, standard-sampling parameters, platform, and backend."""
    if config.frame_count != FRAME_COUNT or config.fps != FPS:
        raise ConfigurationError("local profile is fixed at 81 frames and 16 FPS")
    if config.steps != STEPS or config.cfg != CFG:
        raise ConfigurationError("local S2V profile is fixed at 20 steps and CFG 6.0")
    _validate_dimensions(config.width, config.height)
    backend_root = config.backend_module.split(".", 1)[0]
    if backend_root in FORBIDDEN_BACKENDS:
        raise ConfigurationError(
            "llama.cpp/llama-cpp-python does not implement Wan 2.2 S2V video diffusion"
        )
    model = _require_file(config.model_gguf, "GGUF Q4_K_S model")
    _validate_gguf(model)
    _require_file(config.vae_path, "VAE")
    text_encoder = _require_file(config.text_encoder_path, "GGUF Q4_K_S text encoder")
    _validate_gguf(text_encoder)
    _require_directory(config.tokenizer_path, "UMT5 tokenizer directory")
    _require_file(config.audio_encoder_path, "audio encoder")
    if shutil.which(config.ffmpeg) is None:
        raise ConfigurationError(f"ffmpeg executable was not found: {config.ffmpeg}")
    config.output_root.expanduser().resolve().mkdir(parents=True, exist_ok=True)
    if require_runtime and not config.allow_non_macos_validation:
        if platform.system() != "Darwin" or platform.machine() not in {"arm64", "aarch64"}:
            raise ConfigurationError("local profile requires Apple Silicon macOS")
        try:
            torch = importlib.import_module("torch")
        except ModuleNotFoundError as error:
            raise ConfigurationError("PyTorch with MPS support is required") from error
        if not bool(torch.backends.mps.is_available()):
            raise ConfigurationError("torch.backends.mps.is_available() is false")


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise JobValidationError(f"reference/frame must be PNG: {path}")
    return struct.unpack(">II", header[16:24])


def _leading_digital_silence_seconds(path: Path) -> float:
    """Measure exact zero-valued PCM samples at the start of a WAV file."""
    try:
        with wave.open(str(path), "rb") as audio:
            channels = audio.getnchannels()
            sample_width = audio.getsampwidth()
            sample_rate = audio.getframerate()
            frame_total = audio.getnframes()
            if channels != 1:
                raise JobValidationError("S2V audio must be mono")
            if sample_width not in {1, 2, 3, 4}:
                raise JobValidationError("unsupported PCM sample width")
            zero_frame = b"\x80" if sample_width == 1 else b"\x00" * sample_width
            silent_frames = 0
            chunk_size = 4096
            while silent_frames < frame_total:
                data = audio.readframes(min(chunk_size, frame_total - silent_frames))
                if not data:
                    break
                for offset in range(0, len(data), sample_width):
                    if data[offset : offset + sample_width] != zero_frame:
                        return silent_frames / sample_rate
                    silent_frames += 1
            return silent_frames / sample_rate
    except wave.Error as error:
        raise JobValidationError(f"audio must be an uncompressed PCM WAV: {path}") from error


def parse_job(payload: dict[str, Any], config: WorkerConfig) -> GenerationJob:
    """Validate an untrusted JSON job from an MCP client."""
    if payload.get("command") != "generate":
        raise JobValidationError("job command must be 'generate'")
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt or len(prompt) > 20_000:
        raise JobValidationError("prompt must contain 1 to 20,000 characters")
    negative_prompt = str(payload.get("negative_prompt", "")).strip()
    reference = Path(str(payload.get("reference_image", ""))).expanduser().resolve()
    audio = Path(str(payload.get("audio_path", ""))).expanduser().resolve()
    if not reference.is_file():
        raise JobValidationError(f"reference image does not exist: {reference}")
    if not audio.is_file():
        raise JobValidationError(f"audio does not exist: {audio}")
    image_width, image_height = _png_dimensions(reference)
    if (image_width, image_height) != (config.width, config.height):
        raise JobValidationError(
            f"reference image is {image_width}x{image_height}; expected {config.width}x{config.height}"
        )
    silence = _leading_digital_silence_seconds(audio)
    if not MIN_LEADING_SILENCE_SECONDS <= silence <= MAX_LEADING_SILENCE_SECONDS:
        raise JobValidationError(
            f"leading digital silence is {silence:.6f}s; expected 0.2s to 0.5s"
        )
    output_root = config.output_root.expanduser().resolve()
    output_value = payload.get("output_path") or f"{payload.get('job_id') or uuid.uuid4().hex}.mp4"
    output = Path(str(output_value)).expanduser()
    output = output.resolve() if output.is_absolute() else (output_root / output).resolve()
    try:
        output.relative_to(output_root)
    except ValueError as error:
        raise JobValidationError("output_path must remain inside output_root") from error
    if output.suffix.lower() != ".mp4":
        raise JobValidationError("output_path must end in .mp4")
    seed = int(payload.get("seed", 0))
    if seed < 0:
        raise JobValidationError("seed cannot be negative")
    return GenerationJob(
        job_id=str(payload.get("job_id") or uuid.uuid4().hex),
        prompt=prompt,
        negative_prompt=negative_prompt,
        reference_image=reference,
        audio_path=audio,
        output_path=output,
        seed=seed,
    )


def load_backend(config: WorkerConfig, logger: JsonLogger) -> S2VBackend:
    """Load a verified backend once for the lifetime of the worker."""
    logger.emit("loading", "backend", "initializing memory-mapped GGUF Q4 S2V backend")
    try:
        module = importlib.import_module(config.backend_module)
    except Exception as error:
        raise BackendProtocolError(
            f"could not import backend module '{config.backend_module}': {error}"
        ) from error
    factory = getattr(module, "create_backend", None)
    if not callable(factory):
        raise BackendProtocolError("backend module must export create_backend(config, emit, cleanup)")
    backend = factory(config.backend_payload(), logger.emit, lambda phase: mps_release(logger, phase))
    if not callable(getattr(backend, "generate_to_directory", None)):
        raise BackendProtocolError("backend object must implement generate_to_directory")
    logger.emit("ready", "backend", "GGUF Q4 S2V backend loaded once and ready")
    return backend


def _assemble_video(config: WorkerConfig, job: GenerationJob, frame_dir: Path, target: Path) -> None:
    command = [
        config.ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-framerate",
        str(config.fps),
        "-i",
        str(frame_dir / "%05d.png"),
        "-i",
        str(job.audio_path),
        "-frames:v",
        str(config.frame_count),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-shortest",
        str(target),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise WorkerError(f"ffmpeg failed: {completed.stderr.strip()}")


def run_job(config: WorkerConfig, backend: S2VBackend, job: GenerationJob, logger: JsonLogger) -> Path:
    """Run one job without reloading model weights."""
    logger.emit("running", "job", "accepted validated S2V job", job_id=job.job_id)
    config.output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{job.job_id}-", dir=config.output_root) as temp_value:
        temp_dir = Path(temp_value)
        frame_dir = temp_dir / "frames"
        frame_dir.mkdir()
        mps_release(logger, "before-diffusion", job.job_id)
        backend_job = {
            "job_id": job.job_id,
            "prompt": job.prompt,
            "negative_prompt": job.negative_prompt,
            "reference_image": str(job.reference_image),
            "audio_path": str(job.audio_path),
            "seed": job.seed,
            "width": config.width,
            "height": config.height,
            "frame_count": config.frame_count,
            "fps": config.fps,
            "steps": config.steps,
            "cfg": config.cfg,
        }
        count = int(backend.generate_to_directory(backend_job, str(frame_dir), logger.emit))
        mps_release(logger, "after-vae-decode", job.job_id)
        frames = sorted(frame_dir.glob("*.png"))
        if count != config.frame_count or len(frames) != config.frame_count:
            raise BackendProtocolError(
                f"backend reported {count} and wrote {len(frames)} frames; expected {config.frame_count}"
            )
        for index, frame in enumerate(frames):
            expected = frame_dir / f"{index:05d}.png"
            if frame != expected:
                raise BackendProtocolError(f"frames must be numbered from 00000.png: {frame.name}")
            if _png_dimensions(frame) != (config.width, config.height):
                raise BackendProtocolError(f"frame has wrong dimensions: {frame}")
        temp_video = temp_dir / "assembled.mp4"
        logger.emit("running", "ffmpeg", "assembling sequential PNG frames", job_id=job.job_id)
        _assemble_video(config, job, frame_dir, temp_video)
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_video.replace(job.output_path)
    logger.emit(
        "complete",
        "job",
        "S2V video completed",
        job_id=job.job_id,
        output_path=str(job.output_path),
        frame_count=config.frame_count,
        fps=config.fps,
    )
    return job.output_path


def serve(config: WorkerConfig, logger: JsonLogger, stream: TextIO = sys.stdin) -> int:
    """Serve sequential JSONL commands until shutdown or EOF."""
    validate_config(config)
    backend = load_backend(config, logger)
    logger.emit("ready", "worker", "persistent MCP JSONL worker is ready")
    for raw_line in stream:
        payload: dict[str, Any] | None = None
        if len(raw_line.encode("utf-8")) > MAX_JSON_LINE_BYTES:
            logger.emit("error", "request", "JSON line exceeds size limit")
            continue
        try:
            payload = json.loads(raw_line)
            if not isinstance(payload, dict):
                raise JobValidationError("request must be a JSON object")
            command = payload.get("command")
            if command == "health":
                logger.emit("ready", "health", "worker and backend are loaded")
                continue
            if command == "shutdown":
                logger.emit("stopping", "worker", "shutdown requested")
                return 0
            job = parse_job(payload, config)
            run_job(config, backend, job, logger)
        except Exception as error:  # noqa: BLE001 - isolate one failed persistent-worker job
            logger.emit(
                "error",
                "request",
                str(error),
                job_id=str(payload.get("job_id")) if payload and payload.get("job_id") else None,
                error_type=type(error).__name__,
            )
            mps_release(logger, "error-recovery")
    logger.emit("stopping", "worker", "stdin reached EOF")
    return 0


def _path_argument(value: str) -> Path:
    return Path(value).expanduser()


def build_parser() -> argparse.ArgumentParser:
    """Build the local-worker CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-module", default=os.getenv("LPW_WAN_S2V_BACKEND_MODULE", ""))
    parser.add_argument("--model-gguf", type=_path_argument, default=os.getenv("LPW_WAN_S2V_GGUF", ""))
    parser.add_argument("--vae", dest="vae_path", type=_path_argument, default=os.getenv("LPW_WAN_S2V_VAE", ""))
    parser.add_argument("--text-encoder", type=_path_argument, default=os.getenv("LPW_WAN_S2V_TEXT_ENCODER", ""))
    parser.add_argument("--tokenizer", type=_path_argument, default=os.getenv("LPW_WAN_S2V_TOKENIZER", ""))
    parser.add_argument("--audio-encoder", type=_path_argument, default=os.getenv("LPW_WAN_S2V_AUDIO_ENCODER", ""))
    parser.add_argument("--output-root", type=_path_argument, default=Path("runtime/video/local-s2v"))
    parser.add_argument("--ffmpeg", default=os.getenv("LPW_FFMPEG", "ffmpeg"))
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--allow-non-macos-validation", action="store_true")
    return parser


def config_from_args(args: argparse.Namespace) -> WorkerConfig:
    """Create immutable worker configuration from parsed CLI options."""
    required_strings = {
        "backend_module": args.backend_module,
        "model_gguf": str(args.model_gguf),
        "vae_path": str(args.vae_path),
        "text_encoder_path": str(args.text_encoder),
        "tokenizer_path": str(args.tokenizer),
        "audio_encoder_path": str(args.audio_encoder),
    }
    missing = [key for key, value in required_strings.items() if not value]
    if missing:
        raise ConfigurationError(f"missing required configuration: {', '.join(missing)}")
    return WorkerConfig(
        backend_module=args.backend_module,
        model_gguf=Path(args.model_gguf),
        vae_path=Path(args.vae_path),
        text_encoder_path=Path(args.text_encoder),
        tokenizer_path=Path(args.tokenizer),
        audio_encoder_path=Path(args.audio_encoder),
        output_root=Path(args.output_root).expanduser().resolve(),
        ffmpeg=args.ffmpeg,
        width=args.width,
        height=args.height,
        allow_non_macos_validation=args.allow_non_macos_validation,
    )


def main() -> None:
    """Run config validation or the persistent worker."""
    logger = JsonLogger()
    try:
        args = build_parser().parse_args()
        config = config_from_args(args)
        if args.validate_only:
            validate_config(config, require_runtime=False)
            logger.emit("ok", "validation", "local S2V configuration is structurally valid")
            return
        raise_code = serve(config, logger)
    except Exception as error:  # noqa: BLE001 - CLI boundary must emit structured fatal JSON
        logger.emit("fatal", "startup", str(error), error_type=type(error).__name__)
        raise_code = 2
    raise SystemExit(raise_code)


if __name__ == "__main__":
    main()
