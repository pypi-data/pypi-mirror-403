use pyo3::prelude::*;

use collider_rs::mesh::PyMesh;
use collider_rs::shape::{PyCapsule, PyCone, PyCuboid, PyCylinder, PySphere};

/// A Python module implemented in Rust.
#[pymodule(name = "collider")]
fn collider_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Shapes
    m.add_class::<PyCapsule>()?;
    m.add_class::<PyCone>()?;
    m.add_class::<PyCuboid>()?;
    m.add_class::<PyCylinder>()?;
    m.add_class::<PySphere>()?;

    // Mesh
    m.add_class::<PyMesh>()?;

    Ok(())
}
