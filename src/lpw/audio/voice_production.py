"""Provide voice production services for the LPW cinematic pipeline."""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.audio.compiler import resolved_audio_context, resolved_voice_context
from lpw.config import runtime_root
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, load_json
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier


VOICE_REVIEW_FIELDS = {
    "identity",
    "dialogue_accuracy",
    "emotional_safety",
    "listening_comfort",
}


class VoiceProductionService:
    """Prepare, approve, and lock exact dialogue without generating audio."""

    def __init__(self, state_root: Path | str | None = None) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            state_root (Path | str | None): Root directory used for generated runtime
                state. Defaults to ``None``.
        """
        self._state_root = Path(state_root or runtime_root()).resolve()

    def prepare_exact_dialogue(
        self,
        *,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
        exact_dialogue: str,
        language: str,
        primary_emotion: str,
        ending_emotion: str | None = None,
        emotional_intensity: float = 0.4,
        speaking_speed: str = "slow-to-moderate",
        important_words: list[str] | None = None,
        pronunciation_notes: list[str] | None = None,
        pause_instructions: list[str] | None = None,
        audience_response_pause_seconds: float = 0,
        gesture_guidance: str | None = None,
        facial_expression_guidance: str | None = None,
    ) -> dict[str, Any]:
        """Prepare exact dialogue.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.
            exact_dialogue (str): Exact approved words that must be spoken once.
            language (str): Language used for dialogue and pronunciation rules.
            primary_emotion (str): Primary emotional direction for the performance.
            ending_emotion (str | None): Emotional direction at the end of the line.
                Defaults to ``None``.
            emotional_intensity (float): Child-safe normalized emotional intensity.
                Defaults to ``0.4``.
            speaking_speed (str): Speaking speed used by this operation. Defaults to
                ``'slow-to-moderate'``.
            important_words (list[str] | None): Important words used by this operation.
                Defaults to ``None``.
            pronunciation_notes (list[str] | None): Pronunciation notes used by this
                operation. Defaults to ``None``.
            pause_instructions (list[str] | None): Pause instructions used by this
                operation. Defaults to ``None``.
            audience_response_pause_seconds (float): Audience response pause seconds
                used by this operation. Defaults to ``0``.
            gesture_guidance (str | None): Gesture guidance used by this operation.
                Defaults to ``None``.
            facial_expression_guidance (str | None): Facial expression guidance used by
                this operation. Defaults to ``None``.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
        """
        identifiers = self._identifiers(
            project_id, episode_id, scene_id, shot_id, character_id
        )
        project_id, episode_id, scene_id, shot_id, character_id = identifiers
        exact_dialogue = exact_dialogue.strip()
        if not exact_dialogue:
            raise ValueError("exact_dialogue cannot be empty.")
        if not 0 <= emotional_intensity <= 0.6:
            raise ValueError(
                "emotional_intensity must be between 0 and 0.6 for this audience."
            )
        if audience_response_pause_seconds and not (
            3 <= audience_response_pause_seconds <= 5
        ):
            raise ValueError("Audience-response pauses must be 3 to 5 seconds.")
        voice = resolved_voice_context(project_id, character_id)
        audio = resolved_audio_context(project_id)
        reference = self._select_reference(voice, primary_emotion)
        version = self._next_version(
            project_id, episode_id, scene_id, shot_id, character_id
        )
        directory = self._dialogue_directory(
            project_id, episode_id, scene_id, shot_id, character_id, version
        )
        directory.mkdir(parents=True, exist_ok=False)
        filename = (
            f"{episode_id}_{scene_id}_{shot_id}_{character_id}_final.wav"
        )
        package = {
            "status": "awaiting-generation",
            "dialogue_version": version,
            "project_id": project_id,
            "episode_id": episode_id,
            "scene_id": scene_id,
            "shot_id": shot_id,
            "character_id": character_id,
            "exact_dialogue": exact_dialogue,
            "exact_dialogue_hash": stable_hash(exact_dialogue),
            "language": language,
            "primary_emotion": primary_emotion,
            "ending_emotion": ending_emotion or primary_emotion,
            "emotional_intensity": emotional_intensity,
            "speaking_speed": speaking_speed,
            "important_words": important_words or [],
            "pronunciation_notes": pronunciation_notes or [],
            "pronunciation_dictionary": audio["pronunciation"],
            "pause_instructions": pause_instructions or [],
            "audience_response_pause_seconds": audience_response_pause_seconds,
            "gesture_guidance": gesture_guidance,
            "facial_expression_guidance": facial_expression_guidance,
            "voice_id": voice.get("generation", {}).get("voice_id"),
            "voice_identity": voice["voice_identity"],
            "primary_emotional_reference": reference,
            "clean_audio_only": True,
            "expected_filename": filename,
            "provider": {
                "status": "not-run",
                "reason": "An externally managed voice service must render exact dialogue.",
            },
            "constraints": [
                *voice.get("consistency_constraints", []),
                "speak every approved word exactly once",
                "do not add music, ambience, Foley, or sound effects",
                "avoid shouting, panic, threatening delivery, and sudden loudness",
            ],
            "created_at_utc": self._now_iso(),
        }
        package["package_hash"] = stable_hash(package)
        atomic_write_json(directory / "dialogue-package.json", package)
        return package

    def lock_exact_dialogue(
        self,
        *,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
        dialogue_version: int,
        audio_path: str,
        verified_transcript: str,
        reviewer: str,
        review: dict[str, bool],
    ) -> dict[str, Any]:
        """Execute exact dialogue.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.
            dialogue_version (int): Positive version number of the dialogue package.
            audio_path (str): Path to the audio asset being processed.
            verified_transcript (str): Reviewed transcript expected to match the
                dialogue exactly.
            reviewer (str): Human reviewer identity recorded with the decision.
            review (dict[str, bool]): Required review checks and their pass/fail values.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
            FileNotFoundError: If inputs, context, state, or provider output are invalid.
        """
        identifiers = self._identifiers(
            project_id, episode_id, scene_id, shot_id, character_id
        )
        project_id, episode_id, scene_id, shot_id, character_id = identifiers
        if not reviewer.strip():
            raise ValueError("reviewer cannot be empty.")
        directory = self._dialogue_directory(
            project_id,
            episode_id,
            scene_id,
            shot_id,
            character_id,
            dialogue_version,
        )
        package = load_json(directory / "dialogue-package.json")
        if verified_transcript.strip() != package["exact_dialogue"]:
            raise GenerationPipelineError(
                "Verified transcript does not exactly match the approved dialogue."
            )
        missing = VOICE_REVIEW_FIELDS - review.keys()
        failed = [field for field in VOICE_REVIEW_FIELDS if not review.get(field)]
        if missing or failed:
            raise GenerationPipelineError(
                "Dialogue cannot be locked until every required review check passes."
            )
        source = Path(audio_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Dialogue audio was not found: {source}")
        if source.suffix.lower() != ".wav":
            raise ValueError("Locked clean dialogue must be a WAV file.")
        approval_path = directory / "approval.json"
        if approval_path.exists():
            raise GenerationPipelineError("Dialogue version already has a decision.")
        locked_audio = directory / package["expected_filename"]
        shutil.copy2(source, locked_audio)
        approval = {
            "status": "locked",
            "dialogue_version": dialogue_version,
            "package_hash": package["package_hash"],
            "exact_dialogue_hash": package["exact_dialogue_hash"],
            "audio_path": str(locked_audio),
            "audio_sha256": self._hash_file(locked_audio),
            "reviewer": reviewer.strip(),
            "review": review,
            "locked_at_utc": self._now_iso(),
        }
        approval["approval_hash"] = stable_hash(approval)
        atomic_write_json(approval_path, approval)
        return approval

    def compile_lip_sync_context(
        self,
        *,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
        dialogue_version: int,
    ) -> dict[str, Any]:
        """Compile lip sync context.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.
            dialogue_version (int): Positive version number of the dialogue package.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        project_id, episode_id, scene_id, shot_id, character_id = self._identifiers(
            project_id, episode_id, scene_id, shot_id, character_id
        )
        directory = self._dialogue_directory(
            project_id,
            episode_id,
            scene_id,
            shot_id,
            character_id,
            dialogue_version,
        )
        package = load_json(directory / "dialogue-package.json")
        approval = load_json(directory / "approval.json")
        audio_path = Path(approval["audio_path"])
        if approval.get("status") != "locked" or not audio_path.is_file():
            raise GenerationPipelineError("Lip sync requires locked dialogue audio.")
        return {
            "status": "ready-for-lip-sync",
            "project_id": project_id,
            "scene_id": scene_id,
            "shot_id": shot_id,
            "character_id": character_id,
            "exact_dialogue": package["exact_dialogue"],
            "locked_audio_path": str(audio_path),
            "locked_audio_sha256": approval["audio_sha256"],
            "voice_id": package["voice_id"],
            "emotion": {
                "primary": package["primary_emotion"],
                "ending": package["ending_emotion"],
                "intensity": package["emotional_intensity"],
            },
            "performance": {
                "gesture": package["gesture_guidance"],
                "facial_expression": package["facial_expression_guidance"],
                "audience_response_pause_seconds": package[
                    "audience_response_pause_seconds"
                ],
            },
            "audio_rule": "Use the locked clean dialogue exactly; do not remix it.",
            "generation_provider": {"status": "not-run"},
            "context_hash": stable_hash({"package": package, "approval": approval}),
        }

    @staticmethod
    def _select_reference(voice: dict[str, Any], emotion: str) -> str | None:
        """Select reference.

        Args:
            voice (dict[str, Any]): Voice used by this operation.
            emotion (str): Requested emotional delivery.

        Returns:
            str | None: Result produced by the operation.
        """
        references = voice.get("references", {})
        normalized = emotion.lower().replace("_", "-").replace(" ", "-")
        aliases = {
            "neutral": "neutral-friendly",
            "quiet-concern": "mild-concern",
            "concern": "mild-concern",
            "happy": "happy-gentle",
        }
        key = aliases.get(normalized, normalized)
        return references.get(key) or references.get("neutral-friendly") or references.get(
            "neutral"
        )

    def _next_version(
        self,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
    ) -> int:
        """Execute version.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.

        Returns:
            int: Result produced by the operation.
        """
        root = self._dialogue_root(
            project_id, episode_id, scene_id, shot_id, character_id
        )
        versions = [
            int(path.name[1:])
            for path in root.glob("v[0-9][0-9][0-9]")
            if path.is_dir()
        ] if root.is_dir() else []
        return max(versions, default=0) + 1

    def _dialogue_root(
        self,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
    ) -> Path:
        """Execute root.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.

        Returns:
            Path: Result produced by the operation.
        """
        return (
            self._state_root
            / "audio"
            / project_id
            / "episodes"
            / episode_id
            / "dialogue"
            / scene_id
            / f"{shot_id}-{character_id}"
        )

    def _dialogue_directory(
        self,
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
        version: int,
    ) -> Path:
        """Execute directory.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.
            version (int): Positive version number of the stored artifact.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
        """
        if version < 1:
            raise ValueError("dialogue_version must be at least 1.")
        return self._dialogue_root(
            project_id, episode_id, scene_id, shot_id, character_id
        ) / f"v{version:03d}"

    @staticmethod
    def _identifiers(
        project_id: str,
        episode_id: str,
        scene_id: str,
        shot_id: str,
        character_id: str,
    ) -> tuple[str, str, str, str, str]:
        """Execute identifiers.

        Args:
            project_id (str): Stable identifier of the project whose context is used.
            episode_id (str): Stable identifier of the episode being produced.
            scene_id (str): Stable identifier of the scene being processed.
            shot_id (str): Stable identifier of the shot being processed.
            character_id (str): Stable identifier of the character.

        Returns:
            tuple[str, str, str, str, str]: Result produced by the operation.
        """
        return (
            validate_identifier(project_id, "project_id"),
            validate_identifier(episode_id, "episode_id"),
            validate_identifier(scene_id, "scene_id"),
            validate_identifier(shot_id, "shot_id"),
            validate_identifier(character_id, "character_id"),
        )

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
