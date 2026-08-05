"""Provide pipeline services for the LPW cinematic pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx2 as httpx

from lpw.context.compiler import ContextCompiler
from lpw.context.defaults import (
    DEFAULT_COMFYUI_POLL_INTERVAL_SECONDS,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
)


class GenerationPipelineError(Exception):
    """Raised when a configured generation or editing stage fails."""


class SceneGenerationPipeline:
    """Produce a complete scene from compiled YAML context and configured tools."""

    def __init__(
        self,
        project_root: Path | str,
        context_root: Path | str = DEFAULT_CONTEXT_ROOT,
    ) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            project_root (Path | str): Root directory containing project runtime data.
            context_root (Path | str): Root directory containing source context files.
                Defaults to ``DEFAULT_CONTEXT_ROOT``.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        self._project_root = Path(project_root).expanduser().resolve()
        if not self._project_root.is_dir():
            raise GenerationPipelineError(
                f"Project root is not a directory: {self._project_root}"
            )
        self._context_root = Path(context_root).expanduser().resolve()
        self._compiler = ContextCompiler(context_root=self._context_root)

    def produce_scene(
        self,
        story_id: str,
        scene_id: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Execute scene.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.
            dry_run (bool): Whether to plan without calling external providers. Defaults
                to ``True``.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        package = self._compiler.compile_production_scene(
            story_id=story_id,
            scene_id=scene_id,
            require_enabled_tools=not dry_run,
        )
        if dry_run:
            return self._build_dry_run_plan(package)

        production = package["production"]
        output_directory = self._resolve_project_path(
            production["output_directory"], require_within_project=True
        )
        output_directory.mkdir(parents=True, exist_ok=True)

        # Imported lazily to keep generation and render governance independent.
        from lpw.validation.pipeline import RenderValidationPipeline

        validation_pipeline = RenderValidationPipeline(
            project_root=self._project_root,
            context_root=self._context_root,
        )

        shot_results: list[dict[str, Any]] = []
        segments: list[Path] = []
        for shot in package["scene"]["shots"]:
            result = self._produce_shot(package, shot, output_directory)
            result["attempt"] = validation_pipeline.create_attempt(
                story_id=story_id,
                scene_id=scene_id,
                shot_id=shot["id"],
                video_file=result["normalized_segment"],
                dialogue_file=result["dialogue_audio"],
            )
            shot_results.append(result)
            segments.append(Path(result["normalized_segment"]))

        picture_track = self._concatenate_segments(
            package, segments, output_directory
        )
        audio_layers = self._produce_scene_audio(package, output_directory)
        final_video = self._mix_scene_audio(
            package, picture_track, audio_layers, output_directory
        )
        return {
            "project_id": package["project"]["id"],
            "story_id": story_id,
            "scene_id": scene_id,
            "shots": shot_results,
            "picture_track": str(picture_track),
            "audio_layers": audio_layers,
            "final_video": str(final_video),
        }

    def _produce_shot(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        scene_output_directory: Path,
    ) -> dict[str, Any]:
        """Execute shot.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            scene_output_directory (Path): Scene output directory used by this
                operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        shot_directory = scene_output_directory / shot["id"]
        shot_directory.mkdir(parents=True, exist_ok=True)
        resolved_shot = deepcopy(shot)

        dialogue_audio = self._resolve_dialogue_audio(
            package, resolved_shot, shot_directory
        )
        reference_image = self._resolve_reference_image(
            package, resolved_shot, shot_directory
        )
        if dialogue_audio is not None:
            resolved_shot["generation"]["audio_file"] = str(dialogue_audio)
        if reference_image is not None:
            resolved_shot["generation"]["reference_image"] = str(reference_image)

        generated_clip = self._generate_wan_clip(
            package, resolved_shot, shot_directory
        )
        generated_clip = self._apply_optional_lip_sync(
            package,
            resolved_shot,
            generated_clip,
            dialogue_audio,
            shot_directory,
        )
        normalized_segment = self._normalize_shot_segment(
            package,
            resolved_shot,
            generated_clip,
            dialogue_audio,
            shot_directory,
        )
        return {
            "shot_id": shot["id"],
            "generation_mode": resolved_shot["generation"]["mode"],
            "reference_image": str(reference_image) if reference_image else None,
            "dialogue_audio": str(dialogue_audio) if dialogue_audio else None,
            "generated_clip": str(generated_clip),
            "normalized_segment": str(normalized_segment),
        }

    def _resolve_dialogue_audio(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        shot_directory: Path,
    ) -> Path | None:
        """Resolve dialogue audio.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            shot_directory (Path): Shot directory used by this operation.

        Returns:
            Path | None: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        dialogue = shot.get("dialogue")
        if not isinstance(dialogue, dict):
            return None
        existing_path = shot["generation"].get("audio_file")
        if existing_path:
            resolved = self._resolve_project_path(existing_path)
            if resolved.is_file():
                return resolved

        stage = package["production"]["stages"]["dialogue"]
        if not stage.get("enabled") or not stage.get("generate_when_missing"):
            raise GenerationPipelineError(
                f"Dialogue audio is missing for '{shot['id']}' and generation is unavailable."
            )
        tool = self._get_tool(package, stage["tool"])
        target = shot_directory / "dialogue.wav"
        return self._invoke_output_tool(
            tool,
            {
                "text": dialogue["text"],
                "speaker": dialogue["speaker"],
                "language": dialogue.get("language", "fa"),
                "emotion": dialogue.get("emotion"),
                "delivery": dialogue.get("delivery"),
                "output_path": str(target),
            },
        )

    def _resolve_reference_image(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        shot_directory: Path,
    ) -> Path | None:
        """Resolve reference image.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            shot_directory (Path): Shot directory used by this operation.

        Returns:
            Path | None: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        mode = shot["generation"]["mode"]
        if mode == "t2v":
            return None
        existing_path = shot["generation"].get("reference_image")
        if existing_path:
            resolved = self._resolve_project_path(existing_path)
            if resolved.is_file():
                return resolved

        stage = package["production"]["stages"]["keyframes"]
        if not stage.get("enabled") or not stage.get("generate_when_missing"):
            raise GenerationPipelineError(
                f"Reference image is missing for '{shot['id']}' and generation is unavailable."
            )
        target = shot_directory / "reference.png"
        return self._invoke_output_tool(
            self._get_tool(package, stage["tool"]),
            {
                "shot_id": shot["id"],
                "prompt": shot["generation"]["prompt"],
                "negative_prompt": shot["generation"].get("negative_prompt", ""),
                "characters": shot.get("characters", []),
                "props": shot.get("props", []),
                "camera": shot["camera"],
                "continuity": self._get_shot_continuity(package, shot["id"]),
                "resolved_props": package["props"],
                "resolved_wardrobe": package["wardrobe"],
                "output_path": str(target),
            },
        )

    def _generate_wan_clip(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        shot_directory: Path,
    ) -> Path:
        """Generate wan clip.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            shot_directory (Path): Shot directory used by this operation.

        Returns:
            Path: Result produced by the operation.
        """
        stage = package["production"]["stages"]["video"]
        mode = shot["generation"]["mode"]
        workflow_id = stage["workflow_by_mode"][mode]
        video = package["project"]["video"]
        fps = int(video["fps"])
        values = {
            "prompt": shot["generation"]["prompt"],
            "negative_prompt": shot["generation"].get("negative_prompt", ""),
            "seed": shot["generation"].get("seed", 0),
            "reference_image": shot["generation"].get("reference_image"),
            "audio_file": shot["generation"].get("audio_file"),
            "pose_video": shot["generation"].get("pose_video"),
            "width": int(video["width"]),
            "height": int(video["height"]),
            "frame_count": self._calculate_frame_count(
                float(shot["duration_seconds"]), fps
            ),
            "fps": fps,
        }
        return self._invoke_comfyui(
            self._get_tool(package, stage["tool"]),
            package["workflows"][workflow_id],
            values,
            shot_directory,
        )

    def _apply_optional_lip_sync(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        generated_clip: Path,
        dialogue_audio: Path | None,
        shot_directory: Path,
    ) -> Path:
        """Apply optional lip sync.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            generated_clip (Path): Generated clip used by this operation.
            dialogue_audio (Path | None): Dialogue audio used by this operation.
            shot_directory (Path): Shot directory used by this operation.

        Returns:
            Path: Result produced by the operation.
        """
        stage = package["production"]["stages"].get("lip_sync", {})
        if (
            not stage.get("enabled")
            or dialogue_audio is None
            or shot["generation"]["mode"] not in stage.get("apply_to_modes", [])
        ):
            return generated_clip
        return self._invoke_output_tool(
            self._get_tool(package, stage["tool"]),
            {
                "video_file": str(generated_clip),
                "audio_file": str(dialogue_audio),
                "output_path": str(shot_directory / "lip-synced.mp4"),
            },
        )

    def _normalize_shot_segment(
        self,
        package: dict[str, Any],
        shot: dict[str, Any],
        video_file: Path,
        dialogue_audio: Path | None,
        shot_directory: Path,
    ) -> Path:
        """Normalize shot segment.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot (dict[str, Any]): Shot used by this operation.
            video_file (Path): Path to the video file associated with the operation.
            dialogue_audio (Path | None): Dialogue audio used by this operation.
            shot_directory (Path): Shot directory used by this operation.

        Returns:
            Path: Result produced by the operation.
        """
        stage = package["production"]["stages"]["editing"]
        settings = self._get_tool(package, stage["tool"])["settings"]
        target = shot_directory / "segment.mp4"
        duration = str(shot["duration_seconds"])
        command = [settings["executable"], "-y", "-i", str(video_file)]
        include_dialogue = stage.get("include_dialogue_audio", True)
        if dialogue_audio is not None and include_dialogue:
            command.extend(
                ["-i", str(dialogue_audio), "-map", "0:v:0", "-map", "1:a:0"]
            )
        else:
            command.extend(
                [
                    "-f",
                    "lavfi",
                    "-t",
                    duration,
                    "-i",
                    f"anullsrc=r={settings['audio_sample_rate']}:cl=stereo",
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                ]
            )
        command.extend(
            [
                "-t",
                duration,
                "-r",
                str(package["project"]["video"]["fps"]),
                "-c:v",
                settings["video_codec"],
                "-pix_fmt",
                settings["pixel_format"],
                "-c:a",
                settings["audio_codec"],
                "-ar",
                str(settings["audio_sample_rate"]),
                "-ac",
                str(settings["audio_channels"]),
                "-shortest",
                str(target),
            ]
        )
        self._run_command(command)
        return target

    def _concatenate_segments(
        self,
        package: dict[str, Any],
        segments: list[Path],
        output_directory: Path,
    ) -> Path:
        """Concatenate segments.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            segments (list[Path]): Segments used by this operation.
            output_directory (Path): Output directory used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not segments:
            raise GenerationPipelineError("Cannot concatenate an empty shot list.")
        stage = package["production"]["stages"]["editing"]
        executable = self._get_tool(package, stage["tool"])["settings"]["executable"]
        concat_file = output_directory / "segments.txt"
        concat_file.write_text(
            "\n".join(f"file '{self._escape_concat_path(path)}'" for path in segments),
            encoding="utf-8",
        )
        target = output_directory / "picture-track.mp4"
        self._run_command(
            [
                executable,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(target),
            ]
        )
        return target

    def _produce_scene_audio(
        self, package: dict[str, Any], output_directory: Path
    ) -> list[dict[str, Any]]:
        """Execute scene audio.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            output_directory (Path): Output directory used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        audio = package["production"].get("audio", {})
        layers: list[dict[str, Any]] = []
        ambience = audio.get("ambience")
        if isinstance(ambience, dict) and ambience.get("enabled"):
            layers.append(
                self._generate_audio_layer(package, ambience, "ambience", output_directory)
            )
        for effect in audio.get("sound_effects", []):
            if isinstance(effect, dict) and effect.get("enabled"):
                layers.append(
                    self._generate_audio_layer(
                        package, effect, effect["id"], output_directory
                    )
                )
        music = audio.get("music")
        if isinstance(music, dict) and music.get("enabled"):
            layers.append(
                self._generate_audio_layer(package, music, "music", output_directory)
            )
        return layers

    def _generate_audio_layer(
        self,
        package: dict[str, Any],
        layer: dict[str, Any],
        layer_id: str,
        output_directory: Path,
    ) -> dict[str, Any]:
        """Generate audio layer.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            layer (dict[str, Any]): Layer used by this operation.
            layer_id (str): Layer id used by this operation.
            output_directory (Path): Output directory used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        target = output_directory / f"{layer_id}.wav"
        generated = self._invoke_output_tool(
            self._get_tool(package, layer["tool"]),
            {
                "prompt": layer["prompt"],
                "duration_seconds": layer["duration_seconds"],
                "output_path": str(target),
            },
        )
        return {
            "id": layer_id,
            "path": str(generated),
            "start_seconds": float(layer.get("start_seconds", 0)),
            "volume": float(layer.get("volume", 1)),
        }

    def _mix_scene_audio(
        self,
        package: dict[str, Any],
        picture_track: Path,
        audio_layers: list[dict[str, Any]],
        output_directory: Path,
    ) -> Path:
        """Mix scene audio.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            picture_track (Path): Picture track used by this operation.
            audio_layers (list[dict[str, Any]]): Audio layers used by this operation.
            output_directory (Path): Output directory used by this operation.

        Returns:
            Path: Result produced by the operation.
        """
        stage = package["production"]["stages"]["editing"]
        settings = self._get_tool(package, stage["tool"])["settings"]
        target = output_directory / stage["output_file"]
        if not audio_layers:
            shutil.copy2(picture_track, target)
            return target

        command = [settings["executable"], "-y", "-i", str(picture_track)]
        for layer in audio_layers:
            command.extend(["-i", layer["path"]])
        filter_parts: list[str] = []
        mix_inputs = ["[0:a]"]
        for index, layer in enumerate(audio_layers, start=1):
            delay_ms = int(layer["start_seconds"] * 1000)
            label = f"a{index}"
            filter_parts.append(
                f"[{index}:a]volume={layer['volume']},adelay={delay_ms}|{delay_ms}[{label}]"
            )
            mix_inputs.append(f"[{label}]")
        filter_parts.append(
            "".join(mix_inputs)
            + f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[mixed]"
        )
        command.extend(
            [
                "-filter_complex",
                ";".join(filter_parts),
                "-map",
                "0:v:0",
                "-map",
                "[mixed]",
                "-c:v",
                "copy",
                "-c:a",
                settings["audio_codec"],
                "-ar",
                str(settings["audio_sample_rate"]),
                "-ac",
                str(settings["audio_channels"]),
                str(target),
            ]
        )
        self._run_command(command)
        return target

    def _invoke_output_tool(
        self, tool: dict[str, Any], payload: dict[str, Any]
    ) -> Path:
        """Execute output tool.

        Args:
            tool (dict[str, Any]): Tool used by this operation.
            payload (dict[str, Any]): Payload used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not tool["enabled"]:
            raise GenerationPipelineError(
                f"Tool '{tool.get('provider')}' is disabled."
            )
        if tool["transport"] != "http-json":
            raise GenerationPipelineError(
                f"Tool transport '{tool['transport']}' is not HTTP JSON."
            )
        settings = tool["settings"]
        url = settings["base_url"].rstrip("/") + "/" + settings["endpoint"].lstrip("/")
        request_payload = {**settings.get("defaults", {}), **payload}
        try:
            response = httpx.post(
                url,
                json=request_payload,
                timeout=settings.get("timeout_seconds", DEFAULT_TOOL_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise GenerationPipelineError(f"Tool request failed: {error}") from error
        output_field = settings.get("response_output_field", "output_path")
        output_path = result.get(output_field) if isinstance(result, dict) else None
        if not output_path:
            raise GenerationPipelineError(
                f"Tool response does not contain '{output_field}'."
            )
        resolved = Path(output_path).expanduser().resolve()
        if not resolved.is_file():
            raise GenerationPipelineError(f"Tool output does not exist: {resolved}")
        return resolved

    def _invoke_comfyui(
        self,
        tool: dict[str, Any],
        workflow: dict[str, Any],
        values: dict[str, Any],
        target_directory: Path,
    ) -> Path:
        """Execute comfyui.

        Args:
            tool (dict[str, Any]): Tool used by this operation.
            workflow (dict[str, Any]): Workflow used by this operation.
            values (dict[str, Any]): Values used by this operation.
            target_directory (Path): Target directory used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        if not tool["enabled"]:
            raise GenerationPipelineError("ComfyUI tool is disabled.")
        if tool["transport"] != "comfyui":
            raise GenerationPipelineError("Configured video tool is not ComfyUI.")
        settings = tool["settings"]
        api_workflow_path = self._resolve_project_path(workflow["api_workflow_file"])
        if not api_workflow_path.is_file():
            raise GenerationPipelineError(
                f"ComfyUI API workflow does not exist: {api_workflow_path}"
            )
        try:
            workflow_document = json.loads(api_workflow_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise GenerationPipelineError(
                f"Cannot load ComfyUI workflow: {error}"
            ) from error
        prepared_values = self._prepare_comfyui_inputs(settings, values)
        self._apply_workflow_bindings(
            workflow_document, workflow["input_bindings"], prepared_values
        )
        prompt_url = settings["base_url"].rstrip("/") + settings["prompt_endpoint"]
        try:
            response = httpx.post(
                prompt_url,
                json={"prompt": workflow_document},
                timeout=60,
            )
            response.raise_for_status()
            prompt_id = response.json().get("prompt_id")
        except (httpx.HTTPError, ValueError) as error:
            raise GenerationPipelineError(
                f"ComfyUI submission failed: {error}"
            ) from error
        if not prompt_id:
            raise GenerationPipelineError("ComfyUI did not return prompt_id.")
        history = self._wait_for_comfyui(settings, prompt_id)
        source = self._find_comfyui_output(
            settings, history, workflow["output_nodes"]
        )
        target = target_directory / "generated.mp4"
        shutil.copy2(source, target)
        return target

    def _prepare_comfyui_inputs(
        self, settings: dict[str, Any], values: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare comfyui inputs.

        Args:
            settings (dict[str, Any]): Settings used by this operation.
            values (dict[str, Any]): Values used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        result = deepcopy(values)
        shared_input_directory = Path(
            settings["shared_input_directory"]
        ).expanduser().resolve()
        shared_input_directory.mkdir(parents=True, exist_ok=True)
        for key in ("reference_image", "audio_file", "pose_video"):
            value = result.get(key)
            if not value:
                continue
            source = Path(value).expanduser().resolve()
            if not source.is_file():
                raise GenerationPipelineError(
                    f"ComfyUI input does not exist: {source}"
                )
            target = shared_input_directory / source.name
            shutil.copy2(source, target)
            result[key] = target.name
        return result

    @staticmethod
    def _apply_workflow_bindings(
        workflow_document: dict[str, Any],
        bindings: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        """Apply workflow bindings.

        Args:
            workflow_document (dict[str, Any]): Workflow document used by this
                operation.
            bindings (dict[str, Any]): Bindings used by this operation.
            values (dict[str, Any]): Values used by this operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        for value_name, binding in bindings.items():
            value = values.get(value_name)
            if value is None:
                continue
            node_id = binding["node_id"]
            node = workflow_document.get(node_id)
            if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
                raise GenerationPipelineError(
                    f"Workflow node '{node_id}' has no input object."
                )
            node["inputs"][binding["field"]] = value

    def _wait_for_comfyui(
        self, settings: dict[str, Any], prompt_id: str
    ) -> dict[str, Any]:
        """Execute for comfyui.

        Args:
            settings (dict[str, Any]): Settings used by this operation.
            prompt_id (str): Prompt id used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        deadline = time.monotonic() + settings.get(
            "timeout_seconds", DEFAULT_TOOL_TIMEOUT_SECONDS
        )
        interval = settings.get(
            "poll_interval_seconds", DEFAULT_COMFYUI_POLL_INTERVAL_SECONDS
        )
        endpoint = settings["history_endpoint"].format(prompt_id=prompt_id)
        url = settings["base_url"].rstrip("/") + endpoint
        while time.monotonic() < deadline:
            try:
                response = httpx.get(url, timeout=30)
                response.raise_for_status()
                history = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise GenerationPipelineError(
                    f"ComfyUI history request failed: {error}"
                ) from error
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(interval)
        raise GenerationPipelineError(
            f"ComfyUI generation timed out for prompt '{prompt_id}'."
        )

    @staticmethod
    def _find_comfyui_output(
        settings: dict[str, Any],
        history: dict[str, Any],
        output_nodes: list[str],
    ) -> Path:
        """Find comfyui output.

        Args:
            settings (dict[str, Any]): Settings used by this operation.
            history (dict[str, Any]): History used by this operation.
            output_nodes (list[str]): Output nodes used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        output_directory = Path(settings["output_directory"]).expanduser().resolve()
        outputs = history.get("outputs", {})
        for node_id in output_nodes:
            node_output = outputs.get(node_id, {})
            for output_type in ("videos", "gifs", "images"):
                for file_info in node_output.get(output_type, []):
                    filename = file_info.get("filename")
                    if filename:
                        path = (
                            output_directory
                            / file_info.get("subfolder", "")
                            / filename
                        ).resolve()
                        if path.is_file():
                            return path
        raise GenerationPipelineError(
            "ComfyUI completed but no output file was found."
        )

    def _build_dry_run_plan(self, package: dict[str, Any]) -> dict[str, Any]:
        """Build dry run plan.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        video_stage = package["production"]["stages"]["video"]
        shots = []
        for shot in package["scene"]["shots"]:
            mode = shot["generation"]["mode"]
            shots.append(
                {
                    "shot_id": shot["id"],
                    "mode": mode,
                    "workflow": video_stage["workflow_by_mode"][mode],
                    "dialogue_required": isinstance(shot.get("dialogue"), dict),
                    "reference_image_required": mode in {"i2v", "s2v"},
                    "configured_reference_image": shot["generation"].get(
                        "reference_image"
                    ),
                    "configured_audio_file": shot["generation"].get("audio_file"),
                    "duration_seconds": shot["duration_seconds"],
                }
            )
        return {
            "project_id": package["project"]["id"],
            "scene_id": package["scene"]["id"],
            "required_tools": sorted(package["tools"]),
            "workflows": sorted(package["workflows"]),
            "shots": shots,
            "audio": package["production"].get("audio", {}),
        }

    @staticmethod
    def _get_tool(package: dict[str, Any], tool_id: str) -> dict[str, Any]:
        """Return tool.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            tool_id (str): Tool id used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        tool = package["tools"].get(tool_id)
        if tool is None:
            raise GenerationPipelineError(
                f"Tool '{tool_id}' is not available in the compiled package."
            )
        return tool

    @staticmethod
    def _get_shot_continuity(
        package: dict[str, Any], shot_id: str
    ) -> dict[str, Any]:
        """Return shot continuity.

        Args:
            package (dict[str, Any]): Compiled package consumed by the operation.
            shot_id (str): Stable identifier of the shot being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        return package["continuity"]["shot_state"]["shots"][shot_id]

    def _resolve_project_path(
        self, value: str, *, require_within_project: bool = False
    ) -> Path:
        """Resolve project path.

        Args:
            value (str): Value inspected or transformed by the helper.
            require_within_project (bool): Require within project used by this
                operation. Defaults to ``False``.

        Returns:
            Path: Result produced by the operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        path = Path(value).expanduser()
        resolved = path.resolve() if path.is_absolute() else (
            self._project_root / path
        ).resolve()
        if require_within_project:
            try:
                resolved.relative_to(self._project_root)
            except ValueError as error:
                raise GenerationPipelineError(
                    f"Configured path escapes project root: {value}"
                ) from error
        return resolved

    @staticmethod
    def _calculate_frame_count(duration_seconds: float, fps: int) -> int:
        """Calculate frame count.

        Args:
            duration_seconds (float): Requested duration in seconds.
            fps (int): Fps used by this operation.

        Returns:
            int: Result produced by the operation.
        """
        requested = round(duration_seconds * fps)
        if requested < 1:
            return 1
        return requested - ((requested - 1) % 4)

    @staticmethod
    def _escape_concat_path(path: Path) -> str:
        """Execute concat path.

        Args:
            path (Path): Filesystem path read or written by the operation.

        Returns:
            str: Result produced by the operation.
        """
        return path.resolve().as_posix().replace("'", "'\\''")

    @staticmethod
    def _run_command(command: list[str]) -> None:
        """Run command.

        Args:
            command (list[str]): Command used by this operation.

        Raises:
            GenerationPipelineError: If inputs, context, state, or provider output are invalid.
        """
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as error:
            raise GenerationPipelineError(
                f"Cannot execute '{command[0]}': {error}"
            ) from error
        if result.returncode != 0:
            raise GenerationPipelineError(
                "Command failed:\n" + " ".join(command) + "\n\n" + result.stderr
            )
