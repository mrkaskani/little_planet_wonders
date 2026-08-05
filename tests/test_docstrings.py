"""Enforce complete production docstrings for modules, classes, and functions."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [
    PROJECT_ROOT / name
    for name in ("audio.py", "context_loader.py", "prompt_compiler.py", "server.py")
] + sorted((PROJECT_ROOT / "src" / "lpw").rglob("*.py"))


@pytest.mark.parametrize(
    "path",
    PRODUCTION_FILES,
    ids=lambda path: str(path.relative_to(PROJECT_ROOT)),
)
def test_production_docstrings_describe_modules_parameters_and_returns(
    path: Path,
) -> None:
    """Require documentation contracts on every production definition.

    Args:
        path: Python source file inspected by the documentation audit.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert ast.get_docstring(tree), f"Missing module docstring: {path}"

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node) or ""
        assert docstring, f"Missing docstring: {path}:{node.lineno} {node.name}"
        if isinstance(node, ast.ClassDef):
            annotated_attributes = [
                child
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            ]
            if annotated_attributes:
                assert "Attributes:" in docstring, (
                    f"Missing class attributes: {path}:{node.lineno} {node.name}"
                )
            continue

        parameters = [
            argument.arg
            for argument in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            if argument.arg not in {"self", "cls"}
        ]
        if node.args.vararg:
            parameters.append(node.args.vararg.arg)
        if node.args.kwarg:
            parameters.append(node.args.kwarg.arg)
        if parameters:
            assert "Args:" in docstring, (
                f"Missing parameter docs: {path}:{node.lineno} {node.name}"
            )

        return_annotation = ast.unparse(node.returns) if node.returns else "Any"
        if node.name != "__init__" and return_annotation not in {"None", "NoneType"}:
            assert "Returns:" in docstring or "Yields:" in docstring, (
                f"Missing return docs: {path}:{node.lineno} {node.name}"
            )
