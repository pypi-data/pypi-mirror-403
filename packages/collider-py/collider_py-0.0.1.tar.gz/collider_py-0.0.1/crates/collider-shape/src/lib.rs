//! # **`collider-shape`**: geometric shapes for collision detection
//!
//! `collider-shape` is a sub-crate of the `collider` library, providing
//! definitions and implementations of geometric shapes used in collision detection.
//!
//! ## Overview
//! A shape is a primitive that represents the properties of a 3D geometric object.
//! Note that a shape does not contain any information about the position
//! or orientation of the object, only its geometric properties.

pub use capsule::*;
pub use cone::*;
pub use cuboid::*;
pub use cylinder::*;
pub use sphere::*;

pub use shape::*;

pub mod shape;

pub mod capsule;
pub mod cone;
pub mod cuboid;
pub mod cylinder;
pub mod sphere;
