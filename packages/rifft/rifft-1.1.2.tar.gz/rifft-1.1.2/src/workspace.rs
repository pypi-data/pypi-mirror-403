use crate::types::Result;
use num_complex::Complex32;
use once_cell::sync::Lazy;
use parking_lot::Mutex;
use std::cell::RefCell;
use std::ops::{Deref, DerefMut};
use std::sync::Arc;

pub type Complex = Complex32;

thread_local! {
    static TLS_SCRATCH: RefCell<Vec<Complex>> = const { RefCell::new(Vec::new()) };
}

pub struct WorkspacePool {
    buffers: Mutex<Vec<Vec<Complex>>>,
}

impl WorkspacePool {
    pub fn new() -> Self {
        Self {
            buffers: Mutex::new(Vec::new()),
        }
    }

    pub fn acquire(self: &Arc<Self>, len: usize) -> Result<WorkspaceGuard> {
        let mut buffers = self.buffers.lock();
        if let Some(mut buf) = buffers.pop() {
            if buf.len() < len {
                buf.resize(len, Complex::default());
            } else if buf.len() > len {
                buf.truncate(len);
            }
            return Ok(WorkspaceGuard {
                buffer: Some(buf),
                pool: Arc::clone(self),
            });
        }
        let mut buf = Vec::with_capacity(len);
        buf.resize(len, Complex::default());
        Ok(WorkspaceGuard {
            buffer: Some(buf),
            pool: Arc::clone(self),
        })
    }

    fn release(&self, buf: Vec<Complex>) {
        if buf.capacity() > 4 * 1024 * 1024 {
            return;
        }
        let mut buffers = self.buffers.lock();
        if buffers.len() < 16 {
            buffers.push(buf);
        }
    }
}

impl Default for WorkspacePool {
    fn default() -> Self {
        Self::new()
    }
}

pub struct WorkspaceGuard {
    buffer: Option<Vec<Complex>>,
    pool: Arc<WorkspacePool>,
}

impl Deref for WorkspaceGuard {
    type Target = [Complex];
    fn deref(&self) -> &Self::Target {
        self.buffer.as_ref().unwrap()
    }
}

impl DerefMut for WorkspaceGuard {
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.buffer.as_mut().unwrap()
    }
}

impl Drop for WorkspaceGuard {
    fn drop(&mut self) {
        if let Some(buf) = self.buffer.take() {
            self.pool.release(buf);
        }
    }
}

impl AsMut<[Complex]> for WorkspaceGuard {
    fn as_mut(&mut self) -> &mut [Complex] {
        self.buffer.as_mut().unwrap()
    }
}

pub static GLOBAL_WORKSPACE: Lazy<Arc<WorkspacePool>> =
    Lazy::new(|| Arc::new(WorkspacePool::new()));

pub fn acquire(len: usize) -> Result<WorkspaceGuard> {
    GLOBAL_WORKSPACE.acquire(len)
}

pub fn with_tls_scratch<F, R>(len: usize, f: F) -> R
where
    F: FnOnce(&mut [Complex]) -> R,
{
    TLS_SCRATCH.with(|scratch| {
        let mut buffer = scratch.borrow_mut();
        if buffer.len() < len {
            buffer.resize(len, Complex::default());
        }
        f(&mut buffer[..len])
    })
}
