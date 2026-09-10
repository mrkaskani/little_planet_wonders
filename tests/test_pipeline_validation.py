"""Test isolated local readiness and fail-closed production preflight behavior."""

from __future__ import annotations

from pathlib import Path

import yaml

from lpw.operations.pipeline_validation import PipelineEnvironmentValidator


def _write_yaml(path: Path, content: dict) -> None:
    """Write a YAML mapping for an isolated test configuration.

    Args:
        path: Destination YAML path.
        content: Mapping serialized into the file.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")


def _validator(tmp_path: Path) -> PipelineEnvironmentValidator:
    """Create a validator with minimal isolated configuration.

    Args:
        tmp_path: Temporary repository root.

    Returns:
        Validator configured entirely below the temporary directory.
    """

    config = tmp_path / "config" / "pipeline"
    common_storage = {
        "data": "runtime/local/data",
        "logs": "runtime/local/logs",
        "cache": "runtime/local/cache",
        "outputs": "runtime/local/outputs",
        "jobs": "runtime/local/jobs",
        "reports": "runtime/local/reports",
    }
    dependencies = {"python_modules": ["json"], "executables": ["git"]}
    _write_yaml(
        config / "local.yaml",
        {
            "environment": "local",
            "storage": common_storage,
            "required_dependencies": dependencies,
        },
    )
    production_storage = {
        key: value.replace("local", "production")
        for key, value in common_storage.items()
    }
    _write_yaml(
        config / "production.yaml",
        {
            "environment": "production",
            "requires_local_readiness_report": (
                "runtime/local/reports/local-readiness-report.json"
            ),
            "storage": production_storage,
            "required_dependencies": dependencies,
        },
    )
    _write_yaml(
        config / "hardware.yaml",
        {
            "local": {
                "allowed_backends": ["cpu", "mps", "cuda"],
                "minimum_ram_bytes": 1,
                "minimum_free_disk_bytes": 1,
            },
            "production": {
                "allowed_backends": ["cuda"],
                "minimum_ram_bytes": 1,
                "minimum_free_disk_bytes": 1,
            },
        },
    )
    _write_yaml(
        config / "models.yaml",
        {
            "models": {
                "qwen3_vl": {
                    "name": "Qwen3-VL",
                    "purpose": "qa",
                    "repository": "example/qwen",
                    "revision": "pinned",
                    "local_path": "models/qwen",
                    "expected_files": ["config.json", "model.safetensors"],
                    "expected_size_bytes": None,
                    "precision": "bf16",
                    "local_mode": "required",
                    "production_mode": "required",
                    "checksum": None,
                }
            }
        },
    )
    return PipelineEnvironmentValidator(tmp_path, config)


def test_model_validation_distinguishes_missing_incomplete_and_ready(tmp_path) -> None:
    validator = _validator(tmp_path)
    model = tmp_path / "models" / "qwen"

    assert validator.validate_models("local")["models"]["qwen3_vl"]["status"] == "MISSING"
    model.mkdir(parents=True)
    (model / "config.json").write_text("{}", encoding="utf-8")
    assert validator.validate_models("local")["models"]["qwen3_vl"]["status"] == "INCOMPLETE"
    (model / "model.safetensors").write_bytes(b"weights")
    report = validator.validate_models("local")
    assert report["models"]["qwen3_vl"]["status"] == "READY"
    assert report["required_models_ready"] is True


def test_production_preflight_cannot_bypass_missing_local_readiness(tmp_path) -> None:
    validator = _validator(tmp_path)
    validator.run_check = lambda environment="local": {
        "hardware": "PASS",
        "disk": "PASS",
        "dependencies": "PASS",
        "models": "PASS",
        "mcp": "PASS",
    }

    report = validator.production_preflight()

    assert report["production_allowed"] is False
    assert report["generation_started"] is False
    assert "local-readiness-gate-not-passed" in report["blocking_requirements"]
