//! CPU feature detection and SIMD capability management
//!
//! This module provides runtime detection of SIMD capabilities and manages
//! CPU feature information through a cached singleton pattern for optimal performance.

use std::sync::OnceLock;

/// CPU feature flags detected at runtime
///
/// This struct caches the results of CPU feature detection to avoid repeated
/// runtime checks. It is initialized once and shared across all SIMD operations.
#[derive(Debug, Clone)]
pub struct CpuFeatures {
    /// AVX-512F (512-bit SIMD) support
    pub has_avx512f: bool,
    /// AVX2 (256-bit SIMD) support
    pub has_avx2: bool,
    /// SSE (128-bit SIMD) support
    pub has_sse: bool,
    /// FMA (Fused Multiply-Add) support
    pub has_fma: bool,
    /// NEON (ARM SIMD) support
    pub has_neon: bool,
}

static CPU_FEATURES: OnceLock<CpuFeatures> = OnceLock::new();

/// Get CPU features with lazy initialization
///
/// This function returns a static reference to CPU features, initializing
/// them on first call. Subsequent calls return the cached result.
///
/// # Returns
///
/// A static reference to `CpuFeatures` containing detected CPU capabilities.
pub fn get_cpu_features() -> &'static CpuFeatures {
    CPU_FEATURES.get_or_init(|| {
        #[cfg(target_arch = "x86_64")]
        {
            CpuFeatures {
                has_avx512f: std::arch::is_x86_feature_detected!("avx512f"),
                has_avx2: std::arch::is_x86_feature_detected!("avx2"),
                has_sse: std::arch::is_x86_feature_detected!("sse"),
                has_fma: std::arch::is_x86_feature_detected!("fma"),
                has_neon: false,
            }
        }
        #[cfg(target_arch = "aarch64")]
        {
            CpuFeatures {
                has_avx512f: false,
                has_avx2: false,
                has_sse: false,
                has_fma: false, // ARM uses different FMA instructions
                has_neon: std::arch::is_aarch64_feature_detected!("neon"),
            }
        }
        #[cfg(not(any(target_arch = "x86_64", target_arch = "aarch64")))]
        {
            CpuFeatures {
                has_avx512f: false,
                has_avx2: false,
                has_sse: false,
                has_fma: false,
                has_neon: false,
            }
        }
    })
}

/// Extended SIMD capabilities including cache information
///
/// This struct provides detailed information about the system's SIMD capabilities
/// including vector widths, cache sizes, and optimal prefetch distances.
#[derive(Debug, Clone)]
pub struct SimdCapabilities {
    /// AVX2 (256-bit SIMD) support
    pub has_avx2: bool,
    /// AVX-512 (512-bit SIMD) support
    pub has_avx512: bool,
    /// FMA (Fused Multiply-Add) support
    pub has_fma: bool,
    /// SSE4.2 support
    pub has_sse42: bool,
    /// BMI2 (Bit Manipulation Instructions 2) support
    pub has_bmi2: bool,
    /// Number of f32 elements that can be processed in parallel
    pub vector_width_f32: usize,
    /// Number of f64 elements that can be processed in parallel
    pub vector_width_f64: usize,
    /// CPU cache line size in bytes
    pub cache_line_size: usize,
    /// L1 cache size in bytes
    pub l1_cache_size: usize,
    /// L2 cache size in bytes
    pub l2_cache_size: usize,
    /// Prefetch distance in cache lines
    pub prefetch_distance: usize,
}

impl Default for SimdCapabilities {
    fn default() -> Self {
        let cpu_features = get_cpu_features();

        Self {
            // Use detected CPU features
            has_avx2: cpu_features.has_avx2,
            has_avx512: cpu_features.has_avx512f,
            has_fma: cpu_features.has_fma,
            has_sse42: cpu_features.has_sse,
            has_bmi2: false, // Conservative default, would need specific detection
            vector_width_f32: if cpu_features.has_avx512f {
                16 // AVX-512 can process 16 f32s
            } else if cpu_features.has_avx2 {
                8 // AVX2 can process 8 f32s
            } else if cpu_features.has_sse || cpu_features.has_neon {
                4 // SSE/NEON can process 4 f32s
            } else {
                1 // Scalar fallback
            },
            vector_width_f64: if cpu_features.has_avx512f {
                8 // AVX-512 can process 8 f64s
            } else if cpu_features.has_avx2 {
                4 // AVX2 can process 4 f64s
            } else if cpu_features.has_sse || cpu_features.has_neon {
                2 // SSE/NEON can process 2 f64s
            } else {
                1 // Scalar fallback
            },
            cache_line_size: 64,   // Typical cache line size
            l1_cache_size: 32768,  // 32KB typical L1 cache
            l2_cache_size: 262144, // 256KB typical L2 cache
            prefetch_distance: 16, // Prefetch 16 cache lines ahead
        }
    }
}

/// Detect SIMD capabilities for the current system
///
/// This function returns detailed SIMD capabilities including vector widths,
/// cache information, and supported instruction sets.
///
/// # Returns
///
/// A `SimdCapabilities` struct containing detailed system capabilities.
///
/// # Examples
///
/// ```ignore
/// use scirs2_core::simd::detect::detect_simd_capabilities;
///
/// let caps = detect_simd_capabilities();
/// println!("Vector width for f32: {}", caps.vector_width_f32);
/// println!("Has AVX2: {}", caps.has_avx2);
/// ```
#[allow(dead_code)]
pub fn detect_simd_capabilities() -> SimdCapabilities {
    SimdCapabilities::default()
}
