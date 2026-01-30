"""NumPy-friendly entrypoints for RIFFT."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from . import _internal

Complex64Array = NDArray[np.complex64]


def canonicalize_numpy(array: np.ndarray) -> Complex64Array:
    """Ensure ``array`` is complex64 and C-contiguous."""

    if not isinstance(array, np.ndarray):
        raise TypeError("RIFFT expects a NumPy array.")
    if array.ndim not in (2, 3):
        raise ValueError("RIFFT expects shapes (H, W) or (B, H, W).")
    canonical = array
    if canonical.dtype != np.complex64:
        canonical = canonical.astype(np.complex64, copy=False)
    if not canonical.flags.c_contiguous:
        canonical = np.ascontiguousarray(canonical)
    return cast(Complex64Array, canonical)


def rifft_numpy(array: np.ndarray) -> Complex64Array:
    """Run RIFFT on ``array`` and return a canonicalized NumPy buffer."""

    canonical = canonicalize_numpy(array)
    _internal.fft_numpy(canonical)
    return canonical


def rifft(array: Any) -> Complex64Array:
    """Unified RIFFT entrypoint that accepts NumPy arrays."""

    if isinstance(array, np.ndarray):
        return rifft_numpy(array)
    raise TypeError("RIFFT expects a NumPy array.")


def rifft_out(array: np.ndarray) -> Complex64Array:
    """Return RIFFT(x) leaving ``array`` untouched."""

    copied = np.array(array, copy=True, order="C")
    return rifft_numpy(copied)


def rifft_ifft(array: np.ndarray, *, normalize: bool = True) -> Complex64Array:
    """Run the inverse RIFFT and optionally disable normalization.

    RIFFT's Rust core follows the common "backward" convention: forward FFTs are
    un-normalized and inverse FFTs apply a `1/(H*W)` scale.

    When `normalize` is False, this helper undoes the internal scaling so callers
    can match libraries configured for an un-normalized inverse.
    """

    canonical = canonicalize_numpy(array)
    _internal.ifft_numpy(canonical)
    if not normalize:
        plane = canonical.shape[-2] * canonical.shape[-1]
        canonical *= plane
    return canonical
