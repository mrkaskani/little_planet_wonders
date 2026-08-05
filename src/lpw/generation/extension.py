from __future__ import annotations

import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.config import context_root, runtime_root
from lpw.context.chaining import ContextChainError, ContextChainResolver
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import atomic_write_json, atomic_write_yaml, load_json, load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier
from lpw.utils.mappings import deep_merge


class CinematicExtensionPipeline:
    """Plan and audit short chained segments without invoking model downloads."""

    def __init__(
        self,
        source_root: Path | str | None = None,
        state_root: Path | str | None = None,
    ) -> None:
        self._source_root = Path(source_root or context_root()).resolve()
        self._state_root = Path(state_root or runtime_root()).resolve()
        self._resolver = ContextChainResolver(self._source_root, self._state_root)

    def resolve_context_chain(
        self, project_id: str, scene_id: str, shot_id: str
    ) -> dict[str, Any]:
        uri = self._shot_uri(project_id, scene_id, shot_id)
        resolved = self._resolver.resolve(uri)
        return {
            "context": resolved.context,
            "context_chain": resolved.chain,
            "base_context_hash": resolved.context_hash,
        }

    def validate_context_chain(
        self, project_id: str, scene_id: str, shot_id: str
    ) -> dict[str, Any]:
        result = self.resolve_context_chain(project_id, scene_id, shot_id)
        return {
            "status": "valid",
            "base_context_hash": result["base_context_hash"],
            "context_count": len(result["context_chain"]),
            "pinned_versions": all(
                isinstance(item.get("version"), int)
                for item in result["context_chain"]
            ),
            "errors": [],
        }

    def extend_cinematic_shot(
        self,
        project_id: str,
        scene_id: str,
        shot_id: str,
        target_duration_seconds: float,
        segment_duration_seconds: float = 4.0,
    ) -> dict[str, Any]:
        project_id, scene_id, shot_id = self._identifiers(
            project_id, scene_id, shot_id
        )
        if target_duration_seconds <= 0:
            raise ValueError("target_duration_seconds must be greater than zero.")
        if segment_duration_seconds <= 0 or segment_duration_seconds > 6:
            raise ValueError(
                "segment_duration_seconds must be greater than zero and at most 6."
            )
        base = self.resolve_context_chain(project_id, scene_id, shot_id)
        version = self._next_version(project_id, scene_id, shot_id)
        directory = self._extension_directory(
            project_id, scene_id, shot_id, version
        )
        directory.mkdir(parents=True, exist_ok=False)
        count = math.ceil(target_duration_seconds / segment_duration_seconds)
        segments = []
        for index in range(count):
            start = index * segment_duration_seconds
            end = min(target_duration_seconds, (index + 1) * segment_duration_seconds)
            segment_id = f"{shot_id}-segment-{index + 1:03d}"
            manifest = self._segment_manifest(
                project_id=project_id,
                scene_id=scene_id,
                shot_id=shot_id,
                segment_id=segment_id,
                index=index,
                count=count,
                start=start,
                end=end,
            )
            segment_directory = directory / "segments" / segment_id
            segment_directory.mkdir(parents=True)
            atomic_write_yaml(segment_directory / "segment-context.yaml", manifest)
            segments.append(
                {
                    "segment_id": segment_id,
                    "index": index,
                    "start_seconds": start,
                    "end_seconds": end,
                    "status": "ready-for-generation" if index == 0 else "blocked",
                    "blocked_by": None if index == 0 else segments[-1]["segment_id"],
                }
            )

        first = self._compile_manifest(
            base=base,
            manifest=load_yaml(
                directory / "segments" / segments[0]["segment_id"] / "segment-context.yaml"
            ),
            directory=directory / "segments" / segments[0]["segment_id"],
            runtime_state={},
        )
        plan = {
            "status": "awaiting-segment-generation",
            "project_id": project_id,
            "scene_id": scene_id,
            "shot_id": shot_id,
            "extension_version": version,
            "target_duration_seconds": target_duration_seconds,
            "segment_duration_seconds": segment_duration_seconds,
            "base_context_hash": base["base_context_hash"],
            "segments": segments,
            "current_segment": segments[0]["segment_id"],
            "current_compiled_segment_hash": first["compiled_segment_hash"],
            "generation_provider": {
                "status": "not-run",
                "reason": "A configured external Wan service must generate the segment.",
            },
            "created_at_utc": self._now_iso(),
        }
        plan["plan_hash"] = stable_hash(plan)
        atomic_write_json(directory / "extension-plan.json", plan)
        return plan

    def compile_segment_context(
        self,
        project_id: str,
        scene_id: str,
        shot_id: str,
        extension_version: int,
        segment_id: str,
    ) -> dict[str, Any]:
        project_id, scene_id, shot_id = self._identifiers(
            project_id, scene_id, shot_id
        )
        segment_id = validate_identifier(segment_id, "segment_id")
        directory = self._extension_directory(
            project_id, scene_id, shot_id, extension_version
        )
        plan = load_json(directory / "extension-plan.json")
        entries = {item["segment_id"]: item for item in plan["segments"]}
        if segment_id not in entries:
            raise GenerationPipelineError(
                f"Segment '{segment_id}' is not part of extension v{extension_version:03d}."
            )
        entry = entries[segment_id]
        runtime_state: dict[str, Any] = {}
        if entry["blocked_by"]:
            previous_directory = directory / "segments" / entry["blocked_by"]
            approval_path = previous_directory / "approval.json"
            approval = load_json(approval_path) if approval_path.is_file() else {}
            if approval.get("status") != "approved":
                raise GenerationPipelineError(
                    f"Segment '{segment_id}' requires approved predecessor "
                    f"'{entry['blocked_by']}'."
                )
            runtime_state = load_yaml(previous_directory / "runtime-output-state.yaml")
        base = self.resolve_context_chain(project_id, scene_id, shot_id)
        segment_directory = directory / "segments" / segment_id
        previous = self._previous_segment(plan, segment_id)
        if previous:
            previous_frame = (
                directory / "segments" / previous / "approved-end-frame.png"
            )
            if not previous_frame.is_file():
                raise GenerationPipelineError(
                    f"Approved predecessor '{previous}' has no stable end frame."
                )
            shutil.copy2(previous_frame, segment_directory / "start-frame.png")
        manifest = load_yaml(segment_directory / "segment-context.yaml")
        result = self._compile_manifest(
            base=base,
            manifest=manifest,
            directory=segment_directory,
            runtime_state=runtime_state,
        )
        entry["status"] = "ready-for-generation"
        entry["blocked_by"] = None
        plan["current_segment"] = segment_id
        plan["current_compiled_segment_hash"] = result["compiled_segment_hash"]
        plan["plan_hash"] = stable_hash(
            {key: value for key, value in plan.items() if key != "plan_hash"}
        )
        atomic_write_json(directory / "extension-plan.json", plan)
        return result

    def approve_segment(
        self,
        project_id: str,
        scene_id: str,
        shot_id: str,
        extension_version: int,
        segment_id: str,
        generated_video_path: str,
        approved_end_frame_path: str,
        generated_frames: int,
        approved_end_frame: int,
        continuity_delta: dict[str, Any],
        analysis: dict[str, Any],
        reviewer: str,
    ) -> dict[str, Any]:
        project_id, scene_id, shot_id = self._identifiers(
            project_id, scene_id, shot_id
        )
        segment_id = validate_identifier(segment_id, "segment_id")
        if not reviewer.strip():
            raise ValueError("reviewer cannot be empty.")
        if analysis.get("blocking_errors"):
            raise GenerationPipelineError(
                "A segment with blocking analysis errors cannot be approved."
            )
        if not 0 <= approved_end_frame < generated_frames:
            raise ValueError("approved_end_frame must identify a generated frame.")
        source_video = Path(generated_video_path).expanduser().resolve()
        source_frame = Path(approved_end_frame_path).expanduser().resolve()
        if not source_video.is_file() or not source_frame.is_file():
            raise FileNotFoundError("Generated video and approved end frame must exist.")
        directory = self._extension_directory(
            project_id, scene_id, shot_id, extension_version
        )
        segment_directory = directory / "segments" / segment_id
        compiled = load_json(segment_directory / "compiled-context.json")
        approval_path = segment_directory / "approval.json"
        if approval_path.exists():
            raise GenerationPipelineError("Segment already has an approval decision.")
        video = segment_directory / "generated-video.mp4"
        end_frame = segment_directory / "approved-end-frame.png"
        shutil.copy2(source_video, video)
        shutil.copy2(source_frame, end_frame)
        analysis_document = {
            **analysis,
            "segment_id": segment_id,
            "generated_frames": generated_frames,
            "approved_end_frame": approved_end_frame,
            "approved_end_frame_path": str(end_frame),
            "rejected_tail_frames": generated_frames - approved_end_frame - 1,
        }
        atomic_write_json(segment_directory / "analysis.json", analysis_document)
        delta = {
            "id": f"{segment_id}-end-state",
            "type": "continuity-delta",
            "version": 1,
            "source": {
                "project_id": project_id,
                "scene_id": scene_id,
                "shot_id": shot_id,
                "segment_id": segment_id,
                "compiled_segment_hash": compiled["compiled_segment_hash"],
            },
            **continuity_delta,
        }
        input_state = load_yaml(segment_directory / "runtime-input-state.yaml")
        output_state = deep_merge(input_state, delta)
        delta["runtime_state_hash"] = stable_hash(output_state)
        atomic_write_yaml(segment_directory / "continuity-delta.yaml", delta)
        atomic_write_yaml(segment_directory / "runtime-output-state.yaml", output_state)
        time = compiled["context"].get("time", {})
        segment_number = int(segment_id.rsplit("-", 1)[1])
        edit_event = {
            "event_id": f"v-{shot_id}-{segment_number:03d}",
            "shot_id": shot_id,
            "segment_id": segment_id,
            "source": str(video),
            "source_in": 0.0,
            "source_out": float(time.get("end_seconds", 0))
            - float(time.get("start_seconds", 0)),
            "timeline_start": float(time.get("start_seconds", 0)),
            "timeline_end": float(time.get("end_seconds", 0)),
            "previous_event": (
                None
                if segment_number == 1
                else f"v-{shot_id}-{segment_number - 1:03d}"
            ),
            "transition_in": "none" if segment_number == 1 else "overlap-blend",
            "overlap_frames": 0 if segment_number == 1 else 4,
        }
        atomic_write_json(segment_directory / "edit-event.json", edit_event)
        approval = {
            "status": "approved",
            "segment_id": segment_id,
            "reviewer": reviewer.strip(),
            "compiled_segment_hash": compiled["compiled_segment_hash"],
            "runtime_state_hash": delta["runtime_state_hash"],
            "edit_event": edit_event,
            "generated_video": str(video),
            "approved_end_frame": str(end_frame),
            "approved_at_utc": self._now_iso(),
        }
        approval["approval_hash"] = stable_hash(approval)
        atomic_write_json(approval_path, approval)
        self._mark_approved(directory, segment_id)
        return approval

    def runtime_end_state(self, segment_id: str) -> dict[str, Any]:
        uri = f"cinema://runtime/{validate_identifier(segment_id, 'segment_id')}/end-state@1"
        resolved = self._resolver.resolve(uri)
        return {
            "state": resolved.context,
            "context_chain": resolved.chain,
            "runtime_state_hash": resolved.context_hash,
        }

    def _compile_manifest(
        self,
        *,
        base: dict[str, Any],
        manifest: dict[str, Any],
        directory: Path,
        runtime_state: dict[str, Any],
    ) -> dict[str, Any]:
        runtime_hash = stable_hash(runtime_state)
        document = {**manifest, "runtime_state": runtime_state}
        resolved = self._resolver.compile_document(
            document,
            source_uri=f"runtime-manifest://{manifest['id']}@{manifest['version']}",
        )
        snapshot = {
            "base_context_hash": base["base_context_hash"],
            "runtime_state_hash": runtime_hash,
            "compiled_segment_hash": resolved.context_hash,
            "context": resolved.context,
        }
        atomic_write_json(directory / "compiled-context.json", snapshot)
        atomic_write_json(directory / "context-chain.json", {"chain": resolved.chain})
        atomic_write_yaml(directory / "runtime-input-state.yaml", runtime_state)
        return snapshot

    def _segment_manifest(
        self,
        *,
        project_id: str,
        scene_id: str,
        shot_id: str,
        segment_id: str,
        index: int,
        count: int,
        start: float,
        end: float,
    ) -> dict[str, Any]:
        return {
            "id": segment_id,
            "type": "video-segment-context",
            "version": 1,
            "extends": [self._shot_uri(project_id, scene_id, shot_id)],
            "time": {"start_seconds": start, "end_seconds": end},
            "segment": {"index": index, "count": count},
            "camera": {
                "movement_progress": {
                    "start": round(index / count, 4),
                    "end": round((index + 1) / count, 4),
                }
            },
            "frame_chain": {
                "start_frame_source": (
                    "shot-reference" if index == 0 else "approved-predecessor-end-frame"
                ),
                "reject_unstable_tail_frames": True,
            },
            "audio_chain": {"continue_scene_timeline": True, "restart": False},
        }

    def _mark_approved(self, directory: Path, segment_id: str) -> None:
        plan = load_json(directory / "extension-plan.json")
        for entry in plan["segments"]:
            if entry["segment_id"] == segment_id:
                entry["status"] = "approved"
        approved = [item for item in plan["segments"] if item["status"] == "approved"]
        if len(approved) == len(plan["segments"]):
            plan["status"] = "ready-for-stitching"
            plan["current_segment"] = None
        else:
            next_entry = plan["segments"][len(approved)]
            plan["status"] = "awaiting-next-segment-compilation"
            plan["current_segment"] = next_entry["segment_id"]
        plan["plan_hash"] = stable_hash(
            {key: value for key, value in plan.items() if key != "plan_hash"}
        )
        atomic_write_json(directory / "extension-plan.json", plan)

    @staticmethod
    def _previous_segment(plan: dict[str, Any], segment_id: str) -> str | None:
        identifiers = [item["segment_id"] for item in plan["segments"]]
        index = identifiers.index(segment_id)
        return identifiers[index - 1] if index else None

    def _shot_uri(self, project_id: str, scene_id: str, shot_id: str) -> str:
        project_id, scene_id, shot_id = self._identifiers(
            project_id, scene_id, shot_id
        )
        shot_path = (
            self._source_root
            / "projects"
            / project_id
            / "scenes"
            / scene_id
            / "shots"
            / shot_id
            / "shot.yaml"
        )
        version = load_yaml(shot_path).get("version")
        if not isinstance(version, int):
            raise ContextChainError(f"Shot context must declare an integer version: {shot_path}")
        return (
            f"cinema://projects/{project_id}/scenes/{scene_id}/shots/"
            f"{shot_id}@{version}"
        )

    def _next_version(self, project_id: str, scene_id: str, shot_id: str) -> int:
        root = self._state_root / "extensions" / project_id / scene_id / shot_id
        versions = [
            int(path.name[1:])
            for path in root.glob("v[0-9][0-9][0-9]")
            if path.is_dir()
        ] if root.is_dir() else []
        return max(versions, default=0) + 1

    def _extension_directory(
        self, project_id: str, scene_id: str, shot_id: str, version: int
    ) -> Path:
        if version < 1:
            raise ValueError("extension_version must be at least 1.")
        return (
            self._state_root
            / "extensions"
            / project_id
            / scene_id
            / shot_id
            / f"v{version:03d}"
        )

    @staticmethod
    def _identifiers(
        project_id: str, scene_id: str, shot_id: str
    ) -> tuple[str, str, str]:
        return (
            validate_identifier(project_id, "project_id"),
            validate_identifier(scene_id, "scene_id"),
            validate_identifier(shot_id, "shot_id"),
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
