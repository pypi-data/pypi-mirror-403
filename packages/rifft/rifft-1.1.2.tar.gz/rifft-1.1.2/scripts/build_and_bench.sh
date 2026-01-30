#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LOG_SECTION() {
  printf '\n[%s]\n' "$1"
}

USE_VENV="${RIFFT_USE_VENV:-0}"
export RIFFT_USE_VENV="$USE_VENV"
if [[ "${USE_VENV}" == "1" && -z "${VIRTUAL_ENV:-}" ]]; then
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    export VIRTUAL_ENV="$ROOT/.venv"
  else
    echo "error: RIFFT_USE_VENV=1 but no virtualenv is active" >&2
    echo "hint: python -m venv .venv && source .venv/bin/activate" >&2
    exit 1
  fi
fi

if [[ "${USE_VENV}" == "1" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
else
  PYTHON_BIN="$(command -v python3 || command -v python)"
fi
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "error: python not found in PATH" >&2
  exit 1
fi

echo "[rifft] python=${PYTHON_BIN}"
"${PYTHON_BIN}" -m pip -V 2>/dev/null || true

TOOLCHAIN="${RUSTUP_TOOLCHAIN:-nightly}"
FEATURES="${RIFFT_FEATURES:-python}"
LOCKED=0
INSTALL_ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--locked" ]]; then
    LOCKED=1
  else
    INSTALL_ARGS+=("$arg")
  fi
done
if [[ ${#INSTALL_ARGS[@]} -eq 0 && "${RIFFT_LOCKED:-0}" == "1" ]]; then
  LOCKED=1
fi

export RUSTUP_TOOLCHAIN="$TOOLCHAIN"
export RIFFT_FEATURES="$FEATURES"
export RUSTFLAGS="${RUSTFLAGS:--C target-cpu=native}"

LOG_SECTION "Building Python extension (toolchain=${TOOLCHAIN})"
(
  cd "$ROOT"
  "$PYTHON_BIN" -m pip uninstall -y rifft >/dev/null 2>&1 || true
  export PYO3_PYTHON="$PYTHON_BIN"
  "$PYTHON_BIN" -m pip install --upgrade maturin
  INSTALL_CMD=(
    "$PYTHON_BIN" -m pip install -e .
    --config-settings=--features="${FEATURES}"
    --config-settings=--rust-toolchain="${TOOLCHAIN}"
    --config-settings=--release=true
    --no-build-isolation
    --upgrade
  )
  if [[ "$LOCKED" == "1" ]]; then
    INSTALL_CMD+=(--config-settings=--locked=true)
  fi
  if [[ ${#INSTALL_ARGS[@]} -gt 0 ]]; then
    INSTALL_CMD+=("${INSTALL_ARGS[@]}")
  fi
  "${INSTALL_CMD[@]}"
  "$PYTHON_BIN" - <<'PY'
import rifft, rifft._internal as internal
print(f"[rift] using {rifft.__file__}")
print(f"[rift] native {internal.__file__}")
PY
)

export PYTHONPATH="${PYTHONPATH:-$ROOT/python}"
export RIFFT_TIMING="${RIFFT_TIMING:-1}"
export RIFFT_PREPLAN="${RIFFT_PREPLAN:-auto}"
export RIFFT_BENCH_TUNE="${RIFFT_BENCH_TUNE:-1}"

LOG_SECTION "Running benchmark with RIFFT_TIMING=${RIFFT_TIMING} RIFFT_PREPLAN=${RIFFT_PREPLAN}"
(
  cd "$ROOT"
  "$PYTHON_BIN" scripts/bench_rifft_compare.py
)
