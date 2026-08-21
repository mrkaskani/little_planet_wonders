from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def context_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "context"
    project = root / "projects" / "demo"
    files = {
        root / "studio.yaml": "generation:\n  frame_rate: 30\n",
        project / "project.yaml": (
            "project:\n  id: demo\n"
            "technical:\n  frame_rate: 24\n  aspect_ratio: '2.39:1'\n"
        ),
        project / "visual_style" / "visual_style.yaml": (
            "realism: photorealistic\nforbidden:\n  - anime\n"
        ),
        project / "visual_style" / "palette.yaml": (
            "palette:\n  dominant:\n    blue: '#101827'\n"
        ),
        project / "cinematography" / "camera-language.yaml": (
            "camera_language:\n  closeup:\n    lens: 85mm\n"
        ),
        project / "editing_style.yaml": (
            "timeline:\n"
            "  frame_rate: 24\n"
            "  resolution: 1920x804\n"
            "  aspect_ratio: '2.39:1'\n"
            "cutting:\n  default_transition: hard_cut\n"
        ),
        project / "audios" / "audio.yaml": (
            "dialogue:\n  target_lufs: -16\n"
            "music:\n  dialogue_ducking_db: -6\n"
            "ambience:\n  continuous_room_tone: true\n"
        ),
        project / "audios" / "ambience.yaml": (
            "locations:\n"
            "  kindergarten_garden:\n"
            "    base_layer:\n"
            "      asset: audio-assets/ambience/kindergarten_garden-night-rain.wav\n"
            "    continuity:\n"
            "      preserve_across_cuts: true\n"
        ),
        project / "audios" / "audio-continuity.yaml": (
            "music:\n"
            "  active_cue: tension-theme-02\n"
            "  intensity: 0.45\n"
            "ambience:\n"
            "  active_environment: kindergarten_garden-night-rain\n"
            "active_sounds:\n"
            "  warning_light_hum:\n"
            "    position: west\n"
            "    gain_db: -32\n"
        ),
        project / "characters" / "riri" / "character.yaml": (
            "id: riri\n"
            "reference_images:\n"
            "  face_three_quarter: references/riri-three-quarter.png\n"
        ),
        project / "locations" / "kindergarten_garden" / "location.yaml": (
            "id: kindergarten_garden\n"
            "environment:\n  weather: light-rain\n"
            "reference_images:\n  wide_north: references/kindergarten_garden-wide.png\n"
        ),
        project / "continuity" / "initial-state.yaml": (
            "visual_state:\n  time_of_day: night\n"
        ),
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("CINEMATIC_CONTEXT_ROOT", str(root))
    return root
