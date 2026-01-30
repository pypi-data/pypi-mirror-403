//! Auto-generated module structure

pub mod dwt2dconfig_traits;
pub mod dwt2dvalidationconfig_traits;
pub mod types;
pub mod functions;
pub mod functions_2;
pub mod functions_3;
pub mod functions_4;
pub mod functions_5;

// Re-export all types
pub use dwt2dconfig_traits::*;
pub use dwt2dvalidationconfig_traits::*;
pub use types::*;
pub use functions::*;
pub use functions_2::*;
pub use functions_3::*;
pub use functions_4::*;
pub use functions_5::*;

#[cfg(test)]
#[path = "legacy_tests.rs"]
mod tests;
