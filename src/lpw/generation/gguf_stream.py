"""Bounded-memory GGUF tensor streaming utilities."""

from __future__ import annotations

import gc
from pathlib import Path
from typing import Any, Iterable


class GGUFStreamError(RuntimeError):
    """Raised when a streamed tensor cannot be resolved or decoded."""


class GGUFStore:
    """Memory-map a GGUF and materialize only explicitly requested tensors."""

    def __init__(self, path: str | Path) -> None:
        try:
            from gguf import GGUFReader
        except ModuleNotFoundError as error:
            raise GGUFStreamError("the `gguf` Python package is required") from error
        self.path = Path(path).expanduser().resolve()
        self.reader = GGUFReader(self.path, "r")
        self.tensors = {tensor.name: tensor for tensor in self.reader.tensors}

    def names(self, prefix: str | None = None) -> list[str]:
        names = self.tensors if prefix is None else (n for n in self.tensors if n.startswith(prefix))
        return sorted(names)

    def require(self, names: Iterable[str]) -> None:
        missing = sorted(set(names) - self.tensors.keys())
        if missing:
            raise GGUFStreamError(f"missing GGUF tensors: {missing}")

    def torch_shape(self, name: str) -> tuple[int, ...]:
        tensor = self.tensors.get(name)
        if tensor is None:
            raise GGUFStreamError(f"GGUF tensor does not exist: {name}")
        return tuple(int(value) for value in reversed(tensor.shape))

    def tensor(
        self,
        name: str,
        *,
        device: str = "cpu",
        dtype: Any | None = None,
        rows: Any | None = None,
    ) -> Any:
        """Dequantize a whole tensor, or selected leading rows, into PyTorch."""
        try:
            import torch
            from gguf.quants import dequantize
        except ModuleNotFoundError as error:
            raise GGUFStreamError("PyTorch and gguf are required") from error
        source = self.tensors.get(name)
        if source is None:
            raise GGUFStreamError(f"GGUF tensor does not exist: {name}")
        packed = source.data if rows is None else source.data[rows]
        array = dequantize(packed, source.tensor_type)
        if not array.flags.writeable:
            array = array.copy()
        value = torch.from_numpy(array)
        if dtype is not None or device != "cpu":
            value = value.to(device=device, dtype=dtype)
        return value

    @staticmethod
    def release_mps(*values: Any) -> None:
        """Release caller-owned values first, then invoke this cache cleanup."""
        del values
        gc.collect()
        try:
            import torch
        except ModuleNotFoundError:
            return
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
            torch.mps.synchronize()
