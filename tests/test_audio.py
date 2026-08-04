from __future__ import annotations

from little_planet_wonders.audio.compiler import compile_dialogue_package
from little_planet_wonders.audio.pipeline import compile_cinematic_shot
from little_planet_wonders.models import DialogueRequest, ShotRequest


def test_dialogue_uses_defaults_when_optional_voice_files_are_absent(context_root) -> None:
    package = compile_dialogue_package(
        DialogueRequest(
            project_id="demo",
            scene_id="scene-001",
            shot_id="shot-004",
            character_id="roxana",
            text="شکیبا، اینجا امن نیست.",
            emotion="quiet concern",
        )
    )

    assert package["voice_id"] == "roxana-v1"
    assert package["voice_profile"]["timbre"] == "warm and slightly husky"
    assert package["technical"]["sample_rate"] == 48000
    assert package["pronunciation_dictionary"]["entries"]["MCP"]["spoken_form"] == "M C P"


def test_complete_dialogue_pipeline(context_root) -> None:
    shot = ShotRequest(
        project_id="demo",
        shot_id="shot-004",
        scene_id="scene-001",
        character_ids=["roxana"],
        location_id="rooftop",
        shot_type="dialogue",
        action="Roxana quietly warns Shakiba.",
        framing="close-up",
        lens="85mm",
        camera_height="eye level",
        camera_movement="locked",
        emotional_tone="tense concern",
        start_frame="keyframes/shot-004.png",
    )
    dialogue = DialogueRequest(
        project_id="demo",
        scene_id="scene-001",
        shot_id="shot-004",
        character_id="roxana",
        text="شکیبا، اینجا امن نیست.",
        emotion="quiet concern",
    )

    package = compile_cinematic_shot(shot, dialogue_request=dialogue)

    assert package["dialogue"]["audio_path"].endswith("shot-004-roxana.wav")
    assert package["video"]["audio_path"] == package["dialogue"]["audio_path"]
    assert package["music"]["theme"] == "danger"
    assert package["ambience"]["environment"]["weather"] == "light-rain"
    assert package["pipeline"][-1] == "mix_and_edit_scene"
