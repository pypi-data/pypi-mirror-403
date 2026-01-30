use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::time::Instant;

fn nanos_to_u64(duration: std::time::Duration) -> u64 {
    duration.as_nanos().min(u64::MAX as u128) as u64
}

static ENABLED: AtomicBool = AtomicBool::new(false);
static CALLS: AtomicU64 = AtomicU64::new(0);
static ROW_TOTAL_NS: AtomicU64 = AtomicU64::new(0);
static COL_TOTAL_NS: AtomicU64 = AtomicU64::new(0);
static TRANSPOSE_TOTAL_NS: AtomicU64 = AtomicU64::new(0);
static EXEC_TOTAL_NS: AtomicU64 = AtomicU64::new(0);
static PLAN_CALLS: AtomicU64 = AtomicU64::new(0);
static PLAN_TOTAL_NS: AtomicU64 = AtomicU64::new(0);
static FILTER_FFT_CALLS: AtomicU64 = AtomicU64::new(0);
static FILTER_FFT_HITS: AtomicU64 = AtomicU64::new(0);
static FILTER_FFT_TOTAL_NS: AtomicU64 = AtomicU64::new(0);

pub fn enable(flag: bool) {
    ENABLED.store(flag, Ordering::Relaxed);
}

pub fn is_enabled() -> bool {
    ENABLED.load(Ordering::Relaxed)
}

pub fn reset() {
    CALLS.store(0, Ordering::Relaxed);
    ROW_TOTAL_NS.store(0, Ordering::Relaxed);
    COL_TOTAL_NS.store(0, Ordering::Relaxed);
    TRANSPOSE_TOTAL_NS.store(0, Ordering::Relaxed);
    EXEC_TOTAL_NS.store(0, Ordering::Relaxed);
    PLAN_CALLS.store(0, Ordering::Relaxed);
    PLAN_TOTAL_NS.store(0, Ordering::Relaxed);
    FILTER_FFT_CALLS.store(0, Ordering::Relaxed);
    FILTER_FFT_HITS.store(0, Ordering::Relaxed);
    FILTER_FFT_TOTAL_NS.store(0, Ordering::Relaxed);
}

pub fn record_fft_call(row_ns: u64, col_ns: u64, transpose_ns: u64, exec_ns: u64) {
    CALLS.fetch_add(1, Ordering::Relaxed);
    ROW_TOTAL_NS.fetch_add(row_ns, Ordering::Relaxed);
    COL_TOTAL_NS.fetch_add(col_ns, Ordering::Relaxed);
    TRANSPOSE_TOTAL_NS.fetch_add(transpose_ns, Ordering::Relaxed);
    EXEC_TOTAL_NS.fetch_add(exec_ns, Ordering::Relaxed);
}

pub fn record_plan(ns: u64) {
    PLAN_CALLS.fetch_add(1, Ordering::Relaxed);
    PLAN_TOTAL_NS.fetch_add(ns, Ordering::Relaxed);
}

pub fn record_filter_fft(hit: bool, ns: u64) {
    FILTER_FFT_CALLS.fetch_add(1, Ordering::Relaxed);
    if hit {
        FILTER_FFT_HITS.fetch_add(1, Ordering::Relaxed);
    }
    FILTER_FFT_TOTAL_NS.fetch_add(ns, Ordering::Relaxed);
}

pub struct TimingSummary {
    pub calls: u64,
    pub row_total_ns: u64,
    pub col_total_ns: u64,
    pub transpose_total_ns: u64,
    pub exec_total_ns: u64,
    pub plan_calls: u64,
    pub plan_total_ns: u64,
    pub filter_fft_calls: u64,
    pub filter_fft_hits: u64,
    pub filter_fft_total_ns: u64,
}

impl TimingSummary {
    fn per_call_ms(total_ns: u64, calls: u64) -> f64 {
        if calls == 0 {
            0.0
        } else {
            total_ns as f64 / calls as f64 / 1_000_000.0
        }
    }

    pub fn row_ms(&self) -> f64 {
        Self::per_call_ms(self.row_total_ns, self.calls)
    }

    pub fn col_ms(&self) -> f64 {
        Self::per_call_ms(self.col_total_ns, self.calls)
    }

    pub fn transpose_ms(&self) -> f64 {
        Self::per_call_ms(self.transpose_total_ns, self.calls)
    }

    pub fn exec_ms(&self) -> f64 {
        Self::per_call_ms(self.exec_total_ns, self.calls)
    }

    pub fn plan_ms(&self) -> f64 {
        Self::per_call_ms(self.plan_total_ns, self.plan_calls)
    }

    pub fn filter_fft_ms(&self) -> f64 {
        Self::per_call_ms(self.filter_fft_total_ns, self.filter_fft_calls)
    }
}

pub fn summary() -> TimingSummary {
    TimingSummary {
        calls: CALLS.load(Ordering::Relaxed),
        row_total_ns: ROW_TOTAL_NS.load(Ordering::Relaxed),
        col_total_ns: COL_TOTAL_NS.load(Ordering::Relaxed),
        transpose_total_ns: TRANSPOSE_TOTAL_NS.load(Ordering::Relaxed),
        exec_total_ns: EXEC_TOTAL_NS.load(Ordering::Relaxed),
        plan_calls: PLAN_CALLS.load(Ordering::Relaxed),
        plan_total_ns: PLAN_TOTAL_NS.load(Ordering::Relaxed),
        filter_fft_calls: FILTER_FFT_CALLS.load(Ordering::Relaxed),
        filter_fft_hits: FILTER_FFT_HITS.load(Ordering::Relaxed),
        filter_fft_total_ns: FILTER_FFT_TOTAL_NS.load(Ordering::Relaxed),
    }
}

pub struct CallTimer {
    inner: Option<CallTimerInner>,
}

impl Default for CallTimer {
    fn default() -> Self {
        Self::new()
    }
}

struct CallTimerInner {
    exec_start: Instant,
    row_ns: u64,
    col_ns: u64,
    transpose_ns: u64,
}

impl CallTimer {
    pub fn new() -> Self {
        if !is_enabled() {
            Self { inner: None }
        } else {
            Self {
                inner: Some(CallTimerInner {
                    exec_start: Instant::now(),
                    row_ns: 0,
                    col_ns: 0,
                    transpose_ns: 0,
                }),
            }
        }
    }

    pub fn time_row<F: FnOnce()>(&mut self, f: F) {
        self.time_stage(Stage::Row, f);
    }

    pub fn time_col<F: FnOnce()>(&mut self, f: F) {
        self.time_stage(Stage::Col, f);
    }

    pub fn time_transpose<F: FnOnce()>(&mut self, f: F) {
        self.time_stage(Stage::Transpose, f);
    }

    pub fn finish(self) {
        if let Some(inner) = self.inner {
            let exec_ns = nanos_to_u64(inner.exec_start.elapsed());
            record_fft_call(inner.row_ns, inner.col_ns, inner.transpose_ns, exec_ns);
        }
    }

    fn time_stage<F: FnOnce()>(&mut self, stage: Stage, f: F) {
        if let Some(inner) = &mut self.inner {
            let start = Instant::now();
            f();
            let elapsed = nanos_to_u64(start.elapsed());
            match stage {
                Stage::Row => inner.row_ns = inner.row_ns.saturating_add(elapsed),
                Stage::Col => inner.col_ns = inner.col_ns.saturating_add(elapsed),
                Stage::Transpose => inner.transpose_ns = inner.transpose_ns.saturating_add(elapsed),
            }
        } else {
            f();
        }
    }
}

enum Stage {
    Row,
    Col,
    Transpose,
}

pub fn elapsed_ns(start: Instant) -> u64 {
    nanos_to_u64(start.elapsed())
}
