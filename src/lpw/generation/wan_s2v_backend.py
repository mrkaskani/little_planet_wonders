"""Direct Wan 2.2 S2V GGUF/MPS backend for the persistent LPW worker."""

from __future__ import annotations

import gc
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

from .umt5_gguf_mps import UMT5GGUFEncoder
from .wan_s2v_transformer import WanS2VStreamedTransformer
from .wan_vae import WanVAE, load_reference_pixels
from .wav2vec_s2v import WanAudioEncoder


class DirectWanS2VBackend:
    """Orchestrate text, audio, diffusion, FramePack and VAE locally."""

    def __init__(
        self,
        config: dict[str, Any],
        emit: Callable[..., None],
        cleanup: Callable[[str], None],
    ) -> None:
        self.config = config
        self.emit = emit
        self.cleanup = cleanup
        self.text_encoder = UMT5GGUFEncoder(
            config["text_encoder_path"], config["tokenizer_path"]
        )
        self.audio_encoder = WanAudioEncoder(config["audio_encoder_path"])
        self.transformer = WanS2VStreamedTransformer(config["model_gguf"])
        self.vae = WanVAE(config["vae_path"])
        self._peak_process_rss_bytes = 0
        self._peak_mps_driver_bytes = 0

    def _runtime_metrics(self) -> dict[str, int]:
        """Capture process and unified-memory measurements.

        Returns:
            Integer byte counts suitable for persistent JSON diagnostics.
        """
        import psutil
        import torch

        process_rss = int(psutil.Process().memory_info().rss)
        available = int(psutil.virtual_memory().available)
        current = int(torch.mps.current_allocated_memory())
        driver = int(torch.mps.driver_allocated_memory())
        self._peak_process_rss_bytes = max(self._peak_process_rss_bytes, process_rss)
        self._peak_mps_driver_bytes = max(self._peak_mps_driver_bytes, driver)
        return {
            "process_rss_bytes": process_rss,
            "available_unified_memory_bytes": available,
            "mps_current_allocated_bytes": current,
            "mps_driver_allocated_bytes": driver,
            "peak_process_rss_bytes": self._peak_process_rss_bytes,
            "peak_mps_driver_allocated_bytes": self._peak_mps_driver_bytes,
        }

    def _emit_metrics(self, phase: str, message: str, job_id: str, **fields: Any) -> None:
        """Emit one durable runtime telemetry sample.

        Args:
            phase: Current backend phase.
            message: Human-readable sample description.
            job_id: Active generation identifier.
            **fields: Additional scalar diagnostic fields.
        """
        self.emit(
            "running",
            phase,
            message,
            job_id=job_id,
            **self._runtime_metrics(),
            **fields,
        )

    @staticmethod
    def _checkpoint_signature(job: dict[str, Any]) -> str:
        """Build a stable signature for scheduler-resume compatibility.

        Args:
            job: Validated generation payload.

        Returns:
            SHA-256 signature covering generation-defining inputs.
        """
        fields = {
            key: job[key]
            for key in (
                "prompt", "negative_prompt", "reference_image", "audio_path", "seed",
                "width", "height", "frame_count", "fps", "steps", "cfg",
            )
        }
        for key in ("reference_image", "audio_path"):
            path = Path(str(fields[key])).expanduser().resolve()
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            fields[f"{key}_sha256"] = digest.hexdigest()
            fields[key] = str(path)
        encoded = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _checkpoint_directory(self, job: dict[str, Any], frame_directory: str) -> Path:
        """Resolve and create the durable checkpoint directory.

        Args:
            job: Generation payload, optionally containing ``checkpoint_directory``.
            frame_directory: Destination used by direct smoke renders.

        Returns:
            Existing absolute checkpoint directory.
        """
        explicit = job.get("checkpoint_directory")
        if explicit:
            directory = Path(str(explicit)).expanduser().resolve()
        elif self.config.get("output_root"):
            safe_id = "".join(
                character if character.isalnum() or character in "-_" else "_"
                for character in str(job["job_id"])
            )
            directory = Path(self.config["output_root"]).resolve() / "checkpoints" / safe_id
        else:
            directory = Path(frame_directory).resolve().parent / "checkpoints"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _atomic_safetensors(path: Path, tensors: dict[str, Any]) -> None:
        """Atomically save CPU tensors.

        Args:
            path: Final checkpoint path.
            tensors: Named tensors to serialize.
        """
        from safetensors.torch import save_file

        temporary = path.with_suffix(path.suffix + ".partial")
        save_file(
            {name: value.detach().to("cpu").contiguous() for name, value in tensors.items()},
            str(temporary),
        )
        temporary.replace(path)

    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
        """Atomically save checkpoint metadata.

        Args:
            path: Final JSON path.
            payload: Serializable metadata.
        """
        temporary = path.with_suffix(path.suffix + ".partial")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)

    def _save_scheduler_checkpoint(
        self,
        directory: Path,
        signature: str,
        scheduler: Any,
        latents: Any,
        completed_steps: int,
        total_steps: int,
    ) -> None:
        """Persist all UniPC multistep state needed for exact continuation.

        Args:
            directory: Durable checkpoint directory.
            signature: Compatibility hash for the active job.
            scheduler: Active UniPC scheduler.
            latents: Current denoised latent sample.
            completed_steps: Number of completed scheduler steps.
            total_steps: Configured number of scheduler steps.
        """
        tensors = {"latents": latents}
        if scheduler.last_sample is not None:
            tensors["last_sample"] = scheduler.last_sample
        model_output_slots = []
        for index, value in enumerate(scheduler.model_outputs):
            if value is not None:
                tensors[f"model_output_{index}"] = value
                model_output_slots.append(index)
        tensor_file = f"scheduler-step-{completed_steps:04d}.safetensors"
        self._atomic_safetensors(directory / tensor_file, tensors)
        timestep_list = [
            None if value is None else int(value.item() if hasattr(value, "item") else value)
            for value in scheduler.timestep_list
        ]
        self._atomic_json(
            directory / "scheduler-state.json",
            {
                "signature": signature,
                "completed_steps": completed_steps,
                "total_steps": total_steps,
                "step_index": int(scheduler.step_index),
                "lower_order_nums": int(scheduler.lower_order_nums),
                "this_order": int(scheduler.this_order),
                "model_output_slots": model_output_slots,
                "timestep_list": timestep_list,
                "tensor_file": tensor_file,
            },
        )

    def _load_scheduler_checkpoint(
        self,
        directory: Path,
        signature: str,
        scheduler: Any,
    ) -> tuple[Any | None, int]:
        """Restore a compatible UniPC scheduler checkpoint when present.

        Args:
            directory: Durable checkpoint directory.
            signature: Expected generation compatibility hash.
            scheduler: Fresh scheduler initialized with the same step count.

        Returns:
            Restored latents and completed-step count, or ``(None, 0)``.
        """
        import torch
        from safetensors.torch import load_file

        metadata_path = directory / "scheduler-state.json"
        if not metadata_path.is_file():
            return None, 0
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("signature") != signature:
            return None, 0
        tensor_file = metadata.get("tensor_file")
        if not tensor_file:
            return None, 0
        tensors_path = directory / str(tensor_file)
        if not tensors_path.is_file():
            return None, 0
        tensors = load_file(str(tensors_path), device="cpu")
        scheduler._step_index = int(metadata["step_index"])
        scheduler.lower_order_nums = int(metadata["lower_order_nums"])
        scheduler.this_order = int(metadata["this_order"])
        scheduler.last_sample = (
            tensors["last_sample"].to(self.transformer.device)
            if "last_sample" in tensors else None
        )
        scheduler.model_outputs = [None] * scheduler.config.solver_order
        for index in metadata.get("model_output_slots", []):
            scheduler.model_outputs[int(index)] = tensors[f"model_output_{index}"].to(
                self.transformer.device
            )
        scheduler.timestep_list = [
            None if value is None else torch.tensor(value, device=self.transformer.device)
            for value in metadata.get("timestep_list", [])
        ]
        return tensors["latents"].to(self.transformer.device), int(metadata["completed_steps"])

    @staticmethod
    def _scheduler(steps: int, device: Any) -> Any:
        from diffusers import UniPCMultistepScheduler

        scheduler = UniPCMultistepScheduler(
            num_train_timesteps=1000,
            prediction_type="flow_prediction",
            use_flow_sigmas=True,
            flow_shift=3.0,
            solver_order=2,
            solver_type="bh2",
            final_sigmas_type="zero",
        )
        scheduler.set_timesteps(steps, device=device)
        return scheduler

    @staticmethod
    def _initial_noise(shape: tuple[int, ...], seed: int, device: Any) -> Any:
        import torch

        generator = torch.Generator(device="cpu").manual_seed(seed)
        return torch.randn(shape, generator=generator, dtype=torch.float32).to(
            device=device, dtype=torch.bfloat16
        )

    def _conditioning(self, job: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
        import torch

        job_id = str(job["job_id"])
        self.emit("running", "text", "encoding positive UMT5 context", job_id=job_id)
        positive = self.text_encoder.encode(job["prompt"], emit=self.emit)
        self.emit("running", "text", "encoding negative UMT5 context", job_id=job_id)
        negative = self.text_encoder.encode(job.get("negative_prompt") or "", emit=self.emit)
        self.emit("running", "audio", "encoding Wav2Vec2 speech features", job_id=job_id)
        audio_features = self.audio_encoder.extract(job["audio_path"], emit=self.emit)
        bucket, repeats = self.audio_encoder.bucket(audio_features, fps=16, frames=80)
        if repeats != 1:
            raise RuntimeError(
                f"one S2V job must contain one five-second audio bucket; encoder produced {repeats}"
            )
        audio = bucket.permute(1, 2, 0).unsqueeze(0).contiguous()
        silent_audio = torch.zeros_like(audio)
        del audio_features, bucket
        gc.collect()
        return positive, negative, audio, silent_audio

    def _reference(self, job: dict[str, Any]) -> Any:
        pixels = load_reference_pixels(
            job["reference_image"], int(job["width"]), int(job["height"])
        )
        self.emit("running", "vae", "encoding the single S2V reference image", job_id=job["job_id"])
        return self.vae.encode(pixels)

    def _denoise(
        self,
        job: dict[str, Any],
        reference: Any,
        positive: Any,
        negative: Any,
        audio: Any,
        silent_audio: Any,
        checkpoint_directory: Path,
    ) -> Any:
        import torch

        height = int(job["height"])
        width = int(job["width"])
        latent_height, latent_width = height // 8, width // 8
        latent_frames = 20
        motion = torch.zeros(
            (1, 16, 19, latent_height, latent_width), dtype=torch.bfloat16
        )
        scheduler = self._scheduler(int(job["steps"]), self.transformer.device)
        signature = self._checkpoint_signature(job)
        latents, completed_steps = self._load_scheduler_checkpoint(
            checkpoint_directory, signature, scheduler
        )
        if latents is None:
            latents = self._initial_noise(
                (1, 16, latent_frames, latent_height, latent_width),
                int(job["seed"]),
                self.transformer.device,
            )
            completed_steps = 0
        else:
            self.emit(
                "running", "resume", f"resuming after scheduler step {completed_steps}",
                job_id=job["job_id"], checkpoint_directory=str(checkpoint_directory),
            )
        condition = torch.zeros_like(latents, device="cpu")
        guidance = float(job["cfg"])
        for step_index in range(completed_steps, len(scheduler.timesteps)):
            timestep = scheduler.timesteps[step_index]
            step_started = time.monotonic()
            self.emit(
                "running", "diffusion",
                f"denoising step {step_index + 1}/{len(scheduler.timesteps)}",
                job_id=job["job_id"],
                timestep=int(timestep),
            )
            conditional = self.transformer.forward(
                latents,
                timestep,
                positive,
                reference,
                condition,
                motion,
                audio,
                drop_motion=True,
                emit=self.emit,
            )
            unconditional = self.transformer.forward(
                latents,
                timestep,
                negative,
                reference,
                condition,
                motion,
                silent_audio,
                drop_motion=True,
                emit=self.emit,
            )
            prediction = unconditional + guidance * (conditional - unconditional)
            latents = scheduler.step(
                prediction,
                timestep,
                latents.float(),
                return_dict=False,
            )[0].to(torch.bfloat16)
            del conditional, unconditional, prediction
            gc.collect()
            torch.mps.empty_cache()
            torch.mps.synchronize()
            self._save_scheduler_checkpoint(
                checkpoint_directory,
                signature,
                scheduler,
                latents,
                step_index + 1,
                len(scheduler.timesteps),
            )
            self._emit_metrics(
                "telemetry",
                f"completed denoising step {step_index + 1}/{len(scheduler.timesteps)}",
                str(job["job_id"]),
                step_index=step_index + 1,
                step_elapsed_seconds=round(time.monotonic() - step_started, 3),
            )
        return latents.to("cpu")

    @staticmethod
    def _write_frames(pixels: Any, frame_directory: Path) -> int:
        import numpy as np
        from PIL import Image

        torch = __import__("torch")
        if pixels.shape[2] < 81:
            raise RuntimeError(f"VAE decoded only {pixels.shape[2]} frames; expected at least 81")
        for index in range(81):
            frame = (
                (pixels[0, :, index].permute(1, 2, 0) + 1.0) * 127.5
            ).round().clamp(0, 255).to(dtype=torch.uint8).numpy()
            Image.fromarray(np.asarray(frame), mode="RGB").save(
                frame_directory / f"{index:05d}.png"
            )
        return 81

    def generate_to_directory(
        self,
        job: dict[str, Any],
        frame_directory: str,
        emit: Callable[..., None],
    ) -> int:
        import torch

        if int(job["frame_count"]) != 81 or int(job["fps"]) != 16:
            raise RuntimeError("direct S2V backend requires 81 frames at 16 FPS")
        job_started = time.monotonic()
        checkpoint_directory = self._checkpoint_directory(job, frame_directory)
        decode_checkpoint = job.get("decode_checkpoint")
        if decode_checkpoint:
            from safetensors.torch import load_file

            checkpoint = load_file(str(Path(str(decode_checkpoint)).resolve()), device="cpu")
            decode_latents = checkpoint["decode_latents"]
            self.emit(
                "running", "resume", "loaded final latents for decode-only retry",
                job_id=job["job_id"], decode_checkpoint=str(decode_checkpoint),
            )
            self._emit_metrics("telemetry", "starting decode-only retry", str(job["job_id"]))
            self.emit("running", "vae", "decoding 81 video frames with CPU-offloaded tiles", job_id=job["job_id"])
            pixels = self.vae.decode(
                decode_latents, emit=self.emit, job_id=str(job["job_id"])
            )
            count = self._write_frames(pixels, Path(frame_directory))
            del decode_latents, pixels
            gc.collect()
            torch.mps.empty_cache()
            torch.mps.synchronize()
            return count
        self._emit_metrics("telemetry", "starting full S2V generation", str(job["job_id"]))
        reference = self._reference(job)
        self._emit_metrics("telemetry", "encoded reference image", str(job["job_id"]))
        positive, negative, audio, silent_audio = self._conditioning(job)
        self._emit_metrics("telemetry", "prepared text and audio conditioning", str(job["job_id"]))
        latents = self._denoise(
            job, reference, positive, negative, audio, silent_audio, checkpoint_directory
        )
        self._emit_metrics("telemetry", "completed diffusion", str(job["job_id"]))
        decode_latents = torch.cat([reference, latents], dim=2)
        final_checkpoint = checkpoint_directory / "final-latents.safetensors"
        self._atomic_safetensors(final_checkpoint, {"decode_latents": decode_latents})
        self._atomic_json(
            checkpoint_directory / "final-latents.json",
            {
                "signature": self._checkpoint_signature(job),
                "shape": list(decode_latents.shape),
                "dtype": str(decode_latents.dtype),
                "checkpoint": str(final_checkpoint),
            },
        )
        self.emit(
            "ok", "checkpoint", "saved final latents before VAE decode",
            job_id=job["job_id"], checkpoint=str(final_checkpoint),
        )
        self.emit("running", "vae", "decoding 81 video frames with CPU-offloaded tiles", job_id=job["job_id"])
        pixels = self.vae.decode(
            decode_latents, emit=self.emit, job_id=str(job["job_id"])
        )
        count = self._write_frames(pixels, Path(frame_directory))
        del reference, positive, negative, audio, silent_audio, latents, decode_latents, pixels
        gc.collect()
        torch.mps.empty_cache()
        torch.mps.synchronize()
        self._emit_metrics(
            "telemetry",
            "completed full S2V generation",
            str(job["job_id"]),
            generated_frames=count,
            total_elapsed_seconds=round(time.monotonic() - job_started, 3),
        )
        return count


def create_backend(
    config: dict[str, Any],
    emit: Callable[..., None],
    cleanup: Callable[[str], None],
) -> DirectWanS2VBackend:
    """Worker protocol entry point."""
    return DirectWanS2VBackend(config, emit, cleanup)
