"""High-level helpers to make RIFFT easier to use from Torch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import bridge

if TYPE_CHECKING:  # pragma: no cover - hints only
    import torch


def fft2_inplace(tensor: "torch.Tensor", *, column_major: bool = False) -> "torch.Tensor":
    """Run RIFFT on ``tensor`` without allocating a new buffer."""
    bridge.fft2(tensor, column_major=column_major, copy_input=False)
    return tensor


def ifft2_inplace(tensor: "torch.Tensor") -> "torch.Tensor":
    """Run the inverse 2-D FFT on ``tensor`` without allocating a new buffer."""
    bridge.ifft2(tensor, copy_input=False)
    return tensor


def fft2_out(tensor: "torch.Tensor", *, column_major: bool = False) -> "torch.Tensor":
    """Return the FFT of ``tensor`` while leaving the input untouched."""
    return bridge.fft2(tensor, column_major=column_major, copy_input=True)


def fft_filter_ifft_inplace(signal: "torch.Tensor", filt: "torch.Tensor") -> "torch.Tensor":
    """Apply ``filt`` in the frequency domain mutating ``signal`` in-place."""
    bridge.fft_filter_ifft(signal, filt, copy_signal=False, copy_filter=False)
    return signal
