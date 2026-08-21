from __future__ import annotations

import hashlib
import struct
import wave
from pathlib import Path
from typing import Any, Iterable

import yaml


SUPPORTED_WAN_TASKS = {"t2v", "i2v", "ti2v", "s2v"}


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"expected a mapping at the YAML root: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def _required_files(checklist: dict[str, Any]) -> Iterable[str]:
    for values in checklist.get("required_files", {}).values():
        if isinstance(values, list):
            yield from (str(value) for value in values)


def _reference_records(registry: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("character_references", "style_material_and_lighting_references"):
        records = registry.get(key, [])
        if isinstance(records, list):
            yield from (record for record in records if isinstance(record, dict))

    generation = registry.get("generation_frame_references", {})
    if isinstance(generation, dict):
        records = generation.get("records", [])
        if isinstance(records, list):
            yield from (record for record in records if isinstance(record, dict))

    locations = registry.get("location_references", {})
    if isinstance(locations, dict):
        defaults = locations.get("shared_defaults", {})
        for record in locations.get("records", []):
            if isinstance(record, dict):
                yield {**defaults, **record}

    for key in (
        "prop_references",
        "vehicle_references",
        "background_character_references",
    ):
        section = registry.get(key, {})
        if isinstance(section, dict):
            records = section.get("records", [])
            if isinstance(records, list):
                yield from (record for record in records if isinstance(record, dict))


def _add_reference_issues(
    project_root: Path,
    registry: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    strict_approvals: bool,
) -> None:
    for record in _reference_records(registry):
        reference_id = str(record.get("id", "unknown-reference"))
        status = record.get("status")
        relative = record.get("path")

        if status in {"planned", "candidate", "technical-review", "creative-review"}:
            message = f"reference not approved: {reference_id} ({status})"
            (errors if strict_approvals else warnings).append(message)

        if relative is None:
            if status == "approved":
                errors.append(f"approved reference has no path: {reference_id}")
            continue

        path = project_root / str(relative)
        if not path.is_file():
            errors.append(f"reference path missing: {reference_id}: {relative}")
            continue

        expected_hash = record.get("sha256")
        actual_hash = _sha256(path)
        if not expected_hash or expected_hash == "pending-validation":
            errors.append(f"reference hash missing: {reference_id}")
        elif expected_hash != actual_hash:
            errors.append(f"reference hash mismatch: {reference_id}")

        if path.suffix.lower() == ".png":
            dimensions = _png_dimensions(path)
            if dimensions is None:
                if status == "approved":
                    errors.append(f"approved PNG is invalid: {reference_id}")
                continue
            recorded = record.get("pixel-dimensions")
            actual = f"{dimensions[0]}x{dimensions[1]}"
            if status == "approved" and recorded != actual:
                errors.append(
                    f"approved image dimensions mismatch: {reference_id}: "
                    f"recorded={recorded}, actual={actual}"
                )


def _add_voice_audit_issues(
    project_root: Path,
    audit: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    strict_approvals: bool,
) -> None:
    records = audit.get("records", [])
    if len(records) != 10:
        errors.append(f"voice audit expected 10 records, found {len(records)}")
    for record in records:
        record_id = str(record.get("id", "unknown-voice-reference"))
        path = project_root / str(record.get("path", ""))
        if not path.is_file():
            errors.append(f"voice reference missing: {record_id}")
            continue
        if _sha256(path) != record.get("sha256"):
            errors.append(f"voice reference hash mismatch: {record_id}")
        try:
            with wave.open(str(path), "rb") as stream:
                metadata = {
                    "sample_rate_hz": stream.getframerate(),
                    "channels": stream.getnchannels(),
                    "bit_depth": stream.getsampwidth() * 8,
                }
        except (wave.Error, EOFError) as exc:
            errors.append(f"voice reference WAV invalid: {record_id}: {exc}")
            continue
        for key, value in metadata.items():
            if record.get(key) != value:
                errors.append(
                    f"voice reference metadata mismatch: {record_id}: {key}"
                )

    if audit.get("listening_review", {}).get("status") != "approved":
        message = "voice-reference listening review remains required"
        (errors if strict_approvals else warnings).append(message)


def _add_dry_run_issues(
    project_root: Path, errors: list[str], warnings: list[str]
) -> None:
    path = project_root / "validation" / "dry-run-manifests.yaml"
    if not path.is_file():
        errors.append("dry-run manifest registry is missing")
        return
    document = _load_yaml(path)
    manifests = document.get("manifests", [])
    found = {manifest.get("task") for manifest in manifests if isinstance(manifest, dict)}
    if found != SUPPORTED_WAN_TASKS:
        errors.append(f"dry-run tasks mismatch: {sorted(found)}")
    for manifest in manifests:
        if not isinstance(manifest, dict):
            errors.append("dry-run manifest entry must be a mapping")
            continue
        task = manifest.get("task")
        if manifest.get("queues_generation") is not False:
            errors.append(f"dry-run queues generation: {task}")
        if manifest.get("downloads_weights") is not False:
            errors.append(f"dry-run downloads weights: {task}")
        if manifest.get("enables_provider") is not False:
            errors.append(f"dry-run enables provider: {task}")
        readiness = manifest.get("readiness")
        if task in {"i2v", "s2v"} and readiness != "blocked-missing-approved-inputs":
            errors.append(f"identity-critical dry-run must be blocked: {task}")
        if readiness == "blocked-missing-approved-inputs":
            warnings.append(f"dry-run correctly blocked pending inputs: {task}")


def validate_preproduction(
    project_root: Path | str, *, strict_approvals: bool = False
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    yaml_documents: dict[Path, dict[str, Any]] = {}
    for path in sorted(root.rglob("*.yaml")):
        try:
            yaml_documents[path] = _load_yaml(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"YAML parse error: {path.relative_to(root)}: {exc}")
    info.append(f"parsed YAML files: {len(yaml_documents)}")

    checklist_path = root / "preproduction-checklist.yaml"
    if not checklist_path.is_file():
        errors.append("preproduction-checklist.yaml is missing")
        checklist: dict[str, Any] = {}
    else:
        checklist = yaml_documents.get(checklist_path, _load_yaml(checklist_path))
    for relative in _required_files(checklist):
        if not (root / relative).is_file():
            errors.append(f"required preproduction file missing: {relative}")

    seen: dict[tuple[str, str], Path] = {}
    for path, document in yaml_documents.items():
        document_id = document.get("id")
        document_type = document.get("type")
        if not document_id or not document_type:
            continue
        key = (str(document_type), str(document_id))
        if key in seen:
            errors.append(
                f"duplicate typed YAML id {key}: {seen[key].relative_to(root)} "
                f"and {path.relative_to(root)}"
            )
        else:
            seen[key] = path

    project = yaml_documents.get(root / "project.yaml", {})
    tasks = set(project.get("wan_2_2", {}).get("supported_tasks", []))
    if tasks != SUPPORTED_WAN_TASKS:
        errors.append(f"supported Wan tasks mismatch: {sorted(tasks)}")
    unsupported = set(project.get("wan_2_2", {}).get("unsupported_tasks", []))
    if "animate" not in unsupported:
        errors.append("Wan Animate is not explicitly disabled")

    for relative, count_key in (
        ("assets/props.yaml", "actual_recurring_props_defined"),
        ("assets/costumes.yaml", "actual_approved_costumes_defined"),
        ("assets/vehicles.yaml", "actual_approved_vehicles_defined"),
        ("assets/background-characters.yaml", "actual_approved_background_characters"),
    ):
        document = yaml_documents.get(root / relative, {})
        registry = document.get("registry", [])
        count = document.get("catalog_policy", {}).get(count_key)
        if count != len(registry):
            errors.append(
                f"catalog count mismatch: {relative}: declared={count}, actual={len(registry)}"
            )

    registry_path = root / "references.yaml"
    if registry_path.is_file():
        _add_reference_issues(
            root,
            yaml_documents.get(registry_path, _load_yaml(registry_path)),
            errors,
            warnings,
            strict_approvals,
        )
    else:
        errors.append("references.yaml is missing")

    voice_path = root / "audios" / "voice-reference-audit.yaml"
    if voice_path.is_file():
        _add_voice_audit_issues(
            root,
            yaml_documents.get(voice_path, _load_yaml(voice_path)),
            errors,
            warnings,
            strict_approvals,
        )
    else:
        errors.append("voice-reference audit is missing")

    _add_dry_run_issues(root, errors, warnings)

    return {
        "project_root": str(root),
        "strict_approvals": strict_approvals,
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }

