use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs::File;
use std::io::BufReader;

#[pyclass]
#[derive(Serialize, Deserialize)]
struct IDF {
    data: Value,
}

#[pymethods]
impl IDF {
    #[new]
    fn new(file_path: &str) -> PyResult<Self> {
        let file = File::open(file_path).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        let reader = BufReader::new(file);
        let data: Value = serde_json::from_reader(reader)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(IDF { data })
    }

    fn get_data(&self) -> PyResult<String> {
        serde_json::to_string(&self.data)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }
}

#[pymodule]
fn idf_parser(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<IDF>()?;
    Ok(())
}
