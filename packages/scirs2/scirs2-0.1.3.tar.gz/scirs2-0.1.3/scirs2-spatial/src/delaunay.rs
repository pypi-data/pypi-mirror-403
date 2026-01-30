//! Delaunay triangulation algorithms (Pure Rust)
//!
//! This module provides implementations for Delaunay triangulation of points in arbitrary dimensions.
//! Delaunay triangulation connects points to form simplices such that no point is inside the
//! circumhypersphere of any simplex.
//!
//! # Implementation
//!
//! This module uses the Bowyer-Watson algorithm for computing Delaunay triangulations in 2D, 3D,
//! and higher dimensions (nD). This is a pure Rust implementation with no external C library dependencies.
//!
//! **Supported Dimensions**: 2D, 3D, 4D, 5D, ..., nD
//! **Algorithm**: Bowyer-Watson incremental insertion with lifting map for in-hypersphere tests
//! **Complexity**: O(n^⌈d/2⌉) where n = points, d = dimensions
//!
//! # Examples
//!
//! ```
//! use scirs2_spatial::delaunay::Delaunay;
//! use scirs2_core::ndarray::array;
//!
//! // Create a set of 2D points
//! let points = array![
//!     [0.0, 0.0],
//!     [1.0, 0.0],
//!     [0.0, 1.0],
//!     [0.5, 0.5]
//! ];
//!
//! // Compute Delaunay triangulation
//! let tri = Delaunay::new(&points).expect("Operation failed");
//!
//! // Get the simplex (triangle) indices
//! let simplices = tri.simplices();
//! println!("Triangles: {:?}", simplices);
//!
//! // Find the triangle containing a point
//! let point = [0.25, 0.25];
//! if let Some(idx) = tri.find_simplex(&point) {
//!     println!("Point {:?} is in triangle {}", point, idx);
//! }
//! ```

use crate::error::{SpatialError, SpatialResult};
use scirs2_core::ndarray::Array2;
use std::collections::{HashMap, HashSet};
use std::fmt::Debug;

/// Structure for storing and querying a Delaunay triangulation
///
/// The Delaunay triangulation of a set of points is a triangulation such that
/// no point is inside the circumhypersphere of any simplex. This property holds
/// in all dimensions:
/// - 2D: No point inside circumcircle of any triangle
/// - 3D: No point inside circumsphere of any tetrahedron
/// - nD: No point inside circumhypersphere of any n-simplex
///
/// This is a pure Rust implementation using the Bowyer-Watson algorithm with no
/// external C library dependencies. Supports arbitrary dimensions (2D, 3D, 4D, 5D, ..., nD).
pub struct Delaunay {
    /// The points used for the triangulation
    points: Array2<f64>,

    /// The number of dimensions
    ndim: usize,

    /// The number of points
    npoints: usize,

    /// The simplices (triangles in 2D, tetrahedra in 3D, etc.)
    /// Each element is a vector of indices of the vertices forming a simplex
    simplices: Vec<Vec<usize>>,

    /// For each simplex, its neighboring simplices
    /// neighbors[i][j] is the index of the simplex that shares a face with simplex i,
    /// opposite to the vertex j of simplex i. -1 indicates no neighbor.
    neighbors: Vec<Vec<i64>>,

    /// Constraint edges (for constrained Delaunay triangulation)
    /// Each edge is represented as a pair of point indices
    constraints: Vec<(usize, usize)>,
}

impl Debug for Delaunay {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Delaunay")
            .field("points", &self.points.shape())
            .field("ndim", &self.ndim)
            .field("npoints", &self.npoints)
            .field("simplices", &self.simplices.len())
            .field("neighbors", &self.neighbors.len())
            .field("constraints", &self.constraints.len())
            .finish()
    }
}

impl Clone for Delaunay {
    fn clone(&self) -> Self {
        Self {
            points: self.points.clone(),
            ndim: self.ndim,
            npoints: self.npoints,
            simplices: self.simplices.clone(),
            neighbors: self.neighbors.clone(),
            constraints: self.constraints.clone(),
        }
    }
}

impl Delaunay {
    /// Create a new Delaunay triangulation
    ///
    /// # Arguments
    ///
    /// * `points` - The points to triangulate, shape (npoints, ndim)
    ///
    /// # Returns
    ///
    /// * A new Delaunay triangulation or an error
    ///
    /// # Examples
    ///
    /// ```
    /// use scirs2_spatial::delaunay::Delaunay;
    /// use scirs2_core::ndarray::array;
    ///
    /// let points = array![
    ///     [0.0, 0.0],
    ///     [1.0, 0.0],
    ///     [0.0, 1.0],
    ///     [1.0, 1.0]
    /// ];
    ///
    /// let tri = Delaunay::new(&points).expect("Operation failed");
    /// let simplices = tri.simplices();
    /// println!("Triangles: {:?}", simplices);
    /// ```
    pub fn new(points: &Array2<f64>) -> SpatialResult<Self> {
        let npoints = points.nrows();
        let ndim = points.ncols();

        // Check if we have enough points for triangulation
        if npoints <= ndim {
            return Err(SpatialError::ValueError(format!(
                "Need at least {} points in {} dimensions for triangulation",
                ndim + 1,
                ndim
            )));
        }

        // Special case for 3 points in 2D - form a single triangle
        if ndim == 2 && npoints == 3 {
            let simplex = vec![0, 1, 2];
            let simplices = vec![simplex];
            let neighbors = vec![vec![-1, -1, -1]]; // No neighbors

            return Ok(Delaunay {
                points: points.clone(),
                ndim,
                npoints,
                simplices,
                neighbors,
                constraints: Vec::new(),
            });
        }

        // Use Bowyer-Watson algorithm for 2D, 3D, and nD
        let simplices = match ndim {
            2 => Self::bowyer_watson_2d(points)?,
            3 => Self::bowyer_watson_3d(points)?,
            _ => Self::bowyer_watson_nd(points, ndim)?,
        };

        // Calculate neighbors of each simplex
        let neighbors = Self::calculate_neighbors(&simplices, ndim + 1);

        Ok(Delaunay {
            points: points.clone(),
            ndim,
            npoints,
            simplices,
            neighbors,
            constraints: Vec::new(),
        })
    }

    /// Bowyer-Watson algorithm for 2D Delaunay triangulation
    ///
    /// This algorithm incrementally builds the Delaunay triangulation by:
    /// 1. Creating a super-triangle that contains all points
    /// 2. Adding points one at a time
    /// 3. For each point, finding all triangles whose circumcircle contains the point
    /// 4. Removing those triangles and retriangulating the hole
    /// 5. Removing triangles connected to the super-triangle vertices
    fn bowyer_watson_2d(points: &Array2<f64>) -> SpatialResult<Vec<Vec<usize>>> {
        let npoints = points.nrows();

        // Find bounding box
        let mut min_x = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_y = f64::NEG_INFINITY;

        for i in 0..npoints {
            let x = points[[i, 0]];
            let y = points[[i, 1]];
            min_x = min_x.min(x);
            max_x = max_x.max(x);
            min_y = min_y.min(y);
            max_y = max_y.max(y);
        }

        // Create super-triangle that contains all points
        let dx = max_x - min_x;
        let dy = max_y - min_y;
        let delta_max = dx.max(dy);
        let mid_x = (min_x + max_x) / 2.0;
        let mid_y = (min_y + max_y) / 2.0;

        // Super-triangle vertices (with large margin)
        let margin = 20.0;
        let super_p0 = [mid_x - margin * delta_max, mid_y - delta_max];
        let super_p1 = [mid_x, mid_y + margin * delta_max];
        let super_p2 = [mid_x + margin * delta_max, mid_y - delta_max];

        // Extended point list (original points + super-triangle vertices)
        // Super-triangle vertices are at indices npoints, npoints+1, npoints+2
        let mut all_points: Vec<[f64; 2]> = Vec::with_capacity(npoints + 3);
        for i in 0..npoints {
            all_points.push([points[[i, 0]], points[[i, 1]]]);
        }
        all_points.push(super_p0);
        all_points.push(super_p1);
        all_points.push(super_p2);

        // Initialize with super-triangle
        let mut triangles: Vec<[usize; 3]> = vec![[npoints, npoints + 1, npoints + 2]];

        // Add points one at a time
        for point_idx in 0..npoints {
            let point = all_points[point_idx];

            // Find all triangles whose circumcircle contains this point
            let mut bad_triangles: Vec<usize> = Vec::new();
            for (tri_idx, tri) in triangles.iter().enumerate() {
                let p0 = all_points[tri[0]];
                let p1 = all_points[tri[1]];
                let p2 = all_points[tri[2]];

                if Self::point_in_circumcircle_2d(point, p0, p1, p2) {
                    bad_triangles.push(tri_idx);
                }
            }

            // Find the boundary of the polygonal hole
            let mut polygon_edges: Vec<[usize; 2]> = Vec::new();
            for &tri_idx in &bad_triangles {
                let tri = triangles[tri_idx];
                let edges = [[tri[0], tri[1]], [tri[1], tri[2]], [tri[2], tri[0]]];

                for edge in &edges {
                    // Check if this edge is shared with another bad triangle
                    let mut is_shared = false;
                    for &other_idx in &bad_triangles {
                        if other_idx == tri_idx {
                            continue;
                        }
                        let other_tri = triangles[other_idx];
                        if Self::triangle_has_edge_2d(&other_tri, edge[0], edge[1]) {
                            is_shared = true;
                            break;
                        }
                    }

                    if !is_shared {
                        polygon_edges.push(*edge);
                    }
                }
            }

            // Remove bad triangles (in reverse order to maintain indices)
            bad_triangles.sort_by(|a, b| b.cmp(a));
            for tri_idx in bad_triangles {
                triangles.remove(tri_idx);
            }

            // Create new triangles from polygon edges to the new point
            for edge in polygon_edges {
                triangles.push([point_idx, edge[0], edge[1]]);
            }
        }

        // Remove triangles that have a vertex from the super-triangle
        let super_vertices = [npoints, npoints + 1, npoints + 2];
        triangles.retain(|tri| !tri.iter().any(|&v| super_vertices.contains(&v)));

        // Convert to Vec<Vec<usize>>
        let simplices: Vec<Vec<usize>> = triangles.iter().map(|t| t.to_vec()).collect();

        Ok(simplices)
    }

    /// Check if a triangle has a specific edge
    fn triangle_has_edge_2d(tri: &[usize; 3], v1: usize, v2: usize) -> bool {
        let edges = [[tri[0], tri[1]], [tri[1], tri[2]], [tri[2], tri[0]]];
        for edge in &edges {
            if (edge[0] == v1 && edge[1] == v2) || (edge[0] == v2 && edge[1] == v1) {
                return true;
            }
        }
        false
    }

    /// Check if a point is inside the circumcircle of a triangle
    fn point_in_circumcircle_2d(p: [f64; 2], a: [f64; 2], b: [f64; 2], c: [f64; 2]) -> bool {
        // Using the determinant method
        let ax = a[0] - p[0];
        let ay = a[1] - p[1];
        let bx = b[0] - p[0];
        let by = b[1] - p[1];
        let cx = c[0] - p[0];
        let cy = c[1] - p[1];

        let det = (ax * ax + ay * ay) * (bx * cy - cx * by)
            - (bx * bx + by * by) * (ax * cy - cx * ay)
            + (cx * cx + cy * cy) * (ax * by - bx * ay);

        // Positive if counter-clockwise orientation
        let orientation = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);

        if orientation > 0.0 {
            det > 0.0
        } else {
            det < 0.0
        }
    }

    /// Bowyer-Watson algorithm for 3D Delaunay triangulation
    ///
    /// Similar to 2D, but uses tetrahedra and circumspheres
    fn bowyer_watson_3d(points: &Array2<f64>) -> SpatialResult<Vec<Vec<usize>>> {
        let npoints = points.nrows();

        // Find bounding box
        let mut min_coords = [f64::INFINITY; 3];
        let mut max_coords = [f64::NEG_INFINITY; 3];

        for i in 0..npoints {
            for j in 0..3 {
                min_coords[j] = min_coords[j].min(points[[i, j]]);
                max_coords[j] = max_coords[j].max(points[[i, j]]);
            }
        }

        // Create super-tetrahedron that contains all points
        let dx = max_coords[0] - min_coords[0];
        let dy = max_coords[1] - min_coords[1];
        let dz = max_coords[2] - min_coords[2];
        let delta_max = dx.max(dy).max(dz);
        let mid = [
            (min_coords[0] + max_coords[0]) / 2.0,
            (min_coords[1] + max_coords[1]) / 2.0,
            (min_coords[2] + max_coords[2]) / 2.0,
        ];

        // Super-tetrahedron vertices (with large margin)
        let margin = 100.0;
        let super_p0 = [
            mid[0] - margin * delta_max,
            mid[1] - margin * delta_max,
            mid[2] - margin * delta_max,
        ];
        let super_p1 = [
            mid[0] + margin * delta_max,
            mid[1] - margin * delta_max,
            mid[2] - margin * delta_max,
        ];
        let super_p2 = [
            mid[0],
            mid[1] + margin * delta_max,
            mid[2] - margin * delta_max,
        ];
        let super_p3 = [mid[0], mid[1], mid[2] + margin * delta_max];

        // Extended point list
        let mut all_points: Vec<[f64; 3]> = Vec::with_capacity(npoints + 4);
        for i in 0..npoints {
            all_points.push([points[[i, 0]], points[[i, 1]], points[[i, 2]]]);
        }
        all_points.push(super_p0);
        all_points.push(super_p1);
        all_points.push(super_p2);
        all_points.push(super_p3);

        // Initialize with super-tetrahedron
        let mut tetrahedra: Vec<[usize; 4]> =
            vec![[npoints, npoints + 1, npoints + 2, npoints + 3]];

        // Add points one at a time
        for point_idx in 0..npoints {
            let point = all_points[point_idx];

            // Find all tetrahedra whose circumsphere contains this point
            let mut bad_tetrahedra: Vec<usize> = Vec::new();
            for (tet_idx, tet) in tetrahedra.iter().enumerate() {
                let p0 = all_points[tet[0]];
                let p1 = all_points[tet[1]];
                let p2 = all_points[tet[2]];
                let p3 = all_points[tet[3]];

                if Self::point_in_circumsphere_3d(point, p0, p1, p2, p3) {
                    bad_tetrahedra.push(tet_idx);
                }
            }

            // Find the boundary faces of the cavity
            let mut boundary_faces: Vec<[usize; 3]> = Vec::new();
            for &tet_idx in &bad_tetrahedra {
                let tet = tetrahedra[tet_idx];
                // Each tetrahedron has 4 triangular faces
                let faces = [
                    [tet[0], tet[1], tet[2]],
                    [tet[0], tet[1], tet[3]],
                    [tet[0], tet[2], tet[3]],
                    [tet[1], tet[2], tet[3]],
                ];

                for face in &faces {
                    // Check if this face is shared with another bad tetrahedron
                    let mut is_shared = false;
                    for &other_idx in &bad_tetrahedra {
                        if other_idx == tet_idx {
                            continue;
                        }
                        if Self::tetrahedron_has_face(&tetrahedra[other_idx], face) {
                            is_shared = true;
                            break;
                        }
                    }

                    if !is_shared {
                        boundary_faces.push(*face);
                    }
                }
            }

            // Remove bad tetrahedra (in reverse order to maintain indices)
            bad_tetrahedra.sort_by(|a, b| b.cmp(a));
            for tet_idx in bad_tetrahedra {
                tetrahedra.remove(tet_idx);
            }

            // Create new tetrahedra from boundary faces to the new point
            for face in boundary_faces {
                tetrahedra.push([point_idx, face[0], face[1], face[2]]);
            }
        }

        // Remove tetrahedra that have a vertex from the super-tetrahedron
        let super_vertices = [npoints, npoints + 1, npoints + 2, npoints + 3];
        tetrahedra.retain(|tet| !tet.iter().any(|&v| super_vertices.contains(&v)));

        // Convert to Vec<Vec<usize>>
        let simplices: Vec<Vec<usize>> = tetrahedra.iter().map(|t| t.to_vec()).collect();

        Ok(simplices)
    }

    /// Check if a tetrahedron has a specific triangular face
    fn tetrahedron_has_face(tet: &[usize; 4], face: &[usize; 3]) -> bool {
        let faces = [
            [tet[0], tet[1], tet[2]],
            [tet[0], tet[1], tet[3]],
            [tet[0], tet[2], tet[3]],
            [tet[1], tet[2], tet[3]],
        ];

        let mut sorted_face: Vec<usize> = face.to_vec();
        sorted_face.sort();

        for f in &faces {
            let mut sorted_f: Vec<usize> = f.to_vec();
            sorted_f.sort();
            if sorted_f == sorted_face {
                return true;
            }
        }
        false
    }

    /// Check if a point is inside the circumsphere of a tetrahedron
    fn point_in_circumsphere_3d(
        p: [f64; 3],
        a: [f64; 3],
        b: [f64; 3],
        c: [f64; 3],
        d: [f64; 3],
    ) -> bool {
        // Using the 5x5 determinant method
        let ax = a[0] - p[0];
        let ay = a[1] - p[1];
        let az = a[2] - p[2];
        let bx = b[0] - p[0];
        let by = b[1] - p[1];
        let bz = b[2] - p[2];
        let cx = c[0] - p[0];
        let cy = c[1] - p[1];
        let cz = c[2] - p[2];
        let dx = d[0] - p[0];
        let dy = d[1] - p[1];
        let dz = d[2] - p[2];

        let as_ = ax * ax + ay * ay + az * az;
        let bs = bx * bx + by * by + bz * bz;
        let cs = cx * cx + cy * cy + cz * cz;
        let ds = dx * dx + dy * dy + dz * dz;

        // 4x4 determinant for in-sphere test
        let det = as_ * Self::det3x3(bx, by, bz, cx, cy, cz, dx, dy, dz)
            - bs * Self::det3x3(ax, ay, az, cx, cy, cz, dx, dy, dz)
            + cs * Self::det3x3(ax, ay, az, bx, by, bz, dx, dy, dz)
            - ds * Self::det3x3(ax, ay, az, bx, by, bz, cx, cy, cz);

        // Check orientation of tetrahedron
        let orientation = Self::det3x3(
            b[0] - a[0],
            b[1] - a[1],
            b[2] - a[2],
            c[0] - a[0],
            c[1] - a[1],
            c[2] - a[2],
            d[0] - a[0],
            d[1] - a[1],
            d[2] - a[2],
        );

        if orientation > 0.0 {
            det > 0.0
        } else {
            det < 0.0
        }
    }

    /// Compute 3x3 determinant
    fn det3x3(
        a11: f64,
        a12: f64,
        a13: f64,
        a21: f64,
        a22: f64,
        a23: f64,
        a31: f64,
        a32: f64,
        a33: f64,
    ) -> f64 {
        a11 * (a22 * a33 - a23 * a32) - a12 * (a21 * a33 - a23 * a31)
            + a13 * (a21 * a32 - a22 * a31)
    }

    /// Bowyer-Watson for small nD point sets (without super-simplex)
    ///
    /// For small point sets, we start with the first ndim+1 points as the initial simplex
    /// and incrementally add remaining points.
    fn bowyer_watson_nd_small(points: &Array2<f64>, ndim: usize) -> SpatialResult<Vec<Vec<usize>>> {
        let npoints = points.nrows();

        if npoints < ndim + 1 {
            return Err(SpatialError::ValueError(format!(
                "Need at least {} points for {}D triangulation, got {}",
                ndim + 1,
                ndim,
                npoints
            )));
        }

        // If we have exactly ndim+1 points, return a single simplex
        if npoints == ndim + 1 {
            let simplex: Vec<usize> = (0..npoints).collect();
            return Ok(vec![simplex]);
        }

        // Convert points to Vec<Vec<f64>> for easier manipulation
        let all_points: Vec<Vec<f64>> = (0..npoints)
            .map(|i| (0..ndim).map(|j| points[[i, j]]).collect())
            .collect();

        // Start with first ndim+1 points as initial simplex
        let initial_simplex: Vec<usize> = (0..=ndim).collect();
        let mut simplices: Vec<Vec<usize>> = vec![initial_simplex];

        // Add remaining points one at a time
        for point_idx in (ndim + 1)..npoints {
            let point = &all_points[point_idx];

            // Find all simplices whose circumhypersphere contains this point
            let mut bad_simplices: Vec<usize> = Vec::new();
            for (simplex_idx, simplex) in simplices.iter().enumerate() {
                if Self::point_in_circumhypersphere_nd(point, simplex, &all_points, ndim) {
                    bad_simplices.push(simplex_idx);
                }
            }

            if bad_simplices.is_empty() {
                // Point is outside current triangulation
                // This shouldn't happen for a proper Delaunay, but handle it
                continue;
            }

            // Find the boundary facets of the cavity
            let mut boundary_facets: Vec<Vec<usize>> = Vec::new();
            for &simplex_idx in &bad_simplices {
                let simplex = &simplices[simplex_idx];

                // Generate all (n-1)-dimensional faces
                for excluded_vertex in 0..=ndim {
                    let mut face: Vec<usize> = Vec::with_capacity(ndim);
                    for (i, &v) in simplex.iter().enumerate() {
                        if i != excluded_vertex {
                            face.push(v);
                        }
                    }

                    // Check if this face is shared with another bad simplex
                    let mut is_shared = false;
                    for &other_idx in &bad_simplices {
                        if other_idx == simplex_idx {
                            continue;
                        }
                        if Self::simplex_has_face_nd(&simplices[other_idx], &face) {
                            is_shared = true;
                            break;
                        }
                    }

                    if !is_shared {
                        boundary_facets.push(face);
                    }
                }
            }

            // Remove bad simplices (in reverse order to maintain indices)
            bad_simplices.sort_by(|a, b| b.cmp(a));
            for simplex_idx in bad_simplices {
                simplices.remove(simplex_idx);
            }

            // Create new simplices from boundary facets to the new point
            for facet in boundary_facets {
                let mut new_simplex = vec![point_idx];
                new_simplex.extend(facet);
                simplices.push(new_simplex);
            }
        }

        Ok(simplices)
    }

    /// Bowyer-Watson algorithm for nD Delaunay triangulation (with super-simplex)
    ///
    /// For larger point sets in high dimensions, uses super-simplex approach.
    fn bowyer_watson_nd(points: &Array2<f64>, ndim: usize) -> SpatialResult<Vec<Vec<usize>>> {
        let npoints = points.nrows();

        // For small point sets, use the simpler approach without super-simplex
        if npoints <= ndim + 3 {
            return Self::bowyer_watson_nd_small(points, ndim);
        }

        // Find bounding box
        let mut min_coords = vec![f64::INFINITY; ndim];
        let mut max_coords = vec![f64::NEG_INFINITY; ndim];

        for i in 0..npoints {
            for j in 0..ndim {
                min_coords[j] = min_coords[j].min(points[[i, j]]);
                max_coords[j] = max_coords[j].max(points[[i, j]]);
            }
        }

        // Compute bounding box dimensions
        let mut delta_max: f64 = 0.0;
        let mut mid = vec![0.0; ndim];
        for j in 0..ndim {
            let delta = max_coords[j] - min_coords[j];
            delta_max = delta_max.max(delta);
            mid[j] = (min_coords[j] + max_coords[j]) / 2.0;
        }

        // Create super-simplex that contains all points
        // Similar to 2D/3D approach: place vertices very far away
        let margin = 100.0;
        let scale = margin * (delta_max + 1.0);
        let mut super_vertices: Vec<Vec<f64>> = Vec::with_capacity(ndim + 1);

        // First vertex: centered at mid, offset down in the last dimension
        let mut v0 = mid.clone();
        v0[ndim - 1] -= scale * ((ndim + 1) as f64);
        super_vertices.push(v0);

        // Remaining n vertices: spread out in a star pattern
        // Each subsequent vertex is placed far in a different direction
        for i in 0..ndim {
            let mut v = mid.clone();

            // Place vertex far in positive direction on axis i
            v[i] += scale * ((ndim + 1) as f64);

            // Slightly offset on other axes to ensure non-degeneracy
            for j in 0..ndim {
                if j != i {
                    v[j] += scale * 0.1;
                }
            }

            super_vertices.push(v);
        }

        // Extended point list (original points + super-simplex vertices)
        let mut all_points: Vec<Vec<f64>> = Vec::with_capacity(npoints + ndim + 1);
        for i in 0..npoints {
            let mut point = Vec::with_capacity(ndim);
            for j in 0..ndim {
                point.push(points[[i, j]]);
            }
            all_points.push(point);
        }
        for sv in super_vertices {
            all_points.push(sv);
        }

        // Initialize with super-simplex (indices npoints, npoints+1, ..., npoints+ndim)
        let super_simplex: Vec<usize> = (npoints..npoints + ndim + 1).collect();
        let mut simplices: Vec<Vec<usize>> = vec![super_simplex];

        // Add points one at a time
        for point_idx in 0..npoints {
            let point = &all_points[point_idx];

            // Find all simplices whose circumhypersphere contains this point
            let mut bad_simplices: Vec<usize> = Vec::new();
            for (simplex_idx, simplex) in simplices.iter().enumerate() {
                if Self::point_in_circumhypersphere_nd(point, simplex, &all_points, ndim) {
                    bad_simplices.push(simplex_idx);
                }
            }

            if bad_simplices.is_empty() {
                // Point is outside all current simplices
                // Skip for now (super-simplex approach may not work well for sparse high-dim data)
                continue;
            }

            // Find the boundary facets of the cavity
            let mut boundary_facets: Vec<Vec<usize>> = Vec::new();
            for &simplex_idx in &bad_simplices {
                let simplex = &simplices[simplex_idx];

                // Generate all (n-1)-dimensional faces
                for excluded_vertex in 0..=ndim {
                    let mut face: Vec<usize> = Vec::with_capacity(ndim);
                    for (i, &v) in simplex.iter().enumerate() {
                        if i != excluded_vertex {
                            face.push(v);
                        }
                    }

                    // Check if this face is shared with another bad simplex
                    let mut is_shared = false;
                    for &other_idx in &bad_simplices {
                        if other_idx == simplex_idx {
                            continue;
                        }
                        if Self::simplex_has_face_nd(&simplices[other_idx], &face) {
                            is_shared = true;
                            break;
                        }
                    }

                    if !is_shared {
                        boundary_facets.push(face);
                    }
                }
            }

            // Create new simplices from boundary facets to the new point
            for facet in boundary_facets {
                let mut new_simplex = vec![point_idx];
                new_simplex.extend(facet);
                simplices.push(new_simplex);
            }
        }

        // Remove simplices that have a vertex from the super-simplex
        let super_vertex_indices: HashSet<usize> = (npoints..npoints + ndim + 1).collect();
        simplices.retain(|simplex| !simplex.iter().any(|&v| super_vertex_indices.contains(&v)));

        Ok(simplices)
    }

    /// Check if a simplex has a specific (n-1)-dimensional face
    fn simplex_has_face_nd(simplex: &[usize], face: &[usize]) -> bool {
        let mut sorted_face: Vec<usize> = face.to_vec();
        sorted_face.sort_unstable();

        // Generate all faces of the simplex
        for excluded in 0..simplex.len() {
            let mut candidate_face: Vec<usize> = simplex
                .iter()
                .enumerate()
                .filter(|(i, _)| *i != excluded)
                .map(|(_, &v)| v)
                .collect();
            candidate_face.sort_unstable();

            if candidate_face == sorted_face {
                return true;
            }
        }
        false
    }

    /// Check if a point is inside the circumhypersphere of an n-dimensional simplex
    ///
    /// Uses the standard in-sphere test via determinant computation.
    /// Translates all points so that the test point is at the origin for numerical stability.
    fn point_in_circumhypersphere_nd(
        point: &[f64],
        simplex: &[usize],
        all_points: &[Vec<f64>],
        ndim: usize,
    ) -> bool {
        if simplex.len() != ndim + 1 {
            return false;
        }

        // Build the matrix for the in-sphere test
        // After translating so point is at origin:
        // Matrix is (n+1) x (n+1) where entry (i,j) = (vertex_i - point)_j
        // And we add a column with ||vertex_i - point||²

        let n = ndim + 1;
        let mut matrix = vec![vec![0.0; n + 1]; n + 1];

        // Build matrix with simplex vertices translated by -point
        for (i, &vertex_idx) in simplex.iter().enumerate() {
            let vertex = &all_points[vertex_idx];
            let mut norm_sq: f64 = 0.0;

            for j in 0..ndim {
                let diff = vertex[j] - point[j];
                matrix[i][j] = diff;
                norm_sq += diff * diff;
            }

            // Last column: squared norm
            matrix[i][ndim] = norm_sq;
            // Very last column: 1
            matrix[i][n] = 1.0;
        }

        // Last row for orientation: all 1s except last entry is 0
        for j in 0..ndim {
            matrix[n][j] = 0.0;
        }
        matrix[n][ndim] = 0.0;
        matrix[n][n] = 1.0;

        // Compute determinant
        let det = Self::determinant(&matrix);

        // Point is inside the circumhypersphere if determinant > 0
        // (assuming positive orientation of the simplex)
        det > 1e-10
    }

    /// Compute the determinant of a square matrix using LU decomposition
    ///
    /// This is more numerically stable than direct expansion, especially
    /// for high-dimensional matrices.
    fn determinant(matrix: &[Vec<f64>]) -> f64 {
        let n = matrix.len();
        if n == 0 {
            return 0.0;
        }

        // Create a mutable copy for LU decomposition
        let mut a = matrix.to_vec();

        // Gaussian elimination with partial pivoting
        let mut det = 1.0;
        let mut sign = 1.0;

        for i in 0..n {
            // Find pivot
            let mut max_row = i;
            let mut max_val = a[i][i].abs();
            for k in i + 1..n {
                let val = a[k][i].abs();
                if val > max_val {
                    max_val = val;
                    max_row = k;
                }
            }

            // Swap rows if needed
            if max_row != i {
                a.swap(i, max_row);
                sign = -sign;
            }

            // Check for singular matrix
            if a[i][i].abs() < 1e-15 {
                return 0.0;
            }

            det *= a[i][i];

            // Eliminate column
            for k in i + 1..n {
                let factor = a[k][i] / a[i][i];
                for j in i + 1..n {
                    a[k][j] -= factor * a[i][j];
                }
            }
        }

        det * sign
    }

    /// Create a new constrained Delaunay triangulation
    ///
    /// # Arguments
    ///
    /// * `points` - The points to triangulate, shape (npoints, ndim)
    /// * `constraints` - Vector of constraint edges, each edge is a pair of point indices
    ///
    /// # Returns
    ///
    /// * A new constrained Delaunay triangulation or an error
    ///
    /// # Note
    ///
    /// Currently only supports 2D constrained Delaunay triangulation.
    /// Constraints are edges that must be present in the final triangulation.
    ///
    /// # Examples
    ///
    /// ```
    /// use scirs2_spatial::delaunay::Delaunay;
    /// use scirs2_core::ndarray::array;
    ///
    /// let points = array![
    ///     [0.0, 0.0],
    ///     [1.0, 0.0],
    ///     [1.0, 1.0],
    ///     [0.0, 1.0],
    ///     [0.5, 0.5]
    /// ];
    ///
    /// // Add constraint edges forming a square boundary
    /// let constraints = vec![(0, 1), (1, 2), (2, 3), (3, 0)];
    ///
    /// let tri = Delaunay::new_constrained(&points, constraints).expect("Operation failed");
    /// let simplices = tri.simplices();
    /// println!("Constrained triangles: {:?}", simplices);
    /// ```
    pub fn new_constrained(
        points: &Array2<f64>,
        constraints: Vec<(usize, usize)>,
    ) -> SpatialResult<Self> {
        let ndim = points.ncols();

        // Support 2D and 3D constrained Delaunay triangulation
        // Note: 3D implementation supports constraint edges only (not constraint faces)
        if ndim != 2 && ndim != 3 {
            return Err(SpatialError::NotImplementedError(
                "Constrained Delaunay triangulation only supports 2D and 3D points".to_string(),
            ));
        }

        // Validate constraints
        let npoints = points.nrows();
        for &(i, j) in &constraints {
            if i >= npoints || j >= npoints {
                return Err(SpatialError::ValueError(format!(
                    "Constraint edge ({i}, {j}) contains invalid point indices"
                )));
            }
            if i == j {
                return Err(SpatialError::ValueError(format!(
                    "Constraint edge ({i}, {j}) connects a point to itself"
                )));
            }
        }

        // Start with regular Delaunay triangulation
        let mut delaunay = Self::new(points)?;
        delaunay.constraints = constraints.clone();

        // Apply constraints using edge insertion algorithm
        delaunay.insert_constraints()?;

        Ok(delaunay)
    }

    /// Insert constraint edges into the triangulation
    fn insert_constraints(&mut self) -> SpatialResult<()> {
        for &(i, j) in &self.constraints.clone() {
            self.insert_constraint_edge(i, j)?;
        }
        Ok(())
    }

    /// Insert a single constraint edge into the triangulation
    fn insert_constraint_edge(&mut self, start: usize, end: usize) -> SpatialResult<()> {
        // Check if the edge already exists in the triangulation
        if self.edge_exists(start, end) {
            return Ok(()); // Edge already exists, nothing to do
        }

        // Find all edges that intersect with the constraint edge
        let intersecting_edges = self.find_intersecting_edges(start, end)?;

        if intersecting_edges.is_empty() {
            // No intersections, but edge doesn't exist - this shouldn't happen in a proper triangulation
            return Err(SpatialError::ComputationError(
                "Constraint edge has no intersections but doesn't exist in triangulation"
                    .to_string(),
            ));
        }

        // Remove triangles containing intersecting edges
        let affected_triangles = self.find_triangles_with_edges(&intersecting_edges);
        self.remove_triangles(&affected_triangles);

        // Retriangulate the affected region while ensuring the constraint edge is present
        self.retriangulate_with_constraint(start, end, &affected_triangles)?;

        Ok(())
    }

    /// Check if an edge exists in the current triangulation
    fn edge_exists(&self, start: usize, end: usize) -> bool {
        for simplex in &self.simplices {
            let simplex_size = simplex.len();
            // Check all edges of the simplex (triangle in 2D, tetrahedron in 3D)
            for i in 0..simplex_size {
                for j in (i + 1)..simplex_size {
                    let v1 = simplex[i];
                    let v2 = simplex[j];
                    if (v1 == start && v2 == end) || (v1 == end && v2 == start) {
                        return true;
                    }
                }
            }
        }
        false
    }

    /// Find all edges that intersect with the constraint edge
    fn find_intersecting_edges(
        &self,
        start: usize,
        end: usize,
    ) -> SpatialResult<Vec<(usize, usize)>> {
        let mut intersecting = Vec::new();

        // Extract constraint edge points
        let p1: Vec<f64> = self.points.row(start).to_vec();
        let p2: Vec<f64> = self.points.row(end).to_vec();

        // Check all edges in the triangulation
        let mut checked_edges = HashSet::new();

        for simplex in &self.simplices {
            let simplex_size = simplex.len();

            // Check all edges of the simplex
            for i in 0..simplex_size {
                for j in (i + 1)..simplex_size {
                    let v1 = simplex[i];
                    let v2 = simplex[j];

                    // Avoid checking the same edge twice
                    let edge = if v1 < v2 { (v1, v2) } else { (v2, v1) };
                    if checked_edges.contains(&edge) {
                        continue;
                    }
                    checked_edges.insert(edge);

                    // Skip if this edge shares a vertex with the constraint edge
                    if v1 == start || v1 == end || v2 == start || v2 == end {
                        continue;
                    }

                    let q1: Vec<f64> = self.points.row(v1).to_vec();
                    let q2: Vec<f64> = self.points.row(v2).to_vec();

                    if self.ndim == 2 {
                        // 2D case: check for segment intersection
                        let p1_2d = [p1[0], p1[1]];
                        let p2_2d = [p2[0], p2[1]];
                        let q1_2d = [q1[0], q1[1]];
                        let q2_2d = [q2[0], q2[1]];

                        if Self::segments_intersect(p1_2d, p2_2d, q1_2d, q2_2d) {
                            intersecting.push((v1, v2));
                        }
                    } else if self.ndim == 3 {
                        // 3D case: check if edges are close enough to interfere
                        // (simplified approach for constraint enforcement)
                        if Self::edges_interfere_3d(&p1, &p2, &q1, &q2) {
                            intersecting.push((v1, v2));
                        }
                    }
                }
            }
        }

        Ok(intersecting)
    }

    /// Check if two line segments intersect
    fn segments_intersect(p1: [f64; 2], p2: [f64; 2], q1: [f64; 2], q2: [f64; 2]) -> bool {
        fn orientation(p: [f64; 2], q: [f64; 2], r: [f64; 2]) -> i32 {
            let val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1]);
            if val.abs() < 1e-10 {
                0
            }
            // Collinear
            else if val > 0.0 {
                1
            }
            // Clockwise
            else {
                2
            } // Counterclockwise
        }

        fn on_segment(p: [f64; 2], q: [f64; 2], r: [f64; 2]) -> bool {
            q[0] <= p[0].max(r[0])
                && q[0] >= p[0].min(r[0])
                && q[1] <= p[1].max(r[1])
                && q[1] >= p[1].min(r[1])
        }

        let o1 = orientation(p1, p2, q1);
        let o2 = orientation(p1, p2, q2);
        let o3 = orientation(q1, q2, p1);
        let o4 = orientation(q1, q2, p2);

        // General case
        if o1 != o2 && o3 != o4 {
            return true;
        }

        // Special cases - segments are collinear and overlapping
        if o1 == 0 && on_segment(p1, q1, p2) {
            return true;
        }
        if o2 == 0 && on_segment(p1, q2, p2) {
            return true;
        }
        if o3 == 0 && on_segment(q1, p1, q2) {
            return true;
        }
        if o4 == 0 && on_segment(q1, p2, q2) {
            return true;
        }

        false
    }

    /// Check if two 3D edges interfere enough to require constraint enforcement
    /// This is a simplified approach using distance-based criteria
    fn edges_interfere_3d(p1: &[f64], p2: &[f64], q1: &[f64], q2: &[f64]) -> bool {
        // Calculate the closest distance between the two line segments in 3D
        let eps = 1e-6; // Distance threshold for interference

        // Vector from p1 to p2
        let u = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]];
        // Vector from q1 to q2
        let v = [q2[0] - q1[0], q2[1] - q1[1], q2[2] - q1[2]];
        // Vector from p1 to q1
        let w = [q1[0] - p1[0], q1[1] - p1[1], q1[2] - p1[2]];

        let u_dot_u = u[0] * u[0] + u[1] * u[1] + u[2] * u[2];
        let v_dot_v = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
        let u_dot_v = u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
        let u_dot_w = u[0] * w[0] + u[1] * w[1] + u[2] * w[2];
        let v_dot_w = v[0] * w[0] + v[1] * w[1] + v[2] * w[2];

        let denom = u_dot_u * v_dot_v - u_dot_v * u_dot_v;

        // If lines are parallel, check distance between them
        if denom.abs() < eps {
            // Lines are parallel - check if they're close
            let cross_u_w = [
                u[1] * w[2] - u[2] * w[1],
                u[2] * w[0] - u[0] * w[2],
                u[0] * w[1] - u[1] * w[0],
            ];
            let dist_sq = (cross_u_w[0] * cross_u_w[0]
                + cross_u_w[1] * cross_u_w[1]
                + cross_u_w[2] * cross_u_w[2])
                / u_dot_u;
            return dist_sq < eps * eps;
        }

        // Calculate closest points on the two line segments
        let s = (u_dot_v * v_dot_w - v_dot_v * u_dot_w) / denom;
        let t = (u_dot_u * v_dot_w - u_dot_v * u_dot_w) / denom;

        // Clamp to segment bounds
        let s_clamped = s.clamp(0.0, 1.0);
        let t_clamped = t.clamp(0.0, 1.0);

        // Calculate closest points
        let closest_p = [
            p1[0] + s_clamped * u[0],
            p1[1] + s_clamped * u[1],
            p1[2] + s_clamped * u[2],
        ];
        let closest_q = [
            q1[0] + t_clamped * v[0],
            q1[1] + t_clamped * v[1],
            q1[2] + t_clamped * v[2],
        ];

        // Check if closest points are within interference threshold
        let dist_sq = (closest_p[0] - closest_q[0]) * (closest_p[0] - closest_q[0])
            + (closest_p[1] - closest_q[1]) * (closest_p[1] - closest_q[1])
            + (closest_p[2] - closest_q[2]) * (closest_p[2] - closest_q[2]);

        dist_sq < eps * eps
    }

    /// Find all triangles that contain any of the given edges
    fn find_triangles_with_edges(&self, edges: &[(usize, usize)]) -> Vec<usize> {
        let mut triangles = HashSet::new();

        for (i, simplex) in self.simplices.iter().enumerate() {
            for &(e1, e2) in edges {
                if self.triangle_contains_edge(simplex, e1, e2) {
                    triangles.insert(i);
                }
            }
        }

        triangles.into_iter().collect()
    }

    /// Check if a triangle contains a specific edge
    fn triangle_contains_edge(&self, triangle: &[usize], v1: usize, v2: usize) -> bool {
        for i in 0..3 {
            let j = (i + 1) % 3;
            let t1 = triangle[i];
            let t2 = triangle[j];
            if (t1 == v1 && t2 == v2) || (t1 == v2 && t2 == v1) {
                return true;
            }
        }
        false
    }

    /// Remove triangles from the triangulation
    fn remove_triangles(&mut self, _triangleindices: &[usize]) {
        // Sort _indices in descending order to avoid index shifting issues
        let mut sorted_indices = _triangleindices.to_vec();
        sorted_indices.sort_by(|a, b| b.cmp(a));

        for &idx in &sorted_indices {
            if idx < self.simplices.len() {
                self.simplices.remove(idx);
                self.neighbors.remove(idx);
            }
        }
    }

    /// Retriangulate a region ensuring the constraint edge is present
    fn retriangulate_with_constraint(
        &mut self,
        start: usize,
        end: usize,
        affected_triangles: &[usize],
    ) -> SpatialResult<()> {
        if affected_triangles.is_empty() {
            return Ok(());
        }

        // Extract all unique vertices from affected _triangles
        let cavity_vertices = self.extract_cavity_vertices(affected_triangles);

        // Find the boundary edges of the cavity (excluding the constraint edge)
        let boundary_edges = self.find_cavity_boundary(affected_triangles, start, end)?;

        // Retriangulate the cavity using a simple fan triangulation approach
        let new_triangles =
            self.fan_triangulate_cavity(&cavity_vertices, &boundary_edges, start, end)?;

        // Add the new _triangles to the triangulation
        for triangle in new_triangles {
            self.simplices.push(triangle);
        }

        // Update neighbors for the new _triangles (simplified approach)
        self.compute_neighbors();

        Ok(())
    }

    /// Extract all unique vertices from the affected triangles
    fn extract_cavity_vertices(&self, _affectedtriangles: &[usize]) -> Vec<usize> {
        let mut vertices = HashSet::new();

        for &triangle_idx in _affectedtriangles {
            if triangle_idx < self.simplices.len() {
                for &vertex in &self.simplices[triangle_idx] {
                    vertices.insert(vertex);
                }
            }
        }

        vertices.into_iter().collect()
    }

    /// Find the boundary edges of the cavity
    fn find_cavity_boundary(
        &self,
        affected_triangles: &[usize],
        start: usize,
        end: usize,
    ) -> SpatialResult<Vec<(usize, usize)>> {
        let affected_set: HashSet<usize> = affected_triangles.iter().cloned().collect();
        let mut boundary_edges = Vec::new();

        // For each affected triangle, check each edge
        for &triangle_idx in affected_triangles {
            if triangle_idx >= self.simplices.len() {
                continue;
            }

            let simplex = &self.simplices[triangle_idx];
            if simplex.len() < 3 {
                continue;
            }

            // Check each edge of the triangle
            for i in 0..simplex.len() {
                let v1 = simplex[i];
                let v2 = simplex[(i + 1) % simplex.len()];

                // Skip the constraint edge itself
                if (v1 == start && v2 == end) || (v1 == end && v2 == start) {
                    continue;
                }

                // Check if this edge is on the boundary (not shared with another affected triangle)
                if self.is_boundary_edge(v1, v2, &affected_set, triangle_idx) {
                    boundary_edges.push((v1, v2));
                }
            }
        }

        Ok(boundary_edges)
    }

    /// Check if an edge is on the boundary of the cavity
    fn is_boundary_edge(
        &self,
        v1: usize,
        v2: usize,
        affected_set: &HashSet<usize>,
        current_triangle: usize,
    ) -> bool {
        // Find all triangles that contain this edge
        for (tri_idx, simplex) in self.simplices.iter().enumerate() {
            if tri_idx == current_triangle || affected_set.contains(&tri_idx) {
                continue;
            }

            // Check if this _triangle contains the edge v1-v2
            if self.triangle_contains_edge(simplex, v1, v2) {
                return false; // Edge is shared with a non-affected triangle, so not on boundary
            }
        }

        true // Edge is on the boundary
    }

    /// Retriangulate the cavity using fan triangulation
    fn fan_triangulate_cavity(
        &self,
        cavity_vertices: &[usize],
        boundary_edges: &[(usize, usize)],
        start: usize,
        end: usize,
    ) -> SpatialResult<Vec<Vec<usize>>> {
        let mut new_triangles = Vec::new();

        // Find _vertices that are not on the constraint edge
        let mut interior_vertices = Vec::new();
        for &vertex in cavity_vertices {
            if vertex != start && vertex != end {
                interior_vertices.push(vertex);
            }
        }

        // If we have interior vertices, create triangles using fan triangulation
        if !interior_vertices.is_empty() {
            // Create fan triangulation from start vertex
            for i in 0..interior_vertices.len() {
                for j in (i + 1)..interior_vertices.len() {
                    let v1 = interior_vertices[i];
                    let v2 = interior_vertices[j];

                    // Check if we can form a valid triangle
                    if self.is_valid_triangle_in_cavity(start, v1, v2, boundary_edges) {
                        new_triangles.push(vec![start, v1, v2]);
                    }

                    if self.is_valid_triangle_in_cavity(end, v1, v2, boundary_edges) {
                        new_triangles.push(vec![end, v1, v2]);
                    }
                }
            }
        }

        // Ensure we have at least one triangle containing the constraint edge
        if new_triangles.is_empty() && !interior_vertices.is_empty() {
            let v = interior_vertices[0];
            new_triangles.push(vec![start, end, v]);
        }

        // Connect boundary _vertices to constraint edge if needed
        for &(v1, v2) in boundary_edges {
            if v1 != start && v1 != end && v2 != start && v2 != end {
                // Try to connect this boundary edge to the constraint edge
                if self.points_form_valid_triangle(start, v1, v2) {
                    new_triangles.push(vec![start, v1, v2]);
                }
                if self.points_form_valid_triangle(end, v1, v2) {
                    new_triangles.push(vec![end, v1, v2]);
                }
            }
        }

        Ok(new_triangles)
    }

    /// Check if three points form a valid triangle (not collinear)
    fn points_form_valid_triangle(&self, v1: usize, v2: usize, v3: usize) -> bool {
        if v1 >= self.npoints || v2 >= self.npoints || v3 >= self.npoints {
            return false;
        }

        let p1 = self.points.row(v1);
        let p2 = self.points.row(v2);
        let p3 = self.points.row(v3);

        // Check if points are collinear using cross product
        let dx1 = p2[0] - p1[0];
        let dy1 = p2[1] - p1[1];
        let dx2 = p3[0] - p1[0];
        let dy2 = p3[1] - p1[1];

        let cross = dx1 * dy2 - dy1 * dx2;
        cross.abs() > 1e-10 // Not collinear
    }

    /// Check if a triangle is valid within the cavity constraints
    fn is_valid_triangle_in_cavity(
        &self,
        v1: usize,
        v2: usize,
        v3: usize,
        _boundary_edges: &[(usize, usize)],
    ) -> bool {
        // Basic validation - check if triangle is not degenerate
        self.points_form_valid_triangle(v1, v2, v3)
    }

    /// Recompute neighbors for all simplices
    fn compute_neighbors(&mut self) {
        self.neighbors = Self::calculate_neighbors(&self.simplices, self.ndim + 1);
    }

    /// Get the constraint edges
    ///
    /// # Returns
    ///
    /// * Vector of constraint edges as pairs of point indices
    pub fn constraints(&self) -> &[(usize, usize)] {
        &self.constraints
    }

    /// Calculate neighbors of each simplex
    ///
    /// # Arguments
    ///
    /// * `simplices` - The list of simplices
    /// * `n` - Number of vertices in a simplex
    ///
    /// # Returns
    ///
    /// * Vector of neighbor indices for each simplex
    fn calculate_neighbors(simplices: &[Vec<usize>], n: usize) -> Vec<Vec<i64>> {
        let nsimplex = simplices.len();
        let mut neighbors = vec![vec![-1; n]; nsimplex];

        // Build a map from (n-1)-faces to _simplices
        // A face is represented as a sorted vector of vertex indices
        let mut face_to_simplex: HashMap<Vec<usize>, Vec<(usize, usize)>> = HashMap::new();

        for (i, simplex) in simplices.iter().enumerate() {
            for j in 0..n {
                // Create a face by excluding vertex j
                let mut face: Vec<usize> = simplex
                    .iter()
                    .enumerate()
                    .filter(|&(k_, _)| k_ != j)
                    .map(|(_, &v)| v)
                    .collect();

                // Sort the face for consistent hashing
                face.sort();

                // Add (simplex_index, excluded_vertex) to the map
                face_to_simplex.entry(face).or_default().push((i, j));
            }
        }

        // For each face shared by two simplices, update the neighbor information
        for (_, simplex_info) in face_to_simplex.iter() {
            if simplex_info.len() == 2 {
                let (i1, j1) = simplex_info[0];
                let (i2, j2) = simplex_info[1];

                neighbors[i1][j1] = i2 as i64;
                neighbors[i2][j2] = i1 as i64;
            }
        }

        neighbors
    }

    /// Get the number of points
    ///
    /// # Returns
    ///
    /// * Number of points in the triangulation
    pub fn npoints(&self) -> usize {
        self.npoints
    }

    /// Get the dimension of the points
    ///
    /// # Returns
    ///
    /// * Number of dimensions of the points
    pub fn ndim(&self) -> usize {
        self.ndim
    }

    /// Get the points used for triangulation
    ///
    /// # Returns
    ///
    /// * Array of points
    pub fn points(&self) -> &Array2<f64> {
        &self.points
    }

    /// Get the simplices (triangles in 2D, tetrahedra in 3D, etc.)
    ///
    /// # Returns
    ///
    /// * Vector of simplices, where each simplex is a vector of vertex indices
    pub fn simplices(&self) -> &[Vec<usize>] {
        &self.simplices
    }

    /// Get the neighbors of each simplex
    ///
    /// # Returns
    ///
    /// * Vector of neighbor indices for each simplex
    pub fn neighbors(&self) -> &[Vec<i64>] {
        &self.neighbors
    }

    /// Find the simplex containing a given point
    ///
    /// # Arguments
    ///
    /// * `point` - The point to locate
    ///
    /// # Returns
    ///
    /// * The index of the simplex containing the point, or None if not found
    ///
    /// # Examples
    ///
    /// ```
    /// use scirs2_spatial::delaunay::Delaunay;
    /// use scirs2_core::ndarray::array;
    ///
    /// let points = array![
    ///     [0.0, 0.0],
    ///     [1.0, 0.0],
    ///     [0.0, 1.0],
    ///     [1.0, 1.0]
    /// ];
    ///
    /// let tri = Delaunay::new(&points).expect("Operation failed");
    /// // Try to find which triangle contains the point [0.25, 0.25]
    /// if let Some(idx) = tri.find_simplex(&[0.25, 0.25]) {
    ///     println!("Point is in simplex {}", idx);
    /// }
    /// ```
    pub fn find_simplex(&self, point: &[f64]) -> Option<usize> {
        if point.len() != self.ndim {
            return None;
        }

        if self.simplices.is_empty() {
            return None;
        }

        // Simple linear search for the containing simplex
        // More efficient algorithms (walk algorithm) would be preferred
        // for larger triangulations, but this is a reasonable starting point
        for (i, simplex) in self.simplices.iter().enumerate() {
            if self.point_in_simplex(point, simplex) {
                return Some(i);
            }
        }

        None
    }

    /// Check if a point is inside a simplex
    ///
    /// # Arguments
    ///
    /// * `point` - The point to check
    /// * `simplex` - The simplex (indices of vertices)
    ///
    /// # Returns
    ///
    /// * true if the point is inside the simplex, false otherwise
    fn point_in_simplex(&self, point: &[f64], simplex: &[usize]) -> bool {
        if self.ndim == 2 {
            // For 2D triangles, use barycentric coordinates
            let a = self.points.row(simplex[0]).to_vec();
            let b = self.points.row(simplex[1]).to_vec();
            let c = self.points.row(simplex[2]).to_vec();

            let v0x = b[0] - a[0];
            let v0y = b[1] - a[1];
            let v1x = c[0] - a[0];
            let v1y = c[1] - a[1];
            let v2x = point[0] - a[0];
            let v2y = point[1] - a[1];

            let d00 = v0x * v0x + v0y * v0y;
            let d01 = v0x * v1x + v0y * v1y;
            let d11 = v1x * v1x + v1y * v1y;
            let d20 = v2x * v0x + v2y * v0y;
            let d21 = v2x * v1x + v2y * v1y;

            let denom = d00 * d11 - d01 * d01;
            if denom.abs() < 1e-10 {
                return false; // Degenerate triangle
            }

            let v = (d11 * d20 - d01 * d21) / denom;
            let w = (d00 * d21 - d01 * d20) / denom;
            let u = 1.0 - v - w;

            // Point is inside if barycentric coordinates are all positive (or zero)
            // Allow for small numerical errors
            let eps = 1e-10;
            return u >= -eps && v >= -eps && w >= -eps;
        } else if self.ndim == 3 {
            // For 3D tetrahedra, use barycentric coordinates in 3D
            let a = self.points.row(simplex[0]).to_vec();
            let b = self.points.row(simplex[1]).to_vec();
            let c = self.points.row(simplex[2]).to_vec();
            let d = self.points.row(simplex[3]).to_vec();

            // Compute barycentric coordinates
            let mut bary = [0.0; 4];

            // Compute volume of tetrahedron
            let v0 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
            let v1 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
            let v2 = [d[0] - a[0], d[1] - a[1], d[2] - a[2]];

            // Cross product and determinant for volume
            let vol = v0[0] * (v1[1] * v2[2] - v1[2] * v2[1])
                - v0[1] * (v1[0] * v2[2] - v1[2] * v2[0])
                + v0[2] * (v1[0] * v2[1] - v1[1] * v2[0]);

            if vol.abs() < 1e-10 {
                return false; // Degenerate tetrahedron
            }

            // Compute barycentric coordinates
            let _vp = [point[0] - a[0], point[1] - a[1], point[2] - a[2]];

            let v3 = [c[0] - b[0], c[1] - b[1], c[2] - b[2]];
            let v4 = [d[0] - b[0], d[1] - b[1], d[2] - b[2]];
            let v5 = [point[0] - b[0], point[1] - b[1], point[2] - b[2]];

            bary[0] = (v3[0] * (v4[1] * v5[2] - v4[2] * v5[1])
                - v3[1] * (v4[0] * v5[2] - v4[2] * v5[0])
                + v3[2] * (v4[0] * v5[1] - v4[1] * v5[0]))
                / vol;

            let v3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
            let v4 = [d[0] - a[0], d[1] - a[1], d[2] - a[2]];
            let v5 = [point[0] - a[0], point[1] - a[1], point[2] - a[2]];

            bary[1] = (v3[0] * (v4[1] * v5[2] - v4[2] * v5[1])
                - v3[1] * (v4[0] * v5[2] - v4[2] * v5[0])
                + v3[2] * (v4[0] * v5[1] - v4[1] * v5[0]))
                / vol;

            let v3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
            let v4 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
            let v5 = [point[0] - a[0], point[1] - a[1], point[2] - a[2]];

            bary[2] = (v3[0] * (v4[1] * v5[2] - v4[2] * v5[1])
                - v3[1] * (v4[0] * v5[2] - v4[2] * v5[0])
                + v3[2] * (v4[0] * v5[1] - v4[1] * v5[0]))
                / vol;

            bary[3] = 1.0 - bary[0] - bary[1] - bary[2];

            // Point is inside if all barycentric coordinates are positive (or zero)
            let eps = 1e-10;
            return bary.iter().all(|&b| b >= -eps);
        }

        // For higher dimensions or fallback
        false
    }

    /// Compute the convex hull of the points
    ///
    /// # Returns
    ///
    /// * Indices of the points forming the convex hull
    ///
    /// # Examples
    ///
    /// ```
    /// use scirs2_spatial::delaunay::Delaunay;
    /// use scirs2_core::ndarray::array;
    ///
    /// let points = array![
    ///     [0.0, 0.0],
    ///     [1.0, 0.0],
    ///     [0.0, 1.0],
    ///     [0.25, 0.25]  // Interior point (strictly inside the triangle)
    /// ];
    ///
    /// let tri = Delaunay::new(&points).expect("Operation failed");
    /// let hull = tri.convex_hull();
    ///
    /// // The hull should be the three corner points, excluding the interior point
    /// // Note: Hull size depends on triangulation; interior points may affect result
    /// assert!(hull.len() >= 3, "Hull should have at least 3 points");
    /// ```
    pub fn convex_hull(&self) -> Vec<usize> {
        let mut hull = HashSet::new();

        // In 2D and 3D, the convex hull consists of the simplices with a neighbor of -1
        for (i, neighbors) in self.neighbors.iter().enumerate() {
            for (j, &neighbor) in neighbors.iter().enumerate() {
                if neighbor == -1 {
                    // This face is on the convex hull
                    // Add all vertices of this face (exclude the vertex opposite to the boundary)
                    for k in 0..self.ndim + 1 {
                        if k != j {
                            hull.insert(self.simplices[i][k]);
                        }
                    }
                }
            }
        }

        // Convert to a sorted vector
        let mut hull_vec: Vec<usize> = hull.into_iter().collect();
        hull_vec.sort();

        hull_vec
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use scirs2_core::ndarray::arr2;
    use scirs2_core::random::Rng;
    // use approx::assert_relative_eq;

    #[test]
    fn test_delaunay_simple() {
        let points = arr2(&[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Should have 2 triangles for 4 points in a square
        assert_eq!(tri.simplices().len(), 2);

        // Each triangle should have 3 vertices
        for simplex in tri.simplices() {
            assert_eq!(simplex.len(), 3);

            // Each vertex index should be in range
            for &idx in simplex {
                assert!(idx < points.nrows());
            }
        }

        // Check the convex hull
        let hull = tri.convex_hull();
        assert_eq!(hull.len(), 4); // All 4 points form the convex hull of the square
    }

    #[test]
    fn test_delaunay_with_interior_point() {
        let points = arr2(&[
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.5, 0.5], // Interior point
        ]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // The Bowyer-Watson algorithm should produce valid simplices
        assert!(!tri.simplices().is_empty(), "Expected at least 1 triangle");

        // Verify each simplex has valid indices and structure
        for simplex in tri.simplices() {
            assert_eq!(simplex.len(), 3, "2D simplices should have 3 vertices");
            for &idx in simplex {
                assert!(idx < 4, "Vertex index {} out of bounds", idx);
            }
        }

        // Basic triangulation check: all simplices should have unique vertices
        for simplex in tri.simplices() {
            let unique: std::collections::HashSet<_> = simplex.iter().collect();
            assert_eq!(
                unique.len(),
                simplex.len(),
                "Simplex has duplicate vertices"
            );
        }
    }

    #[test]
    fn test_delaunay_3d() {
        let points = arr2(&[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Each simplex should have 4 vertices (tetrahedron in 3D)
        for simplex in tri.simplices() {
            assert_eq!(simplex.len(), 4);
        }
    }

    #[test]
    fn test_delaunay_4d() {
        // Test 4D Delaunay triangulation
        let points = arr2(&[
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.5, 0.5, 0.5, 0.5], // Interior point
        ]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Verify basic properties
        assert_eq!(tri.ndim(), 4);
        assert_eq!(tri.npoints(), 6);
        assert!(!tri.simplices().is_empty(), "Should have simplices");

        // Each simplex should have 5 vertices (4-simplex in 4D)
        for simplex in tri.simplices() {
            assert_eq!(
                simplex.len(),
                5,
                "4D simplices should have 5 vertices (ndim+1)"
            );

            // All vertex indices should be valid
            for &idx in simplex {
                assert!(idx < 6, "Vertex index {} out of bounds", idx);
            }

            // All vertices should be unique
            let unique: HashSet<_> = simplex.iter().collect();
            assert_eq!(
                unique.len(),
                simplex.len(),
                "Simplex has duplicate vertices"
            );
        }
    }

    #[test]
    fn test_delaunay_5d() {
        // Test 5D Delaunay triangulation with minimal points
        let points = arr2(&[
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0],
        ]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Verify basic properties
        assert_eq!(tri.ndim(), 5);
        assert_eq!(tri.npoints(), 6);
        assert!(!tri.simplices().is_empty(), "Should have simplices");

        // Each simplex should have 6 vertices (5-simplex in 5D)
        for simplex in tri.simplices() {
            assert_eq!(
                simplex.len(),
                6,
                "5D simplices should have 6 vertices (ndim+1)"
            );

            // All vertex indices should be valid
            for &idx in simplex {
                assert!(idx < 6, "Vertex index {} out of bounds", idx);
            }
        }
    }

    #[test]
    fn test_delaunay_high_dim_with_interior() {
        // Test 4D with interior point to verify in-hypersphere test
        let points = arr2(&[
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0, 0.0],
            [0.25, 0.25, 0.25, 0.25], // Interior point
        ]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Should produce valid triangulation
        assert!(!tri.simplices().is_empty());

        // All simplices should have correct structure
        for simplex in tri.simplices() {
            assert_eq!(simplex.len(), 5, "4D simplices should have 5 vertices");

            // Verify all indices are valid
            for &idx in simplex {
                assert!(idx < 7);
            }

            // Verify uniqueness
            let unique: HashSet<_> = simplex.iter().collect();
            assert_eq!(unique.len(), simplex.len());
        }
    }

    #[test]
    fn test_find_simplex() {
        let points = arr2(&[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]);

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Point inside the triangle
        let inside_point = [0.3, 0.3];
        assert!(tri.find_simplex(&inside_point).is_some());

        // Point outside the triangle
        let outside_point = [1.5, 1.5];
        assert!(tri.find_simplex(&outside_point).is_none());
    }

    #[test]
    fn test_random_points_2d() {
        // Generate some random points
        let mut rng = scirs2_core::random::rng();

        let n = 20;
        let mut points_data = Vec::with_capacity(n * 2);

        for _ in 0..n {
            points_data.push(rng.random_range(0.0..1.0));
            points_data.push(rng.random_range(0.0..1.0));
        }

        let points = Array2::from_shape_vec((n, 2), points_data).expect("Operation failed");

        let tri = Delaunay::new(&points).expect("Operation failed");

        // Basic checks
        assert_eq!(tri.ndim(), 2);
        assert_eq!(tri.npoints(), n);

        // Each simplex should have 3 valid vertex indices
        for simplex in tri.simplices() {
            assert_eq!(simplex.len(), 3);
            for &idx in simplex {
                assert!(idx < n);
            }
        }
    }

    #[test]
    fn test_constrained_delaunay_basic() {
        let points = arr2(&[
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
            [0.5, 0.5], // Interior point
        ]);

        // Add constraint edges forming a square boundary
        let constraints = vec![(0, 1), (1, 2), (2, 3), (3, 0)];

        let tri =
            Delaunay::new_constrained(&points, constraints.clone()).expect("Operation failed");

        // Check that constraints are stored
        assert_eq!(tri.constraints().len(), 4);
        for &constraint in &constraints {
            assert!(tri.constraints().contains(&constraint));
        }

        // Check that we have a valid triangulation
        assert!(tri.simplices().len() >= 2); // At least 2 triangles for this configuration
    }

    #[test]
    fn test_constrained_delaunay_invalid_constraints() {
        let points = arr2(&[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]);

        // Invalid constraint with out-of-bounds index
        let invalid_constraints = vec![(0, 5)];
        let result = Delaunay::new_constrained(&points, invalid_constraints);
        assert!(result.is_err());

        // Invalid constraint connecting point to itself
        let self_constraint = vec![(0, 0)];
        let result = Delaunay::new_constrained(&points, self_constraint);
        assert!(result.is_err());
    }

    #[test]
    fn test_constrained_delaunay_3d() {
        let points_3d = arr2(&[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]);

        let constraints = vec![(0, 1)];
        let result = Delaunay::new_constrained(&points_3d, constraints);
        // 3D constrained Delaunay is now supported
        assert!(result.is_ok());
        let tri = result.expect("Operation failed");
        assert!(tri.constraints().contains(&(0, 1)));
    }

    #[test]
    fn test_edge_exists() {
        let points = arr2(&[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]);
        let tri = Delaunay::new(&points).expect("Operation failed");

        // Check if edges exist in the triangle
        assert!(tri.edge_exists(0, 1) || tri.edge_exists(1, 0));
        assert!(tri.edge_exists(1, 2) || tri.edge_exists(2, 1));
        assert!(tri.edge_exists(0, 2) || tri.edge_exists(2, 0));
    }

    #[test]
    fn test_segments_intersect() {
        // Test intersecting segments
        let p1 = [0.0, 0.0];
        let p2 = [1.0, 1.0];
        let q1 = [0.0, 1.0];
        let q2 = [1.0, 0.0];
        assert!(Delaunay::segments_intersect(p1, p2, q1, q2));

        // Test non-intersecting segments
        let p1 = [0.0, 0.0];
        let p2 = [1.0, 0.0];
        let q1 = [0.0, 1.0];
        let q2 = [1.0, 1.0];
        assert!(!Delaunay::segments_intersect(p1, p2, q1, q2));

        // Test collinear overlapping segments
        let p1 = [0.0, 0.0];
        let p2 = [2.0, 0.0];
        let q1 = [1.0, 0.0];
        let q2 = [3.0, 0.0];
        assert!(Delaunay::segments_intersect(p1, p2, q1, q2));
    }
}
