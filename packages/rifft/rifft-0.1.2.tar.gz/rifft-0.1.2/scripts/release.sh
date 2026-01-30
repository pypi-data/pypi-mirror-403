#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${CARGO_REGISTRY_TOKEN:-}" ]]; then
  echo "warning: CARGO_REGISTRY_TOKEN not set; ensure cargo login before publishing" >&2
fi

cargo fmt --all
cargo clippy --all-targets -- -D warnings
cargo test

python -m pip install --upgrade pip maturin

read -p "Publish to crates.io? (y/N) " ans
if [[ "${ans,,}" == "y" ]]; then
  cargo publish
fi

read -p "Publish wheels/sdist via maturin? (y/N) " ans2
if [[ "${ans2,,}" == "y" ]]; then
  RUSTUP_TOOLCHAIN=${RUSTUP_TOOLCHAIN:-nightly} maturin publish --release --features python "$@"
fi
