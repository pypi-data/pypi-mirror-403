use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

mod core;

/// Python-exposed function for InfluxDB queries
#[pyfunction]
fn get_influx_data_async<'py>(
    py: Python<'py>,
    url: String,
    token: String,
    org: String,
    query: String,
) -> PyResult<&'py PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        // Call the Rust async function
        let results = core::query_influx(&url, &token, &org, &query)
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        // Convert Vec<HashMap<String, Value>> to Python list[dict]
        Python::with_gil(|py| -> PyResult<PyObject> {
            let py_list = pyo3::types::PyList::empty(py);
            for map in results {
                let py_dict = hashmap_to_pydict(py, map)?;
                py_list.append(py_dict)?;
            }
            Ok(py_list.into())
        })
    })
}

/// Convert Rust HashMap to Python dict
fn hashmap_to_pydict(py: Python, map: HashMap<String, serde_json::Value>) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    for (key, value) in map {
        let py_value = serde_json_to_py(py, value)?;
        dict.set_item(key, py_value)?;
    }
    Ok(dict.into())
}

/// Convert serde_json::Value to PyObject
fn serde_json_to_py(py: Python, value: serde_json::Value) -> PyResult<PyObject> {
    use serde_json::Value as JValue;
    match value {
        JValue::Null => Ok(py.None()),
        JValue::Bool(b) => Ok(b.into_py(py)),
        JValue::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.into_py(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.into_py(py))
            } else {
                Ok(py.None())
            }
        }
        JValue::String(s) => Ok(s.into_py(py)),
        JValue::Array(arr) => {
            let py_list = pyo3::types::PyList::empty(py);
            for item in arr {
                py_list.append(serde_json_to_py(py, item)?)?;
            }
            Ok(py_list.into())
        }
        JValue::Object(obj) => {
            let py_dict = PyDict::new(py);
            for (key, val) in obj {
                py_dict.set_item(key, serde_json_to_py(py, val)?)?;
            }
            Ok(py_dict.into())
        }
    }
}

#[pymodule]
fn influx_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_influx_data_async, m)?)?;
    Ok(())
}
