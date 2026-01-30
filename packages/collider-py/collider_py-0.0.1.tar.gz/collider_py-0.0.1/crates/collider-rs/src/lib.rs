//! # **`collider`**: efficient collision detection
//!
//! `collider` is a Rust library designed for efficient collision detection in 3D space.
//! The library is still experimental, and the API may change in future releases.
//!
//! ## Shapes
//! The library provides a variety of shapes for collision detection.
//! The following primitives are available:
//! - Capsule
//! - Cone
//! - Cuboid (also known as a Box)
//! - Cylinder
//! - Sphere
//!
//! ## Bounding Volumes
//! The library includes bounding volume types to optimize collision detection.
//! The available bounding volumes are:
//! - Axis-Aligned Bounding Box (AABB)
//! - Sphere Bounding Volume
//!
//! ## Modules
//! The library is organized into several modules:
//! - `collider-shape`: Contains definitions and implementations of geometric shapes.
//! - `collider-bounding-volume`: Contains definitions and implementations of bounding volumes.
//! - `collider-mesh`: Provides functionality for handling mesh data.
//! - `collider-query`: Provides query functionalities for collision detection.
//! - `collider-py`: Python bindings for the collider library.

pub use collider_mesh as mesh;
pub use collider_shape as shape;
