use collider_shape::{Shape, ShapeType};

/// A 3D mesh shape.
pub struct Mesh {
    /// The path to the mesh file.
    pub path: String,
}

impl Mesh {
    /// Creates a new Mesh from the given file path.
    pub fn new(path: String) -> Self {
        Mesh { path }
    }
}

impl Shape for Mesh {
    fn is_convex(&self) -> bool {
        false
    }

    fn clone_box(&self) -> Box<dyn Shape + Send + Sync> {
        Box::new(Mesh {
            path: self.path.clone(),
        })
    }

    fn get_shape_type(&self) -> ShapeType {
        ShapeType::Mesh
    }

    fn get_mesh_path(&self) -> Option<String> {
        Some(self.path.clone())
    }
}

/// A Python wrapper for the Mesh type.
#[pyo3::pyclass]
pub struct PyMesh {
    pub inner: Mesh,
}

#[pyo3::pymethods]
impl PyMesh {
    #[new]
    fn new(path: String) -> Self {
        PyMesh {
            inner: Mesh { path },
        }
    }

    #[getter]
    fn get_mesh_path(&self) -> String {
        self.inner.path.clone()
    }
}
