"""Local Wav2Vec2 conditioning compatible with the official Wan S2V code."""

from __future__ import annotations

import gc
import math
from pathlib import Path
from typing import Any


class WanAudioEncoder:
    """Load the local FP16 XLSR-53 checkpoint and produce 25-layer features."""

    def __init__(self, checkpoint: str | Path, device: str = "mps") -> None:
        import torch
        from safetensors.torch import load_file
        from transformers import Wav2Vec2Config, Wav2Vec2ForCTC

        self.checkpoint = Path(checkpoint).expanduser().resolve()
        self.device = torch.device(device)
        config = Wav2Vec2Config(
            vocab_size=33,
            hidden_size=1024,
            num_hidden_layers=24,
            num_attention_heads=16,
            intermediate_size=4096,
            hidden_act="gelu",
            conv_dim=[512] * 7,
            conv_stride=[5, 2, 2, 2, 2, 2, 2],
            conv_kernel=[10, 3, 3, 3, 3, 2, 2],
            conv_bias=True,
            feat_extract_norm="layer",
            do_stable_layer_norm=True,
            layerdrop=0.1,
            attention_dropout=0.1,
            activation_dropout=0.0,
            hidden_dropout=0.0,
            feat_proj_dropout=0.0,
            final_dropout=0.0,
        )
        with torch.device("meta"):
            model = Wav2Vec2ForCTC(config)
        state = load_file(str(self.checkpoint), device="cpu")
        model.load_state_dict(state, strict=True, assign=True)
        self.model = model.eval().requires_grad_(False)
        self.video_rate = 30

    @staticmethod
    def _normalize(waveform: Any) -> Any:
        import numpy as np

        waveform = waveform.astype(np.float32, copy=False)
        return (waveform - waveform.mean()) / np.sqrt(waveform.var() + 1e-7)

    @staticmethod
    def _interpolate(features: Any, input_fps: int, output_fps: int) -> Any:
        import torch.nn.functional as functional

        features = features.transpose(1, 2)
        output_length = int(features.shape[2] / float(input_fps) * output_fps)
        return functional.interpolate(
            features, size=output_length, align_corners=True, mode="linear"
        ).transpose(1, 2)

    def extract(self, audio_path: str | Path, emit: Any | None = None) -> Any:
        import librosa
        import torch

        if emit is not None:
            emit("loading", "audio", "loading Wav2Vec2 FP16 checkpoint on MPS")
        waveform, _ = librosa.load(str(audio_path), sr=16_000, mono=True)
        input_values = torch.from_numpy(self._normalize(waveform)).unsqueeze(0)
        self.model.to(device=self.device, dtype=torch.float16)
        with torch.inference_mode():
            output = self.model(
                input_values.to(device=self.device, dtype=torch.float16),
                output_hidden_states=True,
            )
            features = torch.cat(output.hidden_states, dim=0)
            features = self._interpolate(features, input_fps=50, output_fps=self.video_rate)
            features = features.to("cpu", dtype=torch.float16)
        self.model.to("cpu")
        del output, input_values
        gc.collect()
        torch.mps.empty_cache()
        torch.mps.synchronize()
        return features

    def bucket(self, audio_features: Any, fps: int = 16, frames: int = 80) -> tuple[Any, int]:
        """Reproduce official get_audio_embed_bucket_fps with audio_sample_m=0."""
        import numpy as np
        import torch

        layers, audio_frames, audio_dim = audio_features.shape
        scale = self.video_rate / fps
        repeats = int(audio_frames / (frames * scale)) + 1
        bucket_frames = repeats * frames
        padded_audio = math.ceil(repeats * frames / fps * self.video_rate) - audio_frames
        required_duration = bucket_frames / fps
        source_total = audio_frames + padded_audio
        time_points = np.linspace(0, required_duration, bucket_frames, endpoint=False)
        indices = np.round(time_points * self.video_rate).astype(int)
        indices = np.clip(indices, 0, source_total - 1)
        values = []
        for index in indices:
            if index < audio_frames:
                values.append(audio_features[:, int(index)])
            else:
                values.append(torch.zeros((layers, audio_dim), dtype=audio_features.dtype))
        return torch.stack(values, dim=0), repeats
