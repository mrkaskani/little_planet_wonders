"""Provide pipeline services for the LPW cinematic pipeline."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.context.compiler import ContextCompiler
from lpw.context.defaults import (
    APPROVAL_FILE_NAME,
    ATTEMPT_METADATA_FILE_NAME,
    COMPILED_CONTEXT_SNAPSHOT_FILE_NAME,
    CONTEXT_SNAPSHOT_DIRECTORY_NAME,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_RENDERS_DIRECTORY_NAME,
    GENERATION_PACKAGE_FILE_NAME,
    RELEASE_MANIFEST_FILE_NAME,
    RELEASES_DIRECTORY_NAME,
    SUPPORTED_REVIEW_STATUSES,
    VALIDATION_REPORT_FILE_NAME,
    VALIDATION_RULES_SNAPSHOT_FILE_NAME,
)
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, load_json
from lpw.utils.identifiers import validate_identifier
from lpw.validation.media import MediaValidator


class RenderValidationPipeline:
    """Store, validate, review, and approve versioned render artifacts."""

    def __init__(
        self,
        project_root: Path | str,
        context_root: Path | str = DEFAULT_CONTEXT_ROOT,
        renders_root: Path | str | None = None,
        media_validator: MediaValidator | None = None,
    ) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            project_root (Path | str): Root directory containing project runtime data.
            context_root (Path | str): Root directory containing source context files.
                Defaults to ``DEFAULT_CONTEXT_ROOT``.
            renders_root (Path | str | None): Renders root used by this operation.
                Defaults to ``None``.
            media_validator (MediaValidator | None): Media validator used by this
                operation. Defaults to ``None``.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        self._project_root = Path(project_root).expanduser().resolve()
        if not self._project_root.is_dir():
            raise GenerationPipelineError(
                f"Project root is not a directory: {self._project_root}"
            )
        configured_root = (
            self._project_root / DEFAULT_RENDERS_DIRECTORY_NAME
            if renders_root is None
            else Path(renders_root).expanduser()
        )
        self._renders_root = configured_root.resolve()
        self._compiler = ContextCompiler(context_root)
        self._media_validator = media_validator or MediaValidator()

    def create_attempt(
        self,
        story_id: str,
        scene_id: str,
        shot_id: str,
        video_file: Path | str,
        dialogue_file: Path | str | None = None,
    ) -> dict[str, Any]:
        """Create attempt.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            video_file (Path | str): Path to the video file associated with the
                operation.
            dialogue_file (Path | str | None): Dialogue file used by this operation.
                Defaults to ``None``.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        story_id = validate_identifier(story_id, "story_id")
        scene_id = validate_identifier(scene_id, "scene_id")
        shot_id = validate_identifier(shot_id, "shot_id")
        package = self._compiler.compile_validation_scene(story_id, scene_id)
        shot = self._find_shot(package["scene"], shot_id)
        source_video = self._require_file(video_file, "Generated video")
        source_dialogue = (
            self._require_file(dialogue_file, "Dialogue file")
            if dialogue_file is not None
            else None
        )

        attempt_number = self._next_number(
            self._renders_root / scene_id / shot_id, "attempt"
        )
        attempt_directory = (
            self._renders_root
            / scene_id
            / shot_id
            / f"attempt-{attempt_number:04d}"
        )
        attempt_directory.mkdir(parents=True, exist_ok=False)
        try:
            stored_video = attempt_directory / "video.mp4"
            shutil.copy2(source_video, stored_video)
            stored_dialogue: Path | None = None
            if source_dialogue is not None:
                stored_dialogue = attempt_directory / "dialogue.wav"
                shutil.copy2(source_dialogue, stored_dialogue)

            snapshot_directory = attempt_directory / CONTEXT_SNAPSHOT_DIRECTORY_NAME
            snapshot_directory.mkdir(exist_ok=False)
            context_hash = self._hash_json(package)
            self._write_new_json(
                snapshot_directory / COMPILED_CONTEXT_SNAPSHOT_FILE_NAME, package
            )
            self._write_new_json(
                snapshot_directory / VALIDATION_RULES_SNAPSHOT_FILE_NAME,
                package["validation"],
            )

            created_at = self._now_iso()
            generation_package = {
                "project_id": package["project"]["id"],
                "story_id": story_id,
                "scene_id": scene_id,
                "shot_id": shot_id,
                "context_hash": context_hash,
                "generation_attempt": attempt_number,
                "created_at_utc": created_at,
                "generation": shot["generation"],
                "camera": shot["camera"],
                "duration_seconds": shot["duration_seconds"],
                "characters": shot.get("characters", []),
                "props": shot.get("props", []),
                "continuity": package["continuity"]["shot_state"]["shots"][shot_id],
                "stored_video": stored_video.name,
                "stored_video_sha256": self._hash_file(stored_video),
                "stored_dialogue": stored_dialogue.name if stored_dialogue else None,
                "stored_dialogue_sha256": (
                    self._hash_file(stored_dialogue) if stored_dialogue else None
                ),
            }
            package_hash = self._hash_json(generation_package)
            generation_package["package_hash"] = package_hash
            self._write_new_json(
                attempt_directory / GENERATION_PACKAGE_FILE_NAME,
                generation_package,
            )

            metadata = {
                "project_id": package["project"]["id"],
                "story_id": story_id,
                "scene_id": scene_id,
                "shot_id": shot_id,
                "context_hash": context_hash,
                "package_hash": package_hash,
                "generation_attempt": attempt_number,
                "created_at_utc": created_at,
                "approved": False,
                "validation_status": "not-run",
                "attempt_directory": str(attempt_directory),
            }
            self._write_new_json(
                attempt_directory / ATTEMPT_METADATA_FILE_NAME, metadata
            )
            return metadata
        except Exception:
            shutil.rmtree(attempt_directory)
            raise

    def validate_attempt(self, attempt_directory: Path | str) -> dict[str, Any]:
        """Validate attempt.

        Args:
            attempt_directory (Path | str): Attempt directory used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        attempt_path = self._resolve_attempt(attempt_directory)
        self._verify_attempt_integrity(attempt_path)
        metadata = load_json(attempt_path / ATTEMPT_METADATA_FILE_NAME)
        snapshot = load_json(
            attempt_path
            / CONTEXT_SNAPSHOT_DIRECTORY_NAME
            / COMPILED_CONTEXT_SNAPSHOT_FILE_NAME
        )
        video_file = self._require_file(attempt_path / "video.mp4", "Attempt video")
        shot = self._find_shot(snapshot["scene"], metadata["shot_id"])
        checks = self._media_validator.run_checks(
            video_file, snapshot["project"], shot, snapshot["validation"]
        )
        statuses = {check["status"] for check in checks}
        automatic_status = (
            "fail" if "fail" in statuses else "warning" if "warning" in statuses else "pass"
        )
        report = {
            "project_id": metadata["project_id"],
            "story_id": metadata["story_id"],
            "scene_id": metadata["scene_id"],
            "shot_id": metadata["shot_id"],
            "generation_attempt": metadata["generation_attempt"],
            "context_hash": metadata["context_hash"],
            "package_hash": metadata["package_hash"],
            "validated_at_utc": self._now_iso(),
            "automatic_status": automatic_status,
            "semantic_status": "pending",
            "approved": False,
            "automatic_checks": checks,
            "semantic_checks": self._build_semantic_checks(
                metadata["shot_id"], snapshot["validation"]
            ),
            "reviewers": [],
        }
        report["report_hash"] = self._hash_without_field(report, "report_hash")
        atomic_write_json(attempt_path / VALIDATION_REPORT_FILE_NAME, report)
        metadata["validation_status"] = automatic_status
        atomic_write_json(attempt_path / ATTEMPT_METADATA_FILE_NAME, metadata)
        return report

    def record_semantic_review(
        self,
        attempt_directory: Path | str,
        reviewer: str,
        results: dict[str, dict[str, str]],
    ) -> dict[str, Any]:
        """Record semantic review.

        Args:
            attempt_directory (Path | str): Attempt directory used by this operation.
            reviewer (str): Human reviewer identity recorded with the decision.
            results (dict[str, dict[str, str]]): Results used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        attempt_path = self._resolve_attempt(attempt_directory)
        self._verify_attempt_integrity(attempt_path)
        reviewer = self._require_text(reviewer, "Reviewer")
        report_path = attempt_path / VALIDATION_REPORT_FILE_NAME
        report = load_json(report_path)
        self._verify_embedded_hash(report, "report_hash", "Validation report")
        known = {check["id"] for check in report["semantic_checks"]}
        unknown = set(results) - known
        if unknown:
            raise GenerationPipelineError(
                "Semantic review contains unknown checks: "
                + ", ".join(sorted(unknown))
            )
        reviewed_at = self._now_iso()
        for check in report["semantic_checks"]:
            result = results.get(check["id"])
            if result is None:
                continue
            status = result.get("status")
            if status not in SUPPORTED_REVIEW_STATUSES:
                raise GenerationPipelineError(
                    f"Semantic check '{check['id']}' has invalid status '{status}'."
                )
            check.update(
                status=status,
                notes=result.get("notes", ""),
                reviewer=reviewer,
                reviewed_at_utc=reviewed_at,
            )
        statuses = {check["status"] for check in report["semantic_checks"]}
        report["semantic_status"] = (
            "fail" if "fail" in statuses else "pending" if "pending" in statuses else "pass"
        )
        report["reviewers"].append(
            {"reviewer": reviewer, "reviewed_at_utc": reviewed_at}
        )
        report["report_hash"] = self._hash_without_field(report, "report_hash")
        atomic_write_json(report_path, report)
        return report

    def approve_attempt(
        self,
        attempt_directory: Path | str,
        reviewer: str,
        notes: str = "",
        scores: dict[str, int] | None = None,
        continuity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Approve attempt.

        Args:
            attempt_directory (Path | str): Attempt directory used by this operation.
            reviewer (str): Human reviewer identity recorded with the decision.
            notes (str): Optional review or production notes. Defaults to ``''``.
            scores (dict[str, int] | None): Named review scores used by approval
                thresholds. Defaults to ``None``.
            continuity (dict[str, Any] | None): Continuity state approved for subsequent
                production. Defaults to ``None``.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        attempt_path = self._resolve_attempt(attempt_directory)
        self._verify_attempt_integrity(attempt_path)
        reviewer = self._require_text(reviewer, "Reviewer")
        report_path = attempt_path / VALIDATION_REPORT_FILE_NAME
        report = load_json(report_path)
        self._verify_embedded_hash(report, "report_hash", "Validation report")
        snapshot = load_json(
            attempt_path
            / CONTEXT_SNAPSHOT_DIRECTORY_NAME
            / COMPILED_CONTEXT_SNAPSHOT_FILE_NAME
        )
        self._assert_approvable(report, snapshot["validation"]["approval"])
        normalized_scores = self._validate_scores(scores or {})
        approved_at = self._now_iso()
        approval = {
            key: report[key]
            for key in (
                "project_id",
                "story_id",
                "scene_id",
                "shot_id",
                "generation_attempt",
                "context_hash",
                "package_hash",
            )
        }
        approval.update(
            approved=True,
            status="approved",
            approved_by=reviewer,
            approved_at_utc=approved_at,
            notes=notes,
            review_notes=[notes] if notes else [],
            scores=normalized_scores,
            continuity=continuity or {},
            approved_version=1,
        )
        approval["approval_hash"] = self._hash_json(approval)
        approval_path = attempt_path / APPROVAL_FILE_NAME
        if approval_path.exists():
            raise GenerationPipelineError(
                f"Attempt already has an approval decision: {approval_path}"
            )
        self._write_new_json(approval_path, approval)
        report.update(approved=True, approved_by=reviewer, approved_at_utc=approved_at)
        report["report_hash"] = self._hash_without_field(report, "report_hash")
        atomic_write_json(report_path, report)
        metadata_path = attempt_path / ATTEMPT_METADATA_FILE_NAME
        metadata = load_json(metadata_path)
        metadata.update(
            approved=True,
            validation_status="approved",
            approved_at_utc=approved_at,
        )
        atomic_write_json(metadata_path, metadata)
        return approval

    def reject_attempt(
        self,
        attempt_directory: Path | str,
        reviewer: str,
        reason: str,
    ) -> dict[str, Any]:
        """Reject attempt.

        Args:
            attempt_directory (Path | str): Attempt directory used by this operation.
            reviewer (str): Human reviewer identity recorded with the decision.
            reason (str): Reason used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        attempt_path = self._resolve_attempt(attempt_directory)
        self._verify_attempt_integrity(attempt_path)
        reviewer = self._require_text(reviewer, "Reviewer")
        reason = self._require_text(reason, "Rejection reason")
        metadata_path = attempt_path / ATTEMPT_METADATA_FILE_NAME
        metadata = load_json(metadata_path)
        rejection = {
            key: metadata[key]
            for key in (
                "project_id",
                "story_id",
                "scene_id",
                "shot_id",
                "generation_attempt",
            )
        }
        rejection.update(
            approved=False,
            rejected=True,
            rejected_by=reviewer,
            rejected_at_utc=self._now_iso(),
            reason=reason,
        )
        rejection["approval_hash"] = self._hash_json(rejection)
        decision_path = attempt_path / APPROVAL_FILE_NAME
        if decision_path.exists():
            raise GenerationPipelineError(
                f"Attempt already has an approval decision: {decision_path}"
            )
        self._write_new_json(decision_path, rejection)
        metadata.update(approved=False, validation_status="rejected")
        atomic_write_json(metadata_path, metadata)
        return rejection

    def create_scene_release(
        self, story_id: str, scene_id: str, final_video: Path | str
    ) -> dict[str, Any]:
        """Create scene release.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.
            final_video (Path | str): Final video used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        story_id = validate_identifier(story_id, "story_id")
        scene_id = validate_identifier(scene_id, "scene_id")
        package = self._compiler.compile_validation_scene(story_id, scene_id)
        approved_attempts = self._find_approved_scene_attempts(package["scene"])
        context_hash = self._hash_json(package)
        stale_shots = [
            item["shot_id"]
            for item in approved_attempts
            if item["context_hash"] != context_hash
        ]
        if stale_shots:
            raise GenerationPipelineError(
                "Scene release is blocked by stale approved context for shots: "
                + ", ".join(stale_shots)
            )
        source_video = self._require_file(final_video, "Final scene video")
        releases_root = self._renders_root / scene_id / RELEASES_DIRECTORY_NAME
        release_number = self._next_number(releases_root, "release")
        release_directory = releases_root / f"release-{release_number:04d}"
        release_directory.mkdir(parents=True, exist_ok=False)
        try:
            stored_video = release_directory / "video.mp4"
            shutil.copy2(source_video, stored_video)
            scene_rules = package["validation"].get("scene_rules", {})
            expected_duration = scene_rules.get(
                "expected_duration_seconds",
                package["scene"]["total_duration_seconds"],
            )
            checks = self._media_validator.run_checks(
                stored_video,
                package["project"],
                {"id": "final-scene", "duration_seconds": expected_duration},
                package["validation"],
                rule_override=scene_rules,
            )
            statuses = {check["status"] for check in checks}
            validation_status = (
                "fail" if "fail" in statuses else "warning" if "warning" in statuses else "pass"
            )
            report = {
                "project_id": package["project"]["id"],
                "story_id": story_id,
                "scene_id": scene_id,
                "release_number": release_number,
                "validated_at_utc": self._now_iso(),
                "automatic_status": validation_status,
                "automatic_checks": checks,
            }
            report["report_hash"] = self._hash_json(report)
            self._write_new_json(
                release_directory / VALIDATION_REPORT_FILE_NAME, report
            )
            manifest = {
                "project_id": package["project"]["id"],
                "story_id": story_id,
                "scene_id": scene_id,
                "release_number": release_number,
                "created_at_utc": self._now_iso(),
                "context_hash": context_hash,
                "approved": validation_status != "fail",
                "video_file": stored_video.name,
                "video_sha256": self._hash_file(stored_video),
                "approved_shot_attempts": approved_attempts,
                "validation_status": validation_status,
            }
            manifest["release_hash"] = self._hash_json(manifest)
            self._write_new_json(
                release_directory / RELEASE_MANIFEST_FILE_NAME, manifest
            )
            return manifest
        except Exception:
            shutil.rmtree(release_directory)
            raise

    def get_approved_scene_attempts(
        self, story_id: str, scene_id: str
    ) -> list[dict[str, Any]]:
        """Return the latest integrity-checked approval for every scene shot.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """

        package = self._compiler.compile_validation_scene(story_id, scene_id)
        return self._find_approved_scene_attempts(package["scene"])

    def _find_approved_scene_attempts(
        self, scene: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find approved scene attempts.

        Args:
            scene (dict[str, Any]): Scene used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        attempts = []
        for shot in scene["shots"]:
            approved = self._latest_approved_attempt(scene["id"], shot["id"])
            if approved is None:
                raise GenerationPipelineError(
                    f"Scene release is blocked because shot '{shot['id']}' has no approved attempt."
                )
            attempts.append(approved)
        return attempts

    def _latest_approved_attempt(
        self, scene_id: str, shot_id: str
    ) -> dict[str, Any] | None:
        """Execute approved attempt.

        Args:
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.

        Returns:
            dict[str, Any] | None: Result produced by the operation.
        """
        directory = self._renders_root / scene_id / shot_id
        if not directory.is_dir():
            return None
        for attempt in sorted(directory.glob("attempt-[0-9][0-9][0-9][0-9]"), reverse=True):
            decision_path = attempt / APPROVAL_FILE_NAME
            if not decision_path.is_file():
                continue
            decision = load_json(decision_path)
            if decision.get("approved") is True:
                self._verify_attempt_integrity(attempt)
                self._verify_embedded_hash(
                    decision, "approval_hash", "Approval decision"
                )
                return {
                    "shot_id": shot_id,
                    "attempt": decision["generation_attempt"],
                    "attempt_directory": str(attempt),
                    "context_hash": decision["context_hash"],
                    "package_hash": decision["package_hash"],
                    "approval_hash": decision["approval_hash"],
                    "video_path": str(attempt / "video.mp4"),
                    "approval_path": str(decision_path),
                }
        return None

    def _verify_attempt_integrity(self, attempt_path: Path) -> None:
        """Execute attempt integrity.

        Args:
            attempt_path (Path): Attempt path used by this operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        metadata = load_json(attempt_path / ATTEMPT_METADATA_FILE_NAME)
        snapshot = load_json(
            attempt_path
            / CONTEXT_SNAPSHOT_DIRECTORY_NAME
            / COMPILED_CONTEXT_SNAPSHOT_FILE_NAME
        )
        generation = load_json(attempt_path / GENERATION_PACKAGE_FILE_NAME)
        if self._hash_json(snapshot) != metadata.get("context_hash"):
            raise GenerationPipelineError(
                f"Attempt context snapshot hash mismatch: {attempt_path}"
            )
        self._verify_embedded_hash(
            generation, "package_hash", "Generation package"
        )
        if generation.get("package_hash") != metadata.get("package_hash"):
            raise GenerationPipelineError(
                f"Attempt package hash mismatch: {attempt_path}"
            )
        video = attempt_path / generation["stored_video"]
        if not video.is_file() or self._hash_file(video) != generation.get(
            "stored_video_sha256"
        ):
            raise GenerationPipelineError(
                f"Attempt video hash mismatch: {attempt_path}"
            )
        dialogue_name = generation.get("stored_dialogue")
        if dialogue_name:
            dialogue = attempt_path / dialogue_name
            if not dialogue.is_file() or self._hash_file(dialogue) != generation.get(
                "stored_dialogue_sha256"
            ):
                raise GenerationPipelineError(
                    f"Attempt dialogue hash mismatch: {attempt_path}"
                )

    @classmethod
    def _verify_embedded_hash(
        cls, value: dict[str, Any], field: str, label: str
    ) -> None:
        """Execute embedded hash.

        Args:
            value (dict[str, Any]): Value inspected or transformed by the helper.
            field (str): Field used by this operation.
            label (str): Label used by this operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        expected = value.get(field)
        actual = cls._hash_without_field(value, field)
        if not isinstance(expected, str) or expected != actual:
            raise GenerationPipelineError(f"{label} hash mismatch.")

    @staticmethod
    def _build_semantic_checks(
        shot_id: str, validation: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build semantic checks.

        Args:
            shot_id (str): Stable identifier of the shot being processed.
            validation (dict[str, Any]): Validation used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        check_ids: list[str] = []
        configured = [
            *validation["semantic"].get("required_checks", []),
            *validation.get("scene_rules", {}).get("required_semantic_checks", []),
            *validation.get("shots", {}).get(shot_id, {}).get("semantic_checks", []),
        ]
        for check_id in configured:
            if check_id not in check_ids:
                check_ids.append(check_id)
        return [
            {
                "id": check_id,
                "status": "pending",
                "notes": "",
                "reviewer": None,
                "reviewed_at_utc": None,
            }
            for check_id in check_ids
        ]

    @staticmethod
    def _assert_approvable(
        report: dict[str, Any], rules: dict[str, Any]
    ) -> None:
        """Execute approvable.

        Args:
            report (dict[str, Any]): Report used by this operation.
            rules (dict[str, Any]): Rules used by this operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        automatic = {check["status"] for check in report["automatic_checks"]}
        if rules.get("require_all_automatic_checks_to_pass", True) and "fail" in automatic:
            raise GenerationPipelineError(
                "Attempt cannot be approved because an automatic check failed."
            )
        if not rules.get("allow_automatic_warnings", True) and "warning" in automatic:
            raise GenerationPipelineError(
                "Attempt cannot be approved because automatic warnings are not allowed."
            )
        semantic = {check["status"] for check in report["semantic_checks"]}
        if rules.get("require_all_semantic_checks_to_pass", True) and semantic & {"fail", "pending"}:
            raise GenerationPipelineError(
                "Attempt cannot be approved until all semantic checks pass."
            )
        reviewers = {item["reviewer"] for item in report.get("reviewers", [])}
        minimum = int(rules.get("minimum_reviewer_count", 1))
        if len(reviewers) < minimum:
            raise GenerationPipelineError(
                f"Attempt requires at least {minimum} reviewer(s)."
            )

    def _resolve_attempt(self, value: Path | str) -> Path:
        """Resolve attempt.

        Args:
            value (Path | str): Value inspected or transformed by the helper.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        path = Path(value).expanduser().resolve()
        try:
            path.relative_to(self._renders_root)
        except ValueError as error:
            raise GenerationPipelineError(
                f"Attempt directory is outside the renders root: {path}"
            ) from error
        if not path.is_dir() or not path.name.startswith("attempt-"):
            raise GenerationPipelineError(f"Invalid attempt directory: {path}")
        return path

    @staticmethod
    def _validate_scores(scores: dict[str, int]) -> dict[str, int]:
        """Validate scores.

        Args:
            scores (dict[str, int]): Named review scores used by approval thresholds.

        Returns:
            dict[str, int]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(scores, dict):
            raise GenerationPipelineError("Approval scores must be an object.")
        normalized: dict[str, int] = {}
        for score_name, value in scores.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= 5
            ):
                raise GenerationPipelineError(
                    f"Approval score '{score_name}' must be an integer from 1 to 5."
                )
            normalized[score_name] = value
        return normalized

    @staticmethod
    def _next_number(directory: Path, prefix: str) -> int:
        """Execute number.

        Args:
            directory (Path): Directory used by this operation.
            prefix (str): Prefix used by this operation.

        Returns:
            int: Result produced by the operation.
        """
        if not directory.is_dir():
            return 1
        numbers = [
            int(path.name.removeprefix(f"{prefix}-"))
            for path in directory.iterdir()
            if path.is_dir()
            and path.name.startswith(f"{prefix}-")
            and path.name.removeprefix(f"{prefix}-").isdigit()
        ]
        return max(numbers, default=0) + 1

    @staticmethod
    def _find_shot(scene: dict[str, Any], shot_id: str) -> dict[str, Any]:
        """Find shot.

        Args:
            scene (dict[str, Any]): Scene used by this operation.
            shot_id (str): Stable identifier of the shot being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        for shot in scene["shots"]:
            if shot["id"] == shot_id:
                return shot
        raise GenerationPipelineError(
            f"Scene '{scene['id']}' does not contain shot '{shot_id}'."
        )

    @staticmethod
    def _require_file(value: Path | str, label: str) -> Path:
        """Execute file.

        Args:
            value (Path | str): Value inspected or transformed by the helper.
            label (str): Label used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise GenerationPipelineError(f"{label} does not exist: {path}")
        return path

    @staticmethod
    def _require_text(value: str, label: str) -> str:
        """Execute text.

        Args:
            value (str): Value inspected or transformed by the helper.
            label (str): Label used by this operation.

        Returns:
            str: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(value, str) or not value.strip():
            raise GenerationPipelineError(f"{label} cannot be empty.")
        return value.strip()

    @staticmethod
    def _write_new_json(path: Path, value: Any) -> None:
        """Execute new json.

        Args:
            path (Path): Filesystem path read or written by the operation.
            value (Any): Value inspected or transformed by the helper.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if path.exists():
            raise GenerationPipelineError(f"Immutable file already exists: {path}")
        atomic_write_json(path, value)

    @staticmethod
    def _hash_json(value: Any) -> str:
        """Execute json.

        Args:
            value (Any): Value inspected or transformed by the helper.

        Returns:
            str: Result produced by the operation.
        """
        canonical = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @classmethod
    def _hash_without_field(cls, value: dict[str, Any], field: str) -> str:
        """Execute without field.

        Args:
            value (dict[str, Any]): Value inspected or transformed by the helper.
            field (str): Field used by this operation.

        Returns:
            str: Result produced by the operation.
        """
        return cls._hash_json({key: item for key, item in value.items() if key != field})

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
    def _now_iso() -> str:
        """Execute iso.

        Returns:
            str: Result produced by the operation.
        """
        return datetime.now(timezone.utc).isoformat()
