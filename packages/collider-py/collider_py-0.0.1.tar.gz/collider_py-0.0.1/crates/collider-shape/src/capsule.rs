use pyo3::{pyclass, pymethods};

use crate::shape::Shape;

/// A capsule shape aligned along the `z`-axis.
///
/// Mathematically, a capsule is the set of points that are at most `radius` units away from the line segment.
/// The line segment is defined by the two endpoints at `(0, 0, -half_length)` and `(0, 0, half_length)`.
#[derive(PartialEq, Debug, Copy, Clone)]
pub struct Capsule {
    /// The radius of the capsule.
    pub radius: f32,
    /// The half length of the capsule along the `z`-axis.
    pub half_length: f32,
}

impl Capsule {
    /// Creates a new capsule with given radius and half length.
    ///
    /// # Arguments
    ///
    /// * `radius` - The radius of the capsule.
    /// * `half_length` - The half length of the capsule along the `z`-axis.
    pub fn new(radius: f32, half_length: f32) -> Self {
        Capsule {
            radius,
            half_length,
        }
    }
}

impl Shape for Capsule {
    fn is_convex(&self) -> bool {
        true
    }

    fn clone_box(&self) -> Box<dyn Shape + Send + Sync> {
        Box::new(*self)
    }

    fn get_shape_type(&self) -> crate::shape::ShapeType {
        crate::shape::ShapeType::Capsule
    }

    fn get_radius(&self) -> Option<f32> {
        Some(self.radius)
    }

    fn get_half_length(&self) -> Option<f32> {
        Some(self.half_length)
    }
}

#[pyclass(name = "Capsule")]
pub struct PyCapsule {
    pub inner: Capsule,
}

#[pymethods]
impl PyCapsule {
    /// Creates a new capsule with given radius and length along the `z` axis.
    #[new]
    fn new(radius: f32, length: f32) -> Self {
        PyCapsule {
            inner: Capsule::new(radius, length / 2.0),
        }
    }
}
