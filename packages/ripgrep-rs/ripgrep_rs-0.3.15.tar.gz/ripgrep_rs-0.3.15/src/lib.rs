use pyo3::prelude::*;

mod ripgrep_core;
use ripgrep_core::{FileInfo, PySortMode, PySortModeKind, py_files, py_files_with_info, py_search};

#[pymodule(gil_used = false)]
fn ripgrep_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySortMode>()?;
    m.add_class::<PySortModeKind>()?;
    m.add_class::<FileInfo>()?;
    m.add_function(wrap_pyfunction!(py_search, m)?)?;
    m.add_function(wrap_pyfunction!(py_files, m)?)?;
    m.add_function(wrap_pyfunction!(py_files_with_info, m)?)?;
    Ok(())
}
