from __future__ import annotations

from pathlib import Path

import pytest

from lpw.audio.music import compile_music_cue_sheet
from lpw.audio.sound_effects import compile_sound_cue_sheet
from lpw.audio.voice_production import VoiceProductionService
from lpw.generation.pipeline import GenerationPipelineError


def test_exact_dialogue_must_be_reviewed_and_locked_before_lip_sync(
    context_root: Path,
    tmp_path: Path,
) -> None:
    service = VoiceProductionService(tmp_path / "runtime")
    package = service.prepare_exact_dialogue(
        project_id="demo",
        episode_id="episode-001",
        scene_id="scene-001",
        shot_id="shot-004",
        character_id="riri",
        exact_dialogue="یویو، اینجا امن است.",
        language="Persian",
        primary_emotion="mild concern",
        ending_emotion="reassuring",
        emotional_intensity=0.4,
        important_words=["یویو", "امن"],
        pause_instructions=["short pause after the name"],
        gesture_guidance="one small open-hand gesture",
        facial_expression_guidance="mild concern becoming reassuring",
    )

    assert package["status"] == "awaiting-generation"
    assert package["provider"]["status"] == "not-run"
    assert package["clean_audio_only"] is True
    assert package["primary_emotional_reference"]
    with pytest.raises(FileNotFoundError):
        service.compile_lip_sync_context(
            project_id="demo",
            episode_id="episode-001",
            scene_id="scene-001",
            shot_id="shot-004",
            character_id="riri",
            dialogue_version=1,
        )

    audio = tmp_path / "provider-dialogue.wav"
    audio.write_bytes(b"reviewed-exact-dialogue")
    with pytest.raises(GenerationPipelineError, match="exactly match"):
        service.lock_exact_dialogue(
            project_id="demo",
            episode_id="episode-001",
            scene_id="scene-001",
            shot_id="shot-004",
            character_id="riri",
            dialogue_version=1,
            audio_path=str(audio),
            verified_transcript="different words",
            reviewer="voice-director",
            review={field: True for field in (
                "identity",
                "dialogue_accuracy",
                "emotional_safety",
                "listening_comfort",
            )},
        )

    approval = service.lock_exact_dialogue(
        project_id="demo",
        episode_id="episode-001",
        scene_id="scene-001",
        shot_id="shot-004",
        character_id="riri",
        dialogue_version=1,
        audio_path=str(audio),
        verified_transcript="یویو، اینجا امن است.",
        reviewer="voice-director",
        review={
            "identity": True,
            "dialogue_accuracy": True,
            "emotional_safety": True,
            "listening_comfort": True,
        },
    )
    lip_sync = service.compile_lip_sync_context(
        project_id="demo",
        episode_id="episode-001",
        scene_id="scene-001",
        shot_id="shot-004",
        character_id="riri",
        dialogue_version=1,
    )

    assert approval["status"] == "locked"
    assert approval["audio_sha256"]
    assert lip_sync["status"] == "ready-for-lip-sync"
    assert lip_sync["locked_audio_sha256"] == approval["audio_sha256"]
    assert lip_sync["generation_provider"]["status"] == "not-run"


def test_sound_cues_preserve_dialogue_and_reject_unsafe_qualities(
    context_root: Path,
) -> None:
    sheet = compile_sound_cue_sheet(
        project_id="demo",
        scene_id="scene-001",
        shot_id="shot-005",
        location_id="kindergarten_garden",
        dialogue_present=True,
        cues=[
            {
                "cue_id": "ball-roll-soft",
                "category": "prop",
                "source": "red rubber ball",
                "action": "rolls and stops",
                "story_purpose": "make the visible movement understandable",
                "material": "soft rubber",
                "start_seconds": 1.0,
                "end_seconds": 3.0,
                "volume": "soft",
                "distance": "close",
            }
        ],
    )

    assert sheet["cues"][0]["relationship_to_dialogue"] == (
        "reduce-beneath-dialogue"
    )
    assert sheet["cues"][0]["provider"]["status"] == "not-run"
    with pytest.raises(ValueError, match="forbidden qualities"):
        compile_sound_cue_sheet(
            project_id="demo",
            scene_id="scene-001",
            shot_id="shot-005",
            location_id="kindergarten_garden",
            dialogue_present=False,
            cues=[
                {
                    "cue_id": "unsafe-impact",
                    "category": "prop",
                    "source": "toy",
                    "action": "falls",
                    "story_purpose": "show the fall",
                    "qualities": ["explosive"],
                }
            ],
        )


def test_music_cues_compile_child_response_space(context_root: Path) -> None:
    sheet = compile_music_cue_sheet(
        project_id="demo",
        episode_id="episode-001",
        scene_id="scene-001",
        dialogue_present=True,
        cues=[
            {
                "cue_id": "curious-question",
                "action": "reduce",
                "theme": "riri",
                "start_seconds": 4,
                "end_seconds": 12,
                "energy": "low",
                "instrumentation": ["soft piano", "gentle flute"],
                "participation_pause": {
                    "start_seconds": 6,
                    "duration_seconds": 4,
                },
            }
        ],
    )

    cue = sheet["cues"][0]
    assert cue["dialogue_relationship"] == "duck-and-simplify"
    assert cue["participation_pause"]["remove_percussion"] is True
    assert cue["participation_pause"]["do_not_reveal_answer"] is True
    assert cue["provider"]["status"] == "not-run"
