from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.config import PROJECT_ROOT, renders_root
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, load_json
from lpw.utils.hashing import stable_hash


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class FinalShotValidationReport:
    shot_id: str
    valid: bool
    probe: dict[str, Any]
    issues: list[ValidationIssue]


def run_process(
    arguments: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        raise RuntimeError(f"Cannot execute '{arguments[0]}': {error}") from error
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed:\n{' '.join(arguments)}\n\n{result.stderr}"
        )
    return result


def probe_media(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Media file not found: {path}")
    result = run_process(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("FFprobe output must be a JSON object.")
    return value


def parse_frame_rate(value: str) -> float:
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    denominator_value = float(denominator)
    return 0.0 if denominator_value == 0 else float(numerator) / denominator_value


def find_stream(
    probe: dict[str, Any], codec_type: str
) -> dict[str, Any] | None:
    return next(
        (
            stream
            for stream in probe.get("streams", [])
            if stream.get("codec_type") == codec_type
        ),
        None,
    )


def detect_black_and_frozen_segments(path: Path) -> tuple[list[float], list[float]]:
    result = run_process(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-vf",
            "blackdetect=d=0.1:pic_th=0.98,freezedetect=n=-60dB:d=0.5",
            "-an",
            "-f",
            "null",
            "-",
        ],
        check=False,
    )
    black = [
        float(value)
        for value in re.findall(r"black_duration:([0-9.]+)", result.stderr)
    ]
    frozen = [
        float(value)
        for value in re.findall(r"freeze_duration:\s*([0-9.]+)", result.stderr)
    ]
    return black, frozen


def validate_shot(
    *,
    shot_id: str,
    video_path: Path,
    video_rules: dict[str, Any],
    validation_rules: dict[str, Any],
) -> FinalShotValidationReport:
    if not video_path.is_file():
        issue = ValidationIssue(
            "blocking", "FILE_NOT_FOUND", f"Video file does not exist: {video_path}"
        )
        return FinalShotValidationReport(shot_id, False, {}, [issue])
    probe = probe_media(video_path)
    video = find_stream(probe, "video")
    if video is None:
        issue = ValidationIssue(
            "blocking", "VIDEO_STREAM_MISSING", "The file contains no video stream."
        )
        return FinalShotValidationReport(shot_id, False, probe, [issue])

    issues: list[ValidationIssue] = []
    width = int(video.get("width", 0))
    height = int(video.get("height", 0))
    frame_rate = parse_frame_rate(str(video.get("avg_frame_rate", "0/1")))
    duration = float(probe.get("format", {}).get("duration", 0))
    if width <= 0 or height <= 0:
        issues.append(
            ValidationIssue(
                "blocking", "INVALID_DIMENSIONS", f"Invalid dimensions: {width}x{height}."
            )
        )
    minimum_duration = float(validation_rules["minimum_duration_seconds"])
    if duration < minimum_duration:
        issues.append(
            ValidationIssue(
                "blocking",
                "TOO_SHORT",
                f"Duration {duration:.2f}s is below the minimum {minimum_duration:.2f}s.",
            )
        )
    expected_fps = float(video_rules["frame_rate"])
    allowed_fps_difference = float(
        validation_rules["allowed_frame_rate_difference"]
    )
    if abs(frame_rate - expected_fps) > allowed_fps_difference:
        issues.append(
            ValidationIssue(
                "warning",
                "FRAME_RATE_MISMATCH",
                f"Source is {frame_rate:.3f} FPS; timeline requires {expected_fps:.3f} FPS.",
            )
        )
    expected_width = int(video_rules["width"])
    expected_height = int(video_rules["height"])
    if width != expected_width or height != expected_height:
        issues.append(
            ValidationIssue(
                "warning",
                "RESOLUTION_MISMATCH",
                f"Source is {width}x{height}; timeline is {expected_width}x{expected_height}.",
            )
        )
    expected_pixel_format = video_rules.get("pixel_format")
    if expected_pixel_format and video.get("pix_fmt") != expected_pixel_format:
        issues.append(
            ValidationIssue(
                "warning",
                "PIXEL_FORMAT_MISMATCH",
                f"Source is {video.get('pix_fmt')}; timeline requires {expected_pixel_format}.",
            )
        )
    black_segments, frozen_segments = detect_black_and_frozen_segments(video_path)
    maximum_black = float(validation_rules["maximum_black_segment_seconds"])
    maximum_freeze = float(validation_rules["maximum_unplanned_freeze_seconds"])
    issues.extend(
        ValidationIssue(
            "blocking",
            "UNEXPECTED_BLACK_SEGMENT",
            f"Detected a {duration_value:.2f}s black segment.",
        )
        for duration_value in black_segments
        if duration_value > maximum_black
    )
    issues.extend(
        ValidationIssue(
            "warning",
            "POSSIBLE_FROZEN_VIDEO",
            f"Detected a {duration_value:.2f}s low-motion or frozen segment.",
        )
        for duration_value in frozen_segments
        if duration_value > maximum_freeze
    )
    valid = not any(issue.severity == "blocking" for issue in issues)
    return FinalShotValidationReport(shot_id, valid, probe, issues)


def validate_approval(
    approval_path: Path, thresholds: dict[str, int]
) -> list[ValidationIssue]:
    if not approval_path.is_file():
        return [
            ValidationIssue(
                "blocking",
                "APPROVAL_MISSING",
                f"Approval file is missing: {approval_path}",
            )
        ]
    approval = load_json(approval_path)
    issues: list[ValidationIssue] = []
    if approval.get("status") != "approved" or approval.get("approved") is not True:
        issues.append(
            ValidationIssue(
                "blocking", "SHOT_NOT_APPROVED", "The shot has not been approved."
            )
        )
    scores = approval.get("scores", {})
    mapping = {
        "character_identity": "minimum_identity_score",
        "motion_quality": "minimum_motion_score",
        "location_consistency": "minimum_location_score",
        "audio_consistency": "minimum_audio_score",
        "lip_sync": "minimum_lip_sync_score",
    }
    for score_name, threshold_name in mapping.items():
        minimum = int(thresholds.get(threshold_name, 0))
        actual = scores.get(score_name) if isinstance(scores, dict) else None
        if actual is None:
            issues.append(
                ValidationIssue(
                    "blocking",
                    "APPROVAL_SCORE_MISSING",
                    f"Missing approval score: {score_name}.",
                )
            )
        elif isinstance(actual, bool) or not isinstance(actual, (int, float)):
            issues.append(
                ValidationIssue(
                    "blocking",
                    "APPROVAL_SCORE_INVALID",
                    f"Approval score {score_name} is not numeric.",
                )
            )
        elif actual < minimum:
            issues.append(
                ValidationIssue(
                    "blocking",
                    "APPROVAL_SCORE_TOO_LOW",
                    f"{score_name} scored {actual}; minimum is {minimum}.",
                )
            )
    return issues


def write_validation_report(
    report: FinalShotValidationReport, destination: Path
) -> None:
    atomic_write_json(destination, asdict(report))


def record_render_approval(
    *,
    render_directory: Path | str,
    reviewer: str,
    scores: dict[str, int],
    continuity: dict[str, Any],
    review_notes: list[str] | None = None,
    project_root: Path | str = PROJECT_ROOT,
) -> dict[str, Any]:
    """Write one immutable creative approval beside a completed Wan render."""

    root = renders_root().resolve() if Path(project_root).resolve() == PROJECT_ROOT else (
        Path(project_root).resolve() / "renders"
    )
    directory = Path(render_directory).expanduser().resolve()
    try:
        directory.relative_to(root)
    except ValueError as error:
        raise GenerationPipelineError(
            f"Render directory is outside render storage: {directory}"
        ) from error
    if not reviewer.strip():
        raise GenerationPipelineError("Reviewer cannot be empty.")
    package = load_json(directory / "generation-package.json")
    result = load_json(directory / "render-result.json")
    if result.get("status") != "completed":
        raise GenerationPipelineError("Only a completed render can be approved.")
    for field in ("project_id", "scene_id", "shot_id", "package_hash"):
        if package.get(field) != result.get(field):
            raise GenerationPipelineError(
                f"Generation package and render result disagree on {field}."
            )
    if directory.name != result["package_hash"]:
        raise GenerationPipelineError(
            "Render directory name does not match the generation package hash."
        )
    normalized_scores: dict[str, int] = {}
    for name, value in scores.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise GenerationPipelineError(
                f"Approval score '{name}' must be an integer from 1 to 5."
            )
        normalized_scores[name] = value
    approval = {
        "project_id": result["project_id"],
        "scene_id": result["scene_id"],
        "shot_id": result["shot_id"],
        "package_hash": result["package_hash"],
        "status": "approved",
        "approved": True,
        "scores": normalized_scores,
        "continuity": continuity,
        "review_notes": review_notes or [],
        "approved_by": reviewer.strip(),
        "approved_version": 1,
        "approved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    approval["approval_hash"] = stable_hash(approval)
    approval_path = directory / "approval.json"
    if approval_path.exists():
        raise GenerationPipelineError(
            f"Render already has an approval decision: {approval_path}"
        )
    atomic_write_json(approval_path, approval)
    return approval
