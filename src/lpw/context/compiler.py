"""Provide compiler services for the LPW cinematic pipeline."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from lpw.context.defaults import (
    CONTINUITY_DIRECTORY_NAME,
    DEFAULT_CAMERA,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_GENERATION,
    DEFAULT_TRANSITION,
    DEFAULT_VIDEO_SETTINGS,
    DIALOGUE_SHOT_TYPES,
    EDITING_MODELS_FILE_NAME,
    GENERATION_TOOLS_FILE_NAME,
    PROJECT_FILE_NAME,
    PRODUCTION_DIRECTORY_NAME,
    PROPS_DIRECTORY_NAME,
    SCENES_DIRECTORY_NAME,
    SHOTS_DIRECTORY_NAME,
    STORIES_DIRECTORY_NAME,
    SUPPORTED_GENERATION_MODES,
    SUPPORTED_TOOL_KINDS,
    SUPPORTED_TOOL_TRANSPORTS,
    TOOLS_DIRECTORY_NAME,
    VALIDATION_DEFAULTS_FILE_NAME,
    VALIDATION_DIRECTORY_NAME,
    VALIDATION_SCENES_DIRECTORY_NAME,
    WAN_MODELS_FILE_NAME,
    WARDROBE_DIRECTORY_NAME,
    WORKFLOWS_DIRECTORY_NAME,
)


class ContextCompilerError(Exception):
    """Raised when story, scene, or shot context cannot be compiled."""


class ContextCompiler:
    """Load hierarchical YAML context and compile complete scene packages."""

    def __init__(self, context_root: Path | str = DEFAULT_CONTEXT_ROOT) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            context_root (Path | str): Root directory containing source context files.
                Defaults to ``DEFAULT_CONTEXT_ROOT``.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        self._context_root = Path(context_root).expanduser().resolve()
        if not self._context_root.exists():
            raise ContextCompilerError(
                f"Context directory does not exist: {self._context_root}"
            )
        if not self._context_root.is_dir():
            raise ContextCompilerError(
                f"Context root is not a directory: {self._context_root}"
            )

    @property
    def context_root(self) -> Path:
        """Execute root.

        Returns:
            Path: Result produced by the operation.
        """
        return self._context_root

    def compile_scene(self, story_id: str, scene_id: str) -> dict[str, Any]:
        """Compile scene.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        project = self.load_project()
        story = self.load_story(story_id)
        scene = self.load_scene(scene_id)
        self._validate_story_scene_relationship(story, scene)
        shots = self._load_scene_shots(scene)
        props = self._load_scene_props(scene)
        wardrobe = self._load_scene_wardrobe(scene)
        continuity = self._load_scene_continuity(scene)
        self._validate_unique_shot_ids(shots)
        self._validate_scene_references(
            scene=scene,
            shots=shots,
            props=props,
            wardrobe=wardrobe,
            continuity=continuity,
        )

        compiled_scene = deepcopy(scene)
        compiled_scene.pop("shot_files", None)
        compiled_scene["shots"] = shots
        compiled_scene["total_duration_seconds"] = sum(
            shot["duration_seconds"] for shot in shots
        )
        return {
            "project": project,
            "story": story,
            "scene": compiled_scene,
            "props": props,
            "wardrobe": wardrobe,
            "continuity": continuity,
        }

    def load_project(self) -> dict[str, Any]:
        """Load project.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        path = self._context_root / PROJECT_FILE_NAME
        project = self._extract_root_object(self._load_yaml(path), "project", path)
        project["video"] = self._merge_defaults(
            DEFAULT_VIDEO_SETTINGS, project.get("video", {})
        )
        self._require_string(project, "id", path)
        self._require_string(project, "name", path)
        return project

    def load_story(self, story_id: str) -> dict[str, Any]:
        """Load story.

        Args:
            story_id (str): Stable identifier of the story to load or compile.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = self._context_root / STORIES_DIRECTORY_NAME / f"{story_id}.yaml"
        story = self._extract_root_object(self._load_yaml(path), "story", path)
        self._require_string(story, "id", path)
        self._require_string(story, "title", path)
        if story["id"] != story_id:
            raise ContextCompilerError(
                f"Story file '{path}' contains ID '{story['id']}', expected '{story_id}'."
            )
        scenes = story.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            raise ContextCompilerError(
                f"Story '{story_id}' must contain a non-empty 'scenes' list."
            )
        if not all(isinstance(scene, str) and scene for scene in scenes):
            raise ContextCompilerError(
                f"Story '{story_id}' scenes must be non-empty strings."
            )
        return story

    def load_scene(self, scene_id: str) -> dict[str, Any]:
        """Load scene.

        Args:
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = self._context_root / SCENES_DIRECTORY_NAME / f"{scene_id}.yaml"
        scene = self._extract_root_object(self._load_yaml(path), "scene", path)
        for field_name in ("id", "story_id", "title", "location"):
            self._require_string(scene, field_name, path)
        if scene["id"] != scene_id:
            raise ContextCompilerError(
                f"Scene file '{path}' contains ID '{scene['id']}', expected '{scene_id}'."
            )
        shot_files = scene.get("shot_files")
        if not isinstance(shot_files, list) or not shot_files:
            raise ContextCompilerError(
                f"Scene '{scene_id}' must contain a non-empty 'shot_files' list."
            )
        props = scene.get("props", [])
        if not isinstance(props, list):
            raise ContextCompilerError(f"Scene '{scene_id}' props must be a list.")
        if not all(isinstance(prop_id, str) and prop_id for prop_id in props):
            raise ContextCompilerError(
                f"Scene '{scene_id}' prop IDs must be non-empty strings."
            )
        wardrobe = scene.get("wardrobe", {})
        if not isinstance(wardrobe, dict):
            raise ContextCompilerError(
                f"Scene '{scene_id}' wardrobe must be an object."
            )
        continuity = scene.get("continuity")
        if not isinstance(continuity, dict):
            raise ContextCompilerError(
                f"Scene '{scene_id}' requires a continuity object."
            )
        self._require_string(continuity, "scene_state_file", path)
        self._require_string(continuity, "shot_state_file", path)
        return scene

    def load_shot(self, scene_id: str, shot_file_name: str) -> dict[str, Any]:
        """Load shot.

        Args:
            scene_id (str): Stable identifier of the scene being processed.
            shot_file_name (str): Shot file name used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = self._context_root / SHOTS_DIRECTORY_NAME / scene_id / shot_file_name
        shot = self._extract_root_object(self._load_yaml(path), "shot", path)
        shot = self._apply_shot_defaults(shot)
        self._validate_shot(shot, path)
        expected_id = Path(shot_file_name).stem
        if shot["id"] != expected_id:
            raise ContextCompilerError(
                f"Shot file '{path}' contains ID '{shot['id']}', expected '{expected_id}'."
            )
        return shot

    def load_prop(self, prop_id: str) -> dict[str, Any]:
        """Load prop.

        Args:
            prop_id (str): Prop id used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = self._context_root / PROPS_DIRECTORY_NAME / f"{prop_id}.yaml"
        prop = self._extract_root_object(self._load_yaml(path), "prop", path)
        for field_name in ("id", "name", "category"):
            self._require_string(prop, field_name, path)
        if prop["id"] != prop_id:
            raise ContextCompilerError(
                f"Prop file '{path}' contains ID '{prop['id']}', expected '{prop_id}'."
            )
        if not isinstance(prop.get("visual_identity"), dict):
            raise ContextCompilerError(
                f"Prop '{prop_id}' requires visual_identity."
            )
        if not isinstance(prop.get("default_state"), dict):
            raise ContextCompilerError(f"Prop '{prop_id}' requires default_state.")
        allowed_conditions = prop.get("allowed_conditions")
        if not isinstance(allowed_conditions, list) or not allowed_conditions:
            raise ContextCompilerError(
                f"Prop '{prop_id}' requires allowed_conditions."
            )
        default_condition = prop["default_state"].get("condition")
        if default_condition not in allowed_conditions:
            raise ContextCompilerError(
                f"Prop '{prop_id}' default condition '{default_condition}' is not allowed."
            )
        return prop

    def load_wardrobe(self, wardrobe_id: str) -> dict[str, Any]:
        """Load wardrobe.

        Args:
            wardrobe_id (str): Wardrobe id used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = self._context_root / WARDROBE_DIRECTORY_NAME / f"{wardrobe_id}.yaml"
        wardrobe = self._extract_root_object(
            self._load_yaml(path), "wardrobe", path
        )
        for field_name in ("id", "character_id", "name"):
            self._require_string(wardrobe, field_name, path)
        if wardrobe["id"] != wardrobe_id:
            raise ContextCompilerError(
                f"Wardrobe file '{path}' contains ID '{wardrobe['id']}', expected '{wardrobe_id}'."
            )
        items = wardrobe.get("items")
        if not isinstance(items, list) or not items:
            raise ContextCompilerError(
                f"Wardrobe '{wardrobe_id}' requires a non-empty items list."
            )
        return wardrobe

    def load_scene_state(self, scene_id: str, file_name: str) -> dict[str, Any]:
        """Load scene state.

        Args:
            scene_id (str): Stable identifier of the scene being processed.
            file_name (str): File name used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = (
            self._context_root
            / CONTINUITY_DIRECTORY_NAME
            / scene_id
            / file_name
        )
        state = self._extract_root_object(
            self._load_yaml(path), "scene_state", path
        )
        self._require_string(state, "scene_id", path)
        if state["scene_id"] != scene_id:
            raise ContextCompilerError(
                f"Scene-state file '{path}' belongs to '{state['scene_id']}', expected '{scene_id}'."
            )
        for field_name in ("opening", "expected_end"):
            if not isinstance(state.get(field_name), dict):
                raise ContextCompilerError(
                    f"Scene state '{scene_id}' requires {field_name}."
                )
        return state

    def load_shot_state(self, scene_id: str, file_name: str) -> dict[str, Any]:
        """Load shot state.

        Args:
            scene_id (str): Stable identifier of the scene being processed.
            file_name (str): File name used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        path = (
            self._context_root
            / CONTINUITY_DIRECTORY_NAME
            / scene_id
            / file_name
        )
        state = self._extract_root_object(
            self._load_yaml(path), "shot_state", path
        )
        self._require_string(state, "scene_id", path)
        if state["scene_id"] != scene_id:
            raise ContextCompilerError(
                f"Shot-state file '{path}' belongs to '{state['scene_id']}', expected '{scene_id}'."
            )
        if not isinstance(state.get("shots"), dict):
            raise ContextCompilerError(
                f"Shot state '{scene_id}' requires a shots object."
            )
        return state

    def load_generation_tools(self) -> dict[str, dict[str, Any]]:
        """Load and validate configurable external generation tools.

        Returns:
            dict[str, dict[str, Any]]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = (
            self._context_root
            / TOOLS_DIRECTORY_NAME
            / GENERATION_TOOLS_FILE_NAME
        )
        document = self._load_yaml(path)
        tools = document.get("tools")
        if not isinstance(tools, dict) or not tools:
            raise ContextCompilerError(
                f"File '{path}' requires a non-empty tools object."
            )

        for tool_id, tool in tools.items():
            if not isinstance(tool_id, str) or not tool_id:
                raise ContextCompilerError(f"Invalid tool ID in '{path}'.")
            if not isinstance(tool, dict):
                raise ContextCompilerError(f"Tool '{tool_id}' must be an object.")
            kind = tool.get("kind")
            transport = tool.get("transport")
            if kind not in SUPPORTED_TOOL_KINDS:
                raise ContextCompilerError(
                    f"Tool '{tool_id}' has unsupported kind '{kind}'."
                )
            if transport not in SUPPORTED_TOOL_TRANSPORTS:
                raise ContextCompilerError(
                    f"Tool '{tool_id}' has unsupported transport '{transport}'."
                )
            if not isinstance(tool.get("provider"), str) or not tool["provider"]:
                raise ContextCompilerError(
                    f"Tool '{tool_id}' requires a provider."
                )
            if not isinstance(tool.get("enabled"), bool):
                raise ContextCompilerError(
                    f"Tool '{tool_id}' requires enabled=true or false."
                )
            if not isinstance(tool.get("settings"), dict):
                raise ContextCompilerError(
                    f"Tool '{tool_id}' requires a settings object."
                )
        return tools

    def load_editing_models(self) -> dict[str, Any]:
        """Load local editing-stack declarations without resolving artifacts.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = self._context_root / TOOLS_DIRECTORY_NAME / EDITING_MODELS_FILE_NAME
        document = self._load_yaml(path)
        models = document.get("models")
        if not isinstance(models, dict) or not models:
            raise ContextCompilerError(
                f"File '{path}' requires a non-empty models object."
            )
        if models.get("download_policy") != "never":
            raise ContextCompilerError(
                f"File '{path}' must set download_policy to 'never'."
            )

        for role, configuration in models.items():
            if role in {"download_policy", "artifact_policy"}:
                continue
            if not isinstance(configuration, dict):
                raise ContextCompilerError(
                    f"Editing model role '{role}' must be an object."
                )
            if not isinstance(configuration.get("enabled"), bool):
                raise ContextCompilerError(
                    f"Editing model role '{role}' requires enabled=true or false."
                )
            if not configuration.get("model") and not configuration.get("engine"):
                raise ContextCompilerError(
                    f"Editing model role '{role}' requires a model or engine."
                )
            purpose = configuration.get("purpose", [])
            if not isinstance(purpose, list) or not all(
                isinstance(item, str) and item for item in purpose
            ):
                raise ContextCompilerError(
                    f"Editing model role '{role}' purpose must be a string list."
                )
            output_schema = configuration.get("output_schema")
            if output_schema is not None:
                if not isinstance(output_schema, str) or not output_schema:
                    raise ContextCompilerError(
                        f"Editing model role '{role}' output_schema must be a path."
                    )
                schema_path = (self._context_root / output_schema).resolve()
                try:
                    schema_path.relative_to(self._context_root)
                except ValueError as error:
                    raise ContextCompilerError(
                        f"Editing model role '{role}' output_schema escapes context root."
                    ) from error
                if not schema_path.is_file():
                    raise ContextCompilerError(
                        f"Editing model role '{role}' output_schema does not exist: "
                        f"{schema_path}"
                    )
        return models

    def load_wan_models(self) -> dict[str, Any]:
        """Load the non-animation Wan 2.2 manifest without resolving weights.

        Returns:
            dict[str, Any]: Validated configuration for T2V, I2V, TI2V, and S2V.

        Raises:
            ContextCompilerError: If download protection, mode coverage, or animation
                exclusion is missing.
        """

        path = self._context_root / TOOLS_DIRECTORY_NAME / WAN_MODELS_FILE_NAME
        document = self._load_yaml(path)
        policy = document.get("wan22")
        if not isinstance(policy, dict):
            raise ContextCompilerError(f"File '{path}' requires a wan22 object.")
        if policy.get("download_policy") != "never":
            raise ContextCompilerError(
                f"File '{path}' must set download_policy to 'never'."
            )
        if policy.get("artifact_policy") != "externally-managed":
            raise ContextCompilerError(
                f"File '{path}' must keep artifacts externally managed."
            )
        if policy.get("animation", {}).get("enabled") is not False:
            raise ContextCompilerError(
                f"File '{path}' must explicitly disable Wan Animate."
            )
        models = policy.get("models")
        if not isinstance(models, dict):
            raise ContextCompilerError(f"File '{path}' requires a models object.")
        required_modes = {"t2v", "i2v", "ti2v", "s2v"}
        if set(models) != required_modes:
            raise ContextCompilerError(
                f"File '{path}' must configure exactly {sorted(required_modes)}."
            )
        for mode, configuration in models.items():
            if not isinstance(configuration, dict):
                raise ContextCompilerError(f"Wan mode '{mode}' must be an object.")
            if configuration.get("enabled") is not False:
                raise ContextCompilerError(
                    f"Wan mode '{mode}' must remain disabled until locally configured."
                )
            if not configuration.get("model") or not configuration.get("workflow"):
                raise ContextCompilerError(
                    f"Wan mode '{mode}' requires model and workflow identifiers."
                )
            if configuration.get("weights_path") is not None:
                raise ContextCompilerError(
                    f"Wan mode '{mode}' weights_path must remain null in source context."
                )
        return policy

    def load_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Load one mode-specific ComfyUI API workflow binding.

        Args:
            workflow_id (str): Workflow id used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = (
            self._context_root
            / TOOLS_DIRECTORY_NAME
            / WORKFLOWS_DIRECTORY_NAME
            / f"{workflow_id}.yaml"
        )
        workflow = self._extract_root_object(
            self._load_yaml(path), "workflow", path
        )
        for field_name in ("id", "mode", "api_workflow_file"):
            self._require_string(workflow, field_name, path)
        if workflow["id"] != workflow_id:
            raise ContextCompilerError(
                f"Workflow file '{path}' contains ID '{workflow['id']}', expected '{workflow_id}'."
            )
        if workflow["mode"] not in SUPPORTED_GENERATION_MODES:
            raise ContextCompilerError(
                f"Workflow '{workflow_id}' has unsupported mode '{workflow['mode']}'."
            )

        bindings = workflow.get("input_bindings")
        if not isinstance(bindings, dict) or not bindings:
            raise ContextCompilerError(
                f"Workflow '{workflow_id}' requires input_bindings."
            )
        for binding_name, binding in bindings.items():
            if not isinstance(binding, dict):
                raise ContextCompilerError(
                    f"Workflow binding '{binding_name}' must be an object."
                )
            for field_name in ("node_id", "field"):
                value = binding.get(field_name)
                if not isinstance(value, str) or not value:
                    raise ContextCompilerError(
                        f"Workflow binding '{binding_name}' requires {field_name}."
                    )

        output_nodes = workflow.get("output_nodes")
        if (
            not isinstance(output_nodes, list)
            or not output_nodes
            or not all(isinstance(node, str) and node for node in output_nodes)
        ):
            raise ContextCompilerError(
                f"Workflow '{workflow_id}' requires string output_nodes."
            )
        return workflow

    def load_production_plan(self, scene_id: str) -> dict[str, Any]:
        """Load the tool and workflow selection for a scene.

        Args:
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = (
            self._context_root
            / PRODUCTION_DIRECTORY_NAME
            / f"{scene_id}.yaml"
        )
        production = self._extract_root_object(
            self._load_yaml(path), "production", path
        )
        self._require_string(production, "scene_id", path)
        self._require_string(production, "output_directory", path)
        if production["scene_id"] != scene_id:
            raise ContextCompilerError(
                f"Production plan '{path}' belongs to scene '{production['scene_id']}', expected '{scene_id}'."
            )

        stages = production.get("stages")
        if not isinstance(stages, dict):
            raise ContextCompilerError(
                f"Production plan '{scene_id}' requires stages."
            )
        video_stage = stages.get("video")
        if not isinstance(video_stage, dict):
            raise ContextCompilerError(
                f"Production plan '{scene_id}' requires video stage."
            )
        workflow_by_mode = video_stage.get("workflow_by_mode")
        if not isinstance(workflow_by_mode, dict):
            raise ContextCompilerError("Video stage requires workflow_by_mode.")
        return production

    def compile_production_scene(
        self,
        story_id: str,
        scene_id: str,
        require_enabled_tools: bool = False,
    ) -> dict[str, Any]:
        """Resolve scene context, production tools, and used workflows.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.
            require_enabled_tools (bool): Require enabled tools used by this operation.
                Defaults to ``False``.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        context = self.compile_scene(story_id=story_id, scene_id=scene_id)
        production = self.load_production_plan(scene_id)
        all_tools = self.load_generation_tools()
        required_tool_ids = self._collect_tool_ids(production)
        resolved_tools: dict[str, dict[str, Any]] = {}

        for tool_id in required_tool_ids:
            if tool_id not in all_tools:
                raise ContextCompilerError(
                    f"Production plan references unknown tool '{tool_id}'."
                )
            tool = all_tools[tool_id]
            if require_enabled_tools and not tool["enabled"]:
                raise ContextCompilerError(f"Required tool '{tool_id}' is disabled.")
            resolved_tools[tool_id] = tool

        video_stage = production["stages"]["video"]
        workflow_by_mode = video_stage["workflow_by_mode"]
        used_modes = {
            shot["generation"]["mode"] for shot in context["scene"]["shots"]
        }
        resolved_workflows: dict[str, dict[str, Any]] = {}
        for mode in used_modes:
            workflow_id = workflow_by_mode.get(mode)
            if not isinstance(workflow_id, str) or not workflow_id:
                raise ContextCompilerError(
                    f"No workflow configured for generation mode '{mode}'."
                )
            workflow = self.load_workflow(workflow_id)
            if workflow["mode"] != mode:
                raise ContextCompilerError(
                    f"Workflow '{workflow_id}' is configured for '{workflow['mode']}', not '{mode}'."
                )
            resolved_workflows[workflow_id] = workflow

        context["production"] = production
        context["tools"] = resolved_tools
        context["workflows"] = resolved_workflows
        return context

    def load_validation_defaults(self) -> dict[str, Any]:
        """Load validation rules shared by all scenes.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = (
            self._context_root
            / VALIDATION_DIRECTORY_NAME
            / VALIDATION_DEFAULTS_FILE_NAME
        )
        validation = self._extract_root_object(
            self._load_yaml(path), "validation", path
        )
        for section in ("automatic", "semantic", "approval"):
            if not isinstance(validation.get(section), dict):
                raise ContextCompilerError(
                    f"Validation defaults '{path}' require {section} rules."
                )
        required_checks = validation["semantic"].get("required_checks")
        if not isinstance(required_checks, list) or not all(
            isinstance(check_id, str) and check_id for check_id in required_checks
        ):
            raise ContextCompilerError(
                "Validation semantic.required_checks must be a string list."
            )
        return validation

    def load_scene_validation(self, scene_id: str) -> dict[str, Any]:
        """Load scene and shot-specific validation expectations.

        Args:
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """

        path = (
            self._context_root
            / VALIDATION_DIRECTORY_NAME
            / VALIDATION_SCENES_DIRECTORY_NAME
            / f"{scene_id}.yaml"
        )
        validation = self._extract_root_object(
            self._load_yaml(path), "scene_validation", path
        )
        self._require_string(validation, "scene_id", path)
        if validation["scene_id"] != scene_id:
            raise ContextCompilerError(
                f"Validation file '{path}' belongs to scene "
                f"'{validation['scene_id']}', expected '{scene_id}'."
            )
        if not isinstance(validation.get("scene_rules", {}), dict):
            raise ContextCompilerError(
                f"Scene validation '{scene_id}' scene_rules must be an object."
            )
        if not isinstance(validation.get("shots", {}), dict):
            raise ContextCompilerError(
                f"Scene validation '{scene_id}' shots must be an object."
            )
        return validation

    def compile_validation_scene(
        self, story_id: str, scene_id: str
    ) -> dict[str, Any]:
        """Compile production context together with effective validation rules.

        Args:
            story_id (str): Stable identifier of the story to load or compile.
            scene_id (str): Stable identifier of the scene being processed.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """

        package = self.compile_production_scene(story_id, scene_id)
        defaults = self.load_validation_defaults()
        scene_validation = self.load_scene_validation(scene_id)
        merged = self._deep_merge(
            defaults,
            {
                "scene_rules": scene_validation.get("scene_rules", {}),
                "shots": scene_validation.get("shots", {}),
            },
        )
        self._validate_validation_shot_ids(package["scene"], merged)
        package["validation"] = merged
        return package

    @staticmethod
    def _validate_validation_shot_ids(
        scene: dict[str, Any], validation: dict[str, Any]
    ) -> None:
        """Validate validation shot ids.

        Args:
            scene (dict[str, Any]): Scene used by this operation.
            validation (dict[str, Any]): Validation used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        expected = {shot["id"] for shot in scene["shots"]}
        shot_rules = validation.get("shots", {})
        if not isinstance(shot_rules, dict):
            raise ContextCompilerError(
                "Compiled validation shots must be an object."
            )
        configured = set(shot_rules)
        missing = expected - configured
        unknown = configured - expected
        if missing:
            raise ContextCompilerError(
                "Validation rules are missing shots: " + ", ".join(sorted(missing))
            )
        if unknown:
            raise ContextCompilerError(
                "Validation rules contain unknown shots: "
                + ", ".join(sorted(unknown))
            )

    @staticmethod
    def _deep_merge(
        base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute merge.

        Args:
            base (dict[str, Any]): Base used by this operation.
            override (dict[str, Any]): Override used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = deepcopy(base)
        for key, value in override.items():
            existing = result.get(key)
            if isinstance(existing, dict) and isinstance(value, dict):
                result[key] = ContextCompiler._deep_merge(existing, value)
            else:
                result[key] = deepcopy(value)
        return result

    @staticmethod
    def _collect_tool_ids(production: dict[str, Any]) -> set[str]:
        """Collect tool ids.

        Args:
            production (dict[str, Any]): Production used by this operation.

        Returns:
            set[str]: Result produced by the operation.
        """
        tool_ids: set[str] = set()
        for stage in production.get("stages", {}).values():
            if isinstance(stage, dict):
                tool_id = stage.get("tool")
                if isinstance(tool_id, str) and tool_id:
                    tool_ids.add(tool_id)

        audio = production.get("audio", {})
        for layer_name in ("ambience", "music"):
            layer = audio.get(layer_name)
            if isinstance(layer, dict):
                tool_id = layer.get("tool")
                if isinstance(tool_id, str) and tool_id:
                    tool_ids.add(tool_id)
        sound_effects = audio.get("sound_effects", [])
        if isinstance(sound_effects, list):
            for effect in sound_effects:
                if isinstance(effect, dict):
                    tool_id = effect.get("tool")
                    if isinstance(tool_id, str) and tool_id:
                        tool_ids.add(tool_id)
        return tool_ids

    def _load_scene_shots(self, scene: dict[str, Any]) -> list[dict[str, Any]]:
        """Load scene shots.

        Args:
            scene (dict[str, Any]): Scene used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        scene_id = scene["id"]
        shots: list[dict[str, Any]] = []
        for shot_file_name in scene["shot_files"]:
            if not isinstance(shot_file_name, str) or not shot_file_name:
                raise ContextCompilerError(
                    f"Scene '{scene_id}' contains an invalid shot filename."
                )
            shots.append(self.load_shot(scene_id, shot_file_name))
        return shots

    def _load_scene_props(
        self, scene: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Load scene props.

        Args:
            scene (dict[str, Any]): Scene used by this operation.

        Returns:
            dict[str, dict[str, Any]]: Result produced by the operation.
        """
        return {
            prop_id: self.load_prop(prop_id)
            for prop_id in scene.get("props", [])
        }

    def _load_scene_wardrobe(
        self, scene: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Load scene wardrobe.

        Args:
            scene (dict[str, Any]): Scene used by this operation.

        Returns:
            dict[str, dict[str, Any]]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        result: dict[str, dict[str, Any]] = {}
        for character_id, wardrobe_id in scene.get("wardrobe", {}).items():
            if not isinstance(character_id, str) or not character_id:
                raise ContextCompilerError(
                    f"Scene '{scene['id']}' has an invalid wardrobe character ID."
                )
            if not isinstance(wardrobe_id, str) or not wardrobe_id:
                raise ContextCompilerError(
                    f"Wardrobe ID for '{character_id}' must be a non-empty string."
                )
            wardrobe = self.load_wardrobe(wardrobe_id)
            if wardrobe["character_id"] != character_id:
                raise ContextCompilerError(
                    f"Wardrobe '{wardrobe_id}' belongs to '{wardrobe['character_id']}', not '{character_id}'."
                )
            result[character_id] = wardrobe
        return result

    def _load_scene_continuity(self, scene: dict[str, Any]) -> dict[str, Any]:
        """Load scene continuity.

        Args:
            scene (dict[str, Any]): Scene used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        files = scene["continuity"]
        return {
            "scene_state": self.load_scene_state(
                scene["id"], files["scene_state_file"]
            ),
            "shot_state": self.load_shot_state(
                scene["id"], files["shot_state_file"]
            ),
        }

    def _apply_shot_defaults(self, shot: dict[str, Any]) -> dict[str, Any]:
        """Apply shot defaults.

        Args:
            shot (dict[str, Any]): Shot used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = deepcopy(shot)
        result.setdefault("characters", [])
        result.setdefault("props", [])
        result.setdefault("dialogue", None)
        result["camera"] = self._merge_defaults(
            DEFAULT_CAMERA, result.get("camera", {})
        )
        result["transition"] = self._merge_defaults(
            DEFAULT_TRANSITION, result.get("transition", {})
        )
        result["generation"] = self._merge_defaults(
            DEFAULT_GENERATION, result.get("generation", {})
        )
        return result

    def _validate_shot(self, shot: dict[str, Any], path: Path) -> None:
        """Validate shot.

        Args:
            shot (dict[str, Any]): Shot used by this operation.
            path (Path): Filesystem path read or written by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        for field_name in ("id", "type", "location", "action"):
            self._require_string(shot, field_name, path)
        duration = shot.get("duration_seconds")
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or duration <= 0
        ):
            raise ContextCompilerError(
                f"Shot '{shot.get('id')}' in '{path}' requires a positive duration_seconds value."
            )
        if not isinstance(shot.get("characters"), list):
            raise ContextCompilerError(
                f"Shot '{shot['id']}' characters must be a list."
            )
        if not isinstance(shot.get("props"), list):
            raise ContextCompilerError(f"Shot '{shot['id']}' props must be a list.")
        for section_name in ("camera", "transition", "generation"):
            if not isinstance(shot.get(section_name), dict):
                raise ContextCompilerError(
                    f"Shot '{shot['id']}' requires {section_name} settings."
                )
        generation = shot["generation"]
        mode = generation.get("mode")
        if mode not in SUPPORTED_GENERATION_MODES:
            raise ContextCompilerError(
                f"Shot '{shot['id']}' uses unsupported generation mode '{mode}'."
            )
        prompt = generation.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ContextCompilerError(
                f"Shot '{shot['id']}' requires a non-empty generation prompt."
            )
        self._validate_generation_inputs(shot, generation)
        self._validate_dialogue(shot, mode)

    def _validate_scene_references(
        self,
        scene: dict[str, Any],
        shots: list[dict[str, Any]],
        props: dict[str, dict[str, Any]],
        wardrobe: dict[str, dict[str, Any]],
        continuity: dict[str, Any],
    ) -> None:
        """Validate scene references.

        Args:
            scene (dict[str, Any]): Scene used by this operation.
            shots (list[dict[str, Any]]): Shots used by this operation.
            props (dict[str, dict[str, Any]]): Props used by this operation.
            wardrobe (dict[str, dict[str, Any]]): Wardrobe used by this operation.
            continuity (dict[str, Any]): Continuity state approved for subsequent
                production.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        known_prop_ids = set(props)
        known_character_ids = {
            character_id
            for shot in shots
            for character_id in shot["characters"]
        }

        for shot in shots:
            for prop_id in shot["props"]:
                if prop_id not in known_prop_ids:
                    raise ContextCompilerError(
                        f"Shot '{shot['id']}' references unknown prop '{prop_id}'."
                    )

        for character_id in wardrobe:
            if character_id not in known_character_ids:
                raise ContextCompilerError(
                    f"Scene wardrobe references character '{character_id}', but the character does not appear in any shot."
                )

        scene_state = continuity["scene_state"]
        shot_state = continuity["shot_state"]
        self._validate_state_block(
            scene_state["opening"],
            "scene opening",
            known_character_ids,
            known_prop_ids,
            wardrobe,
        )
        self._validate_state_block(
            scene_state["expected_end"],
            "scene expected end",
            known_character_ids,
            known_prop_ids,
            wardrobe,
        )

        expected_shot_ids = {shot["id"] for shot in shots}
        actual_shot_ids = set(shot_state["shots"])
        missing_shots = expected_shot_ids - actual_shot_ids
        unknown_shots = actual_shot_ids - expected_shot_ids
        if missing_shots:
            raise ContextCompilerError(
                "Missing continuity state for shots: "
                + ", ".join(sorted(missing_shots))
            )
        if unknown_shots:
            raise ContextCompilerError(
                "Continuity contains unknown shots: "
                + ", ".join(sorted(unknown_shots))
            )

        for shot_id, state in shot_state["shots"].items():
            if not isinstance(state, dict):
                raise ContextCompilerError(
                    f"Continuity state for '{shot_id}' must be an object."
                )
            before = state.get("before")
            after = state.get("after")
            if not isinstance(before, dict):
                raise ContextCompilerError(f"Shot '{shot_id}' requires before state.")
            if not isinstance(after, dict):
                raise ContextCompilerError(f"Shot '{shot_id}' requires after state.")
            self._validate_state_block(
                before,
                f"{shot_id} before",
                known_character_ids,
                known_prop_ids,
                wardrobe,
            )
            self._validate_state_block(
                after,
                f"{shot_id} after",
                known_character_ids,
                known_prop_ids,
                wardrobe,
            )

    @staticmethod
    def _validate_state_block(
        state: dict[str, Any],
        state_name: str,
        known_character_ids: set[str],
        known_prop_ids: set[str],
        wardrobe: dict[str, dict[str, Any]],
    ) -> None:
        """Validate state block.

        Args:
            state (dict[str, Any]): State used by this operation.
            state_name (str): State name used by this operation.
            known_character_ids (set[str]): Known character ids used by this operation.
            known_prop_ids (set[str]): Known prop ids used by this operation.
            wardrobe (dict[str, dict[str, Any]]): Wardrobe used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        character_state = state.get("characters", {})
        prop_state = state.get("props", {})
        if not isinstance(character_state, dict):
            raise ContextCompilerError(
                f"Characters in '{state_name}' must be an object."
            )
        if not isinstance(prop_state, dict):
            raise ContextCompilerError(
                f"Props in '{state_name}' must be an object."
            )

        for character_id, values in character_state.items():
            if character_id not in known_character_ids:
                raise ContextCompilerError(
                    f"State '{state_name}' references unknown character '{character_id}'."
                )
            if not isinstance(values, dict):
                raise ContextCompilerError(
                    f"State for character '{character_id}' in '{state_name}' must be an object."
                )
            wardrobe_id = values.get("wardrobe")
            if wardrobe_id is not None:
                expected = wardrobe.get(character_id)
                if expected is None:
                    raise ContextCompilerError(
                        f"Character '{character_id}' has wardrobe state but no scene wardrobe definition."
                    )
                if expected["id"] != wardrobe_id:
                    raise ContextCompilerError(
                        f"Character '{character_id}' uses wardrobe '{wardrobe_id}' in '{state_name}', expected '{expected['id']}'."
                    )

        for prop_id, values in prop_state.items():
            if prop_id not in known_prop_ids:
                raise ContextCompilerError(
                    f"State '{state_name}' references unknown prop '{prop_id}'."
                )
            if not isinstance(values, dict):
                raise ContextCompilerError(
                    f"State for prop '{prop_id}' in '{state_name}' must be an object."
                )

    @staticmethod
    def _validate_generation_inputs(
        shot: dict[str, Any], generation: dict[str, Any]
    ) -> None:
        """Validate generation inputs.

        Args:
            shot (dict[str, Any]): Shot used by this operation.
            generation (dict[str, Any]): Generation used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        shot_id = shot["id"]
        mode = generation["mode"]
        if mode in {"i2v", "s2v"} and not generation.get("reference_image"):
            raise ContextCompilerError(
                f"{mode.upper()} shot '{shot_id}' requires reference_image."
            )
        if mode == "s2v" and not generation.get("audio_file"):
            raise ContextCompilerError(
                f"S2V shot '{shot_id}' requires audio_file."
            )

    @staticmethod
    def _validate_dialogue(shot: dict[str, Any], generation_mode: str) -> None:
        """Validate dialogue.

        Args:
            shot (dict[str, Any]): Shot used by this operation.
            generation_mode (str): Generation mode used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        shot_id = shot["id"]
        if shot["type"] not in DIALOGUE_SHOT_TYPES:
            return
        dialogue = shot.get("dialogue")
        if not isinstance(dialogue, dict):
            raise ContextCompilerError(
                f"Dialogue shot '{shot_id}' requires a dialogue object."
            )
        speaker = dialogue.get("speaker")
        text = dialogue.get("text")
        if not isinstance(speaker, str) or not speaker:
            raise ContextCompilerError(
                f"Dialogue shot '{shot_id}' requires a speaker."
            )
        if not isinstance(text, str) or not text.strip():
            raise ContextCompilerError(
                f"Dialogue shot '{shot_id}' requires dialogue text."
            )
        if speaker not in shot["characters"]:
            raise ContextCompilerError(
                f"Speaker '{speaker}' is not included in the characters list for shot '{shot_id}'."
            )
        if generation_mode != "s2v":
            raise ContextCompilerError(
                f"Dialogue shot '{shot_id}' must use S2V."
            )

    @staticmethod
    def _validate_story_scene_relationship(
        story: dict[str, Any], scene: dict[str, Any]
    ) -> None:
        """Validate story scene relationship.

        Args:
            story (dict[str, Any]): Story used by this operation.
            scene (dict[str, Any]): Scene used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        if scene["story_id"] != story["id"]:
            raise ContextCompilerError(
                f"Scene '{scene['id']}' belongs to story '{scene['story_id']}', not '{story['id']}'."
            )
        if scene["id"] not in story["scenes"]:
            raise ContextCompilerError(
                f"Scene '{scene['id']}' is not registered in story '{story['id']}'."
            )

    @staticmethod
    def _validate_unique_shot_ids(shots: list[dict[str, Any]]) -> None:
        """Validate unique shot ids.

        Args:
            shots (list[dict[str, Any]]): Shots used by this operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        shot_ids = [shot["id"] for shot in shots]
        duplicates = sorted(
            shot_id for shot_id in set(shot_ids) if shot_ids.count(shot_id) > 1
        )
        if duplicates:
            raise ContextCompilerError(
                f"Duplicate shot IDs found: {', '.join(duplicates)}."
            )

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load yaml.

        Args:
            path (Path): Filesystem path read or written by the operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        safe_path = path.resolve()
        try:
            safe_path.relative_to(self._context_root)
        except ValueError as error:
            raise ContextCompilerError(
                f"Context path escapes the context root: {path}"
            ) from error
        if not safe_path.is_file():
            raise ContextCompilerError(f"Context file does not exist: {safe_path}")
        try:
            with safe_path.open("r", encoding="utf-8") as yaml_file:
                document = yaml.safe_load(yaml_file)
        except yaml.YAMLError as error:
            raise ContextCompilerError(
                f"Invalid YAML in '{safe_path}': {error}"
            ) from error
        if not isinstance(document, dict):
            raise ContextCompilerError(
                f"Top-level YAML value must be an object in '{safe_path}'."
            )
        return document

    @staticmethod
    def _extract_root_object(
        document: dict[str, Any], root_key: str, path: Path
    ) -> dict[str, Any]:
        """Extract root object.

        Args:
            document (dict[str, Any]): Structured document to validate, merge, or
                persist.
            root_key (str): Root key used by this operation.
            path (Path): Filesystem path read or written by the operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        value = document.get(root_key)
        if not isinstance(value, dict):
            raise ContextCompilerError(
                f"File '{path}' must contain a '{root_key}' object."
            )
        return value

    @staticmethod
    def _require_string(
        values: dict[str, Any], field_name: str, path: Path
    ) -> None:
        """Execute string.

        Args:
            values (dict[str, Any]): Values used by this operation.
            field_name (str): Field name used by this operation.
            path (Path): Filesystem path read or written by the operation.

        Raises:
            ContextCompilerError: If inputs, context, state, or provider output are invalid.
        """
        value = values.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ContextCompilerError(
                f"Field '{field_name}' in '{path}' must be a non-empty string."
            )

    @staticmethod
    def _merge_defaults(
        defaults: dict[str, Any], values: Any
    ) -> dict[str, Any]:
        """Execute defaults.

        Args:
            defaults (dict[str, Any]): Defaults used by this operation.
            values (Any): Values used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = deepcopy(defaults)
        if isinstance(values, dict):
            result.update(values)
        return result
