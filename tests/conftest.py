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
            "ambience:\n  continuous_room_tone: true\n"
        ),
        project / "characters" / "roxana" / "character.yaml": (
            "id: roxana\n"
            "reference_images:\n"
            "  face_three_quarter: references/roxana-three-quarter.png\n"
        ),
        project / "locations" / "rooftop" / "location.yaml": (
            "id: rooftop\n"
            "environment:\n  weather: light-rain\n"
            "reference_images:\n  wide_north: references/rooftop-wide.png\n"
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
