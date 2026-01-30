#!/usr/bin/env python3
"""Compare RIFFT FFT timings against torch.fft and numpy.fft."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _configure_thread_env_defaults(threads: int) -> None:
    # These are read by various BLAS/FFT backends. They must be set before importing
    # numpy/torch to take full effect.
    for var in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]:
        os.environ.setdefault(var, str(threads))


_DEFAULT_THREADS = (
    _env_int("RIFFT_BENCH_THREADS", 0)
    or _env_int("RUSTFFT_THREADS", 0)
    or _env_int("RAYON_NUM_THREADS", 0)
    or (os.cpu_count() or 1)
)

_TUNE = os.environ.get("RIFFT_BENCH_TUNE", "0") == "1"
if _TUNE:
    _configure_thread_env_defaults(_DEFAULT_THREADS)

import numpy as np

try:
    import torch

    _TORCH_AVAILABLE = True
except ModuleNotFoundError:
    torch = None
    _TORCH_AVAILABLE = False

from rifft import (
    fft2 as riff_fft2,
    fft_filter_ifft as riff_fft_filter_ifft,
    rifft as riff_numpy_fft,
    rifft_out as riff_numpy_fft_out,
)

try:
    from rifft import enable_timing, timing_reset, timing_summary
except ImportError:
    enable_timing = None
    timing_reset = None
    timing_summary = None

WARMUP_RUNS = _env_int("RIFFT_BENCH_WARMUP_RUNS", 1)
BENCH_RUNS = _env_int("RIFFT_BENCH_RUNS", 1000)
ROOT = Path(__file__).resolve().parents[1]
_EQUIV_CHECKED: set[Tuple[int, int]] = set()

_TIMING_AVAILABLE = enable_timing is not None and timing_reset is not None and timing_summary is not None

if _TIMING_AVAILABLE:
    try:
        enable_timing(True)
        timing_reset()
    except Exception:
        _TIMING_AVAILABLE = False


def _ensure_single_thread_numpy() -> None:
    for var in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]:
        os.environ.setdefault(var, "1")


def _configure_torch_threads() -> None:
    if not _TORCH_AVAILABLE or torch is None:
        return
    if os.environ.get("RIFFT_BENCH_TUNE_TORCH", "1" if _TUNE else "0") != "1":
        return
    threads = _env_int("RIFFT_TORCH_THREADS", _DEFAULT_THREADS)
    interop = _env_int("RIFFT_TORCH_INTEROP_THREADS", max(1, min(threads, 4)))
    try:
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(interop)
    except Exception:
        pass


_configure_torch_threads()


def _current_timing() -> Optional[Dict[str, float]]:
    if not _TIMING_AVAILABLE:
        return None
    try:
        return timing_summary()
    except Exception:
        return None


def timing_delta(
    start: Optional[Dict[str, float]], end: Optional[Dict[str, float]]
) -> Optional[Dict[str, float]]:
    if not start or not end:
        return None
    delta_calls = int(end["calls"] - start["calls"])
    delta_plan_calls = int(end.get("plan_calls", 0) - start.get("plan_calls", 0))
    delta_filter_calls = int(end.get("filter_fft_calls", 0) - start.get("filter_fft_calls", 0))
    delta_filter_hits = int(end.get("filter_fft_hits", 0) - start.get("filter_fft_hits", 0))

    def avg_ms(total_key: str, calls: int) -> Optional[float]:
        if calls <= 0:
            return None
        delta_ns = end.get(total_key, 0.0) - start.get(total_key, 0.0)
        return delta_ns / calls / 1_000_000.0

    return {
        "calls": delta_calls,
        "row_ms": avg_ms("row_total_ns", delta_calls),
        "col_ms": avg_ms("col_total_ns", delta_calls),
        "transpose_ms": avg_ms("transpose_total_ns", delta_calls),
        "exec_ms": avg_ms("exec_total_ns", delta_calls),
        "plan_calls": delta_plan_calls,
        "plan_ms": avg_ms("plan_total_ns", delta_plan_calls),
        "filter_fft_calls": delta_filter_calls,
        "filter_fft_hits": delta_filter_hits,
        "filter_fft_ms": avg_ms("filter_fft_total_ns", delta_filter_calls),
    }


def print_timing_delta(delta: Dict[str, float]) -> None:
    calls = delta.get("calls", 0)
    if calls and delta["row_ms"] is not None:
        exec_ms = delta.get("exec_ms") or 0.0

        def pct(part: Optional[float]) -> float:
            return (part or 0.0) / exec_ms * 100.0 if exec_ms else 0.0

        print(
            "  RIFFT core  : "
            f"row={delta['row_ms']:.3f} ms ({pct(delta['row_ms']):5.1f}%), "
            f"col={delta['col_ms']:.3f} ms ({pct(delta['col_ms']):5.1f}%), "
            f"transp={delta['transpose_ms']:.3f} ms ({pct(delta['transpose_ms']):5.1f}%), "
            f"exec={exec_ms:.3f} ms "
            f"({calls} calls)"
        )
    plan_calls = delta.get("plan_calls", 0)
    if plan_calls and delta["plan_ms"] is not None:
        print(
            "    planner   : "
            f"{delta['plan_ms']:.3f} ms avg over {plan_calls} calls"
        )


def _format_samples(tensor: torch.Tensor) -> str:
    flat = tensor.flatten()
    if flat.numel() == 0:
        return "[]"
    count = min(3, flat.numel())
    first = flat[:count]
    last = flat[-count:]

    def fmt(val: torch.Tensor) -> str:
        real = val.real.item()
        imag = val.imag.item()
        return f"{real:+.4e}{imag:+.4e}j"

    return (
        "first="
        + ", ".join(fmt(v) for v in first)
        + " | last="
        + ", ".join(fmt(v) for v in last)
    )


def verify_equivalence_torch(tensor: "torch.Tensor") -> None:
    """Validate that numpy, torch, and RIFFT agree on the same input."""

    numpy_fft = torch.from_numpy(np.fft.fft2(tensor.numpy()).copy()).to(torch.complex64)
    torch_fft = torch.fft.fft2(tensor)
    riff_tensor = riff_fft2(tensor.clone())

    elements = tensor.numel()
    if elements <= 512 * 512:
        tol = 2e-4
    elif elements <= 1024 * 1024:
        tol = 5e-4
    else:
        tol = 1.25e-3
    torch.testing.assert_close(riff_tensor, torch_fft, atol=tol, rtol=tol)
    torch.testing.assert_close(numpy_fft, torch_fft, atol=tol, rtol=tol)
    print("Equivalence check: Confirmed")


def verify_equivalence_numpy(array: np.ndarray) -> None:
    numpy_fft = np.fft.fft2(array)
    riff_out = riff_numpy_fft(array.copy())
    atol = 1e-4 if array.size <= 512 * 512 else 5e-4
    rtol = 1e-4 if array.size <= 512 * 512 else 3e-4
    np.testing.assert_allclose(
        riff_out,
        numpy_fft.astype(np.complex64),
        rtol=rtol,
        atol=atol,
    )
    print("Equivalence check (NumPy): Confirmed")


@dataclass
class TimingSummary:
    median_ms: float
    mean_ms: float
    std_ms: float

    @classmethod
    def from_samples(cls, samples: Iterable[float]) -> "TimingSummary":
        data = list(samples)
        return cls(
            median_ms=statistics.median(data) * 1000.0,
            mean_ms=statistics.fmean(data) * 1000.0,
            std_ms=statistics.pstdev(data) * 1000.0 if len(data) > 1 else 0.0,
        )


def _time(fn) -> List[float]:
    for _ in range(WARMUP_RUNS):
        fn()
    out: List[float] = []
    for _ in range(BENCH_RUNS):
        start = time.perf_counter()
        fn()
        out.append(time.perf_counter() - start)
    return out


def run_backend(label: str, fn) -> TimingSummary:
    start = time.perf_counter()
    samples = _time(fn)
    elapsed = time.perf_counter() - start
    summary = TimingSummary.from_samples(samples)
    print(
        f"  {label:<10} avg={summary.mean_ms:6.3f} ms "
        f"(median={summary.median_ms:6.3f} ms, std={summary.std_ms:6.3f} ms) "
        f"[bench {elapsed:.2f}s]"
    )
    return summary


def benchmark_shape(
    height: int,
    width: int,
    *,
    numpy_all: bool = False,
    use_torch: bool = True,
) -> Dict[str, object]:
    shape = (height, width)
    rng = np.random.default_rng(0)
    numpy_seed = (
        rng.standard_normal(shape, dtype=np.float32)
        + 1j * rng.standard_normal(shape, dtype=np.float32)
    ).astype(np.complex64)
    torch_input = None
    torch_buffer = None
    torch_enabled = use_torch and _TORCH_AVAILABLE
    if torch_enabled:
        torch.manual_seed(0)
        torch_input = torch.from_numpy(numpy_seed.copy()).contiguous()
        torch_buffer = torch_input.clone()
    numpy_input = numpy_seed.copy()
    start_timing = _current_timing()

    if shape not in _EQUIV_CHECKED:
        print(f"\nVerifying equivalence for {shape} shape.")
        if torch_enabled and torch_input is not None:
            verify_equivalence_torch(torch_input.clone())
        else:
            verify_equivalence_numpy(numpy_input.copy())
        _EQUIV_CHECKED.add(shape)

    print(f"\nBenchmarking shape {shape}")
    numpy_stats = None
    if numpy_all or height <= 512:
        numpy_stats = TimingSummary.from_samples(_time(lambda: np.fft.fft2(numpy_input)))
    torch_stats = None
    if torch_enabled and torch_input is not None:
        torch_stats = TimingSummary.from_samples(
            _time(lambda: torch.fft.fft2(torch_input))
        )

    numpy_base = numpy_input.copy()
    numpy_buffer = numpy_base.copy()

    riff_stats = None
    if torch_enabled and torch_buffer is not None and torch_input is not None:
        def run_rifft() -> None:
            torch_buffer.copy_(torch_input)
            riff_fft2(torch_buffer, copy_input=False)

        riff_stats = TimingSummary.from_samples(_time(run_rifft))

    def run_rifft_numpy() -> None:
        numpy_buffer[...] = numpy_base
        riff_numpy_fft(numpy_buffer)

    def run_rifft_numpy_out() -> None:
        riff_numpy_fft_out(numpy_base)

    riff_numpy_stats = TimingSummary.from_samples(_time(run_rifft_numpy))
    riff_numpy_out_stats = TimingSummary.from_samples(_time(run_rifft_numpy_out))
    riff_timing = timing_delta(start_timing, _current_timing())
    if riff_timing:
        print_timing_delta(riff_timing)

    return {
        "shape": shape,
        "numpy": numpy_stats.__dict__ if numpy_stats else None,
        "torch": torch_stats.__dict__ if torch_stats else None,
        "rifft_torch": riff_stats.__dict__ if riff_stats else None,
        "rifft_numpy": riff_numpy_stats.__dict__,
        "rifft_numpy_out": riff_numpy_out_stats.__dict__,
    }


def environment_summary() -> str:
    cpu = platform.processor() or platform.machine()
    threads = os.environ.get("RUSTFFT_THREADS") or os.environ.get("RAYON_NUM_THREADS")
    threads = threads or os.cpu_count() or "unknown"
    rustflags = os.environ.get("RUSTFLAGS", "unset")
    return f"cpu={cpu}, threads={threads}, RUSTFLAGS={rustflags}"


def print_report(entries: List[Dict[str, object]]) -> None:
    print("\n" + "=" * 80)
    print("RIFFT Benchmark Summary")
    print("=" * 80)
    print("Environment:", environment_summary())
    header = f"{'Shape':<12} {'Impl':<12} {'Median (ms)':>14} {'Mean (ms)':>12} {'Std (ms)':>10}"
    print(header)
    print("-" * len(header))

    def row(stats: Dict[str, float] | None, label: str, shape: Tuple[int, int]) -> None:
        if stats is None:
            print(f"{str(shape):<12} {label:<12} {'n/a':>14} {'n/a':>12} {'n/a':>10}")
            return
        print(
            f"{str(shape):<12} {label:<12} "
            f"{stats['median_ms']:>14.3f} {stats['mean_ms']:>12.3f} {stats['std_ms']:>10.3f}"
        )

    for entry in entries:
        shape = entry["shape"]
        row(entry["torch"], "torch.fft", shape)
        row(entry["numpy"], "numpy", shape)
        row(entry["rifft_torch"], "rifft.torch", shape)
        row(entry["rifft_numpy"], "rifft.np", shape)
        row(entry["rifft_numpy_out"], "rifft.np_out", shape)
        print("-" * len(header))


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--numpy-all",
        action="store_true",
        help=(
            "Run NumPy (and rifft.numpy) benchmarks for all shapes. "
            "By default sizes larger than 512x512 are skipped to keep runs short."
        ),
    )
    parser.add_argument(
        "--skip-torch",
        action="store_true",
        help="Skip torch.fft and rifft.torch benchmarks even if PyTorch is installed.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.skip_torch and _TORCH_AVAILABLE:
        print("Skipping torch benchmarks per --skip-torch", file=sys.stderr)
    if not _TORCH_AVAILABLE and not args.skip_torch:
        print(
            "PyTorch not available; skipping torch benchmarks.",
            file=sys.stderr,
        )
    shapes = [(256, 256), (512, 512), (1024, 1024), (1536, 1536), (2048, 2048)]
    use_torch = (not args.skip_torch) and _TORCH_AVAILABLE
    results = [
        benchmark_shape(h, w, numpy_all=args.numpy_all, use_torch=use_torch)
        for h, w in shapes
    ]
    if _TIMING_AVAILABLE:
        try:
            summary = timing_summary()
            exec_ms = summary.get("exec_ms", 0.0)
            row_ms = summary["row_ms"]
            col_ms = summary["col_ms"]
            trans_ms = summary["transpose_ms"]

            def pct(part: float) -> float:
                return part / exec_ms * 100.0 if exec_ms else 0.0

            print(
                "\nRIFFT core avg timings over "
                f"{summary['calls']} calls: "
                f"row={row_ms:.3f} ms ({pct(row_ms):5.1f}%), "
                f"col={col_ms:.3f} ms ({pct(col_ms):5.1f}%), "
                f"transpose={trans_ms:.3f} ms ({pct(trans_ms):5.1f}%), "
                f"exec={exec_ms:.3f} ms"
            )
            plan_calls = summary.get("plan_calls", 0)
            if plan_calls:
                print(
                    f"Planner avg over {plan_calls} calls: "
                    f"{summary.get('plan_ms', 0.0):.3f} ms"
                )
        except Exception:
            pass
    out_path = ROOT / "results" / "rifft_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved results to {out_path}")
    print_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
