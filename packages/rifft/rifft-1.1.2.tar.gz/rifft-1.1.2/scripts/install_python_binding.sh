#!/usr/bin/env bash
set -euo pipefail

if ! command -v maturin >/dev/null 2>&1; then
  echo "maturin not found in PATH. Install it via 'pip install maturin' first." >&2
  exit 1
fi

TOOLCHAIN=${RUSTUP_TOOLCHAIN:-nightly}
FEATURES=${RIFFT_FEATURES:-python}
USE_VENV="${RIFFT_USE_VENV:-0}"
if [[ "${USE_VENV}" == "1" && -z "${VIRTUAL_ENV:-}" ]]; then
  echo "error: RIFFT_USE_VENV=1 but no virtualenv is active" >&2
  echo "hint: python -m venv .venv && source .venv/bin/activate" >&2
  exit 1
fi
if ! command -v rustup >/dev/null 2>&1; then
  echo "rustup not found; make sure the Rust toolchain (${TOOLCHAIN}) is available." >&2
fi

PYTHON_BIN="${MATURIN_PYTHON:-$(command -v python)}"
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python binary not found in PATH." >&2
  exit 1
fi

set -x
if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("maturin")
PY
then
  "${PYTHON_BIN}" -m pip install --upgrade maturin
fi

LOCKED=0
EXTRA_ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--locked" ]]; then
    LOCKED=1
  else
    EXTRA_ARGS+=("$arg")
  fi
done
PIP_CMD=("${PYTHON_BIN}" -m pip)
BUILD_ARGS=(
  install
  -e .
  --config-settings=--features="${FEATURES}"
  --config-settings=--rust-toolchain="${TOOLCHAIN}"
  --config-settings=--release=true
  --no-build-isolation
  --upgrade
)
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  BUILD_ARGS+=("${EXTRA_ARGS[@]}")
fi
if [[ "$LOCKED" == "1" ]]; then
  BUILD_ARGS+=(--config-settings=--locked=true)
fi
RUSTUP_TOOLCHAIN="$TOOLCHAIN" "${PIP_CMD[@]}" "${BUILD_ARGS[@]}"
