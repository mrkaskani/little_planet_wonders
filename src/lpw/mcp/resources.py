from __future__ import annotations

import json

import yaml

from lpw.audio.compiler import (
    resolved_audio_context,
    resolved_voice_context,
)
from lpw.config import context_root, runtime_root
from lpw.context.loader import (
    get_project_directory,
    load_character,
    load_location,
    load_project_context,
)
from lpw.context.pipeline import SceneContextPipeline
from lpw.context.chaining import ContextChainResolver
from lpw.editing.automation import AutomatedEditingPipeline
from lpw.generation.extension import CinematicExtensionPipeline
from lpw.context.compiler import ContextCompiler
from lpw.utils.files import load_yaml


def studio_context() -> str:
    return yaml.safe_dump(
        load_yaml(context_root() / "studio.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def studio_profile(profile: str) -> str:
    return yaml.safe_dump(
        load_yaml(context_root() / "studio" / f"{profile}.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def editing_models_context() -> str:
    """Return configured local editing roles without loading model artifacts."""

    return yaml.safe_dump(
        {"models": ContextCompiler().load_editing_models()},
        sort_keys=False,
        allow_unicode=True,
    )


def project_context(project_id: str) -> str:
    return yaml.safe_dump(
        load_project_context(project_id), sort_keys=False, allow_unicode=True
    )


def character_context(project_id: str, character_id: str) -> str:
    return yaml.safe_dump(
        load_character(get_project_directory(project_id), character_id),
        sort_keys=False,
        allow_unicode=True,
    )


def location_context(project_id: str, location_id: str) -> str:
    return yaml.safe_dump(
        load_location(get_project_directory(project_id), location_id),
        sort_keys=False,
        allow_unicode=True,
    )


def project_audio_context(project_id: str) -> str:
    return json.dumps(resolved_audio_context(project_id), ensure_ascii=False, indent=2)


def character_voice_context(project_id: str, character_id: str) -> str:
    return json.dumps(
        resolved_voice_context(project_id, character_id), ensure_ascii=False, indent=2
    )


def voice_production_context(project_id: str) -> str:
    context = resolved_audio_context(project_id)
    return yaml.safe_dump(
        context.get("voice_production", {}),
        sort_keys=False,
        allow_unicode=True,
    )


def sound_effects_context(project_id: str) -> str:
    context = resolved_audio_context(project_id)
    return yaml.safe_dump(
        context["sound_effects"], sort_keys=False, allow_unicode=True
    )


def music_context(project_id: str) -> str:
    context = resolved_audio_context(project_id)
    return yaml.safe_dump(context["music"], sort_keys=False, allow_unicode=True)


def editing_context(project_id: str) -> str:
    context = load_project_context(project_id)
    result = {
        "editing": context["editing_style"],
        "palette": context["color_palette"],
        "audio": context["audio"],
        "camera": context["camera_language"],
        "continuity": context["continuity"],
    }
    return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)


def post_editing_context(project_id: str) -> str:
    project_directory = get_project_directory(project_id)
    return yaml.safe_dump(
        load_yaml(project_directory / "post-editing.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def export_context(project_id: str) -> str:
    project_directory = get_project_directory(project_id)
    return yaml.safe_dump(
        load_yaml(project_directory / "export.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def continuity_context(project_id: str) -> str:
    project_directory = get_project_directory(project_id)
    source = load_yaml(project_directory / "continuity.yaml", required=False)
    runtime_directory = runtime_root() / "continuity" / project_id
    runtime = {
        path.stem: load_yaml(path)
        for path in sorted(runtime_directory.glob("*.yaml"))
    } if runtime_directory.is_dir() else {}
    return yaml.safe_dump(
        {"source": source, "runtime": runtime},
        sort_keys=False,
        allow_unicode=True,
    )


def scene_editing_context(project_id: str, scene_id: str) -> str:
    project_directory = get_project_directory(project_id)
    return yaml.safe_dump(
        load_yaml(project_directory / "scenes" / scene_id / "edit-context.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def prepared_editing_package(project_id: str, scene_id: str) -> str:
    package = AutomatedEditingPipeline().load_latest_prepared_package(
        project_id, scene_id
    )
    return json.dumps(package, ensure_ascii=False, indent=2)


def scene_context(story_id: str, scene_id: str) -> str:
    """Return a story-linked scene with all referenced shots expanded."""

    context = SceneContextPipeline().load_scene(story_id, scene_id)
    return json.dumps(context, ensure_ascii=False, indent=2)


def inherited_scene_context(project_id: str, scene_id: str) -> str:
    path = get_project_directory(project_id) / "scenes" / scene_id / "scene.yaml"
    version = load_yaml(path).get("version")
    resolved = ContextChainResolver().resolve(
        f"cinema://projects/{project_id}/scenes/{scene_id}@{version}"
    )
    return json.dumps(
        {
            "context": resolved.context,
            "context_chain": resolved.chain,
            "context_hash": resolved.context_hash,
        },
        ensure_ascii=False,
        indent=2,
    )


def inherited_shot_context(project_id: str, shot_id: str) -> str:
    project = get_project_directory(project_id)
    matches = list(project.glob(f"scenes/*/shots/{shot_id}/shot.yaml"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected one inherited shot context for '{shot_id}', found {len(matches)}."
        )
    scene_id = matches[0].parents[2].name
    result = CinematicExtensionPipeline().resolve_context_chain(
        project_id, scene_id, shot_id
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


def segment_end_state(segment_id: str) -> str:
    return json.dumps(
        CinematicExtensionPipeline().runtime_end_state(segment_id),
        ensure_ascii=False,
        indent=2,
    )


def runtime_audio_state(scene_id: str) -> str:
    return yaml.safe_dump(
        load_yaml(runtime_root() / "audio" / f"{scene_id}.yaml", required=False),
        sort_keys=False,
        allow_unicode=True,
    )


def runtime_editing_state(scene_id: str) -> str:
    return yaml.safe_dump(
        load_yaml(runtime_root() / "editing" / f"{scene_id}.yaml", required=False),
        sort_keys=False,
        allow_unicode=True,
    )
