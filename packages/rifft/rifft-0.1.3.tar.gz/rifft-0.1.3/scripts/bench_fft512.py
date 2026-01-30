#!/usr/bin/env python3
"""Compare the 512-point FFT microbenchmarks with and without the special kernel.

The script runs the vendor RustFFT benches twice per datatype (f32/f64):
1. With `RUSTFFT_DISABLE_SPECIAL=1` to record the baseline.
2. With the optimized kernel enabled (default) to capture the improved timing.

By default it uses `cargo +nightly bench` because the upstream benches rely on
Rust's unstable `test` harness. Override the toolchain by setting the
`RIFFT_BENCH_TOOLCHAIN` environment variable (empty string disables the
explicit toolchain argument). Set `CARGO` if you need to point at a custom
Cargo binary.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Tuple

BENCHES = (
    ("planned32_p2_00000512", "f32"),
    ("planned64_p2_00000512", "f64"),
)
BENCH_MANIFEST = os.path.join("vendor", "rustfft", "Cargo.toml")
BENCH_TARGET = "bench_rustfft"
NS_RE = re.compile(r"bench:\s*([0-9,]+)\s*ns/iter")


def build_cargo_command() -> Tuple[str, ...]:
    cargo_bin = os.environ.get("CARGO", "cargo")
    toolchain = os.environ.get("RIFFT_BENCH_TOOLCHAIN", "+nightly")
    parts = [cargo_bin]
    if toolchain:
        parts.append(toolchain)
    parts.extend([
        "bench",
        "--manifest-path",
        BENCH_MANIFEST,
        "--bench",
        BENCH_TARGET,
    ])
    return tuple(parts)


def run_bench(disable_special: bool, bench_name: str) -> int:
    env = os.environ.copy()
    if disable_special:
        env["RUSTFFT_DISABLE_SPECIAL"] = "1"
    else:
        env.pop("RUSTFFT_DISABLE_SPECIAL", None)

    cmd = list(build_cargo_command()) + [bench_name]
    label = "baseline" if disable_special else "special"
    print(f"\nRunning {bench_name} ({label})...", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"command {' '.join(cmd)} failed with {proc.returncode}")

    match = NS_RE.search(proc.stdout)
    if not match:
        sys.stderr.write(proc.stdout)
        raise RuntimeError(f"unable to parse bench output for {bench_name}")
    return int(match.group(1).replace(",", ""))


@dataclass
class BenchResult:
    baseline_ns: int
    special_ns: int

    @property
    def speedup(self) -> float:
        return self.baseline_ns / self.special_ns if self.special_ns else float("inf")

    def formatted(self) -> str:
        return (
            f"{self.baseline_ns / 1e3:9.1f} µs   "
            f"{self.special_ns / 1e3:9.1f} µs   "
            f"{self.speedup:5.2f}x"
        )


def main() -> None:
    results: Dict[str, BenchResult] = {}
    for bench, label in BENCHES:
        baseline = run_bench(True, bench)
        special = run_bench(False, bench)
        results[label] = BenchResult(baseline_ns=baseline, special_ns=special)

    print("\nBench results (lower is better):")
    print("type        without special   with special      speedup")
    print("--------------------------------------------------------")
    for label in ("f32", "f64"):
        result = results[label]
        print(f"{label:>4}   {result.formatted()}")
    print()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as err:
        sys.stderr.write(f"error: {err}\n")
        sys.exit(1)
