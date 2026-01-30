//! # SciRS2 Core Prelude
//!
//! The prelude module provides convenient access to the most commonly used items
//! in the SciRS2 ecosystem. Import this module to get started quickly without
//! needing to know the exact paths of all core functionality.
//!
//! ## Usage
//!
//! ```rust,no_run
//! use scirs2_core::prelude::*;
//!
//! // Now you have access to all common functionality:
//! let data = array![[1.0, 2.0], [3.0, 4.0]];  // Array creation
//! let mean = data.mean().expect("Operation failed");             // Array operations
//! let counter = Counter::new("requests".into()); // Metrics
//! ```
//!
//! ## What's Included
//!
//! ### Array Types and Operations
//! - `Array`, `Array1`, `Array2`, `ArrayD` - N-dimensional array types
//! - `ArrayView`, `ArrayViewMut` - Array views
//! - `Axis`, `Ix1`, `Ix2`, `IxDyn` - Shape and axis types
//! - `array!`, `s!` - Convenient macros for array creation and slicing
//!
//! ### Random Number Generation
//! - `random()` - Convenient random value generation
//! - `Rng` - Random number generator trait
//! - `SeedableRng` - Seedable RNG trait for reproducibility
//! - `ChaCha8Rng`, `ChaCha12Rng`, `ChaCha20Rng` - Secure random number generators
//! - Common distributions: `Normal`, `Uniform`, `Exponential`, `Gamma`, `Bernoulli`
//!
//! ### Validation Utilities
//! - `check_positive()` - Validate positive values
//! - `check_shape()` - Validate array shapes
//! - `check_finite()` - Validate finite values
//! - `check_in_bounds()` - Validate value bounds
//!
//! ### Metrics and Observability
//! - `Counter` - Monotonically increasing metric
//! - `Gauge` - Arbitrary up/down metric
//! - `Histogram` - Distribution of values
//! - `Timer` - Duration measurements
//! - `global_metrics_registry()` - Global metrics collection
//!
//! ### Error Handling
//! - `CoreError` - Main error type
//! - `CoreResult<T>` - Result type alias
//!
//! ### Complex Numbers
//! - `Complex`, `Complex32`, `Complex64` - Complex number types
//!
//! ## Examples
//!
//! ### Basic Array Operations
//!
//! ```rust
//! use scirs2_core::prelude::*;
//!
//! // Create arrays
//! let a = array![1.0, 2.0, 3.0, 4.0];
//! let b = array![[1.0, 2.0], [3.0, 4.0]];
//!
//! // Array slicing
//! let slice = b.slice(s![.., 0]);
//!
//! // Array operations
//! let sum = a.sum();
//! let mean = a.mean().expect("Operation failed");
//! ```
//!
//! ### Random Number Generation
//!
//! ```rust,ignore
//! use scirs2_core::prelude::*;
//!
//! // Quick random values
//! let x: f64 = random();
//! let y: bool = random();
//!
//! // Reproducible random generation
//! let mut rng = ChaCha8Rng::seed_from_u64(42);
//! let sample = rng.random::<f64>();
//!
//! // Sample from distributions
//! let normal = Normal::new(0.0, 1.0).expect("Operation failed");
//! let value = normal.sample(&mut rng);
//! ```
//!
//! ### Parameter Validation
//!
//! ```rust,ignore
//! use scirs2_core::prelude::*;
//!
//! pub fn my_function(data: &Array2<f64>, k: usize) -> CoreResult<Array1<f64>> {
//!     // Validate inputs
//!     check_positive(k, "k")?;
//!     checkarray_finite(data, "data")?;
//!
//!     // Your implementation here
//!     Ok(Array1::zeros(k))
//! }
//! ```
//!
//! ### Metrics Collection
//!
//! ```rust
//! use scirs2_core::prelude::*;
//!
//! // Create metrics
//! let counter = Counter::new("requests_total".into());
//! counter.inc();
//!
//! let gauge = Gauge::new("active_connections".into());
//! gauge.set(42.0);
//!
//! let histogram = Histogram::new("response_time".into());
//! histogram.observe(0.123);
//!
//! let timer = Timer::new("operation_duration".into());
//! let _guard = timer.start(); // Auto-records on drop
//! ```

// ================================
// Array Types and Operations
// ================================

/// Re-export core array types
/// These are re-exported from crate root (see lib.rs lines 521-540)
pub use crate::{
    Array,  // Generic N-dimensional array
    Array1, // 1-dimensional array
    Array2, // 2-dimensional array
    ArrayD, // Dynamic-dimensional array
    ArrayView,
    ArrayView1,
    ArrayView2,   // Immutable array views
    ArrayViewMut, // Mutable array view
    Axis,         // Array axis type
    Ix1,          // 1-dimensional index
    Ix2,          // 2-dimensional index
    IxDyn,        // Dynamic index
};

/// Re-export array creation and manipulation macros
/// These are re-exported from crate root (see lib.rs lines 521-540)
pub use crate::{
    array, // Create arrays: array![[1, 2], [3, 4]]
    s,     // Slice arrays: arr.slice(s![.., 0])
};

// ================================
// Random Number Generation
// ================================

#[cfg(feature = "random")]
pub use crate::random::{
    random,       // Convenient random value generation: let x: f64 = random();
    thread_rng,   // Thread-local RNG
    Distribution, // Distribution trait
    Rng,          // Random number generator trait
    RngCore,      // Core RNG operations
    SeedableRng,  // Seedable RNG trait for reproducibility
};

#[cfg(feature = "random")]
pub use crate::random::{
    ChaCha12Rng, // Balanced cryptographic RNG
    ChaCha20Rng, // Secure cryptographic RNG
    ChaCha8Rng,  // Fast cryptographic RNG
};

/// Common distributions for convenience
#[cfg(feature = "random")]
pub use crate::random::{
    Bernoulli,   // Bernoulli distribution (coin flip)
    Exponential, // Exponential distribution
    Gamma,       // Gamma distribution
    Normal,      // Normal/Gaussian distribution
    Uniform,     // Uniform distribution
};

// ================================
// Validation Utilities
// ================================

pub use crate::validation::{
    check_finite,    // Validate finite values (no NaN/Inf)
    check_in_bounds, // Validate value is within bounds
    check_positive,  // Validate positive values
};

// For backwards compatibility, also provide the array validation functions
pub use crate::validation::{
    checkarray_finite as check_array_finite, // Validate all array values are finite
    checkshape as check_shape,               // Validate array shape
};

// ================================
// Metrics and Observability
// ================================

pub use crate::metrics::{
    global_metrics_registry, // Access global metrics registry
    Counter,                 // Monotonically increasing counter
    Gauge,                   // Arbitrary up/down value
    Histogram,               // Distribution of values
    Timer,                   // Duration measurements
};

// ================================
// Error Handling
// ================================

pub use crate::error::{
    CoreError,  // Main error type
    CoreResult, // Result<T, CoreError> alias
};

// ================================
// Complex Numbers
// ================================

pub use num_complex::{
    Complex,   // Generic complex number
    Complex32, // 32-bit complex (f32 real/imag)
    Complex64, // 64-bit complex (f64 real/imag)
};

// ================================
// Common Traits
// ================================

/// Re-export commonly used numerical traits
pub use num_traits::{
    Float,         // Floating-point operations
    FromPrimitive, // Convert from primitive types
    Num,           // Basic numeric operations
    NumCast,       // Numeric type conversions
    One,           // Multiplicative identity (1)
    ToPrimitive,   // Convert to primitive types
    Zero,          // Additive identity (0)
};

// ================================
// Configuration
// ================================

pub use crate::config::{
    get_config,        // Get current configuration
    set_global_config, // Set global configuration
    Config,            // Configuration management
};

// ================================
// Constants
// ================================

/// Mathematical constants (π, e, φ, etc.)
pub use crate::constants::math;

/// Physical constants (c, h, G, etc.)
pub use crate::constants::physical;
