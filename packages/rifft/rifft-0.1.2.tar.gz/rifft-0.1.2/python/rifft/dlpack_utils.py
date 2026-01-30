"""Helper utilities for shuttling Torch tensors through DLPack."""

from __future__ import annotations

import importlib
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    import torch

_TORCH = None
_TORCH_DLPACK = None


def _missing_torch_error() -> RuntimeError:
    return RuntimeError(
        "PyTorch is required for RIFFT's Python helpers. "
        "Install it via `pip install \"rifft[torch]\"`."
    )


def require_torch():
    global _TORCH, _TORCH_DLPACK
    if _TORCH is None:
        try:
            torch_mod = importlib.import_module("torch")
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise _missing_torch_error() from exc
        _TORCH = torch_mod
        _TORCH_DLPACK = torch_mod.utils.dlpack
    return _TORCH


def require_torch_dlpack():
    global _TORCH_DLPACK
    if _TORCH_DLPACK is None:
        require_torch()
    return _TORCH_DLPACK


def ensure_fft_ready(tensor: "torch.Tensor", *, copy: bool = True) -> "torch.Tensor":
    """Validate dtype/layout and return a contiguous complex64 view.

    When ``copy`` is False, the returned tensor may share storage with the input and
    RIFFT is allowed to mutate it in-place.
    """
    torch = require_torch()
    if tensor.dtype not in (torch.complex64, torch.float32):
        raise TypeError("RIFFT expects float32 or complex64 tensors")
    if tensor.dim() < 2:
        raise ValueError("Need at least 2 dimensions (height, width)")
    if tensor.dtype == torch.float32:
        tensor = tensor.to(torch.complex64)
    if not tensor.is_contiguous():
        tensor = tensor.contiguous()
    if copy:
        return tensor.clone()
    return tensor


def to_dlpack(tensor: "torch.Tensor"):
    torch_dlpack = require_torch_dlpack()
    return torch_dlpack.to_dlpack(tensor)


def from_dlpack(capsule) -> "torch.Tensor":
    torch_dlpack = require_torch_dlpack()
    return torch_dlpack.from_dlpack(capsule)


def spatial_dims(tensor: "torch.Tensor") -> Tuple[int, int]:
    if tensor.dim() < 2:
        raise ValueError("Tensor needs height/width dims")
    return tensor.shape[-2], tensor.shape[-1]
