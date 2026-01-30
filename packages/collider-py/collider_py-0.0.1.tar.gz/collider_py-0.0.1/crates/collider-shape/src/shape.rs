//! This module defines a trait for geometric shapes and a wrapper type for dynamic dispatch.

use std::fmt::Debug;

use nalgebra::Vector3;
use numpy::{ToPyArray, ndarray::Array1};
use pyo3::prelude::*;

/// A type alias for an object implementing the Shape trait.
/// This is separated from ShapeWrapper to allow for implementing the Debug trait.
pub type InnerShapeWrapper = dyn Shape + Send + Sync;

impl Debug for &InnerShapeWrapper {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("InnerShapeWrapper")
            .field("shape_type", &self.get_shape_type())
            .field("radius", &self.get_radius())
            .field("half_extents", &self.get_half_extents())
            .field("half_length", &self.get_half_length())
            .finish()
    }
}

impl PartialEq for &InnerShapeWrapper {
    fn eq(&self, other: &Self) -> bool {
        self.get_shape_type() == other.get_shape_type()
            && self.get_radius() == other.get_radius()
            && self.get_half_extents() == other.get_half_extents()
            && self.get_half_length() == other.get_half_length()
    }
}

/// A wrapper type for the Shape trait to allow dynamic dispatch.
pub type ShapeWrapper = Box<InnerShapeWrapper>;

impl PartialEq for ShapeWrapper {
    fn eq(&self, other: &Self) -> bool {
        self.get_shape_type() == other.get_shape_type()
            && self.get_radius() == other.get_radius()
            && self.get_half_extents() == other.get_half_extents()
            && self.get_half_length() == other.get_half_length()
    }
}

/// Shape trait for defining geometric shapes.
pub trait Shape {
    /// Returns whether the shape is convex or not.
    fn is_convex(&self) -> bool;

    /// Clones the shape and returns a boxed version of it.
    fn clone_box(&self) -> ShapeWrapper;

    /// Returns the shape type.
    fn get_shape_type(&self) -> ShapeType;

    /// Returns the radius of the shape.
    fn get_radius(&self) -> Option<f32> {
        None
    }

    /// Returns the half extents of the shape.
    fn get_half_extents(&self) -> Option<Vector3<f32>> {
        None
    }

    /// Returns the half length of the shape.
    fn get_half_length(&self) -> Option<f32> {
        None
    }

    /// Returns the mesh path of the shape.
    fn get_mesh_path(&self) -> Option<String> {
        None
    }
}

#[pyclass]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ShapeType {
    Capsule,
    Cone,
    Cuboid,
    Cylinder,
    Sphere,
    Mesh,
}

/// A Python wrapper for the ShapeWrapper type.
#[pyo3::pyclass(name = "Shape")]
pub struct PyShapeWrapper {
    pub inner: ShapeWrapper,
}

#[pyo3::pymethods]
impl PyShapeWrapper {
    #[getter]
    fn get_shape_type(&self) -> PyResult<ShapeType> {
        Ok(self.inner.get_shape_type())
    }

    #[getter]
    fn get_radius(&self) -> PyResult<f32> {
        if let Some(radius) = self.inner.get_radius() {
            Ok(radius)
        } else {
            Err(pyo3::exceptions::PyValueError::new_err(
                "Shape does not have a radius",
            ))
        }
    }

    #[getter]
    fn get_half_extents(&self, py: Python) -> PyResult<Py<PyAny>> {
        if let Some(half_extents) = self.inner.get_half_extents() {
            Ok(Array1::from_shape_vec(3, half_extents.as_slice().to_vec())
                .unwrap()
                .to_pyarray(py)
                .into_any()
                .unbind())
        } else {
            Err(pyo3::exceptions::PyValueError::new_err(
                "Shape does not have half extents",
            ))
        }
    }

    #[getter]
    fn get_half_length(&self) -> PyResult<f32> {
        if let Some(half_length) = self.inner.get_half_length() {
            Ok(half_length)
        } else {
            Err(pyo3::exceptions::PyValueError::new_err(
                "Shape does not have a half length",
            ))
        }
    }

    #[getter]
    fn get_mesh_path(&self) -> PyResult<String> {
        if let Some(path) = self.inner.get_mesh_path() {
            Ok(path)
        } else {
            Err(pyo3::exceptions::PyValueError::new_err(
                "Shape is not a mesh and does not have a path",
            ))
        }
    }
}
