#!/usr/bin/env python3
"""Rank voice families and pairs using speaker-embedding cosine similarity."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly
from transformers import AutoFeatureExtractor, WavLMForXVector


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = PROJECT_ROOT / "models/speaker-embeddings/wavlm-base-plus-sv"
DEFAULT_BATCHES = PROJECT_ROOT / "outputs/qwen3-tts/contrast-batches"
DEFAULT_REPORT = PROJECT_ROOT / "outputs/qwen3-tts/contrast-analysis"
TARGET_SAMPLE_RATE = 16_000


@dataclass
class VoiceSample:
    family: str
    path: str
    duration_seconds: float
    median_f0_hz: float | None
    spectral_centroid_hz: float
    rms_dbfs: float
    family_cohesion: float | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        action="append",
        help="Family mapping NAME=DIR; repeat for two or more families.",
    )
    parser.add_argument(
        "--batch-dir",
        type=Path,
        help="Immutable batch to analyze; defaults to the newest completed batch.",
    )
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--device", choices=("auto", "cpu", "mps"), default="auto")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument(
        "--max-pair-cosine",
        type=float,
        default=0.85,
        help="Reject pairs at or above this speaker-identity similarity (default: 0.85).",
    )
    parser.add_argument(
        "--min-pair-family-margin",
        type=float,
        default=0.08,
        help="Required cohesion-minus-cross-cosine margin (default: 0.08).",
    )
    parser.add_argument(
        "--min-f0-separation",
        type=float,
        default=0.35,
        help="Required median-pitch separation in octaves (default: 0.35).",
    )
    return parser.parse_args()


def newest_batch() -> Path:
    completed: list[Path] = []
    for manifest in DEFAULT_BATCHES.glob("*/manifest.json"):
        try:
            if json.loads(manifest.read_text()).get("status") == "complete":
                completed.append(manifest.parent)
        except (json.JSONDecodeError, OSError):
            continue
    if not completed:
        raise SystemExit(f"No completed contrast batches found under {DEFAULT_BATCHES}")
    return max(completed, key=lambda path: path.stat().st_mtime)


def family_directories(
    values: list[str] | None,
    batch_dir: Path | None,
) -> tuple[dict[str, Path], Path | None]:
    if values and batch_dir:
        raise SystemExit("Use either --batch-dir or --family mappings, not both")
    if not values:
        selected = batch_dir.expanduser().resolve() if batch_dir else newest_batch()
        manifest_path = selected / "manifest.json"
        if not manifest_path.is_file():
            raise SystemExit(f"Batch manifest is missing: {manifest_path}")
        try:
            batch_status = json.loads(manifest_path.read_text()).get("status")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Batch manifest is invalid: {manifest_path}: {exc}") from exc
        if batch_status != "complete":
            raise SystemExit(
                f"Batch is not complete ({batch_status}): {selected}\n"
                "Resume generation before analysis."
            )
        return {
            "yoyo": selected / "yoyo",
            "riri": selected / "riri",
        }, selected
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid --family {value!r}; expected NAME=DIR")
        name, raw_path = value.split("=", 1)
        if not name or not raw_path:
            raise SystemExit(f"Invalid --family {value!r}; expected NAME=DIR")
        result[name] = Path(raw_path).expanduser().resolve()
    if len(result) < 2:
        raise SystemExit("At least two voice families are required")
    return result, None


def load_audio(path: Path) -> np.ndarray:
    audio, sample_rate = sf.read(path, always_2d=False, dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if not np.isfinite(audio).all() or not audio.size:
        raise ValueError("empty audio or non-finite samples")
    peak = float(np.max(np.abs(audio)))
    if peak <= 1e-6:
        raise ValueError("audio is silent")
    active = np.flatnonzero(np.abs(audio) >= peak * 0.01)
    if active.size:
        audio = audio[active[0] : active[-1] + 1]
    if sample_rate != TARGET_SAMPLE_RATE:
        divisor = math.gcd(sample_rate, TARGET_SAMPLE_RATE)
        audio = resample_poly(
            audio,
            TARGET_SAMPLE_RATE // divisor,
            sample_rate // divisor,
        ).astype(np.float32)
    return audio


def acoustic_features(audio: np.ndarray) -> tuple[float, float | None, float, float]:
    duration = len(audio) / TARGET_SAMPLE_RATE
    rms = float(np.sqrt(np.mean(np.square(audio), dtype=np.float64)))
    rms_dbfs = 20.0 * math.log10(max(rms, 1e-9))
    centroid = librosa.feature.spectral_centroid(y=audio, sr=TARGET_SAMPLE_RATE)
    centroid_hz = float(np.median(centroid))
    try:
        f0 = librosa.yin(
            audio,
            fmin=70,
            fmax=800,
            sr=TARGET_SAMPLE_RATE,
        )
        voiced = f0[np.isfinite(f0)]
        median_f0 = float(np.median(voiced)) if voiced.size else None
    except (ValueError, librosa.util.exceptions.ParameterError):
        median_f0 = None
    return duration, median_f0, centroid_hz, rms_dbfs


def choose_device(requested: str) -> torch.device:
    if requested == "mps" and not torch.backends.mps.is_available():
        raise SystemExit("MPS was requested but is unavailable")
    if requested == "auto":
        requested = "mps" if torch.backends.mps.is_available() else "cpu"
    return torch.device(requested)


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def format_metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def bounded_ratio(value: float | None, useful_maximum: float) -> float:
    """Map a non-negative acoustic difference to 0..1 for heuristic ranking."""
    if value is None or value <= 0:
        return 0.0
    return min(value / useful_maximum, 1.0)


def profile_direction_score(left: VoiceSample, right: VoiceSample) -> float | None:
    """Check the two measurable Riri/Yoyo direction constraints."""
    by_family = {left.family: left, right.family: right}
    if set(by_family) != {"riri", "yoyo"}:
        return None
    riri = by_family["riri"]
    yoyo = by_family["yoyo"]
    checks = [float(riri.duration_seconds > yoyo.duration_seconds)]
    if riri.median_f0_hz is not None and yoyo.median_f0_hz is not None:
        checks.append(float(riri.median_f0_hz > yoyo.median_f0_hz))
    return float(np.mean(checks))


def main() -> None:
    args = parse_args()
    if not -1 <= args.max_pair_cosine <= 1:
        raise SystemExit("--max-pair-cosine must be between -1 and 1")
    if args.min_pair_family_margin < 0:
        raise SystemExit("--min-pair-family-margin must be non-negative")
    if args.min_f0_separation < 0:
        raise SystemExit("--min-f0-separation must be non-negative")
    model_dir = args.model_dir.expanduser().resolve()
    if not (model_dir / "config.json").is_file():
        raise SystemExit(
            f"Speaker model is missing: {model_dir}\n"
            "Download it explicitly with scripts/qwen3_tts/download-speaker-analyzer.sh"
        )

    families, selected_batch = family_directories(args.family, args.batch_dir)
    paths: list[tuple[str, Path]] = []
    for family, directory in families.items():
        files = sorted(directory.glob("*.wav"))
        if not files:
            raise SystemExit(f"No WAV candidates found for {family}: {directory}")
        paths.extend((family, path.resolve()) for path in files)

    device = choose_device(args.device)
    print(f"Loading local WavLM speaker verifier on {device}...")
    extractor = AutoFeatureExtractor.from_pretrained(model_dir, local_files_only=True)
    model = WavLMForXVector.from_pretrained(model_dir, local_files_only=True).to(device)
    model.eval()

    samples: list[VoiceSample] = []
    embeddings: list[np.ndarray] = []
    with torch.inference_mode():
        for family, path in paths:
            print(f"Analyzing {family}: {path.name}")
            audio = load_audio(path)
            duration, f0, centroid, rms_dbfs = acoustic_features(audio)
            inputs = extractor(audio, sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt")
            input_values = inputs["input_values"].to(device)
            attention_mask = inputs.get("attention_mask")
            if attention_mask is not None:
                attention_mask = attention_mask.to(device)
            embedding = model(
                input_values=input_values,
                attention_mask=attention_mask,
            ).embeddings[0]
            embedding = torch.nn.functional.normalize(embedding, dim=0)
            embeddings.append(embedding.cpu().float().numpy())
            samples.append(
                VoiceSample(
                    family=family,
                    path=str(path),
                    duration_seconds=round(duration, 4),
                    median_f0_hz=round(f0, 2) if f0 is not None else None,
                    spectral_centroid_hz=round(centroid, 2),
                    rms_dbfs=round(rms_dbfs, 2),
                )
            )

    for index, sample in enumerate(samples):
        same_family_cosines = [
            float(np.dot(embeddings[index], embeddings[other_index]))
            for other_index, other in enumerate(samples)
            if other_index != index and other.family == sample.family
        ]
        sample.family_cohesion = mean_or_none(same_family_cosines)

    pairs: list[dict[str, object]] = []
    for left_index, right_index in combinations(range(len(samples)), 2):
        left, right = samples[left_index], samples[right_index]
        cosine = float(np.dot(embeddings[left_index], embeddings[right_index]))
        f0_octaves = None
        if left.median_f0_hz and right.median_f0_hz:
            f0_octaves = abs(math.log2(left.median_f0_hz / right.median_f0_hz))
        cadence_octaves = abs(math.log2(left.duration_seconds / right.duration_seconds))
        cohesion_values = [
            value
            for value in (left.family_cohesion, right.family_cohesion)
            if value is not None
        ]
        mean_pair_cohesion = mean_or_none(cohesion_values)

        # Speaker distance is the primary signal. Pitch and duration provide
        # secondary contrast evidence, while cohesion avoids recommending a
        # wild identity outlier from either character family.
        identity_component = bounded_ratio(1.0 - cosine, 0.25)
        pitch_component = bounded_ratio(f0_octaves, 0.75)
        cadence_component = bounded_ratio(cadence_octaves, math.log2(1.35))
        cohesion_component = max(0.0, min(mean_pair_cohesion or 0.0, 1.0))
        direction_score = profile_direction_score(left, right)
        direction_component = direction_score if direction_score is not None else 0.5
        selection_score = (
            0.60 * identity_component
            + 0.15 * pitch_component
            + 0.05 * cadence_component
            + 0.10 * cohesion_component
            + 0.10 * direction_component
        )
        pair_family_margin = (
            mean_pair_cohesion - cosine if mean_pair_cohesion is not None else None
        )
        passes_contrast_gate = (
            left.family != right.family
            and cosine < args.max_pair_cosine
            and pair_family_margin is not None
            and pair_family_margin >= args.min_pair_family_margin
            and f0_octaves is not None
            and f0_octaves >= args.min_f0_separation
            and (direction_score is None or direction_score == 1.0)
        )
        pairs.append(
            {
                "left_family": left.family,
                "left_file": left.path,
                "right_family": right.family,
                "right_file": right.path,
                "same_family": left.family == right.family,
                "cosine_similarity": round(cosine, 6),
                "cosine_distance": round(1.0 - cosine, 6),
                "mean_family_cohesion": round(mean_pair_cohesion, 6)
                if mean_pair_cohesion is not None
                else None,
                "pair_family_margin": round(pair_family_margin, 6)
                if pair_family_margin is not None
                else None,
                "f0_separation_octaves": round(f0_octaves, 4) if f0_octaves is not None else None,
                "cadence_separation_octaves": round(cadence_octaves, 4),
                "profile_direction_score": direction_score,
                "spectral_centroid_difference_hz": round(
                    abs(left.spectral_centroid_hz - right.spectral_centroid_hz), 2
                ),
                "selection_score": round(selection_score, 6),
                "passes_contrast_gate": passes_contrast_gate,
            }
        )

    cross_pairs = sorted(
        (pair for pair in pairs if not pair["same_family"]),
        key=lambda pair: (
            -float(pair["selection_score"]),
            float(pair["cosine_similarity"]),
        ),
    )
    cross_cosines = [float(pair["cosine_similarity"]) for pair in cross_pairs]
    passing_pairs = [pair for pair in cross_pairs if pair["passes_contrast_gate"]]
    family_summary: dict[str, dict[str, float | int | None]] = {}
    for family in families:
        within = [
            float(pair["cosine_similarity"])
            for pair in pairs
            if pair["same_family"] and pair["left_family"] == family
        ]
        family_summary[family] = {
            "sample_count": sum(sample.family == family for sample in samples),
            "mean_within_family_cosine": mean_or_none(within),
            "minimum_within_family_cosine": min(within) if within else None,
            "maximum_within_family_cosine": max(within) if within else None,
        }

    within_means = [
        float(summary["mean_within_family_cosine"])
        for summary in family_summary.values()
        if summary["mean_within_family_cosine"] is not None
    ]
    mean_within_cosine = mean_or_none(within_means)
    mean_cross_cosine = mean_or_none(cross_cosines)
    contrast_margin = (
        mean_within_cosine - mean_cross_cosine
        if mean_within_cosine is not None and mean_cross_cosine is not None
        else None
    )
    contrast_summary = {
        "minimum_cross_family_cosine": min(cross_cosines),
        "mean_cross_family_cosine": mean_cross_cosine,
        "maximum_cross_family_cosine": max(cross_cosines),
        "mean_within_family_cosine": mean_within_cosine,
        "contrast_margin": contrast_margin,
        "passing_pair_count": len(passing_pairs),
        "batch_passes_contrast_gate": bool(passing_pairs),
        "contrast_gate": {
            "max_pair_cosine_exclusive": args.max_pair_cosine,
            "min_pair_family_margin": args.min_pair_family_margin,
            "min_f0_separation_octaves": args.min_f0_separation,
            "require_profile_direction_match": True,
        },
    }

    if args.report_dir:
        report_dir = args.report_dir.expanduser().resolve()
    elif selected_batch:
        report_dir = DEFAULT_REPORT / selected_batch.name
    else:
        report_dir = DEFAULT_REPORT / datetime.now().strftime("custom-%Y%m%d-%H%M%S-%f")
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "batch_dir": str(selected_batch) if selected_batch else None,
        "embedding_model": str(model_dir),
        "interpretation": "Lower cross-family cosine means greater speaker contrast.",
        "selection_score": (
            "Heuristic 0..1 score: 60% speaker-embedding distance, 15% F0 separation, "
            "5% cadence separation, 10% within-family cohesion, and 10% profile-direction fit. "
            "Higher is better; "
            "always confirm by blind listening."
        ),
        "contrast_summary": contrast_summary,
        "families": family_summary,
        "samples": [asdict(sample) for sample in samples],
        "cross_family_pairs_ranked": cross_pairs,
        "all_pairs": pairs,
    }
    (report_dir / "voice-contrast.json").write_text(json.dumps(payload, indent=2) + "\n")

    with (report_dir / "cross-family-pairs.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cross_pairs[0]))
        writer.writeheader()
        writer.writerows(cross_pairs)

    lines = [
        "# Voice contrast analysis",
        "",
        "Lower cross-family cosine similarity means greater estimated speaker contrast.",
        "Always listen before approving a pair; embeddings do not measure acting quality.",
        "",
        "## How to read this report",
        "",
        "- **Cross-family cosine similarity:** estimated speaker-identity similarity between two voices. "
        "Lower is more contrasting; higher is more alike.",
        "- **Within-family cosine similarity:** consistency among candidates generated for one character. "
        "Higher means the prompt produces a tighter voice family; lower means more identity drift.",
        "- **Contrast margin:** mean within-family cosine minus mean cross-family cosine. "
        "A larger positive margin is desirable because each character clusters with itself more than with the other character.",
        "- **F0 separation (octaves):** difference in median fundamental frequency. "
        "0 means similar median pitch, 0.5 is half an octave, and 1.0 is one octave. Pitch difference alone does not prove different identity.",
        "- **Spectral-centroid difference:** rough brightness difference in hertz. "
        "Larger can indicate darker-versus-brighter tone, but microphone/noise can influence it.",
        "- **RMS dBFS:** recording level, useful for detecting unusually quiet/loud files; it is not an identity score.",
        "- **Selection score:** batch-relative heuristic combining 60% speaker-embedding distance, "
        "15% pitch separation, 5% cadence separation, 10% within-family cohesion, and "
        "10% profile-direction fit. Higher is better; "
        "it is a shortlist score, not a pass/fail test.",
        "- **Profile-direction fit:** checks that Riri is higher-pitched and slower than Yoyo. "
        "1 means both measurable directions match, 0.5 means one matches, and 0 means neither matches.",
        "- **Contrast gate:** a pair passes only when speaker cosine is below "
        f"{args.max_pair_cosine:.2f}, its family-cohesion margin is at least "
        f"{args.min_pair_family_margin:.2f}, F0 separation is at least "
        f"{args.min_f0_separation:.2f} octaves, and the measurable profile directions match.",
        "",
        "There is no universal cosine pass threshold. Compare scores only within runs made with the same analysis model, "
        "same audition text, and similar recording conditions.",
        "",
        "## Contrast summary",
        "",
        f"- Minimum cross-family cosine (most contrasting pair): **{min(cross_cosines):.4f}**",
        f"- Mean cross-family cosine: **{format_metric(mean_cross_cosine)}**",
        f"- Mean within-family cosine: **{format_metric(mean_within_cosine)}**",
        f"- Contrast margin: **{format_metric(contrast_margin)}**",
        f"- Pairs passing the hard contrast gate: **{len(passing_pairs)} / {len(cross_pairs)}**",
        f"- Batch decision: **{'PASS' if passing_pairs else 'REJECT — voices remain too similar'}**",
        "",
        "A positive margin means candidates resemble their own character family more than the other family on average. "
        "Use a larger margin to compare batches analyzed with the same setup.",
        "",
        "## Recommended decision process",
        "",
        "1. Start with the highest selection-score pairs; use cosine distance as the primary tie-breaker.",
        "2. Listen blind using the identical audition sentence; confirm the speakers are immediately distinguishable.",
        "3. Confirm Yoyo immediately reads as a boy: low natural child pitch, firm modal phonation, grounded/chest-forward, lightly nasal/reedy, slightly rough-edged, punchy, dry, and stop-start—not girlish, androgynous, airy, or sing-song.",
        "4. Confirm Riri sounds higher, light-head, smooth, round, non-nasal, softly connected, airy, and flowing.",
        "5. Reject artifacts, poor pronunciation, wrong age, or an extreme outlier even if its cosine is low.",
        "6. Approve the best natural pair, then lock both voices with Base-model cloning.",
        "",
        "## Family consistency",
        "",
        "| Family | Samples | Mean within-family cosine | Min | Max |",
        "|---|---:|---:|---:|---:|",
    ]
    for family, summary in family_summary.items():
        lines.append(
            f"| {family} | {summary['sample_count']} | "
            f"{format_metric(summary['mean_within_family_cosine'])} | "
            f"{format_metric(summary['minimum_within_family_cosine'])} | "
            f"{format_metric(summary['maximum_within_family_cosine'])} |"
        )
    lines.extend(
        [
            "",
            f"## Top {min(args.top, len(cross_pairs))} most contrasting pairs",
            "",
            "| Rank | Gate | Score | Cosine | Family margin | Direction | F0 octaves | Cadence | Left | Right |",
            "|---:|:---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for rank, pair in enumerate(cross_pairs[: args.top], start=1):
        f0_display = pair["f0_separation_octaves"]
        lines.append(
            f"| {rank} | {'PASS' if pair['passes_contrast_gate'] else 'FAIL'} | "
            f"{pair['selection_score']:.4f} | "
            f"{pair['cosine_similarity']:.4f} | "
            f"{format_metric(pair['pair_family_margin'])} | "
            f"{format_metric(pair['profile_direction_score'])} | "
            f"{f0_display if f0_display is not None else 'n/a'} | "
            f"{pair['cadence_separation_octaves']:.4f} | "
            f"{Path(str(pair['left_file'])).name} | {Path(str(pair['right_file'])).name} |"
        )
    (report_dir / "voice-contrast.md").write_text("\n".join(lines) + "\n")

    print(f"Ranked {len(cross_pairs)} cross-family pairs.")
    print(f"Best selection score: {cross_pairs[0]['selection_score']:.4f}")
    print(f"Best-pair cosine similarity: {cross_pairs[0]['cosine_similarity']:.4f}")
    print(f"Pairs passing hard contrast gate: {len(passing_pairs)}/{len(cross_pairs)}")
    print(f"Report: {report_dir / 'voice-contrast.md'}")
    if not passing_pairs:
        raise SystemExit(
            "REJECTED: no candidate pair has enough speaker-identity contrast. "
            "Do not approve this batch; use independent source voices or a different voice model."
        )


if __name__ == "__main__":
    main()
