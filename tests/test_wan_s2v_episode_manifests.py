from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIRECTORY = PROJECT_ROOT / (
    "src/lpw/context/projects/riri-yoyo/generation-records/video-jobs"
)
MANIFESTS = (
    MANIFEST_DIRECTORY
    / "episode-001--moonlit-garden-greeting--wan22-s2v-fp8-480p--v002.yaml",
    MANIFEST_DIRECTORY
    / "episode-002--sharing-shapes--wan22-s2v-fp8-480p--v001.yaml",
)


def load_manifest(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_episode_manifests_use_selected_rtx4090_quality_profile() -> None:
    for path in MANIFESTS:
        manifest = load_manifest(path)

        assert manifest["video"] == {
            "width": 832,
            "height": 480,
            "resolution_class": "480p-landscape",
            "aspect_ratio": "16:9",
            "divisible_by": 16,
            "fps": 16,
            "infer_frames_per_window": 80,
            "logical_frames_per_five_seconds": 81,
            "start_from_reference": True,
        }
        assert manifest["sampling"]["steps"] == 20
        assert manifest["sampling"]["solver"] == "unipc"
        assert manifest["sampling"]["shift"] == 3.0
        assert manifest["sampling"]["guide_scale"] == 5.0
        assert manifest["memory"]["retained_motion_frames"] == 73


def test_episode_manifest_timing_and_window_contracts_are_consistent() -> None:
    for path in MANIFESTS:
        manifest = load_manifest(path)
        contract = manifest["execution_contract"]

        assert contract["final_encoded_frame_count"] == round(
            contract["final_duration_seconds"] * manifest["video"]["fps"]
        )
        assert contract["generated_duration_seconds"] == (
            len(contract["internal_windows"]) * 5
        )
        assert contract["generated_duration_seconds"] >= contract["final_duration_seconds"]


def test_episode_two_uses_vocal_stem_for_s2v_and_song_for_delivery() -> None:
    manifest = load_manifest(MANIFESTS[1])
    conditioning = manifest["inputs"]["conditioning_audio"]

    assert conditioning["vocal_only"] is True
    assert conditioning["path"].endswith("--lead-vocal-only.wav")
    assert manifest["assembly"]["replace_conditioning_audio_with_final_mix"] is True
    assert manifest["assembly"]["final_audio_authority"].endswith(
        "sharing-shapes-v007-seed-950053.wav"
    )
    assert [item["window_id"] for item in manifest["window_prompts"]] == [
        item["window_id"]
        for item in manifest["execution_contract"]["internal_windows"]
    ]


def test_each_episode_has_an_executable_shell_launcher() -> None:
    launchers = (
        PROJECT_ROOT / "scripts/production/run_episode001_wan22_s2v_fp8_480p.sh",
        PROJECT_ROOT / "scripts/production/run_episode002_wan22_s2v_fp8_480p.sh",
    )

    for launcher in launchers:
        assert launcher.is_file()
        assert launcher.stat().st_mode & 0o111


def test_gpu_setup_scripts_install_the_project_package() -> None:
    setup_scripts = (
        PROJECT_ROOT / "scripts/production/setup_rtx3090_wan22_s2v.sh",
        PROJECT_ROOT / "scripts/production/setup_rtx4090_wan22_s2v.sh",
    )

    for setup_script in setup_scripts:
        script = setup_script.read_text(encoding="utf-8")
        assert setup_script.stat().st_mode & 0o111
        assert 'pip install -e "${PROJECT_ROOT}"' in script


def test_rtx3090_setup_downloads_the_model_unless_explicitly_skipped() -> None:
    setup_script = PROJECT_ROOT / "scripts/production/setup_rtx3090_wan22_s2v.sh"
    script = setup_script.read_text(encoding="utf-8")

    assert "LPW_SKIP_MODEL_DOWNLOAD" in script
    assert 'scripts/models/download_wan22_s2v.sh"' in script
