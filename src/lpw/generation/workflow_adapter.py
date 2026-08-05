from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml


class WorkflowBindingError(RuntimeError):
    """Raised when a semantic workflow binding cannot be applied."""


def load_workflow(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"ComfyUI API workflow not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowBindingError(
            f"ComfyUI API workflow contains invalid JSON: {path}"
        ) from error
    if not isinstance(value, dict):
        raise WorkflowBindingError("ComfyUI API workflow must be a JSON object.")
    return value


def load_bindings(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.is_file():
        raise FileNotFoundError(f"Workflow bindings not found: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise WorkflowBindingError("Workflow bindings must be a YAML object.")
    normalized: dict[str, list[dict[str, str]]] = {}
    for semantic_name, targets in value.items():
        if isinstance(targets, dict):
            targets = [targets]
        if not isinstance(targets, list) or not targets:
            raise WorkflowBindingError(
                f"Binding '{semantic_name}' must contain at least one target."
            )
        normalized_targets = []
        for target in targets:
            if not isinstance(target, dict):
                raise WorkflowBindingError(
                    f"Binding target for '{semantic_name}' must be an object."
                )
            title = target.get("title")
            input_name = target.get("input")
            if not isinstance(title, str) or not title:
                raise WorkflowBindingError(
                    f"Binding target for '{semantic_name}' requires title."
                )
            if not isinstance(input_name, str) or not input_name:
                raise WorkflowBindingError(
                    f"Binding target for '{semantic_name}' requires input."
                )
            normalized_targets.append({"title": title, "input": input_name})
        normalized[str(semantic_name)] = normalized_targets
    return normalized


def find_node_by_title(
    workflow: dict[str, Any], title: str
) -> tuple[str, dict[str, Any]]:
    matches = [
        (node_id, node)
        for node_id, node in workflow.items()
        if isinstance(node, dict) and node.get("_meta", {}).get("title") == title
    ]
    if not matches:
        raise WorkflowBindingError(f'No workflow node has title "{title}".')
    if len(matches) > 1:
        raise WorkflowBindingError(f'Multiple workflow nodes have title "{title}".')
    return matches[0]


def set_node_input(
    workflow: dict[str, Any], *, title: str, input_name: str, value: Any
) -> None:
    node_id, node = find_node_by_title(workflow, title)
    inputs = node.get("inputs")
    if not isinstance(inputs, dict):
        raise WorkflowBindingError(f'Node "{title}" ({node_id}) has no inputs object.')
    if input_name not in inputs:
        available = ", ".join(sorted(inputs))
        raise WorkflowBindingError(
            f'Input "{input_name}" was not found on node "{title}". '
            f"Available inputs: {available}"
        )
    inputs[input_name] = value


def apply_workflow_values(
    workflow_template: dict[str, Any],
    bindings: dict[str, list[dict[str, str]]],
    values: dict[str, Any],
) -> dict[str, Any]:
    """Apply semantic cinematic values to a copied ComfyUI API workflow."""

    workflow = copy.deepcopy(workflow_template)
    for semantic_name, value in values.items():
        for target in bindings.get(semantic_name, []):
            set_node_input(
                workflow,
                title=target["title"],
                input_name=target["input"],
                value=value,
            )
    return workflow
