from __future__ import annotations

import io
import json
import struct
import wave
from pathlib import Path

import pytest

from lpw.generation import local_s2v_worker as worker


def _png_header(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(
        ">II", width, height
    )


def _write_audio(path: Path, leading_seconds: float = 0.25) -> None:
    sample_rate = 48_000
    silent_frames = round(sample_rate * leading_seconds)
    voiced_frames = sample_rate - silent_frames
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\x00\x00" * silent_frames)
        audio.writeframes(b"\x01\x00" * voiced_frames)


def _config(tmp_path: Path, backend_module: str = "verified_wan_backend") -> worker.WorkerConfig:
    files = {}
    for name in ("vae.pth", "t5.gguf", "audio.safetensors"):
        path = tmp_path / name
        path.write_bytes(b"fixture")
        files[name] = path
    model = tmp_path / "model.gguf"
    model.write_bytes(b"GGUFfixture")
    text_encoder = files["t5.gguf"]
    text_encoder.write_bytes(b"GGUFfixture")
    tokenizer = tmp_path / "tokenizer"
    tokenizer.mkdir()
    return worker.WorkerConfig(
        backend_module=backend_module,
        model_gguf=model,
        vae_path=files["vae.pth"],
        text_encoder_path=text_encoder,
        tokenizer_path=tokenizer,
        audio_encoder_path=files["audio.safetensors"],
        output_root=tmp_path / "output",
        ffmpeg="true",
        allow_non_macos_validation=True,
    )


def test_local_profile_is_fixed_and_structurally_valid(tmp_path: Path) -> None:
    config = _config(tmp_path)

    worker.validate_config(config, require_runtime=False)

    payload = config.backend_payload()
    assert payload["device"] == "mps"
    assert payload["model_format"] == "gguf"
    assert payload["quantization"] == "q4-k-s"
    assert payload["text_encoder_device"] == "cpu"
    assert payload["text_encoder_format"] == "gguf"
    assert payload["text_encoder_quantization"] == "q4-k-s"
    assert payload["audio_encoder_device"] == "cpu"
    assert payload["audio_encoder_dtype"] == "float16"
    assert payload["lora_enabled"] is False
    assert payload["steps"] == 20
    assert payload["cfg"] == 6.0


def test_llama_cpp_is_rejected_as_wan_video_backend(tmp_path: Path) -> None:
    config = _config(tmp_path, backend_module="llama_cpp")

    with pytest.raises(worker.ConfigurationError, match="does not implement Wan"):
        worker.validate_config(config, require_runtime=False)


def test_parse_job_requires_reference_size_and_audio_buffer(tmp_path: Path) -> None:
    config = _config(tmp_path)
    reference = tmp_path / "reference.png"
    reference.write_bytes(_png_header(480, 480))
    audio = tmp_path / "dialogue.wav"
    _write_audio(audio, 0.25)

    job = worker.parse_job(
        {
            "command": "generate",
            "job_id": "job-001",
            "prompt": "Riri speaks softly.",
            "negative_prompt": "identity drift",
            "reference_image": str(reference),
            "audio_path": str(audio),
            "output_path": "job-001.mp4",
            "seed": 42,
        },
        config,
    )

    assert job.job_id == "job-001"
    assert job.output_path == (config.output_root / "job-001.mp4").resolve()
    assert worker._leading_digital_silence_seconds(audio) == pytest.approx(0.25)


def test_parse_job_rejects_missing_audio_buffer(tmp_path: Path) -> None:
    config = _config(tmp_path)
    reference = tmp_path / "reference.png"
    reference.write_bytes(_png_header(480, 480))
    audio = tmp_path / "dialogue.wav"
    _write_audio(audio, 0.1)

    with pytest.raises(worker.JobValidationError, match="expected 0.2s to 0.5s"):
        worker.parse_job(
            {
                "command": "generate",
                "prompt": "Riri speaks softly.",
                "reference_image": str(reference),
                "audio_path": str(audio),
            },
            config,
        )


def test_json_logger_emits_machine_parseable_json() -> None:
    stream = io.StringIO()
    logger = worker.JsonLogger(stream)

    logger.emit("ready", "worker", "loaded", model="q4")

    payload = json.loads(stream.getvalue())
    assert payload["status"] == "ready"
    assert payload["phase"] == "worker"
    assert payload["model"] == "q4"


def test_run_job_requires_and_assembles_81_streamed_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    reference = tmp_path / "reference.png"
    reference.write_bytes(_png_header(480, 480))
    audio = tmp_path / "dialogue.wav"
    _write_audio(audio, 0.25)
    job = worker.parse_job(
        {
            "command": "generate",
            "job_id": "stream-test",
            "prompt": "Yoyo speaks.",
            "reference_image": str(reference),
            "audio_path": str(audio),
            "output_path": "stream-test.mp4",
        },
        config,
    )

    class FakeBackend:
        def generate_to_directory(self, job_payload, frame_directory, emit):
            directory = Path(frame_directory)
            for index in range(81):
                (directory / f"{index:05d}.png").write_bytes(_png_header(480, 480))
            return 81

    def fake_assemble(config_value, job_value, frame_dir, target):
        assert len(list(frame_dir.glob("*.png"))) == 81
        target.write_bytes(b"video")

    monkeypatch.setattr(worker, "mps_release", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker, "_assemble_video", fake_assemble)

    output = worker.run_job(config, FakeBackend(), job, worker.JsonLogger(io.StringIO()))

    assert output.read_bytes() == b"video"
