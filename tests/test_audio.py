from __future__ import annotations

from lpw.audio.compiler import compile_dialogue_package
from lpw.audio.pipeline import compile_cinematic_shot
from lpw.models import DialogueRequest, ShotRequest


def test_dialogue_uses_defaults_when_optional_voice_files_are_absent(context_root) -> None:
    package = compile_dialogue_package(
        DialogueRequest(
            project_id="demo",
            scene_id="scene-001",
            shot_id="shot-004",
            character_id="riri",
            text="یویو، اینجا امن است.",
            emotion="quiet concern",
        )
    )

    assert package["voice_id"] == "riri-v1"
    assert package["emotion"] == "quiet concern"
    assert package["intensity"] == 0.5
    assert package["voice_profile"]["timbre"] == (
        "smooth, round, light, airy, and non-nasal"
    )
    assert package["technical"]["sample_rate"] == 48000
    assert package["pronunciation_dictionary"]["entries"]["MCP"]["spoken_form"] == "M C P"
    assert package["status"] == "instructions-only"
    assert package["exact_dialogue_required"] is True
    assert package["clean_audio_only"] is True
    assert package["authoritative_audio"] is False


def test_complete_dialogue_pipeline(context_root) -> None:
    shot = ShotRequest(
        project_id="demo",
        shot_id="shot-004",
        scene_id="scene-001",
        character_ids=["riri"],
        location_id="kindergarten_garden",
        shot_type="dialogue",
        action="Riri quietly warns Yoyo.",
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
        character_id="riri",
        text="یویو، اینجا امن است.",
        emotion="quiet concern",
    )

    package = compile_cinematic_shot(shot, dialogue_request=dialogue)

    assert package["shot_id"] == "shot-004"
    assert package["video"]["model"] == "wan2.2-s2v-14b"
    assert package["video"]["frame_rate"] == 24
    assert package["video"]["frame_count"] == 117
    assert package["dialogue"]["character_id"] == "riri"
    assert package["dialogue"]["emotion"] == "quiet concern"
    assert package["dialogue"]["audio_path"].endswith("shot-004-riri.wav")
    assert package["video"]["audio_path"] == package["dialogue"]["audio_path"]
    assert package["music"] == {
        "cue": "tension-theme-02",
        "intensity": 0.45,
        "continue_from_previous_scene": True,
    }
    assert package["ambience"] == {
        "environment": "kindergarten_garden-night-rain",
        "continue_across_cut": True,
    }
    assert package["sound_effects"] == [
        {"id": "warning-light-hum", "position": "west", "gain_db": -32}
    ]
    assert package["mixing"] == {
        "target_lufs": -16,
        "music_ducking_db": -6,
    }
    assert package["context_hash"] == package["video"]["context_hash"]
