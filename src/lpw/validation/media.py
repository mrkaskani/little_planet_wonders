"""Provide media services for the LPW cinematic pipeline."""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

from lpw.generation.pipeline import GenerationPipelineError


class MediaValidator:
    """Run deterministic FFprobe and FFmpeg checks for rendered media."""

    def run_checks(
        self,
        video_file: Path,
        project: dict[str, Any],
        shot: dict[str, Any],
        validation: dict[str, Any],
        rule_override: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Run checks.

        Args:
            video_file (Path): Path to the video file associated with the operation.
            project (dict[str, Any]): Project used by this operation.
            shot (dict[str, Any]): Shot used by this operation.
            validation (dict[str, Any]): Validation used by this operation.
            rule_override (dict[str, Any] | None): Rule override used by this operation.
                Defaults to ``None``.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        automatic = validation["automatic"]
        video_rules = automatic["video"]
        effective = dict(video_rules)
        if rule_override:
            effective.update(rule_override)
        effective.update(
            {
                key: value
                for key, value in validation.get("shots", {})
                .get(shot["id"], {})
                .items()
                if key in {"expected_duration_seconds", "audio_required"}
            }
        )

        probe = self._probe_media(video_file)
        video_stream = self._first_stream(probe, "video")
        audio_stream = self._first_stream(probe, "audio")
        audio_required = bool(
            effective.get(
                "audio_required", video_rules.get("require_audio_stream", True)
            )
        )
        checks = [
            self._check(
                "video-stream",
                video_stream is not None
                if video_rules.get("require_video_stream", True)
                else True,
                "video stream present",
                "present" if video_stream else "missing",
            ),
            self._check(
                "audio-stream",
                audio_stream is not None if audio_required else True,
                "audio stream present" if audio_required else "audio optional",
                "present" if audio_stream else "missing",
            ),
        ]

        if video_stream is not None:
            expected_width = int(effective.get("expected_width", project["video"]["width"]))
            expected_height = int(
                effective.get("expected_height", project["video"]["height"])
            )
            expected_fps = float(effective.get("expected_fps", project["video"]["fps"]))
            expected_duration = float(
                effective.get("expected_duration_seconds", shot["duration_seconds"])
            )
            actual_fps = self._parse_fraction(video_stream.get("avg_frame_rate", "0/1"))
            actual_duration = self._media_duration(probe, video_stream)
            checks.extend(
                [
                    self._check("width", int(video_stream.get("width", 0)) == expected_width, expected_width, int(video_stream.get("width", 0))),
                    self._check("height", int(video_stream.get("height", 0)) == expected_height, expected_height, int(video_stream.get("height", 0))),
                    self._check("fps", math.isclose(actual_fps, expected_fps, abs_tol=0.05), expected_fps, actual_fps),
                ]
            )
            pixel_format = video_rules.get("expected_pixel_format")
            if pixel_format:
                checks.append(
                    self._check(
                        "pixel-format",
                        video_stream.get("pix_fmt") == pixel_format,
                        pixel_format,
                        video_stream.get("pix_fmt"),
                    )
                )
            duration_tolerance = float(
                effective.get("duration_tolerance_seconds", 0.25)
            )
            checks.append(
                self._check(
                    "duration",
                    math.isclose(actual_duration, expected_duration, abs_tol=duration_tolerance),
                    {"seconds": expected_duration, "tolerance": duration_tolerance},
                    actual_duration,
                )
            )
            actual_frames = self._frame_count(video_stream, actual_duration, actual_fps)
            expected_frames = round(expected_duration * expected_fps)
            frame_tolerance = int(video_rules.get("frame_count_tolerance", 2))
            checks.append(
                self._check(
                    "frame-count",
                    abs(actual_frames - expected_frames) <= frame_tolerance,
                    {"frames": expected_frames, "tolerance": frame_tolerance},
                    actual_frames,
                )
            )

        if automatic.get("corruption", {}).get("enabled", True):
            checks.append(self._check_corruption(video_file))
        black_rules = automatic.get("black_frames", {})
        if black_rules.get("enabled", True):
            checks.append(self._check_black_frames(video_file, black_rules))
        audio_rules = automatic.get("audio", {})
        if audio_rules.get("enabled", True) and audio_stream is not None:
            checks.append(self._check_audio_peak(video_file, audio_rules))
        return checks

    @staticmethod
    def _execute(command: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute execute.

        Args:
            command (list[str]): Command used by this operation.

        Returns:
            subprocess.CompletedProcess[str]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        try:
            return subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError as error:
            raise GenerationPipelineError(
                f"Cannot execute '{command[0]}': {error}"
            ) from error

    def _probe_media(self, media_file: Path) -> dict[str, Any]:
        """Execute media.

        Args:
            media_file (Path): Media file used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        result = self._execute(
            ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(media_file)]
        )
        if result.returncode != 0:
            raise GenerationPipelineError(
                f"FFprobe failed for '{media_file}':\n{result.stderr}"
            )
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise GenerationPipelineError("FFprobe returned invalid JSON.") from error
        if not isinstance(value, dict):
            raise GenerationPipelineError("FFprobe JSON must be an object.")
        return value

    def _check_corruption(self, video_file: Path) -> dict[str, Any]:
        """Execute corruption.

        Args:
            video_file (Path): Path to the video file associated with the operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = self._execute(["ffmpeg", "-v", "error", "-i", str(video_file), "-f", "null", "-"])
        passed = result.returncode == 0 and not result.stderr.strip()
        return self._check("decode-corruption", passed, "no decoding errors", "none" if passed else result.stderr.strip())

    def _check_black_frames(self, video_file: Path, rules: dict[str, Any]) -> dict[str, Any]:
        """Execute black frames.

        Args:
            video_file (Path): Path to the video file associated with the operation.
            rules (dict[str, Any]): Rules used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        picture_ratio = float(rules.get("picture_black_ratio", 0.98))
        pixel_threshold = float(rules.get("pixel_black_threshold", 0.10))
        result = self._execute(
            ["ffmpeg", "-hide_banner", "-i", str(video_file), "-vf", f"blackdetect=d=0:pic_th={picture_ratio}:pix_th={pixel_threshold}", "-an", "-f", "null", "-"]
        )
        durations = [float(value) for value in re.findall(r"black_duration:([0-9.]+)", result.stderr)]
        maximum = max(durations, default=0.0)
        total = sum(durations)
        allowed_maximum = float(rules.get("maximum_single_black_duration_seconds", 0.20))
        allowed_total = float(rules.get("maximum_total_black_duration_seconds", 0.30))
        return self._check(
            "black-frames",
            result.returncode == 0 and maximum <= allowed_maximum and total <= allowed_total,
            {"maximum_single_seconds": allowed_maximum, "maximum_total_seconds": allowed_total},
            {"maximum_single_seconds": maximum, "total_seconds": total, "segments": durations},
        )

    def _check_audio_peak(self, video_file: Path, rules: dict[str, Any]) -> dict[str, Any]:
        """Execute audio peak.

        Args:
            video_file (Path): Path to the video file associated with the operation.
            rules (dict[str, Any]): Rules used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = self._execute(["ffmpeg", "-hide_banner", "-i", str(video_file), "-vn", "-af", "volumedetect", "-f", "null", "-"])
        match = re.search(r"max_volume:\s*(-?inf|-?[0-9.]+)\s*dB", result.stderr)
        if match is None:
            return self._check("audio-peak", False, "measurable audio peak", "not detected")
        peak = float("-inf") if match.group(1) == "-inf" else float(match.group(1))
        minimum = float(rules.get("minimum_peak_dbfs", -45.0))
        maximum = float(rules.get("maximum_peak_dbfs", -1.0))
        silent = math.isinf(peak)
        passed = not (silent and rules.get("fail_when_silent", True)) and minimum <= peak <= maximum
        return self._check("audio-peak", passed, {"minimum_dbfs": minimum, "maximum_dbfs": maximum}, "-inf" if silent else peak)

    @staticmethod
    def _check(check_id: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
        """Execute check.

        Args:
            check_id (str): Check id used by this operation.
            passed (bool): Passed used by this operation.
            expected (Any): Expected used by this operation.
            actual (Any): Actual used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        return {"id": check_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual, "message": "Validation passed." if passed else "Validation failed."}

    @staticmethod
    def _first_stream(probe: dict[str, Any], codec_type: str) -> dict[str, Any] | None:
        """Execute stream.

        Args:
            probe (dict[str, Any]): Probe used by this operation.
            codec_type (str): Codec type used by this operation.

        Returns:
            dict[str, Any] | None: Result produced by the operation.
        """
        return next((stream for stream in probe.get("streams", []) if stream.get("codec_type") == codec_type), None)

    @staticmethod
    def _media_duration(probe: dict[str, Any], video_stream: dict[str, Any]) -> float:
        """Execute duration.

        Args:
            probe (dict[str, Any]): Probe used by this operation.
            video_stream (dict[str, Any]): Video stream used by this operation.

        Returns:
            float: Result produced by the operation.
        """
        value = video_stream.get("duration")
        if value in {None, "N/A"}:
            value = probe.get("format", {}).get("duration")
        return 0.0 if value in {None, "N/A"} else float(value)

    @staticmethod
    def _frame_count(video_stream: dict[str, Any], duration: float, fps: float) -> int:
        """Execute count.

        Args:
            video_stream (dict[str, Any]): Video stream used by this operation.
            duration (float): Duration used by this operation.
            fps (float): Fps used by this operation.

        Returns:
            int: Result produced by the operation.
        """
        for field in ("nb_read_frames", "nb_frames"):
            value = video_stream.get(field)
            if value not in {None, "N/A"}:
                return int(value)
        return round(duration * fps)

    @staticmethod
    def _parse_fraction(value: str) -> float:
        """Parse fraction.

        Args:
            value (str): Value inspected or transformed by the helper.

        Returns:
            float: Result produced by the operation.
        """
        if "/" not in value:
            return float(value)
        numerator, denominator = (float(part) for part in value.split("/", 1))
        return 0.0 if denominator == 0 else numerator / denominator
