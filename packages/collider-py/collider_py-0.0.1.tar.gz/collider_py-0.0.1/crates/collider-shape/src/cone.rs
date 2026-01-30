use pyo3::{pyclass, pymethods};

use crate::shape::Shape;

/// A cone shape aligned along the `z`-axis.
///
/// The base of the cone is at `(0, 0, -half_length)` and the tip is at `(0, 0, half_length)`.
#[derive(PartialEq, Debug, Copy, Clone)]
pub struct Cone {
    /// The radius of the cone.
    pub radius: f32,
    /// The half length of the cone along the `z`-axis.
    pub half_length: f32,
}
impl Cone {
    /// Creates a new cone with given radius and half height.
    ///
    /// # Arguments
    ///
    /// * `radius` - The radius of the cone.
    /// * `half_length` - The half length of the cone along the `z`-axis.
    pub fn new(radius: f32, half_length: f32) -> Self {
        Cone {
            radius,
            half_length,
        }
    }
}

impl Shape for Cone {
    fn is_convex(&self) -> bool {
        true
    }

    fn clone_box(&self) -> Box<dyn Shape + Send + Sync> {
        Box::new(*self)
    }

    fn get_shape_type(&self) -> crate::shape::ShapeType {
        crate::shape::ShapeType::Cone
    }

    fn get_radius(&self) -> Option<f32> {
        Some(self.radius)
    }

    fn get_half_length(&self) -> Option<f32> {
        Some(self.half_length)
    }
}

#[pyclass(name = "Cone")]
pub struct PyCone {
    pub inner: Cone,
}

#[pymethods]
impl PyCone {
    /// Creates a new cone with given radius and half height.
    ///
    /// # Arguments
    ///
    /// * `radius` - The radius of the cone.
    /// * `ength` - The length of the cone along the `z`-axis.
    #[new]
    fn new(radius: f32, length: f32) -> Self {
        PyCone {
            inner: Cone::new(radius, length / 2.0),
        }
    }

    /// Returns the radius of the cone.
    fn radius(&self) -> f32 {
        self.inner.radius
    }

    /// Returns the half length of the cone.
    fn half_length(&self) -> f32 {
        self.inner.half_length
    }
}
