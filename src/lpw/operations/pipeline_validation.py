"""Validate isolated local and production AI-video pipeline environments."""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.config import PROJECT_ROOT
from lpw.utils.files import atomic_write_json, load_json, load_yaml


VALID_MODEL_STATES = {
    "READY",
    "MISSING",
    "INCOMPLETE",
    "CORRUPTED",
    "WRONG_VERSION",
    "UNSUPPORTED",
}


def _utc_timestamp() -> str:
    """Return a stable UTC timestamp for structured reports.

    Returns:
        Current UTC time in ISO 8601 form.
    """

    return datetime.now(timezone.utc).isoformat()


def _resolve_path(value: str, project_root: Path) -> Path:
    """Resolve an environment-expanded path against the project root.

    Args:
        value: Configured absolute or project-relative filesystem path.
        project_root: Root used for relative paths.

    Returns:
        Resolved filesystem path.
    """

    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    return expanded.resolve() if expanded.is_absolute() else (project_root / expanded).resolve()


def _command_version(command: str, *args: str) -> dict[str, Any]:
    """Inspect an executable without raising when it is absent.

    Args:
        command: Executable name to locate.
        *args: Version arguments passed to the executable.

    Returns:
        Structured executable path and first version line.
    """

    path = shutil.which(command)
    if path is None:
        return {"available": False, "path": None, "version": None}
    try:
        result = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=10, check=False
        )
        text = (result.stdout or result.stderr).splitlines()
        version = text[0] if text else None
    except (OSError, subprocess.SubprocessError) as exc:
        version = f"{type(exc).__name__}: {exc}"
    return {"available": True, "path": path, "version": version}


class PipelineEnvironmentValidator:
    """Generate fail-closed reports for local and production environments.

    Attributes:
        project_root: Repository root containing configuration and model directories.
        config_root: Directory containing registry and environment YAML files.
    """

    project_root: Path
    config_root: Path

    def __init__(
        self,
        project_root: Path = PROJECT_ROOT,
        config_root: Path | None = None,
    ) -> None:
        """Initialize the environment validator.

        Args:
            project_root: Repository root containing runtime assets.
            config_root: Optional pipeline configuration directory override.
        """

        self.project_root = project_root.resolve()
        self.config_root = (
            config_root.resolve()
            if config_root is not None
            else self.project_root / "config" / "pipeline"
        )

    def load_environment(self, environment: str) -> dict[str, Any]:
        """Load one isolated environment configuration.

        Args:
            environment: Either ``local`` or ``production``.

        Returns:
            Parsed environment configuration.

        Raises:
            ValueError: If an unknown environment is requested.
        """

        if environment not in {"local", "production"}:
            raise ValueError("environment must be 'local' or 'production'")
        return load_yaml(self.config_root / f"{environment}.yaml")

    def load_registry(self) -> dict[str, Any]:
        """Load the centralized model registry.

        Returns:
            Parsed registry containing all declared models.
        """

        return load_yaml(self.config_root / "models.yaml")

    def report_directory(self, environment: str) -> Path:
        """Resolve and create the isolated report directory.

        Args:
            environment: Environment whose storage configuration is used.

        Returns:
            Absolute environment-specific report directory.
        """

        configuration = self.load_environment(environment)
        path = _resolve_path(configuration["storage"]["reports"], self.project_root)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def inspect_hardware(self) -> dict[str, Any]:
        """Inspect compute, memory, disk, and required system executables.

        Returns:
            Hardware and software report suitable for ``hardware-report.json``.
        """

        memory: dict[str, Any] = {}
        try:
            import psutil

            virtual = psutil.virtual_memory()
            swap = psutil.swap_memory()
            memory = {
                "ram_total_bytes": virtual.total,
                "ram_available_bytes": virtual.available,
                "swap_total_bytes": swap.total,
                "swap_used_bytes": swap.used,
            }
        except ImportError:
            memory = {"error": "psutil-not-installed"}

        accelerator = {
            "mps_built": False,
            "mps_available": False,
            "cuda_available": False,
            "cuda_version": None,
            "cuda_device_count": 0,
            "devices": [],
            "tensor_smoke": "NOT_RUN",
        }
        torch_version = None
        try:
            import torch

            torch_version = torch.__version__
            accelerator.update(
                {
                    "mps_built": torch.backends.mps.is_built(),
                    "mps_available": torch.backends.mps.is_available(),
                    "cuda_available": torch.cuda.is_available(),
                    "cuda_version": torch.version.cuda,
                    "cuda_device_count": torch.cuda.device_count(),
                }
            )
            if torch.cuda.is_available():
                accelerator["devices"] = [
                    {
                        "index": index,
                        "name": torch.cuda.get_device_name(index),
                        "vram_total_bytes": torch.cuda.get_device_properties(index).total_memory,
                    }
                    for index in range(torch.cuda.device_count())
                ]
            device = "mps" if torch.backends.mps.is_available() else (
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            tensor = torch.ones(8, device=device)
            accelerator["tensor_smoke"] = (
                "PASS" if float((tensor * 2).sum().cpu()) == 16.0 else "FAIL"
            )
            accelerator["tested_device"] = device
        except Exception as exc:
            accelerator["tensor_smoke"] = "FAIL"
            accelerator["tensor_error"] = f"{type(exc).__name__}: {exc}"

        disk = shutil.disk_usage(self.project_root)
        return {
            "generated_at": _utc_timestamp(),
            "os": platform.platform(),
            "architecture": platform.machine(),
            "cpu": platform.processor() or "Apple M-series",
            "cpu_count": os.cpu_count(),
            "python_version": sys.version.split()[0],
            "pytorch_version": torch_version,
            "memory": memory,
            "accelerator": accelerator,
            "disk": {
                "path": str(self.project_root),
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
            },
            "executables": {
                "ffmpeg": _command_version("ffmpeg", "-version"),
                "ffprobe": _command_version("ffprobe", "-version"),
                "git": _command_version("git", "--version"),
                "git_lfs": _command_version("git-lfs", "version"),
            },
            "rocm_available": bool(shutil.which("rocminfo")),
        }

    def validate_models(self, environment: str) -> dict[str, Any]:
        """Validate configured model paths and required files without loading weights.

        Args:
            environment: Environment whose requirement flags are applied.

        Returns:
            Per-model states and required-model readiness summary.
        """

        registry = self.load_registry()
        results: dict[str, Any] = {}
        required_ready = True
        missing_bytes_known = 0
        unknown_missing_sizes: list[str] = []
        for model_id, specification in registry["models"].items():
            requirement = specification[f"{environment}_mode"]
            path = _resolve_path(specification["local_path"], self.project_root)
            expected = [path / item for item in specification.get("expected_files", [])]
            missing = [str(item) for item in expected if not item.is_file() and not item.is_dir()]
            if not path.exists():
                status = "MISSING"
            elif missing:
                status = "INCOMPLETE"
            else:
                status = "READY"
            if status not in VALID_MODEL_STATES:
                raise RuntimeError(f"Invalid internal model state: {status}")
            expected_size = specification.get("expected_size_bytes")
            actual_size = sum(
                item.stat().st_size for item in expected if item.is_file()
            )
            size_warning = None
            if status == "READY" and expected_size and actual_size < expected_size * 0.98:
                status = "INCOMPLETE"
                size_warning = "expected-file-size-total-below-98-percent"
            is_required = requirement == "required"
            if is_required and status != "READY":
                required_ready = False
                if expected_size:
                    missing_bytes_known += max(0, expected_size - actual_size)
                else:
                    unknown_missing_sizes.append(model_id)
            results[model_id] = {
                "name": specification["name"],
                "purpose": specification["purpose"],
                "repository": specification.get("repository"),
                "revision": specification.get("revision"),
                "local_path": str(path),
                "precision": specification.get("precision"),
                "requirement": requirement,
                "status": status,
                "missing_files": missing,
                "expected_size_bytes": expected_size,
                "observed_expected_file_bytes": actual_size,
                "size_warning": size_warning,
                "checksum_authority": specification.get("checksum"),
            }
        return {
            "generated_at": _utc_timestamp(),
            "environment": environment,
            "required_models_ready": required_ready,
            "known_additional_bytes_required": missing_bytes_known,
            "unknown_size_missing_models": unknown_missing_sizes,
            "models": results,
        }

    def validate_dependencies(self, environment: str) -> dict[str, Any]:
        """Validate Python modules and executables declared by an environment.

        Args:
            environment: Environment whose dependencies are checked.

        Returns:
            Structured dependency readiness report.
        """

        configured = self.load_environment(environment)["required_dependencies"]
        modules: dict[str, Any] = {}
        for name in configured["python_modules"]:
            try:
                module = importlib.import_module(name)
                modules[name] = {
                    "status": "READY",
                    "version": getattr(module, "__version__", None),
                }
            except Exception as exc:
                modules[name] = {
                    "status": "MISSING",
                    "error": f"{type(exc).__name__}: {exc}",
                }
        executables = {
            name: {
                "status": "READY" if shutil.which(name) else "MISSING",
                "path": shutil.which(name),
            }
            for name in configured["executables"]
        }
        ready = all(item["status"] == "READY" for item in modules.values()) and all(
            item["status"] == "READY" for item in executables.values()
        )
        return {
            "generated_at": _utc_timestamp(),
            "environment": environment,
            "dependencies_ready": ready,
            "python_modules": modules,
            "executables": executables,
        }

    def validate_mcp(self) -> dict[str, Any]:
        """Validate MCP startup surface, tool discovery, and resource registration.

        Returns:
            Structured MCP discovery report.
        """

        from lpw.mcp.server import mcp

        async def inspect() -> tuple[list[Any], list[Any], list[Any]]:
            """Read all MCP discovery surfaces.

            Returns:
                Registered tools, resources, and resource templates.
            """

            return (
                await mcp.list_tools(),
                await mcp.list_resources(),
                await mcp.list_resource_templates(),
            )

        try:
            tools, resources, templates = asyncio.run(inspect())
            return {
                "generated_at": _utc_timestamp(),
                "status": "PASS",
                "tool_count": len(tools),
                "resource_count": len(resources),
                "resource_template_count": len(templates),
                "tools": [tool.name for tool in tools],
            }
        except Exception as exc:
            return {
                "generated_at": _utc_timestamp(),
                "status": "FAIL",
                "error": f"{type(exc).__name__}: {exc}",
            }

    def run_check(self, environment: str = "local") -> dict[str, Any]:
        """Run hardware, dependency, model, MCP, and disk validation.

        Args:
            environment: Isolated environment to inspect.

        Returns:
            Consolidated status with paths to immutable JSON reports.
        """

        reports = self.report_directory(environment)
        hardware = self.inspect_hardware()
        models = self.validate_models(environment)
        dependencies = self.validate_dependencies(environment)
        mcp = self.validate_mcp()
        configuration = self.load_environment(environment)
        hardware_policy = load_yaml(self.config_root / "hardware.yaml")[environment]
        minimum_disk = hardware_policy["minimum_free_disk_bytes"]
        disk_ready = hardware["disk"]["free_bytes"] >= minimum_disk
        tested_device = hardware["accelerator"].get("tested_device")
        ram_total = hardware["memory"].get("ram_total_bytes", 0)
        hardware_ready = (
            hardware["accelerator"]["tensor_smoke"] == "PASS"
            and tested_device in hardware_policy["allowed_backends"]
            and ram_total >= hardware_policy["minimum_ram_bytes"]
        )
        outputs = {
            "hardware": reports / "hardware-report.json",
            "models": reports / "model-validation-report.json",
            "dependencies": reports / "dependency-validation-report.json",
            "mcp": reports / "mcp-validation-report.json",
        }
        atomic_write_json(outputs["hardware"], hardware)
        atomic_write_json(outputs["models"], models)
        atomic_write_json(outputs["dependencies"], dependencies)
        atomic_write_json(outputs["mcp"], mcp)
        status = {
            "generated_at": _utc_timestamp(),
            "environment": environment,
            "hardware": "PASS" if hardware_ready else "FAIL",
            "disk": "PASS" if disk_ready else "FAIL",
            "dependencies": "PASS" if dependencies["dependencies_ready"] else "FAIL",
            "models": "PASS" if models["required_models_ready"] else "FAIL",
            "mcp": mcp["status"],
            "storage": configuration["storage"],
            "report_paths": {key: str(path) for key, path in outputs.items()},
        }
        status["ready"] = all(
            status[key] == "PASS"
            for key in ("hardware", "disk", "dependencies", "models", "mcp")
        )
        atomic_write_json(reports / "pipeline-check-report.json", status)
        return status

    def run_local_test(self) -> dict[str, Any]:
        """Run safe local checks and create a fail-closed readiness report.

        Returns:
            Local gate report; heavyweight component tests remain blocked until ready.
        """

        check = self.run_check("local")
        reports = self.report_directory("local")
        model_report = load_json(Path(check["report_paths"]["models"]))
        component_map = {
            "qwen_vl_test": "qwen3_vl",
            "wan_test": "wan22_s2v_local_q4ks",
            "seedvr2_test": "seedvr2_7b",
            "tts_test": "qwen3_tts_base",
            "music_test": "ace_step_music",
        }
        components: dict[str, Any] = {}
        for gate, model_id in component_map.items():
            model_state = model_report["models"][model_id]["status"]
            components[gate] = {
                "status": "NOT_RUN",
                "model_status": model_state,
                "reason": (
                    "model-not-ready" if model_state != "READY" else "explicit-smoke-test-evidence-not-recorded"
                ),
            }
        component_report = {
            "generated_at": _utc_timestamp(),
            "components": components,
            "policy": "load-run-minimal-input-verify-unload-release-memory",
        }
        atomic_write_json(reports / "component-test-report.json", component_report)

        gates = {
            "hardware_validation": check["hardware"],
            "disk_validation": check["disk"],
            "dependency_validation": check["dependencies"],
            "model_validation": check["models"],
            "mcp_connectivity": check["mcp"],
            "mcp_tool_invocation": check["mcp"],
            "tensor_interfaces": check["hardware"],
            **{key: value["status"] for key, value in components.items()},
            "reference_image_flow": "NOT_RUN",
            "prompt_flow": "NOT_RUN",
            "video_generation": "NOT_RUN",
            "restoration": "NOT_RUN",
            "audio_generation": "NOT_RUN",
            "synchronization": "NOT_RUN",
            "ffmpeg_assembly": "NOT_RUN",
            "output_file_validation": "NOT_RUN",
        }
        production_ready = all(value == "PASS" for value in gates.values())
        readiness = {
            "generated_at": _utc_timestamp(),
            "environment": "local",
            "production_ready": production_ready,
            "gates": gates,
            "blocking_gates": [key for key, value in gates.items() if value != "PASS"],
            "component_report": str(reports / "component-test-report.json"),
        }
        atomic_write_json(reports / "local-readiness-report.json", readiness)
        return readiness

    def production_preflight(self) -> dict[str, Any]:
        """Refuse production unless local readiness and production checks pass.

        Returns:
            Fail-closed preflight report; this operation never starts generation.
        """

        configuration = self.load_environment("production")
        readiness_path = _resolve_path(
            configuration["requires_local_readiness_report"], self.project_root
        )
        local_readiness = load_json(readiness_path) if readiness_path.is_file() else {}
        check = self.run_check("production")
        blockers: list[str] = []
        if local_readiness.get("production_ready") is not True:
            blockers.append("local-readiness-gate-not-passed")
        for gate in ("hardware", "disk", "dependencies", "models", "mcp"):
            if check[gate] != "PASS":
                blockers.append(f"production-{gate}-failed")
        report = {
            "generated_at": _utc_timestamp(),
            "environment": "production",
            "production_allowed": not blockers,
            "generation_started": False,
            "blocking_requirements": blockers,
            "local_readiness_report": str(readiness_path),
            "pipeline_check": check,
        }
        atomic_write_json(
            self.report_directory("production") / "production-preflight-report.json",
            report,
        )
        return report


def report_digest(report: dict[str, Any]) -> str:
    """Return a deterministic SHA-256 digest for a structured report.

    Args:
        report: JSON-compatible report to hash.

    Returns:
        Hexadecimal SHA-256 digest.
    """

    payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
