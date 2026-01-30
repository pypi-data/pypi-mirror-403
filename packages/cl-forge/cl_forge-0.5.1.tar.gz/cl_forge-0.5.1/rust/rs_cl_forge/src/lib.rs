use pyo3::prelude::*;

#[pymodule]
#[pyo3(name = "_rs_cl_forge")]
fn _rs_cl_forge(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let cmf = PyModule::new(py, "_rs_cmf")?;
    rs_cmf::_rs_cmf(&cmf)?;
    m.add_submodule(&cmf)?;

    let verify = PyModule::new(py, "_rs_verify")?;
    rs_verify::_rs_verify(&verify)?;
    m.add_submodule(&verify)?;

    Ok(())
}