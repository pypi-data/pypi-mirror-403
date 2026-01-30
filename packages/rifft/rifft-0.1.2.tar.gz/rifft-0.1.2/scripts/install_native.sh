#!/usr/bin/env bash
# Install RIFFT from source with CPU-optimised flags (target-cpu=native).

set -euo pipefail

log() {
  printf '[rifft-native] %s\n' "$*" >&2
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

PY_BIN="${PYTHON:-python3}"
require_cmd "$PY_BIN"
require_cmd rustup
require_cmd cargo

detect_threads() {
  local threads
  threads="$("$PY_BIN" - <<'PY' 2>/dev/null || true
import multiprocessing as m
print(m.cpu_count())
PY
)"
  if [[ -n "$threads" ]]; then
    echo "$threads"
    return
  fi
  if command -v getconf >/dev/null 2>&1; then
    getconf _NPROCESSORS_ONLN
    return
  fi
  echo 1
}

ARCH="$(uname -m | tr '[:upper:]' '[:lower:]')"
EXTRA_FLAGS=""
case "$ARCH" in
  x86_64|amd64)
    EXTRA_FLAGS="-C target-feature=+avx2,+fma"
    ;;
  arm64|aarch64)
    EXTRA_FLAGS="-C target-feature=+neon"
    ;;
esac

export RUSTUP_TOOLCHAIN="${RUSTUP_TOOLCHAIN:-nightly}"
export RIFFT_FEATURES="${RIFFT_FEATURES:-python}"
export RUSTFLAGS="${RUSTFLAGS:-"-C target-cpu=native $EXTRA_FLAGS"}"
export RIFFT_PREPLAN="${RIFFT_PREPLAN:-auto}"
if [[ -z "${RUSTFFT_THREADS:-}" ]]; then
  export RUSTFFT_THREADS="$(detect_threads)"
fi

RIFFT_GIT_URL="${RIFFT_GIT_URL:-https://github.com/benschneider/rifft.git}"
RIFFT_GIT_REF="${RIFFT_GIT_REF:-main}"

log "Toolchain=${RUSTUP_TOOLCHAIN} RUSTFLAGS='${RUSTFLAGS}' Threads=${RUSTFFT_THREADS} PREPLAN=${RIFFT_PREPLAN}"
log "Installing from ${RIFFT_GIT_URL}@${RIFFT_GIT_REF}"

PIP_ARGS=("$@")
INSTALL_TARGET="git+${RIFFT_GIT_URL}@${RIFFT_GIT_REF}"

"$PY_BIN" -m pip install --upgrade pip >/dev/null
if ((${#PIP_ARGS[@]} == 0)); then
  "$PY_BIN" -m pip install \
    --no-binary rifft \
    --force-reinstall \
    "${INSTALL_TARGET}"
else
  "$PY_BIN" -m pip install \
    --no-binary rifft \
    --force-reinstall \
    "${PIP_ARGS[@]}" \
    "${INSTALL_TARGET}"
fi

log "Installation complete. Export RIFFT_PREPLAN=auto before benchmarking to warm planner caches."
