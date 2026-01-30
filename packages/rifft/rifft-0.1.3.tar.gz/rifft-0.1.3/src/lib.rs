//! Deterministic CPU 2-D FFTs with optional C/Python interop.
//!
//! The primary entry point for Rust callers is [`RifftHandle`]. For the C ABI see
//! [`crate::api_c`]. For Python bindings build with the `python` feature via `maturin`.
//!
//! ## Example
//!
//! ```no_run
//! use num_complex::Complex32;
//! use rifft::RifftHandle;
//!
//! let handle = RifftHandle::new();
//! let mut plane = vec![Complex32::default(); 512 * 512];
//! handle.fft2d_forward(&mut plane, 512, 512).unwrap();
//! ```
//!
//! ## Environment variables
//!
//! - `RUSTFFT_THREADS`: controls Rayon thread count for FFT execution.
//! - `RIFFT_PREPLAN`: set to `auto` or a comma-separated list like `256x256,1024x512` to warm plan
//!   caches when constructing a new [`RifftHandle`].

pub mod api_c;
pub mod dlpack;
pub mod fft2d;
pub mod fused;
pub mod planner;
#[cfg(feature = "python")]
mod pybindings;
pub mod simd;
pub mod timing;
pub mod transpose;
pub mod types;
pub mod workspace;

use crate::fft2d::OutputLayout;
use once_cell::sync::Lazy;
use planner::{PlanEntry, GLOBAL_PLANNER};
use std::env;
use std::sync::Arc;
use types::{FftDirection, Result};

pub struct RifftHandle {
    planner: Arc<planner::Planner>,
}

impl RifftHandle {
    pub fn new() -> Self {
        let handle = Self {
            planner: GLOBAL_PLANNER.clone(),
        };
        if let Some(shapes) = PREPLAN_SHAPES.as_ref() {
            if let Err(err) = handle.preplan(shapes) {
                log::warn!("preplan failed for {:?}: {}", shapes, err);
            }
        }
        handle
    }

    fn plan(&self, height: usize, width: usize, direction: FftDirection) -> Result<Arc<PlanEntry>> {
        self.planner.plan(height, width, direction)
    }

    pub fn fft2d_forward(
        &self,
        data: &mut [types::Complex],
        height: usize,
        width: usize,
    ) -> Result<()> {
        let plan = self.plan(height, width, FftDirection::Forward)?;
        fft2d::execute(&plan, data)
    }

    pub fn fft2d_forward_transposed(
        &self,
        data: &mut [types::Complex],
        height: usize,
        width: usize,
    ) -> Result<()> {
        let plan = self.plan(height, width, FftDirection::Forward)?;
        fft2d::execute_with_layout(&plan, data, OutputLayout::ColumnMajor)
    }

    pub fn fft2d_inverse(
        &self,
        data: &mut [types::Complex],
        height: usize,
        width: usize,
    ) -> Result<()> {
        let plan = self.plan(height, width, FftDirection::Inverse)?;
        fft2d::execute(&plan, data)
    }

    pub fn fft_filter_ifft(
        &self,
        data: &mut [types::Complex],
        filter: &[types::Complex],
        height: usize,
        width: usize,
    ) -> Result<()> {
        let forward = self.plan(height, width, FftDirection::Forward)?;
        let inverse = self.plan(height, width, FftDirection::Inverse)?;
        fused::fft_filter_ifft(&forward, &inverse, data, filter)
    }

    pub fn preplan(&self, shapes: &[(usize, usize)]) -> Result<()> {
        for &(h, w) in shapes {
            self.plan(h, w, FftDirection::Forward)?;
            self.plan(h, w, FftDirection::Inverse)?;
        }
        Ok(())
    }
}

impl Default for RifftHandle {
    fn default() -> Self {
        Self::new()
    }
}

pub fn get_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

pub fn get_backend_name() -> &'static str {
    types::BACKEND_NAME
}

static PREPLAN_SHAPES: Lazy<Option<Vec<(usize, usize)>>> = Lazy::new(preplan_shapes_from_env);

const DEFAULT_PREPLAN_SHAPES: &[(usize, usize)] =
    &[(256, 256), (512, 512), (1024, 1024), (1536, 1536)];

fn preplan_shapes_from_env() -> Option<Vec<(usize, usize)>> {
    let raw = env::var("RIFFT_PREPLAN").ok()?;
    decode_preplan_shapes(raw.trim())
}

fn decode_preplan_shapes(value: &str) -> Option<Vec<(usize, usize)>> {
    if value.is_empty() || matches_disabled(value) {
        return None;
    }
    if matches_auto(value) {
        return Some(DEFAULT_PREPLAN_SHAPES.to_vec());
    }
    let mut shapes = Vec::new();
    for token in value.split(|c: char| [',', ';'].contains(&c)) {
        let token = token.trim();
        if token.is_empty() {
            continue;
        }
        match parse_shape_pair(token) {
            Some(shape) => shapes.push(shape),
            None => log::warn!("RIFFT: invalid RIFFT_PREPLAN entry '{token}'"),
        }
    }
    if shapes.is_empty() {
        None
    } else {
        Some(shapes)
    }
}

fn matches_disabled(value: &str) -> bool {
    matches_ignore_case(value, &["0", "false", "off", "none"])
}

fn matches_auto(value: &str) -> bool {
    matches_ignore_case(value, &["1", "true", "on", "auto"])
}

fn matches_ignore_case(value: &str, options: &[&str]) -> bool {
    options.iter().any(|opt| value.eq_ignore_ascii_case(opt))
}

fn parse_shape_pair(token: &str) -> Option<(usize, usize)> {
    let trimmed = token.trim_matches(|c| matches!(c, '(' | ')' | '[' | ']'));
    for sep in ['x', 'X', '×', '*'] {
        if let Some((h, w)) = trimmed.split_once(sep) {
            return Some((h.trim().parse().ok()?, w.trim().parse().ok()?));
        }
    }
    None
}

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn _internal(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pybindings::register(py, m)
}
