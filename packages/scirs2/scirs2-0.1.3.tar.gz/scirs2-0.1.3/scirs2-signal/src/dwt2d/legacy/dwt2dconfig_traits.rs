//! # Dwt2dConfig - Trait Implementations
//!
//! This module contains trait implementations for `Dwt2dConfig`.
//!
//! ## Implemented Traits
//!
//! - `Default`
//!
//! 🤖 Generated with [SplitRS](https://github.com/cool-japan/splitrs)

use super::types::{Dwt2dConfig, Dwt2dResult, MemoryPool, ThresholdMethod};
use scirs2_core::parallel_ops::*;
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

use super::types::Dwt2dConfig;

impl Default for Dwt2dConfig {
    fn default() -> Self {
        Self {
            preallocate_memory: true,
            use_inplace: false,
            memory_alignment: 32,
            chunk_size: Some(1024 * 1024),
        }
    }
}

