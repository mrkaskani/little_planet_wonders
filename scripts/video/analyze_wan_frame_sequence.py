#!/usr/bin/env python3
"""Analyze a Wan frame sequence for local technical continuity defects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def parser() -> argparse.ArgumentParser:
    """Build the frame-analysis command line.

    Returns:
        Configured argument parser.
    """
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("frames", type=Path)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--fps", type=int, default=16)
    value.add_argument("--mouth-roi", default="300,292,370,346")
    value.add_argument("--speech-seconds", default="0.25,3.296")
    value.add_argument("--tile-stride", type=int, default=96)
    value.add_argument("--reference", type=Path)
    return value


def _parse_quad(value: str) -> tuple[int, int, int, int]:
    """Parse four comma-separated integers.

    Args:
        value: Coordinate string in ``x0,y0,x1,y1`` order.

    Returns:
        Four integer coordinates.
    """
    values = tuple(int(item) for item in value.split(","))
    if len(values) != 4:
        raise ValueError("mouth ROI must contain four comma-separated integers")
    return values


def _parse_pair(value: str) -> tuple[float, float]:
    """Parse two comma-separated floating-point values.

    Args:
        value: Range string in ``start,end`` order.

    Returns:
        Start and end values.
    """
    values = tuple(float(item) for item in value.split(","))
    if len(values) != 2:
        raise ValueError("range must contain two comma-separated numbers")
    return values


def _seam_ratios(frames: np.ndarray, stride: int) -> dict[str, object]:
    """Compare tile-border gradients with ordinary image gradients.

    Args:
        frames: RGB frame array in ``T,H,W,C`` order.
        stride: Decoder tile stride in output pixels.

    Returns:
        Vertical and horizontal seam ratios and sampled positions.
    """
    gray = frames.astype(np.float32).mean(axis=3)
    vertical = np.abs(gray[:, :, 1:] - gray[:, :, :-1]).mean(axis=(0, 1))
    horizontal = np.abs(gray[:, 1:, :] - gray[:, :-1, :]).mean(axis=(0, 2))
    vertical_positions = list(range(stride, frames.shape[2], stride))
    horizontal_positions = list(range(stride, frames.shape[1], stride))
    vertical_values = [float(vertical[position - 1]) for position in vertical_positions]
    horizontal_values = [float(horizontal[position - 1]) for position in horizontal_positions]
    vertical_baseline = float(np.median(vertical)) or 1.0
    horizontal_baseline = float(np.median(horizontal)) or 1.0
    return {
        "vertical_positions": vertical_positions,
        "horizontal_positions": horizontal_positions,
        "vertical_max_ratio": max(vertical_values, default=0.0) / vertical_baseline,
        "horizontal_max_ratio": max(horizontal_values, default=0.0) / horizontal_baseline,
        "threshold_ratio": 2.5,
    }


def _contact_sheet(paths: list[Path], destination: Path) -> None:
    """Write a compact nine-frame visual inspection sheet.

    Args:
        paths: Ordered PNG frame paths.
        destination: Contact-sheet PNG destination.
    """
    indices = sorted({0, 1, 4, 16, 32, 48, 64, 79, 80})
    selected = [(index, Image.open(paths[index]).convert("RGB")) for index in indices]
    thumb_width = 416
    thumb_height = 240
    label_height = 24
    sheet = Image.new("RGB", (thumb_width * 3, (thumb_height + label_height) * 3), "white")
    draw = ImageDraw.Draw(sheet)
    for slot, (index, image) in enumerate(selected):
        left = (slot % 3) * thumb_width
        top = (slot // 3) * (thumb_height + label_height)
        sheet.paste(image.resize((thumb_width, thumb_height)), (left, top))
        draw.text((left + 8, top + thumb_height + 4), f"frame {index:05d}", fill="black")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def analyze(
    frame_directory: Path,
    *,
    fps: int,
    mouth_roi: tuple[int, int, int, int],
    speech_seconds: tuple[float, float],
    tile_stride: int,
    reference: Path | None = None,
) -> tuple[dict[str, object], list[Path]]:
    """Compute technical continuity measurements for 81 Wan frames.

    Args:
        frame_directory: Directory containing zero-padded PNG frames.
        fps: Playback frame rate.
        mouth_roi: Riri mouth-region coordinates.
        speech_seconds: Expected local speech interval.
        tile_stride: VAE sample-space tile stride.
        reference: Optional approved first-frame reference image.

    Returns:
        Analysis report and ordered frame paths.
    """
    paths = sorted(frame_directory.glob("*.png"))
    if len(paths) != 81 or [path.name for path in paths] != [f"{i:05d}.png" for i in range(81)]:
        raise ValueError(f"expected frames 00000.png through 00080.png; found {len(paths)}")
    frames = np.stack([np.asarray(Image.open(path).convert("RGB")) for path in paths])
    height, width = frames.shape[1:3]
    adjacent_mae = np.abs(np.diff(frames.astype(np.float32), axis=0)).mean(axis=(1, 2, 3))
    median_mae = float(np.median(adjacent_mae))
    mad = float(np.median(np.abs(adjacent_mae - median_mae)))
    spike_threshold = median_mae + 4.0 * max(mad, 0.01)
    spike_transitions = [int(index + 1) for index, value in enumerate(adjacent_mae) if value > spike_threshold]
    # Ignore the first two four-frame groups, where causal VAE cache warm-up can
    # create larger transitions that are not evidence of FramePack instability.
    framepack_boundaries = list(range(9, 81, 4))
    framepack_spikes = sorted(set(spike_transitions).intersection(framepack_boundaries))

    x0, y0, x1, y1 = mouth_roi
    mouth = frames[:, y0:y1, x0:x1].astype(np.float32)
    mouth_motion = np.abs(np.diff(mouth, axis=0)).mean(axis=(1, 2, 3))
    speech_start = max(0, round(speech_seconds[0] * fps))
    speech_end = min(80, round(speech_seconds[1] * fps))
    speech_motion = float(np.mean(mouth_motion[speech_start:speech_end]))
    silent_values = np.concatenate((mouth_motion[:speech_start], mouth_motion[speech_end:]))
    silent_motion = float(np.mean(silent_values)) if silent_values.size else 0.0

    luminance = frames.astype(np.float32).mean(axis=(1, 2, 3))
    first_transition = float(adjacent_mae[0])
    later_transition = float(np.median(adjacent_mae[1:])) or 1.0
    first_luma_delta = abs(float(luminance[0]) - float(np.median(luminance[1:9])))
    clipping = ((frames <= 2) | (frames >= 253)).mean(axis=(1, 2, 3))
    variance = frames.var(axis=(1, 2, 3))
    malformed = [
        int(index)
        for index in range(81)
        if variance[index] < 2.0 or clipping[index] > 0.75
    ]
    seams = _seam_ratios(frames, tile_stride)
    reference_metrics = None
    if reference is not None:
        reference_frame = np.asarray(
            Image.open(reference).convert("RGB").resize((width, height))
        ).astype(np.float32)
        first = frames[0].astype(np.float32)
        reference_mae = float(np.abs(first - reference_frame).mean())
        reference_luma_delta = abs(float(first.mean()) - float(reference_frame.mean()))
        reference_clipping_delta = abs(
            float(((first <= 2) | (first >= 253)).mean())
            - float(((reference_frame <= 2) | (reference_frame >= 253)).mean())
        )
        reference_metrics = {
            "frame_zero_reference_mae": reference_mae,
            "frame_zero_luminance_delta": reference_luma_delta,
            "frame_zero_clipping_delta": reference_clipping_delta,
            "suspected": reference_mae > 25.0
            or reference_luma_delta > 30.0
            or reference_clipping_delta > 0.2,
        }
    report = {
        "frame_count": 81,
        "dimensions": [width, height],
        "fps": fps,
        "vae_burn": {
            "first_transition_mae": first_transition,
            "later_median_transition_mae": later_transition,
            "transition_ratio": first_transition / later_transition,
            "first_luminance_delta": first_luma_delta,
            "reference_comparison": reference_metrics,
            "suspected": (
                reference_metrics["suspected"]
                if reference_metrics is not None
                else first_transition / later_transition > 3.0 or first_luma_delta > 35.0
            ),
            "note": "A frame-0 transition spike alone is not VAE burn when frame 0 matches the approved reference.",
        },
        "tile_seams": {
            **seams,
            "suspected": seams["vertical_max_ratio"] > 2.5 or seams["horizontal_max_ratio"] > 2.5,
        },
        "temporal_continuity": {
            "median_adjacent_mae": median_mae,
            "mad_adjacent_mae": mad,
            "spike_threshold": spike_threshold,
            "spike_transition_frames": spike_transitions,
            "framepack_boundary_spikes": framepack_spikes,
            "suspected_framepack_discontinuity": len(framepack_spikes) >= 2,
        },
        "malformed_frames": {
            "indices": malformed,
            "suspected": bool(malformed),
        },
        "mouth_motion": {
            "roi": list(mouth_roi),
            "expected_speech_frames": [speech_start, speech_end],
            "speech_interval_mean_mae": speech_motion,
            "silence_interval_mean_mae": silent_motion,
            "motion_present": speech_motion > 0.5 and speech_motion > silent_motion * 1.1,
            "lip_sync_certified": False,
            "note": "Pixel motion can detect activity but cannot certify phoneme alignment.",
        },
    }
    return report, paths


def main() -> int:
    """Run analysis and write JSON plus a contact sheet.

    Returns:
        Process exit status.
    """
    args = parser().parse_args()
    report, paths = analyze(
        args.frames,
        fps=args.fps,
        mouth_roi=_parse_quad(args.mouth_roi),
        speech_seconds=_parse_pair(args.speech_seconds),
        tile_stride=args.tile_stride,
        reference=args.reference,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "technical-review.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    _contact_sheet(paths, args.output / "contact-sheet.png")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
