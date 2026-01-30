"""Torch-friendly wrappers around the RIFFT core."""

from __future__ import annotations

import argparse
import time
from typing import Iterable, Sequence, Tuple, TYPE_CHECKING

from . import dlpack_utils
from . import _internal  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    import torch

_HANDLE = _internal.Handle()


def _require_torch():
    return dlpack_utils.require_torch()


def _maybe_preplan(shapes):
    try:
        _HANDLE.preplan(shapes)
    except AttributeError:
        pass


def _to_capsule(tensor: "torch.Tensor", *, copy_input: bool = True):
    tensor = dlpack_utils.ensure_fft_ready(tensor, copy=copy_input)
    return dlpack_utils.to_dlpack(tensor)


def _from_capsule(capsule) -> "torch.Tensor":
    return dlpack_utils.from_dlpack(capsule)


def fft2(
    tensor: "torch.Tensor",
    *,
    column_major: bool = False,
    copy_input: bool = True,
) -> "torch.Tensor":
    """Compute a 2-D FFT via RIFFT (returns a new tensor).

    When ``column_major`` is True, the caller receives the transpose-domain buffer
    that RIFFT already holds internally, avoiding the final transpose step. Callers
    are responsible for interpreting the data with swapped strides/dimensions.
    """
    capsule = _to_capsule(tensor, copy_input=copy_input)
    out_capsule = _HANDLE.fft2(capsule, column_major=column_major)
    return _from_capsule(out_capsule)


def ifft2(tensor: "torch.Tensor", *, copy_input: bool = True) -> "torch.Tensor":
    capsule = _to_capsule(tensor, copy_input=copy_input)
    out_capsule = _HANDLE.ifft2(capsule)
    return _from_capsule(out_capsule)


def fft_filter_ifft(
    signal: "torch.Tensor",
    filt: "torch.Tensor",
    *,
    copy_signal: bool = True,
    copy_filter: bool = True,
) -> Tuple["torch.Tensor", "torch.Tensor"]:
    signal_capsule = _to_capsule(signal, copy_input=copy_signal)
    filter_capsule = _to_capsule(filt, copy_input=copy_filter)
    out_capsule, filter_capsule = _HANDLE.fft_filter_ifft(signal_capsule, filter_capsule)
    return _from_capsule(out_capsule), _from_capsule(filter_capsule)


def batched_fft2(
    tensor: "torch.Tensor",
    *,
    column_major: bool = False,
    copy_input: bool = True,
) -> "torch.Tensor":
    return fft2(tensor, column_major=column_major, copy_input=copy_input)


def batched_ifft2(tensor: "torch.Tensor", *, copy_input: bool = True) -> "torch.Tensor":
    return ifft2(tensor, copy_input=copy_input)


def batched_fft_filter_ifft(
    signal: "torch.Tensor",
    filt: "torch.Tensor",
    *,
    copy_signal: bool = True,
    copy_filter: bool = True,
) -> Tuple["torch.Tensor", "torch.Tensor"]:
    return fft_filter_ifft(signal, filt, copy_signal=copy_signal, copy_filter=copy_filter)


def get_version() -> str:
    return getattr(_internal, "__version__", "0.0.0")


def run_benchmarks(sizes: Sequence[int], iters: int = 50, device: str = "cpu"):
    torch = _require_torch()
    _maybe_preplan([(s, s) for s in sizes])
    results = []
    for size in sizes:
        shape = (size, size)
        data = torch.randn(shape, dtype=torch.complex64, device=device)
        start = time.perf_counter()
        tmp = data
        for _ in range(iters):
            tmp = fft2(tmp)
        elapsed = time.perf_counter() - start
        results.append({
            "size": size,
            "ms_per_call": (elapsed / iters) * 1000.0,
        })
    return results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run RIFFT Python benchmarks")
    parser.add_argument("--sizes", nargs="*", type=int, default=[256, 512, 1024])
    parser.add_argument("--iters", type=int, default=25)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args(list(argv) if argv is not None else None)
    results = run_benchmarks(args.sizes, args.iters, args.device)
    for row in results:
        print(f"{row['size']}^2 : {row['ms_per_call']:.4f} ms")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
