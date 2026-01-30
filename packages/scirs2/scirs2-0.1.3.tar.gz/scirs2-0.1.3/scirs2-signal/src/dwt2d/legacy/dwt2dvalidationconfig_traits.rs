//! # Dwt2dValidationConfig - Trait Implementations
//!
//! This module contains trait implementations for `Dwt2dValidationConfig`.
//!
//! ## Implemented Traits
//!
//! - `Default`
//!
//! 🤖 Generated with [SplitRS](https://github.com/cool-japan/splitrs)

use crate::dwt::{self, Wavelet};
use scirs2_core::parallel_ops::*;
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

use super::types::Dwt2dValidationConfig;

impl Default for Dwt2dValidationConfig {
    fn default() -> Self {
        Self {
            tolerance: 1e-12,
            test_sizes: vec![(4, 4), (8, 8), (16, 16), (32, 32), (64, 64)],
            test_wavelets: vec![Wavelet::Haar, Wavelet::DB(2), Wavelet::DB(4)],
            benchmark_performance: true,
            test_memory_efficiency: true,
            test_numerical_stability: true,
            test_edge_cases: true,
        }
    }
}

