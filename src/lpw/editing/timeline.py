from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from lpw.config import PROJECT_ROOT
from lpw.context.loader import get_project_directory
from lpw.editing.state import commit_scene_continuity
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, load_json, load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier
from lpw.validation.finalization import (
    ValidationIssue,
    validate_approval,
    validate_shot,
)


def run_command(arguments: list[str]) -> None:
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
        raise GenerationPipelineError(
            f"Cannot execute '{arguments[0]}': {error}"
        ) from error
    if result.returncode != 0:
        raise GenerationPipelineError(
            f"Command failed:\n{' '.join(arguments)}\n\n{result.stderr}"
        )


def normalize_clip(
    *,
    source: Path,
    destination: Path,
    in_seconds: float,
    out_seconds: float,
    video_rules: dict[str, Any],
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    width = int(video_rules["width"])
    height = int(video_rules["height"])
    frame_rate = int(video_rules["frame_rate"])
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={frame_rate},format={video_rules['pixel_format']},setpts=PTS-STARTPTS"
    )
    run_command(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(in_seconds),
            "-to",
            str(out_seconds),
            "-i",
            str(source),
            "-an",
            "-vf",
            video_filter,
            "-c:v",
            str(video_rules["working_codec"]),
            "-preset",
            "medium",
            "-crf",
            str(video_rules["working_quality_crf"]),
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )
    return destination


def concatenate_clips(clip_paths: list[Path], output_path: Path) -> Path:
    if not clip_paths:
        raise ValueError("No clips were provided.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_path.parent / "concat-list.txt"
    lines = []
    for path in clip_paths:
        escaped = path.resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    concat_file.write_text("\n".join(lines), encoding="utf-8")
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]
    )
    return output_path


def mix_scene_audio(
    *,
    silent_video: Path,
    stems: dict[str, Path],
    output_path: Path,
    video_rules: dict[str, Any],
    audio_rules: dict[str, Any],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = int(audio_rules["sample_rate"])
    filter_graph = (
        f"[1:a]aresample={sample_rate},asetpts=PTS-STARTPTS,volume=1.0[dialogue];"
        f"[2:a]aresample={sample_rate},asetpts=PTS-STARTPTS,volume=0.75[music];"
        "[music][dialogue]sidechaincompress=threshold=0.025:ratio=8:"
        "attack=80:release=500[ducked_music];"
        f"[3:a]aresample={sample_rate},asetpts=PTS-STARTPTS,volume=0.65[ambience];"
        f"[4:a]aresample={sample_rate},asetpts=PTS-STARTPTS,volume=0.90[sfx];"
        "[dialogue][ducked_music][ambience][sfx]"
        "amix=inputs=4:duration=longest:normalize=0,"
        f"loudnorm=I={audio_rules['target_lufs']}:"
        f"LRA={audio_rules['loudness_range']}:"
        f"TP={audio_rules['maximum_true_peak_db']},"
        f"aresample={sample_rate}[mixed]"
    )
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(stems["dialogue_stem"]),
            "-i",
            str(stems["music_stem"]),
            "-i",
            str(stems["ambience_stem"]),
            "-i",
            str(stems["sound_effects_stem"]),
            "-filter_complex",
            filter_graph,
            "-map",
            "0:v:0",
            "-map",
            "[mixed]",
            "-c:v",
            str(video_rules["delivery_codec"]),
            "-preset",
            str(video_rules["delivery_preset"]),
            "-crf",
            str(video_rules["delivery_quality_crf"]),
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-ar",
            str(sample_rate),
            "-ac",
            str(audio_rules["channels"]),
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return output_path


class SceneFinalizationService:
    """Validate, assemble, release, then commit continuity for one scene."""

    def __init__(
        self,
        project_root: Path | str = PROJECT_ROOT,
    ) -> None:
        self._project_root = Path(project_root).expanduser().resolve()

    def finalize_scene(
        self,
        project_id: str,
        scene_id: str,
        edit_version: int = 1,
    ) -> dict[str, Any]:
        project_id = validate_identifier(project_id, "project_id")
        scene_id = validate_identifier(scene_id, "scene_id")
        if edit_version < 1:
            raise ValueError("edit_version must be at least 1.")
        project_directory = get_project_directory(project_id)
        timeline = load_yaml(
            project_directory / "scenes" / scene_id / "timeline.yaml"
        )
        export = load_yaml(project_directory / "export.yaml")
        self._validate_context(project_id, scene_id, timeline, export)
        reports: list[tuple[dict[str, Any], Any, list[ValidationIssue]]] = []
        all_issues: list[dict[str, Any]] = []
        for shot in timeline["shots"]:
            video_path = self._resolve_project_file(shot["video_path"])
            technical = validate_shot(
                shot_id=shot["id"],
                video_path=video_path,
                video_rules=export["video"],
                validation_rules=export["validation"],
            )
            creative = validate_approval(
                video_path.parent / "approval.json", export["approval"]
            )
            approval_path = video_path.parent / "approval.json"
            if approval_path.is_file():
                approval = load_json(approval_path)
                if approval.get("project_id") != project_id:
                    creative.append(
                        ValidationIssue(
                            "blocking",
                            "APPROVAL_PROJECT_MISMATCH",
                            f"Approval belongs to '{approval.get('project_id')}', not '{project_id}'.",
                        )
                    )
                if approval.get("package_hash") != shot["package_hash"]:
                    creative.append(
                        ValidationIssue(
                            "blocking",
                            "PACKAGE_HASH_MISMATCH",
                            f"Timeline and approval hashes differ for '{shot['id']}'.",
                        )
                    )
            duration = float(technical.probe.get("format", {}).get("duration", 0))
            if technical.probe and float(shot["out_seconds"]) > duration + 0.01:
                creative.append(
                    ValidationIssue(
                        "blocking",
                        "TRIM_OUT_OF_RANGE",
                        f"Shot '{shot['id']}' trim ends at {shot['out_seconds']}s, "
                        f"but source duration is {duration:.2f}s.",
                    )
                )
            reports.append((shot, technical, creative))
            all_issues.extend(
                {
                    "shot_id": shot["id"],
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in [*technical.issues, *creative]
            )

        stems = {
            name: self._resolve_project_file(value)
            for name, value in timeline["audio"].items()
        }
        for name, path in stems.items():
            if not path.is_file():
                all_issues.append(
                    {
                        "shot_id": None,
                        "severity": "blocking",
                        "code": "AUDIO_STEM_MISSING",
                        "message": f"Required {name} does not exist: {path}",
                    }
                )
        blockers = [
            issue for issue in all_issues if issue["severity"] == "blocking"
        ]
        if blockers:
            return {
                "status": "rejected",
                "scene_id": scene_id,
                "edit_version": edit_version,
                "blocking_errors": blockers,
                "all_issues": all_issues,
            }

        working_directory = (
            self._project_root
            / "renders"
            / project_id
            / scene_id
            / "edits"
            / f"v{edit_version:03d}"
        )
        working_directory.mkdir(parents=True, exist_ok=False)
        try:
            normalized = []
            for index, (shot, technical, creative) in enumerate(reports):
                atomic_write_json(
                    working_directory
                    / "validation"
                    / f"{index:03d}-{shot['id']}.json",
                    {
                        "technical": asdict(technical),
                        "creative_issues": [asdict(issue) for issue in creative],
                    },
                )
                normalized.append(
                    normalize_clip(
                        source=self._resolve_project_file(shot["video_path"]),
                        destination=working_directory
                        / "normalized"
                        / f"{index:03d}-{shot['id']}.mp4",
                        in_seconds=float(shot["in_seconds"]),
                        out_seconds=float(shot["out_seconds"]),
                        video_rules=export["video"],
                    )
                )
            silent_video = concatenate_clips(
                normalized, working_directory / "silent-scene.mp4"
            )
            filename_template = timeline["output"].get(
                "filename_template", f"{scene_id}-v{{edit_version:03d}}.mp4"
            )
            final_output = mix_scene_audio(
                silent_video=silent_video,
                stems=stems,
                output_path=working_directory
                / filename_template.format(edit_version=edit_version),
                video_rules=export["video"],
                audio_rules=export["audio"],
            )
            final_validation = validate_shot(
                shot_id="final-scene",
                video_path=final_output,
                video_rules=export["video"],
                validation_rules=export["validation"],
            )
            atomic_write_json(
                working_directory / "final-validation-report.json",
                asdict(final_validation),
            )
            final_blockers = [
                issue
                for issue in final_validation.issues
                if issue.severity == "blocking"
            ]
            if final_blockers:
                raise GenerationPipelineError(
                    "Final scene output failed technical validation: "
                    + ", ".join(issue.code for issue in final_blockers)
                )
            last_approval = load_json(
                self._resolve_project_file(timeline["shots"][-1]["video_path"])
                .parent
                / "approval.json"
            )
            continuity = commit_scene_continuity(
                project_id=project_id,
                scene_id=scene_id,
                edit_version=edit_version,
                last_shot_approval=last_approval,
                output_path=final_output,
            )
            result = {
                "status": "completed",
                "project_id": project_id,
                "scene_id": scene_id,
                "edit_version": edit_version,
                "output": str(final_output),
                "shot_count": len(normalized),
                "warnings": [
                    issue
                    for issue in all_issues
                    if issue["severity"] == "warning"
                ]
                + [
                    {
                        "shot_id": "final-scene",
                        "severity": issue.severity,
                        "code": issue.code,
                        "message": issue.message,
                    }
                    for issue in final_validation.issues
                    if issue.severity == "warning"
                ],
                "continuity": continuity,
            }
            result["release_hash"] = stable_hash(result)
            atomic_write_json(
                working_directory / "scene-export-result.json", result
            )
            return result
        except Exception:
            shutil.rmtree(working_directory)
            raise

    @staticmethod
    def _validate_context(
        project_id: str,
        scene_id: str,
        timeline: dict[str, Any],
        export: dict[str, Any],
    ) -> None:
        scene = timeline.get("scene")
        if not isinstance(scene, dict):
            raise GenerationPipelineError("Timeline requires a scene object.")
        if scene.get("id") != scene_id or scene.get("project_id") != project_id:
            raise GenerationPipelineError(
                "Timeline scene or project identifier does not match the request."
            )
        shots = timeline.get("shots")
        if not isinstance(shots, list) or not shots:
            raise GenerationPipelineError("Timeline requires a non-empty shots list.")
        seen: set[str] = set()
        for shot in shots:
            if not isinstance(shot, dict):
                raise GenerationPipelineError("Timeline shots must be objects.")
            shot_id = validate_identifier(shot.get("id"), "shot_id")
            if shot_id in seen:
                raise GenerationPipelineError(f"Duplicate timeline shot: {shot_id}")
            seen.add(shot_id)
            for field in ("package_hash", "video_path", "transition_after"):
                if not isinstance(shot.get(field), str) or not shot[field]:
                    raise GenerationPipelineError(
                        f"Timeline shot '{shot_id}' requires {field}."
                    )
            start = shot.get("in_seconds")
            end = shot.get("out_seconds")
            if (
                isinstance(start, bool)
                or isinstance(end, bool)
                or not isinstance(start, (int, float))
                or not isinstance(end, (int, float))
                or start < 0
                or end <= start
            ):
                raise GenerationPipelineError(
                    f"Timeline shot '{shot_id}' has an invalid trim range."
                )
            if shot["transition_after"] != "hard-cut":
                raise GenerationPipelineError(
                    "Only hard-cut transitions are supported by the finalizer."
                )
        for section in ("audio", "output"):
            if not isinstance(timeline.get(section), dict):
                raise GenerationPipelineError(f"Timeline requires {section} settings.")
        for section in ("video", "audio", "validation", "approval"):
            if not isinstance(export.get(section), dict):
                raise GenerationPipelineError(
                    f"Export context requires {section} settings."
                )

    def _resolve_project_file(self, value: str) -> Path:
        path = Path(value).expanduser()
        resolved = (
            path.resolve()
            if path.is_absolute()
            else (self._project_root / path).resolve()
        )
        try:
            resolved.relative_to(self._project_root)
        except ValueError as error:
            raise GenerationPipelineError(
                f"Timeline path escapes project root: {value}"
            ) from error
        return resolved
