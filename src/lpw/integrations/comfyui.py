"""Provide comfyui services for the LPW cinematic pipeline."""

from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any

import httpx2 as httpx


class ComfyUIError(RuntimeError):
    """Base error for ComfyUI API failures."""


class ComfyUIExecutionError(ComfyUIError):
    """Raised when a ComfyUI workflow fails or times out."""


class ComfyUIClient:
    """Async client for ComfyUI's built-in HTTP API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        *,
        request_timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            base_url (str): Base url used by this operation. Defaults to
                ``'http://127.0.0.1:8188'``.
            request_timeout_seconds (float): Request timeout seconds used by this
                operation. Defaults to ``60.0``.
            poll_interval_seconds (float): Poll interval seconds used by this operation.
                Defaults to ``1.0``.

        Raises:
            ValueError: If inputs, context, state, or provider output are invalid.
        """
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("ComfyUI base URL must use HTTP or HTTPS.")
        self.base_url = base_url.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    async def health_check(self) -> dict[str, Any]:
        """Execute check.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/system_stats")
            response.raise_for_status()
            return self._json_object(response.json(), "system_stats")

    async def upload_image(self, image_path: Path) -> str:
        """Upload image.

        Args:
            image_path (Path): Image path used by this operation.

        Returns:
            str: Result produced by the operation.

        Raises:
            FileNotFoundError: If inputs, context, state, or provider output are invalid.
            ComfyUIError: If inputs, context, state, or provider output are invalid.
        """
        image_path = image_path.expanduser().resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Reference image not found: {image_path}")
        mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            with image_path.open("rb") as image_file:
                response = await client.post(
                    f"{self.base_url}/upload/image",
                    files={"image": (image_path.name, image_file, mime_type)},
                    data={"type": "input", "overwrite": "false"},
                )
        response.raise_for_status()
        result = self._json_object(response.json(), "upload response")
        name = result.get("name")
        if not isinstance(name, str) or not name:
            raise ComfyUIError(f"Upload response has no filename: {result}")
        subfolder = result.get("subfolder", "")
        return f"{subfolder}/{name}" if subfolder else name

    async def queue_workflow(
        self, workflow: dict[str, Any], client_id: str | None = None
    ) -> str:
        """Queue workflow.

        Args:
            workflow (dict[str, Any]): Workflow used by this operation.
            client_id (str | None): Client id used by this operation. Defaults to
                ``None``.

        Returns:
            str: Result produced by the operation.

        Raises:
            ComfyUIExecutionError: If inputs, context, state, or provider output are invalid.
            ComfyUIError: If inputs, context, state, or provider output are invalid.
        """
        payload = {"prompt": workflow, "client_id": client_id or str(uuid.uuid4())}
        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/prompt", json=payload)
        response.raise_for_status()
        result = self._json_object(response.json(), "queue response")
        if result.get("error"):
            raise ComfyUIExecutionError(
                json.dumps(result, ensure_ascii=False, indent=2)
            )
        prompt_id = result.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(f"ComfyUI returned no prompt_id: {result}")
        return str(prompt_id)

    async def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        """Return history.

        Args:
            prompt_id (str): Prompt id used by this operation.

        Returns:
            dict[str, Any] | None: Result produced by the operation.
        """
        async with httpx.AsyncClient(timeout=self.request_timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/history/{prompt_id}")
        response.raise_for_status()
        result = self._json_object(response.json(), "history response")
        history = result.get(prompt_id)
        return history if isinstance(history, dict) else None

    async def execute(
        self,
        workflow: dict[str, Any],
        *,
        timeout_seconds: float = 3600,
    ) -> tuple[str, dict[str, Any]]:
        """Execute execute.

        Args:
            workflow (dict[str, Any]): Workflow used by this operation.
            timeout_seconds (float): Timeout seconds used by this operation. Defaults to
                ``3600``.

        Returns:
            tuple[str, dict[str, Any]]: Result produced by the operation.

        Raises:
            ComfyUIExecutionError: If inputs, context, state, or provider output are invalid.
        """
        prompt_id = await self.queue_workflow(workflow)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            history = await self.get_history(prompt_id)
            if history is not None:
                status = history.get("status", {})
                if status.get("status_str") in {"error", "failed"}:
                    raise ComfyUIExecutionError(
                        json.dumps(history, ensure_ascii=False, indent=2)
                    )
                return prompt_id, history
            await asyncio.sleep(self.poll_interval_seconds)
        raise ComfyUIExecutionError(f"ComfyUI execution timed out: {prompt_id}")

    async def download_output(
        self, descriptor: dict[str, Any], destination: Path
    ) -> Path:
        """Download output.

        Args:
            descriptor (dict[str, Any]): Descriptor used by this operation.
            destination (Path): Destination path for the transformed asset.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ComfyUIError: If inputs, context, state, or provider output are invalid.
        """
        filename = descriptor.get("filename")
        if not isinstance(filename, str) or not filename:
            raise ComfyUIError(f"Output descriptor has no filename: {descriptor}")
        params = {
            "filename": filename,
            "subfolder": descriptor.get("subfolder", ""),
            "type": descriptor.get("type", "output"),
        }
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.get(f"{self.base_url}/view", params=params)
        response.raise_for_status()
        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
        temporary.write_bytes(response.content)
        os.replace(temporary, destination)
        return destination

    @staticmethod
    def _json_object(value: Any, label: str) -> dict[str, Any]:
        """Execute object.

        Args:
            value (Any): Value inspected or transformed by the helper.
            label (str): Label used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.

        Raises:
            ComfyUIError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(value, dict):
            raise ComfyUIError(f"ComfyUI {label} must be a JSON object.")
        return value
