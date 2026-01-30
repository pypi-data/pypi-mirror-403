//! # StorageConfig - Trait Implementations
//!
//! This module contains trait implementations for `StorageConfig`.
//!
//! ## Implemented Traits
//!
//! - `Default`
//!
//! 🤖 Generated with [SplitRS](https://github.com/cool-japan/splitrs)

use scirs2_core::{
    parallel_ops::*,
    simd_ops::{PlatformCapabilities, SimdUnifiedOps},
};

use super::types::{FileSystemConfig, NamingStrategy, StorageConfig, StorageType};

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            storage_type: StorageType::FileSystem,
            storage_path: "/tmp/scirs2_stats".to_string(),
            naming_strategy: NamingStrategy::UUID,
            fs_optimization: FileSystemConfig::default(),
        }
    }
}
