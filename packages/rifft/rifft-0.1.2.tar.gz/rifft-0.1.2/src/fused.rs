use crate::fft2d::{col_fft_transposed, normalize_inverse, row_fft};
use crate::planner::PlanEntry;
use crate::simd;
use crate::timing::{self, CallTimer};
use crate::transpose::transpose;
use crate::types::{Complex, Result, RifftError};
use crate::workspace;
use ahash::AHasher;
use once_cell::sync::Lazy;
use parking_lot::RwLock;
use std::collections::VecDeque;
use std::env;
use std::hash::Hasher;
use std::sync::Arc;
use std::time::Instant;

pub fn fft_filter_ifft(
    plan_forward: &PlanEntry,
    plan_inverse: &PlanEntry,
    data: &mut [crate::types::Complex],
    filter: &[crate::types::Complex],
) -> Result<()> {
    if data.len() != filter.len() {
        return Err(RifftError::ShapeMismatch {
            expected: data.len(),
            got: filter.len(),
        });
    }
    let width = plan_forward.key.width;
    let height = plan_forward.key.height;
    let len = plan_forward.len;

    let mut scratch_guard = workspace::acquire(len)?;
    let scratch = scratch_guard.as_mut();

    let mut forward_timer = CallTimer::new();
    forward_timer.time_row(|| row_fft(plan_forward, data, width));
    forward_timer.time_transpose(|| transpose(data, scratch, width, height));
    forward_timer.time_col(|| col_fft_transposed(plan_forward, scratch, height));
    forward_timer.finish();

    let filter_freq = get_filter_spectrum(plan_forward, filter)?;
    simd::complex_mul_inplace(scratch, filter_freq.as_ref());

    let mut inverse_timer = CallTimer::new();
    inverse_timer.time_col(|| col_fft_transposed(plan_inverse, scratch, height));
    inverse_timer.time_transpose(|| transpose(scratch, data, height, width));
    inverse_timer.time_row(|| row_fft(plan_inverse, data, width));
    inverse_timer.finish();

    normalize_inverse(data, len);
    Ok(())
}

static FILTER_CACHE: Lazy<RwLock<FilterCache>> =
    Lazy::new(|| RwLock::new(FilterCache::new(filter_cache_capacity())));

fn get_filter_spectrum(plan_forward: &PlanEntry, filter: &[Complex]) -> Result<Arc<Vec<Complex>>> {
    let width = plan_forward.key.width;
    let height = plan_forward.key.height;
    let len = plan_forward.len;
    let hash = filter_hash(filter);
    if let Some(hit) = FILTER_CACHE.write().get(len, width, height, hash, filter) {
        if timing::is_enabled() {
            timing::record_filter_fft(true, 0);
        }
        return Ok(hit);
    }
    let start = if timing::is_enabled() {
        Some(Instant::now())
    } else {
        None
    };
    let mut temp = filter.to_vec();
    let owned_filter: Arc<[Complex]> = temp.clone().into_boxed_slice().into();
    row_fft(plan_forward, &mut temp, width);
    let mut transposed = vec![Complex::default(); temp.len()];
    transpose(&temp, &mut transposed, width, height);
    col_fft_transposed(plan_forward, &mut transposed, height);
    let entry = Arc::new(transposed);
    FILTER_CACHE.write().insert(FilterCacheEntry {
        len,
        width,
        height,
        hash,
        filter: owned_filter,
        spectrum: entry.clone(),
    });
    if let Some(start) = start {
        timing::record_filter_fft(false, timing::elapsed_ns(start));
    }
    Ok(entry)
}

fn filter_hash(filter: &[Complex]) -> u64 {
    let mut hasher = AHasher::default();
    unsafe {
        let bytes =
            std::slice::from_raw_parts(filter.as_ptr() as *const u8, std::mem::size_of_val(filter));
        hasher.write(bytes);
    }
    hasher.finish()
}

fn filter_cache_capacity() -> usize {
    env::var("RIFFT_FILTER_CACHE")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(32)
}

struct FilterCacheEntry {
    len: usize,
    width: usize,
    height: usize,
    hash: u64,
    filter: Arc<[Complex]>,
    spectrum: Arc<Vec<Complex>>,
}

struct FilterCache {
    entries: VecDeque<FilterCacheEntry>,
    capacity: usize,
}

impl FilterCache {
    fn new(capacity: usize) -> Self {
        Self {
            entries: VecDeque::new(),
            capacity,
        }
    }

    fn get(
        &mut self,
        len: usize,
        width: usize,
        height: usize,
        hash: u64,
        filter: &[Complex],
    ) -> Option<Arc<Vec<Complex>>> {
        if self.capacity == 0 {
            return None;
        }
        for idx in 0..self.entries.len() {
            if let Some(entry) = self.entries.get(idx) {
                if entry.len == len
                    && entry.width == width
                    && entry.height == height
                    && entry.hash == hash
                    && entry.filter.as_ref() == filter
                {
                    let entry = self.entries.remove(idx).expect("entry exists");
                    let spectrum = entry.spectrum.clone();
                    self.entries.push_back(entry);
                    return Some(spectrum);
                }
            }
        }
        None
    }

    fn insert(&mut self, entry: FilterCacheEntry) {
        if self.capacity == 0 {
            return;
        }
        if self.entries.len() >= self.capacity {
            self.entries.pop_front();
        }
        self.entries.push_back(entry);
    }
}
