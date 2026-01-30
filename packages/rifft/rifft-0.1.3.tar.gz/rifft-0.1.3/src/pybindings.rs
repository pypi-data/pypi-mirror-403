use crate::dlpack::{self, DLManagedTensor, DlManagedTensorHandle};
use crate::timing;
use crate::RifftHandle;
use num_complex::Complex32;
use numpy::{PyArrayDyn, PyArrayMethods, PyUntypedArrayMethods};
use once_cell::sync::Lazy;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyCapsule, PyDict, PyTuple};
use pyo3::wrap_pyfunction;
use std::ffi::CStr;
use std::os::raw::c_void;

static NUMPY_HANDLE: Lazy<RifftHandle> = Lazy::new(RifftHandle::new);

#[pyclass(name = "Handle")]
pub struct PyHandle {
    inner: RifftHandle,
}

#[pymethods]
impl PyHandle {
    #[new]
    pub fn new() -> Self {
        Self {
            inner: RifftHandle::new(),
        }
    }

    #[pyo3(signature = (capsule, *, column_major = false))]
    fn fft2<'py>(
        &mut self,
        py: Python<'py>,
        capsule: &Bound<'py, PyCapsule>,
        column_major: bool,
    ) -> PyResult<Bound<'py, PyCapsule>> {
        transform_capsule(py, capsule, |data, h, w| {
            if column_major {
                self.inner.fft2d_forward_transposed(data, h, w)
            } else {
                self.inner.fft2d_forward(data, h, w)
            }
        })
    }

    fn ifft2<'py>(
        &mut self,
        py: Python<'py>,
        capsule: &Bound<'py, PyCapsule>,
    ) -> PyResult<Bound<'py, PyCapsule>> {
        transform_capsule(py, capsule, |data, h, w| {
            self.inner.fft2d_inverse(data, h, w)
        })
    }

    fn fft_filter_ifft<'py>(
        &mut self,
        py: Python<'py>,
        data_capsule: &Bound<'py, PyCapsule>,
        filter_capsule: &Bound<'py, PyCapsule>,
    ) -> PyResult<Bound<'py, PyTuple>> {
        transform_two_capsules(py, data_capsule, filter_capsule, |data, filter, h, w| {
            self.inner.fft_filter_ifft(data, filter, h, w)
        })
    }

    fn preplan(&mut self, shapes: Vec<(usize, usize)>) -> PyResult<()> {
        self.inner.preplan(&shapes).map_err(py_err)
    }
}

pub fn register(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyHandle>()?;
    module.add_function(wrap_pyfunction!(fft_numpy, module)?)?;
    module.add_function(wrap_pyfunction!(ifft_numpy, module)?)?;
    module.add_function(wrap_pyfunction!(enable_timing_py, module)?)?;
    module.add_function(wrap_pyfunction!(timing_reset_py, module)?)?;
    module.add_function(wrap_pyfunction!(timing_summary_py, module)?)?;
    module.add("__version__", crate::get_version())?;
    Ok(())
}

#[pyfunction]
fn fft_numpy<'py>(
    array: &Bound<'py, PyArrayDyn<Complex32>>,
) -> PyResult<Bound<'py, PyArrayDyn<Complex32>>> {
    if !array.is_c_contiguous() {
        return Err(PyRuntimeError::new_err(
            "RIFFT expects a C_CONTIGUOUS NumPy array",
        ));
    }
    let (height, width) = infer_hw(array.shape())?;
    let data = unsafe { array.as_slice_mut()? };
    NUMPY_HANDLE
        .fft2d_forward(data, height, width)
        .map_err(py_err)?;
    Ok(array.clone())
}

#[pyfunction]
fn ifft_numpy<'py>(
    array: &Bound<'py, PyArrayDyn<Complex32>>,
) -> PyResult<Bound<'py, PyArrayDyn<Complex32>>> {
    if !array.is_c_contiguous() {
        return Err(PyRuntimeError::new_err(
            "RIFFT expects a C_CONTIGUOUS NumPy array",
        ));
    }
    let (height, width) = infer_hw(array.shape())?;
    let data = unsafe { array.as_slice_mut()? };
    NUMPY_HANDLE
        .fft2d_inverse(data, height, width)
        .map_err(py_err)?;
    Ok(array.clone())
}

fn infer_hw(shape: &[usize]) -> PyResult<(usize, usize)> {
    match shape.len() {
        2 => Ok((shape[0], shape[1])),
        3 => Ok((shape[shape.len() - 2], shape[shape.len() - 1])),
        _ => Err(PyRuntimeError::new_err(
            "RIFFT expects inputs shaped (H, W) or (B, H, W)",
        )),
    }
}

#[pyfunction(name = "enable_timing")]
fn enable_timing_py(enabled: bool) -> PyResult<()> {
    timing::enable(enabled);
    Ok(())
}

#[pyfunction(name = "timing_reset")]
fn timing_reset_py() -> PyResult<()> {
    timing::reset();
    Ok(())
}

#[pyfunction(name = "timing_summary")]
fn timing_summary_py(py: Python<'_>) -> PyResult<Bound<'_, PyDict>> {
    let summary = timing::summary();
    let dict = PyDict::new_bound(py);
    dict.set_item("calls", summary.calls)?;
    dict.set_item("row_total_ns", summary.row_total_ns)?;
    dict.set_item("col_total_ns", summary.col_total_ns)?;
    dict.set_item("transpose_total_ns", summary.transpose_total_ns)?;
    dict.set_item("exec_total_ns", summary.exec_total_ns)?;
    dict.set_item("row_ms", summary.row_ms())?;
    dict.set_item("col_ms", summary.col_ms())?;
    dict.set_item("transpose_ms", summary.transpose_ms())?;
    dict.set_item("exec_ms", summary.exec_ms())?;
    dict.set_item("plan_calls", summary.plan_calls)?;
    dict.set_item("plan_total_ns", summary.plan_total_ns)?;
    dict.set_item("plan_ms", summary.plan_ms())?;
    dict.set_item("filter_fft_calls", summary.filter_fft_calls)?;
    dict.set_item("filter_fft_hits", summary.filter_fft_hits)?;
    dict.set_item("filter_fft_total_ns", summary.filter_fft_total_ns)?;
    dict.set_item("filter_fft_ms", summary.filter_fft_ms())?;
    Ok(dict)
}

fn transform_capsule<'py, F>(
    py: Python<'py>,
    capsule: &Bound<'py, PyCapsule>,
    f: F,
) -> PyResult<Bound<'py, PyCapsule>>
where
    F: FnOnce(&mut [Complex32], usize, usize) -> crate::types::Result<()>,
{
    let mut handle = take_capsule(py, capsule)?;
    let height = handle.height();
    let width = handle.width();
    let slice = unsafe { handle.as_mut_slice() };
    f(slice, height, width).map_err(py_err)?;
    make_capsule(py, handle)
}

fn transform_two_capsules<'py, F>(
    py: Python<'py>,
    data_capsule: &Bound<'py, PyCapsule>,
    filter_capsule: &Bound<'py, PyCapsule>,
    f: F,
) -> PyResult<Bound<'py, PyTuple>>
where
    F: FnOnce(&mut [Complex32], &[Complex32], usize, usize) -> crate::types::Result<()>,
{
    let mut data_handle = take_capsule(py, data_capsule)?;
    let mut filter_handle = take_capsule(py, filter_capsule)?;
    if data_handle.len() != filter_handle.len() {
        return Err(PyRuntimeError::new_err("filter and data size mismatch"));
    }
    let height = data_handle.height();
    let width = data_handle.width();
    let data_slice = unsafe { data_handle.as_mut_slice() };
    let filter_slice = unsafe { filter_handle.as_mut_slice() };
    f(data_slice, filter_slice, height, width).map_err(py_err)?;
    let data_capsule_obj = make_capsule(py, data_handle)?;
    let filter_capsule_obj = make_capsule(py, filter_handle)?;
    let tuple = PyTuple::new_bound(
        py,
        &[data_capsule_obj.into_any(), filter_capsule_obj.into_any()],
    );
    Ok(tuple)
}

fn take_capsule<'py>(
    py: Python<'py>,
    capsule: &Bound<'py, PyCapsule>,
) -> PyResult<DlManagedTensorHandle> {
    let ptr = capsule.pointer();
    if ptr.is_null() {
        return Err(PyRuntimeError::new_err("capsule pointer was null"));
    }
    let status =
        unsafe { pyo3::ffi::PyCapsule_SetName(capsule.as_ptr(), used_dlpack_name().as_ptr()) };
    if status != 0 {
        return Err(PyErr::fetch(py));
    }
    unsafe { dlpack::from_dlpack_capsule(ptr) }.map_err(py_err)
}

fn make_capsule<'py>(
    py: Python<'py>,
    handle: DlManagedTensorHandle,
) -> PyResult<Bound<'py, PyCapsule>> {
    let raw = handle.into_raw() as *mut c_void;
    let capsule_ptr =
        unsafe { pyo3::ffi::PyCapsule_New(raw, dlpack_name().as_ptr(), Some(drop_dlpack_capsule)) };
    if capsule_ptr.is_null() {
        return Err(PyErr::fetch(py));
    }
    let any = unsafe { Bound::from_owned_ptr(py, capsule_ptr) };
    any.downcast_into::<PyCapsule>().map_err(|err| err.into())
}

fn dlpack_name() -> &'static CStr {
    unsafe { CStr::from_bytes_with_nul_unchecked(b"dltensor\0") }
}

fn used_dlpack_name() -> &'static CStr {
    unsafe { CStr::from_bytes_with_nul_unchecked(b"used_dltensor\0") }
}

fn py_err<E: std::fmt::Display>(err: E) -> PyErr {
    PyRuntimeError::new_err(err.to_string())
}

unsafe extern "C" fn drop_dlpack_capsule(obj: *mut pyo3::ffi::PyObject) {
    if obj.is_null() {
        return;
    }
    let ptr = pyo3::ffi::PyCapsule_GetPointer(obj, std::ptr::null());
    if ptr.is_null() {
        unsafe { pyo3::ffi::PyErr_Clear() };
        return;
    }
    // Reconstruct handle and drop immediately to invoke deleter.
    let _ = dlpack::DlManagedTensorHandle::from_raw(ptr as *mut DLManagedTensor);
}
