use nalgebra::Vector3;
use pyo3::prelude::*;

use crate::shape::Shape;

/// A cuboid shape.
///
/// The cuboid is zero-centered and defined by its half extents along the `x`, `y`, and `z` axes.
#[derive(PartialEq, Debug, Clone, Copy)]
pub struct Cuboid {
    /// The half extents of the cuboid.
    pub half_extents: Vector3<f32>,
}

impl Cuboid {
    /// Creates a new cuboid with given half extents.
    ///
    /// # Arguments
    ///
    /// * `half_extents` - The half extents of the cuboid along the `x`, `y`, and `z` axes.
    pub fn new(half_extents: Vector3<f32>) -> Self {
        Cuboid { half_extents }
    }
}

impl Shape for Cuboid {
    fn is_convex(&self) -> bool {
        true
    }

    fn clone_box(&self) -> Box<dyn Shape + Send + Sync> {
        Box::new(*self)
    }

    fn get_shape_type(&self) -> crate::shape::ShapeType {
        crate::shape::ShapeType::Cuboid
    }

    fn get_half_extents(&self) -> Option<Vector3<f32>> {
        Some(self.half_extents)
    }
}

#[pyclass(name = "Cuboid")]
pub struct PyCuboid {
    pub inner: Cuboid,
}

#[pymethods]
impl PyCuboid {
    /// Creates a new cuboid with given half extents.
    ///
    /// # Arguments
    ///
    /// * `sides` - The length of the sides of the cuboid along the `x`, `y`, and `z` axes.
    #[new]
    fn new(sides: Vec<f32>) -> Self {
        PyCuboid {
            inner: Cuboid::new(Vector3::new(sides[0] / 2.0, sides[1] / 2.0, sides[2] / 2.0)),
        }
    }
}
