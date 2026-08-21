"""Run ACE-Step's API without duplicating its DiT weights into MLX.

ACE-Step enables its native MLX DiT and VAE automatically on Apple Silicon.
During initialization it first loads the PyTorch models and then converts
second copies to MLX; those transient peaks exceed the memory available on the
local M4. This adapter keeps ACE-Step's official API and generation code, but
disables the implicit MLX copies so the requested CPU backend holds one model.
"""

from __future__ import annotations

import argparse
from functools import wraps
from typing import Any, Callable


def _disable_implicit_mlx_copy() -> None:
    from acestep.handler import AceStepHandler

    original: Callable[..., Any] = AceStepHandler.initialize_service
    if getattr(original, "_lpw_no_implicit_mlx", False):
        return

    @wraps(original)
    def initialize_service(self: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("use_mlx_dit", False)
        return original(self, *args, **kwargs)

    initialize_service._lpw_no_implicit_mlx = True  # type: ignore[attr-defined]
    AceStepHandler.initialize_service = initialize_service

    def skip_mlx_vae(self: Any) -> bool:
        self.mlx_vae = None
        self.use_mlx_vae = False
        self._mlx_compiled_decode = None
        self._mlx_compiled_encode_sample = None
        self._mlx_vae_dtype = None
        return False

    AceStepHandler._init_mlx_vae = skip_mlx_vae


def main() -> None:
    parser = argparse.ArgumentParser(description="Low-memory ACE-Step API adapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    _disable_implicit_mlx_copy()

    import uvicorn
    from acestep.api_server import app

    uvicorn.run(app, host=args.host, port=args.port, reload=False, workers=1)


if __name__ == "__main__":
    main()
