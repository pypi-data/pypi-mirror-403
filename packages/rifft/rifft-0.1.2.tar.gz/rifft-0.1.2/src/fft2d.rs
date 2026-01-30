use crate::planner::PlanEntry;
use crate::timing::{self, CallTimer};
use crate::transpose::transpose;
use crate::types::{Complex, FftDirection, Result};
use crate::workspace;
use once_cell::sync::Lazy;
use rayon::prelude::*;
use rayon::ThreadPool;
use std::env;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OutputLayout {
    RowMajor,
    ColumnMajor,
}

pub fn execute(plan: &PlanEntry, data: &mut [Complex]) -> Result<()> {
    execute_with_layout(plan, data, OutputLayout::RowMajor)
}

pub fn execute_with_layout(
    plan: &PlanEntry,
    data: &mut [Complex],
    layout: OutputLayout,
) -> Result<()> {
    let plane = plan.len;
    assert_eq!(data.len() % plane, 0, "data must contain whole planes");
    let batch = data.len() / plane;
    let width = plan.key.width;
    let height = plan.key.height;
    let mut scratch_buf = workspace::acquire(plane)?;
    let scratch = scratch_buf.as_mut();
    let timing_enabled = timing::is_enabled();
    RAYON_POOL.install(|| {
        for b in 0..batch {
            let plane_slice = &mut data[b * plane..(b + 1) * plane];
            if timing_enabled {
                let mut timer = CallTimer::new();
                timer.time_row(|| row_fft(plan, plane_slice, width));
                col_fft_with_layout(
                    plan,
                    plane_slice,
                    scratch,
                    width,
                    height,
                    layout,
                    Some(&mut timer),
                );
                timer.finish();
            } else {
                row_fft(plan, plane_slice, width);
                col_fft_with_layout(plan, plane_slice, scratch, width, height, layout, None);
            }
            if plan.key.direction == FftDirection::Inverse {
                normalize_inverse(plane_slice, plane);
            }
        }
    });
    Ok(())
}

pub(crate) fn row_fft(plan: &PlanEntry, plane: &mut [Complex], width: usize) {
    plane
        .par_chunks_mut(width)
        .for_each(|row| plan.row_fft.process(row));
}

pub(crate) fn col_fft_with_layout(
    plan: &PlanEntry,
    plane: &mut [Complex],
    scratch: &mut [Complex],
    width: usize,
    height: usize,
    layout: OutputLayout,
    mut timer: Option<&mut CallTimer>,
) {
    if let Some(ref mut t) = timer {
        t.time_transpose(|| transpose(plane, scratch, width, height));
        t.time_col(|| col_fft_transposed(plan, scratch, height));
    } else {
        transpose(plane, scratch, width, height);
        col_fft_transposed(plan, scratch, height);
    }
    match layout {
        OutputLayout::RowMajor => {
            if let Some(ref mut t) = timer {
                t.time_transpose(|| transpose(scratch, plane, height, width));
            } else {
                transpose(scratch, plane, height, width);
            }
        }
        OutputLayout::ColumnMajor => plane.copy_from_slice(scratch),
    }
}

pub(crate) fn col_fft_transposed(plan: &PlanEntry, buffer: &mut [Complex], height: usize) {
    buffer
        .par_chunks_mut(height)
        .for_each(|row| plan.col_fft.process(row));
}

pub(crate) fn normalize_inverse(buffer: &mut [Complex], len: usize) {
    if len == 0 {
        return;
    }
    let norm = len as f32;
    if norm <= 0.0 {
        return;
    }
    let scale = norm.recip();
    for value in buffer.iter_mut() {
        value.re *= scale;
        value.im *= scale;
    }
}

fn parse_threads(var: &str) -> Option<usize> {
    env::var(var)
        .ok()
        .and_then(|v| v.parse::<usize>().ok())
        .filter(|&threads| threads > 0)
}

fn default_thread_count() -> usize {
    parse_threads("RUSTFFT_THREADS")
        .or_else(|| parse_threads("RAYON_NUM_THREADS"))
        .unwrap_or_else(|| {
            #[cfg(target_os = "linux")]
            {
                let logical = num_cpus::get().max(1);
                if logical <= 2 {
                    // GitHub runners and similar low-core VMs often scale better
                    // when RIFFT stays on a single worker.
                    1
                } else {
                    let physical = num_cpus::get_physical();
                    if physical > 0 {
                        physical
                    } else {
                        logical
                    }
                }
            }
            #[cfg(not(target_os = "linux"))]
            {
                num_cpus::get().max(1)
            }
        })
}

static RAYON_POOL: Lazy<ThreadPool> = Lazy::new(|| {
    let threads = default_thread_count();
    log::debug!("RIFFT thread pool configured for {threads} threads");
    rayon::ThreadPoolBuilder::new()
        .num_threads(threads)
        .build()
        .expect("failed to build Rayon pool")
});

#[cfg(test)]
mod tests {
    use num_complex::Complex32;
    use rustfft::FftPlanner;

    #[test]
    fn rustfft_inverse_is_unnormalized() {
        let n = 16usize;
        let mut planner = FftPlanner::<f32>::new();
        let fft = planner.plan_fft_forward(n);
        let ifft = planner.plan_fft_inverse(n);

        let mut data = vec![Complex32::new(0.0, 0.0); n];
        data[0] = Complex32::new(1.0, 0.0);
        fft.process(&mut data);
        ifft.process(&mut data);

        // rustfft's inverse transform is unnormalized: inverse(forward(x)) = N * x.
        assert!(
            (data[0].re - n as f32).abs() < 1e-4,
            "data[0]={:?}",
            data[0]
        );
    }
}
