"""Runtime helpers for planning and instrumentation."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence, Tuple

from . import _internal

_PLAN_HANDLE = _internal.Handle()


def preplan(shapes: Iterable[Sequence[int] | Tuple[int, int]]) -> None:
    """Warm the shared planner for the given shapes."""

    pairs = []
    for shape in shapes:
        dims = tuple(shape)
        if len(dims) != 2:
            raise ValueError("preplan expects (height, width) pairs")
        h, w = int(dims[0]), int(dims[1])
        pairs.append((h, w))
    if pairs:
        _PLAN_HANDLE.preplan(pairs)


def enable_timing(flag: bool) -> None:
    """Enable or disable RIFFT timing counters."""

    _internal.enable_timing(flag)


def timing_reset() -> None:
    """Reset timing counters back to zero."""

    _internal.timing_reset()


def timing_summary() -> Mapping[str, float]:
    """Return the current timing snapshot as a dict."""

    summary = _internal.timing_summary()
    return dict(summary)
