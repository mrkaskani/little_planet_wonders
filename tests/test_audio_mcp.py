from __future__ import annotations

import asyncio
import json

from lpw.mcp.server import mcp


def test_audio_resources_and_dialogue_tool_are_exposed(context_root) -> None:
    async def exercise_mcp():
        audio_result = await mcp.read_resource("cinema://projects/demo/audio")
        voice_result = await mcp.read_resource(
            "cinema://projects/demo/voices/riri"
        )
        dialogue_result = await mcp.call_tool(
            "compile_dialogue",
            {
                "project_id": "demo",
                "scene_id": "scene-001",
                "shot_id": "shot-004",
                "character_id": "riri",
                "text": "یویو، اینجا امن است.",
                "emotion": "quiet concern",
                "intensity": 0.5,
                "language": "Persian",
            },
        )
        return (
            json.loads(audio_result[0].content),
            json.loads(voice_result[0].content),
            dialogue_result.structured_content,
        )

    audio, voice, dialogue = asyncio.run(exercise_mcp())

    assert audio["continuity"]["music"]["active_cue"] == "tension-theme-02"
    assert audio["mixing"]["loudness"]["web_target_lufs"] == -16
    assert voice["generation"]["voice_id"] == "riri-v1"
    assert dialogue["voice_id"] == "riri-v1"
    assert dialogue["emotion"] == "quiet concern"


def test_complete_shot_package_is_exposed_as_an_mcp_tool(context_root) -> None:
    async def compile_package():
        return await mcp.call_tool(
            "compile_cinematic_shot",
            {
                "project_id": "demo",
                "shot_id": "shot-004",
                "scene_id": "scene-001",
                "character_ids": ["riri"],
                "location_id": "kindergarten_garden",
                "shot_type": "dialogue",
                "action": "Riri quietly warns Yoyo.",
                "framing": "close-up",
                "lens": "85mm",
                "camera_height": "eye level",
                "camera_movement": "locked",
                "emotional_tone": "tense concern",
                "dialogue_character_id": "riri",
                "dialogue_text": "یویو، اینجا امن است.",
                "dialogue_emotion": "quiet concern",
                "start_frame": "shot-004-keyframe.png",
            },
        )

    result = asyncio.run(compile_package())
    package = result.structured_content

    assert result.is_error is False
    assert package["video"]["model"] == "wan2.2-s2v-14b"
    assert package["dialogue"]["voice_id"] == "riri-v1"
    assert package["music"]["cue"] == "tension-theme-02"
    assert package["ambience"]["environment"] == "kindergarten_garden-night-rain"
    assert package["sound_effects"][0]["id"] == "warning-light-hum"
    assert package["mixing"]["target_lufs"] == -16
