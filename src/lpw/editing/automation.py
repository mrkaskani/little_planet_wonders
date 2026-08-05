"""Provide automation services for the LPW cinematic pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.config import PROJECT_ROOT
from lpw.context.loader import get_project_directory, load_project_context
from lpw.editing.timeline import (
    SceneFinalizationService,
    concatenate_clips,
    normalize_clip,
)
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, load_json, load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier
from lpw.validation.finalization import validate_approval, validate_shot


REVIEW_NOTE_TYPES = {"trim", "audio", "color", "continuity", "visual", "subtitle"}
REVIEW_PRIORITIES = {"low", "medium", "high", "blocking"}
TIMECODE = re.compile(r"^\d{2}:\d{2}:\d{2}:\d{2}$")


class AutomatedEditingPipeline:
    """Controlled preparation, assisted editing, and post-edit orchestration."""

    def __init__(self, project_root: Path | str = PROJECT_ROOT) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            project_root (Path | str): Root directory containing project runtime data.
                Defaults to ``PROJECT_ROOT``.
        """
        self._project_root = Path(project_root).expanduser().resolve()
        self._edits_root = self._project_root / "edits"

    def prepare_automated_edit(
        self, project_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Prepare automated edit.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        project_id, scene_id = self._identifiers(project_id, scene_id)
        project_directory = get_project_directory(project_id)
        timeline = self._load_timeline(project_directory, project_id, scene_id)
        export = load_yaml(project_directory / "export.yaml")
        weights_context = load_yaml(project_directory / "take-selection.yaml")
        project_context = load_project_context(project_id)
        takes: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        for index, shot in enumerate(timeline["shots"]):
            video_path = self._resolve_project_path(shot["video_path"])
            technical = validate_shot(
                shot_id=shot["id"],
                video_path=video_path,
                video_rules=export["video"],
                validation_rules=export["validation"],
            )
            approval_path = video_path.parent / "approval.json"
            approval_issues = validate_approval(approval_path, export["approval"])
            approval = load_json(approval_path) if approval_path.is_file() else {}
            identity_issues = []
            for field, expected in (
                ("project_id", project_id),
                ("scene_id", scene_id),
                ("shot_id", shot["id"]),
                ("package_hash", shot["package_hash"]),
            ):
                if approval and approval.get(field) != expected:
                    identity_issues.append(
                        {
                            "shot_id": shot["id"],
                            "severity": "blocking",
                            "code": "APPROVAL_IDENTITY_MISMATCH",
                            "message": f"Approval {field} does not match prepared context.",
                        }
                    )
            issues = [*technical.issues, *approval_issues]
            warnings.extend(
                {
                    "shot_id": shot["id"],
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in issues
            )
            warnings.extend(identity_issues)
            generation_path = video_path.parent / "generation-package.json"
            generation = load_json(generation_path) if generation_path.is_file() else {}
            if not generation:
                warnings.append(
                    {
                        "shot_id": shot["id"],
                        "severity": "blocking",
                        "code": "GENERATION_METADATA_MISSING",
                        "message": f"Generation metadata is missing: {generation_path}",
                    }
                )
            elif generation.get("package_hash") != shot["package_hash"]:
                warnings.append(
                    {
                        "shot_id": shot["id"],
                        "severity": "blocking",
                        "code": "GENERATION_HASH_MISMATCH",
                        "message": "Generation package hash does not match the timeline.",
                    }
                )
            has_blocker = any(issue.severity == "blocking" for issue in issues) or bool(
                identity_issues
            ) or not generation or generation.get("package_hash") != shot["package_hash"]
            takes.append(
                {
                    "shot_id": shot["id"],
                    "take_id": f"take-{index + 1:02d}",
                    "source": str(video_path),
                    "source_in": float(shot["in_seconds"]),
                    "source_out": float(shot["out_seconds"]),
                    "package_hash": shot["package_hash"],
                    "context_hash": generation.get("context_hash"),
                    "scores": approval.get("scores", {}),
                    "weighted_score": self._weighted_score(
                        approval.get("scores", {}),
                        weights_context.get("take_selection_weights", {}),
                    ),
                    "continuity_start": generation.get("continuity_start", {}),
                    "continuity_end": approval.get("continuity", {}),
                    "technical_report": asdict(technical),
                    "valid": not has_blocker,
                    "analysis": {
                        "status": "not-run",
                        "reason": "External visual/audio analyzers are disabled.",
                    },
                }
            )

        audio_assets = {
            name: str(self._resolve_project_path(value))
            for name, value in timeline["audio"].items()
        }
        missing_audio = [
            name for name, value in audio_assets.items() if not Path(value).is_file()
        ]
        warnings.extend(
            {
                "shot_id": None,
                "severity": "blocking",
                "code": "AUDIO_ASSET_MISSING",
                "message": f"Required audio asset is missing: {name}",
            }
            for name in missing_audio
        )
        approved_takes = [take for take in takes if take["valid"]]
        expected_shots = {shot["id"] for shot in timeline["shots"]}
        prepared_shots = {take["shot_id"] for take in approved_takes}
        blockers = [item for item in warnings if item["severity"] == "blocking"]
        status = (
            "prepared"
            if not blockers and prepared_shots == expected_shots
            else "rejected"
        )
        version = self._next_version(
            self._edits_root / project_id / scene_id / "prepared", "v"
        )
        package = {
            "status": status,
            "project_id": project_id,
            "scene_id": scene_id,
            "package_version": version,
            "created_at_utc": self._now_iso(),
            "editorial_context": str(
                project_directory / "scenes" / scene_id / "edit-context.yaml"
            ),
            "approved_takes": approved_takes,
            "all_takes": takes,
            "audio_assets": audio_assets,
            "continuity_snapshot": project_context.get("continuity", {}),
            "warnings": warnings,
            "blocking_errors": blockers,
        }
        package["package_hash"] = stable_hash(package)
        directory = (
            self._edits_root
            / project_id
            / scene_id
            / "prepared"
            / f"v{version:03d}"
        )
        directory.mkdir(parents=True, exist_ok=False)
        atomic_write_json(directory / "prepared-package.json", package)
        return package

    def automate_scene_edit(
        self,
        project_id: str,
        scene_id: str,
        prepared_package_version: int,
    ) -> dict[str, Any]:
        """Execute scene edit.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            prepared_package_version (int): Version of the prepared editing package.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        project_id, scene_id = self._identifiers(project_id, scene_id)
        package = self.load_prepared_package(
            project_id, scene_id, prepared_package_version
        )
        if package.get("status") != "prepared":
            return {
                "status": "rejected",
                "errors": package.get("blocking_errors", []),
                "repair_suggestions": [
                    "Resolve blocking preparation issues and create a new package version."
                ],
            }
        project_directory = get_project_directory(project_id)
        editing_context = load_yaml(project_directory / "editing_style.yaml")
        automation_context = load_yaml(project_directory / "auto-editing.yaml")
        scene_context = load_yaml(
            project_directory / "scenes" / scene_id / "edit-context.yaml"
        )
        selected = self._select_best_takes(package["approved_takes"])
        preferred_order = scene_context.get("scene", {}).get("preferred_order", [])
        selected_by_shot = {take["shot_id"]: take for take in selected}
        ordered_ids = [shot_id for shot_id in preferred_order if shot_id in selected_by_shot]
        ordered_ids.extend(
            shot_id for shot_id in selected_by_shot if shot_id not in ordered_ids
        )
        timeline_start = 0.0
        video_events = []
        continuity_warnings = []
        previous: dict[str, Any] | None = None
        for index, shot_id in enumerate(ordered_ids, start=1):
            take = selected_by_shot[shot_id]
            duration = float(take["source_out"]) - float(take["source_in"])
            event = {
                "event_id": f"v{index:03d}",
                "shot_id": shot_id,
                "take_id": take["take_id"],
                "source": take["source"],
                "source_in": take["source_in"],
                "source_out": take["source_out"],
                "timeline_start": round(timeline_start, 3),
                "timeline_end": round(timeline_start + duration, 3),
                "transition_in": "none" if index == 1 else "hard_cut",
                "transition_out": "hard_cut",
                "package_hash": take["package_hash"],
            }
            if previous is not None:
                continuity_warnings.extend(
                    self._adjacency_warnings(previous, take)
                )
            video_events.append(event)
            previous = take
            timeline_start += duration
        edit_version = self._next_version(
            self._edits_root / project_id / scene_id, "v"
        )
        plan = {
            "project_id": project_id,
            "scene_id": scene_id,
            "edit_version": edit_version,
            "prepared_package_version": prepared_package_version,
            "created_at_utc": self._now_iso(),
            "timeline": {
                **editing_context["timeline"],
                "duration_seconds": round(timeline_start, 3),
            },
            "video_events": video_events,
            "audio_events": self._audio_events(package["audio_assets"], timeline_start),
            "continuity_warnings": continuity_warnings,
            "blocking_errors": [],
            "automation": automation_context["automation"],
        }
        plan["plan_hash"] = stable_hash(plan)
        directory = self._edits_root / project_id / scene_id / f"v{edit_version:03d}"
        directory.mkdir(parents=True, exist_ok=False)
        atomic_write_json(directory / "prepared-package.json", package)
        atomic_write_json(directory / "edit-plan.json", plan)
        preview = self._render_preview(plan, automation_context["preview"], directory)
        state = {
            "status": "awaiting-review",
            "project_id": project_id,
            "scene_id": scene_id,
            "edit_version": edit_version,
            "preview": str(preview),
            "plan_hash": plan["plan_hash"],
        }
        atomic_write_json(directory / "edit-state.json", state)
        return {
            "status": "awaiting-approval",
            "edit_plan": plan,
            "preview": str(preview),
            "warnings": continuity_warnings,
        }

    def approve_edit_preview(
        self,
        project_id: str,
        scene_id: str,
        edit_version: int,
        reviewer: str,
        notes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Approve edit preview.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            edit_version (int): Positive version number of the edit.
            reviewer (str): Human reviewer identity recorded with the decision.
            notes (list[dict[str, Any]] | None): Optional review or production notes.
                Defaults to ``None``.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        project_id, scene_id = self._identifiers(project_id, scene_id)
        if not reviewer.strip():
            raise GenerationPipelineError("Reviewer cannot be empty.")
        directory = self._edit_directory(project_id, scene_id, edit_version)
        plan = load_json(directory / "edit-plan.json")
        approval_path = directory / "approval.json"
        if approval_path.exists():
            raise GenerationPipelineError("Edit version already has an approval decision.")
        approval = {
            "status": "approved",
            "project_id": project_id,
            "scene_id": scene_id,
            "edit_version": edit_version,
            "plan_hash": plan["plan_hash"],
            "reviewer": reviewer.strip(),
            "review_notes": self._validate_review_notes(notes or []),
            "approved_at_utc": self._now_iso(),
        }
        approval["approval_hash"] = stable_hash(approval)
        atomic_write_json(approval_path, approval)
        state = load_json(directory / "edit-state.json")
        state.update(status="approved", approved_at_utc=approval["approved_at_utc"])
        atomic_write_json(directory / "edit-state.json", state)
        return approval

    def post_edit_scene(
        self,
        project_id: str,
        scene_id: str,
        approved_edit_version: int,
        review_notes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute edit scene.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            approved_edit_version (int): Version of the edit approved for post-
                production.
            review_notes (list[dict[str, Any]]): Structured or textual notes supplied by
                the reviewer.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        project_id, scene_id = self._identifiers(project_id, scene_id)
        directory = self._edit_directory(project_id, scene_id, approved_edit_version)
        approval = load_json(directory / "approval.json")
        if approval.get("status") != "approved":
            raise GenerationPipelineError("Post-editing requires an approved preview.")
        project_directory = get_project_directory(project_id)
        post_context = load_yaml(project_directory / "post-editing.yaml")
        notes = self._validate_review_notes(review_notes)
        patch = {
            "base_edit_version": approved_edit_version,
            "new_edit_version": approved_edit_version + 1,
            "created_at_utc": self._now_iso(),
            "review_notes": notes,
            "operations": [self._note_to_operation(note) for note in notes],
            "post_editing_context": post_context,
        }
        patch["patch_hash"] = stable_hash(patch)
        patch_path = directory / f"post-edit-patch-v{approved_edit_version + 1:03d}.json"
        if patch_path.exists():
            raise GenerationPipelineError(
                f"Post-edit patch already exists: {patch_path}"
            )
        atomic_write_json(patch_path, patch)
        if notes:
            return {
                "status": "changes-requested",
                "patch": patch,
                "message": (
                    "Review changes were compiled but not executed automatically; "
                    "visual repair and color operations require configured providers."
                ),
            }
        result = SceneFinalizationService(self._project_root).finalize_scene(
            project_id, scene_id, approved_edit_version
        )
        if result.get("status") != "completed":
            return {**result, "post_edit_patch": patch}
        archive = self._write_archive_manifest(
            project_id,
            scene_id,
            approved_edit_version,
            directory,
            result,
        )
        return {
            **result,
            "post_edit_patch": patch,
            "delivery_files": {"web": result["output"]},
            "archive": archive,
            "provider_status": {
                "visual_cleanup": "not-run",
                "color_match": "not-run",
                "subtitles": "not-run",
                "master_profile": "not-run",
            },
        }

    def load_prepared_package(
        self, project_id: str, scene_id: str, version: int
    ) -> dict[str, Any]:
        """Load prepared package.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            version (int): Positive version number of the stored artifact.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
        """
        if version < 1:
            raise ValueError("prepared_package_version must be at least 1.")
        return load_json(
            self._edits_root
            / project_id
            / scene_id
            / "prepared"
            / f"v{version:03d}"
            / "prepared-package.json"
        )

    def load_latest_prepared_package(
        self, project_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Load latest prepared package.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            FileNotFoundError: If inputs, context, state, or provider output are invalid.
        """
        directory = self._edits_root / project_id / scene_id / "prepared"
        version = self._next_version(directory, "v") - 1
        if version < 1:
            raise FileNotFoundError(
                f"No prepared package exists for {project_id}/{scene_id}."
            )
        return self.load_prepared_package(project_id, scene_id, version)

    def _render_preview(
        self,
        plan: dict[str, Any],
        preview_rules: dict[str, Any],
        directory: Path,
    ) -> Path:
        """Render preview.

        Args:
            plan (dict[str, Any]): Plan used by this operation.
            preview_rules (dict[str, Any]): Preview rules used by this operation.
            directory (Path): Directory used by this operation.

        Returns:
            Path: Result produced by the operation.
        """
        video_rules = {
            "width": preview_rules["width"],
            "height": preview_rules["height"],
            "frame_rate": plan["timeline"]["frame_rate"],
            "pixel_format": "yuv420p",
            "working_codec": preview_rules["codec"],
            "working_quality_crf": preview_rules["crf"],
        }
        clips = [
            normalize_clip(
                source=Path(event["source"]),
                destination=directory / "preview-clips" / f"{event['event_id']}.mp4",
                in_seconds=float(event["source_in"]),
                out_seconds=float(event["source_out"]),
                video_rules=video_rules,
            )
            for event in plan["video_events"]
        ]
        return concatenate_clips(clips, directory / "preview.mp4")

    @staticmethod
    def _select_best_takes(takes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Select best takes.

        Args:
            takes (list[dict[str, Any]]): Takes used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        selected: dict[str, dict[str, Any]] = {}
        for take in takes:
            current = selected.get(take["shot_id"])
            if current is None or take["weighted_score"] > current["weighted_score"]:
                selected[take["shot_id"]] = take
        return list(selected.values())

    @staticmethod
    def _weighted_score(scores: Any, weights: Any) -> float:
        """Execute score.

        Args:
            scores (Any): Named review scores used by approval thresholds.
            weights (Any): Weights used by this operation.

        Returns:
            float: Result produced by the operation.
        """
        if not isinstance(scores, dict) or not isinstance(weights, dict):
            return 0.0
        available = {
            name: float(weight)
            for name, weight in weights.items()
            if name in scores and isinstance(scores[name], (int, float))
        }
        total_weight = sum(available.values())
        if total_weight <= 0:
            return 0.0
        return round(
            sum(float(scores[name]) * weight for name, weight in available.items())
            / total_weight,
            4,
        )

    @staticmethod
    def _adjacency_warnings(
        previous: dict[str, Any], current: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute warnings.

        Args:
            previous (dict[str, Any]): Previous used by this operation.
            current (dict[str, Any]): Current used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        before = previous.get("continuity_end", {})
        after = current.get("continuity_start", {})
        warnings = []
        for key in before.keys() & after.keys():
            if before[key] != after[key]:
                warnings.append(
                    {
                        "from_shot": previous["shot_id"],
                        "to_shot": current["shot_id"],
                        "status": "warning",
                        "code": f"CONTINUITY_{key.upper()}_MISMATCH",
                        "message": f"{key}: {before[key]!r} -> {after[key]!r}",
                    }
                )
        return warnings

    @staticmethod
    def _audio_events(assets: dict[str, str], duration: float) -> list[dict[str, Any]]:
        """Execute events.

        Args:
            assets (dict[str, str]): Assets used by this operation.
            duration (float): Duration used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        event_types = {
            "dialogue_stem": "dialogue",
            "music_stem": "music",
            "ambience_stem": "ambience",
            "sound_effects_stem": "sound_effects",
        }
        return [
            {
                "event_id": f"a{index:03d}",
                "type": event_types[name],
                "source": source,
                "timeline_start": 0.0,
                "timeline_end": round(duration, 3),
                "gain_db": 0,
                "duck_under_dialogue": name == "music_stem",
            }
            for index, (name, source) in enumerate(assets.items(), start=1)
        ]

    @staticmethod
    def _note_to_operation(note: dict[str, Any]) -> dict[str, Any]:
        """Execute to operation.

        Args:
            note (dict[str, Any]): Note used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        return {
            "operation": f"review_{note['type']}",
            "note_id": note["id"],
            "timecode": note["timecode"],
            "instruction": note["instruction"],
            "execution": "provider-required",
        }

    @staticmethod
    def _validate_review_notes(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate review notes.

        Args:
            notes (list[dict[str, Any]]): Optional review or production notes.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(notes, list):
            raise GenerationPipelineError("Review notes must be a list.")
        normalized = []
        seen = set()
        for note in notes:
            if not isinstance(note, dict):
                raise GenerationPipelineError("Each review note must be an object.")
            note_id = note.get("id")
            if not isinstance(note_id, str) or not note_id or note_id in seen:
                raise GenerationPipelineError("Review note IDs must be unique strings.")
            seen.add(note_id)
            if not isinstance(note.get("timecode"), str) or not TIMECODE.fullmatch(
                note["timecode"]
            ):
                raise GenerationPipelineError(
                    f"Review note '{note_id}' requires HH:MM:SS:FF timecode."
                )
            if note.get("type") not in REVIEW_NOTE_TYPES:
                raise GenerationPipelineError(f"Review note '{note_id}' has invalid type.")
            if note.get("priority") not in REVIEW_PRIORITIES:
                raise GenerationPipelineError(
                    f"Review note '{note_id}' has invalid priority."
                )
            instruction = note.get("instruction")
            if not isinstance(instruction, str) or not instruction.strip():
                raise GenerationPipelineError(
                    f"Review note '{note_id}' requires an instruction."
                )
            normalized.append(dict(note))
        return normalized

    def _load_timeline(
        self, project_directory: Path, project_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Load timeline.

        Args:
            project_directory (Path): Project directory used by this operation.
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        timeline = load_yaml(
            project_directory / "scenes" / scene_id / "timeline.yaml"
        )
        scene = timeline.get("scene", {})
        if scene.get("id") != scene_id or scene.get("project_id") != project_id:
            raise GenerationPipelineError("Timeline identifiers do not match the request.")
        return timeline

    def _resolve_project_path(self, value: str) -> Path:
        """Resolve project path.

        Args:
            value (str): Value inspected or transformed by the helper.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        path = Path(value).expanduser()
        resolved = path.resolve() if path.is_absolute() else (
            self._project_root / path
        ).resolve()
        try:
            resolved.relative_to(self._project_root)
        except ValueError as error:
            raise GenerationPipelineError(
                f"Editing asset path escapes project root: {value}"
            ) from error
        return resolved

    def _edit_directory(self, project_id: str, scene_id: str, version: int) -> Path:
        """Execute directory.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            version (int): Positive version number of the stored artifact.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
            FileNotFoundError: If inputs, context, state, or provider output are invalid.
        """
        if version < 1:
            raise ValueError("edit_version must be at least 1.")
        directory = self._edits_root / project_id / scene_id / f"v{version:03d}"
        if not directory.is_dir():
            raise FileNotFoundError(f"Edit version does not exist: {directory}")
        return directory

    def _write_archive_manifest(
        self,
        project_id: str,
        scene_id: str,
        edit_version: int,
        edit_directory: Path,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute archive manifest.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.
            edit_version (int): Positive version number of the edit.
            edit_directory (Path): Edit directory used by this operation.
            result (dict[str, Any]): Result used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        archive_directory = (
            self._project_root
            / "archive"
            / project_id
            / scene_id
            / f"v{edit_version:03d}"
        )
        archive_directory.mkdir(parents=True, exist_ok=False)
        project_directory = get_project_directory(project_id)
        context_snapshot = {
            "project": load_project_context(project_id),
            "editing": load_yaml(project_directory / "editing_style.yaml"),
            "post_editing": load_yaml(project_directory / "post-editing.yaml"),
            "export": load_yaml(project_directory / "export.yaml"),
            "scene": load_yaml(
                project_directory / "scenes" / scene_id / "edit-context.yaml"
            ),
        }
        atomic_write_json(
            archive_directory / "context-snapshot.json", context_snapshot
        )
        files = {
            "master_video": Path(result["output"]),
            "edit_plan": edit_directory / "edit-plan.json",
            "approval_report": edit_directory / "approval.json",
            "post_edit_patch": (
                edit_directory
                / f"post-edit-patch-v{edit_version + 1:03d}.json"
            ),
        }
        manifest = {
            "project_id": project_id,
            "scene_id": scene_id,
            "edit_version": edit_version,
            "created_at_utc": self._now_iso(),
            "files": {
                name: {
                    "path": str(path.resolve()),
                    "sha256": self._hash_file(path),
                }
                for name, path in files.items()
                if path.is_file()
            },
            "context_snapshot": str(
                archive_directory / "context-snapshot.json"
            ),
        }
        manifest["archive_hash"] = stable_hash(manifest)
        atomic_write_json(archive_directory / "archive-manifest.json", manifest)
        return manifest

    @staticmethod
    def _hash_file(path: Path) -> str:
        """Execute file.

        Args:
            path (Path): Filesystem path read or written by the operation.

        Returns:
            str: Result produced by the operation.
        """
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _next_version(directory: Path, prefix: str) -> int:
        """Execute version.

        Args:
            directory (Path): Directory used by this operation.
            prefix (str): Prefix used by this operation.

        Returns:
            int: Result produced by the operation.
        """
        if not directory.is_dir():
            return 1
        values = [
            int(path.name.removeprefix(prefix))
            for path in directory.iterdir()
            if path.is_dir()
            and path.name.startswith(prefix)
            and path.name.removeprefix(prefix).isdigit()
        ]
        return max(values, default=0) + 1

    @staticmethod
    def _identifiers(project_id: str, scene_id: str) -> tuple[str, str]:
        """Execute identifiers.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            tuple[str, str]: Result produced by the operation.
        """
        return (
            validate_identifier(project_id, "project_id"),
            validate_identifier(scene_id, "scene_id"),
        )

    @staticmethod
    def _now_iso() -> str:
        """Execute iso.

        Returns:
            str: Result produced by the operation.
        """
        return datetime.now(timezone.utc).isoformat()
