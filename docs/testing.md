# Testing

## Full suite

```bash
pytest
```

Offline with the existing environment:

```bash
.venv/bin/pytest -q
```

## Compilation and whitespace

```bash
.venv/bin/python -m compileall -q src tests
git diff --check
```

## Coverage areas

- context schema loading and relationship validation;
- module/class/function docstring contracts;
- generation packages and Wan frame-count rules;
- disabled/non-downloading model policies and Animate rejection;
- ComfyUI request, binding, polling, and storage adapters with mocks;
- exact dialogue locking and audio safety;
- context inheritance, circular detection, immutable fields, and segment chaining;
- render validation, semantic review, approval, rejection, and release;
- automated editing, finalization, delivery, and archive manifests;
- MCP resource/tool registration and representative calls.

Tests do not download weights or create animation/video with a model. External
requests and media execution are mocked where appropriate; local FFmpeg behavior
is isolated behind tested argument-building functions.
