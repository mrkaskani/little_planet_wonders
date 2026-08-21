from __future__ import annotations

from pathlib import Path

import yaml

from lpw.context.preproduction_validation import validate_preproduction


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "lpw"
    / "context"
    / "projects"
    / "riri-yoyo"
)


def test_current_preproduction_has_no_technical_validation_errors() -> None:
    report = validate_preproduction(PROJECT_ROOT)

    assert report["errors"] == []
    assert report["status"] == "passed"


def test_strict_approval_mode_reports_open_location_reference_sets() -> None:
    report = validate_preproduction(PROJECT_ROOT, strict_approvals=True)

    assert report["status"] == "failed"
    assert not any("listening review" in issue for issue in report["errors"])
    assert any(
        "reference-set-v001 (planned)" in issue for issue in report["errors"]
    )


def test_validator_rejects_animate_and_missing_core_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "project.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "demo",
                "type": "project-context",
                "wan_2_2": {
                    "supported_tasks": ["t2v", "animate"],
                    "unsupported_tasks": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (project / "preproduction-checklist.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "demo-checklist",
                "type": "checklist",
                "required_files": {"core": ["missing.yaml"]},
            }
        ),
        encoding="utf-8",
    )

    report = validate_preproduction(project)

    assert report["status"] == "failed"
    assert any("supported Wan tasks mismatch" in issue for issue in report["errors"])
    assert any("Wan Animate" in issue for issue in report["errors"])
    assert any("missing.yaml" in issue for issue in report["errors"])
