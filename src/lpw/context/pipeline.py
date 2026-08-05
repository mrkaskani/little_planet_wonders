"""Provide pipeline services for the LPW cinematic pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from lpw.context.compiler import ContextCompiler
from lpw.context.defaults import DEFAULT_CONTEXT_ROOT


class SceneContextPipeline:
    """Provide validated scene context to generation and MCP services."""

    def __init__(self, context_root: Path | str = DEFAULT_CONTEXT_ROOT) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            context_root (Path | str): Root directory containing source context files.
                Defaults to ``DEFAULT_CONTEXT_ROOT``.
        """
        self._compiler = ContextCompiler(context_root=context_root)

    def load_scene(self, story_id: str, scene_id: str) -> dict[str, Any]:
        """Load scene.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        return self._compiler.compile_scene(story_id=story_id, scene_id=scene_id)

    def get_scene_summary(self, story_id: str, scene_id: str) -> dict[str, Any]:
        """Return scene summary.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        context = self.load_scene(story_id=story_id, scene_id=scene_id)
        project = context["project"]
        story = context["story"]
        scene = context["scene"]
        return {
            "project_id": project["id"],
            "story_id": story["id"],
            "scene_id": scene["id"],
            "scene_title": scene["title"],
            "location": scene["location"],
            "shot_count": len(scene["shots"]),
            "prop_count": len(context["props"]),
            "wardrobe_characters": sorted(context["wardrobe"]),
            "total_duration_seconds": scene["total_duration_seconds"],
            "generation_modes": [
                shot["generation"]["mode"] for shot in scene["shots"]
            ],
        }

    def iter_shots(
        self, story_id: str, scene_id: str
    ) -> Iterator[dict[str, Any]]:
        """Iterate over shots.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Yields:
            Iterator[dict[str, Any]]: Result produced by the operation.
        """
        context = self.load_scene(story_id=story_id, scene_id=scene_id)
        shot_states = context["continuity"]["shot_state"]["shots"]
        for shot in context["scene"]["shots"]:
            yield {
                "shot": shot,
                "continuity": shot_states[shot["id"]],
            }

    def build_generation_plan(
        self, story_id: str, scene_id: str
    ) -> list[dict[str, Any]]:
        """Build generation plan.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        context = self.load_scene(story_id=story_id, scene_id=scene_id)
        props = context["props"]
        wardrobe = context["wardrobe"]
        shot_states = context["continuity"]["shot_state"]["shots"]
        plan: list[dict[str, Any]] = []

        for order, shot in enumerate(context["scene"]["shots"], start=1):
            generation = shot["generation"]
            dialogue = shot.get("dialogue")
            continuity = shot_states[shot["id"]]
            resolved_wardrobe = {
                character_id: wardrobe[character_id]
                for character_id in shot["characters"]
                if character_id in wardrobe
            }
            resolved_props = {
                prop_id: props[prop_id]
                for prop_id in shot["props"]
                if prop_id in props
            }
            plan.append(
                {
                    "order": order,
                    "shot_id": shot["id"],
                    "shot_type": shot["type"],
                    "duration_seconds": shot["duration_seconds"],
                    "generation_mode": generation["mode"],
                    "prompt": generation["prompt"],
                    "negative_prompt": generation.get("negative_prompt", ""),
                    "seed": generation.get("seed"),
                    "reference_image": generation.get("reference_image"),
                    "audio_file": generation.get("audio_file"),
                    "pose_video": generation.get("pose_video"),
                    "dialogue": (
                        dialogue["text"] if isinstance(dialogue, dict) else None
                    ),
                    "speaker": (
                        dialogue["speaker"] if isinstance(dialogue, dict) else None
                    ),
                    "camera": shot["camera"],
                    "transition": shot["transition"],
                    "wardrobe": resolved_wardrobe,
                    "props": resolved_props,
                    "continuity_before": continuity["before"],
                    "continuity_after": continuity["after"],
                }
            )
        return plan

    def get_scene_opening_state(
        self, story_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Return scene opening state.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        context = self.load_scene(story_id=story_id, scene_id=scene_id)
        return context["continuity"]["scene_state"]["opening"]

    def get_scene_expected_end_state(
        self, story_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Return scene expected end state.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        context = self.load_scene(story_id=story_id, scene_id=scene_id)
        return context["continuity"]["scene_state"]["expected_end"]
