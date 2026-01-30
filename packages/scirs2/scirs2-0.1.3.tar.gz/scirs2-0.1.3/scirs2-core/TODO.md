# scirs2-core TODO (0.1.0)

Status snapshot: 2025-12-29

This file is a feature readiness checklist for the initial 0.1.0 release.
It focuses on what is IMPLEMENTED vs what remains.

Legend:
- [x] IMPLEMENTED (present in the repo and intended to ship in 0.1.0)
- [ ] TODO (not yet implemented, incomplete, or needs verification/hardening)

# scirs2-core TODO (0.1.0)

Status snapshot: 2025-12-29

This file is a 0.1.0-first-release checklist.
It is intentionally not a timeline: it focuses on what is IMPLEMENTED vs what remains.

Legend:
- [x] IMPLEMENTED (implemented in the repo and intended to ship in 0.1.0)
- [ ] TODO (not implemented yet, incomplete, or needs verification/hardening)

## 0.1.0 release checklist

### Public API and stability
- [x] Public prelude exists (see `src/prelude.rs`)
- [x] Error module exists (see `src/error/`)
- [x] API versioning utilities exist (see `src/apiversioning.rs`)
- [x] Deprecation/versioning support exists (see `src/versioning/deprecation.rs`)
- [x] API standards docs exist (see `docs/API_STANDARDS.md`)
- [x] Reference docs exist (see `docs/REFERENCE.md`)
- [x] API freeze notes exist (see `docs/API_FREEZE_1.0.md`)
- [ ] Confirm what is considered stable in 0.1.0 (public modules + feature flags)
- [ ] Ensure any "experimental" APIs are clearly feature-gated and documented
- [ ] Verify the top-level module exports are intentional (avoid accidental public surface)

### ndarray core + ndarray_ext

#### Core ndarray facade
- [x] New ndarray facade exists (see `src/ndarray/mod.rs`)
- [x] Backward-compat re-exports to `ndarray_ext` exist (see `src/ndarray/mod.rs`)
- [ ] Verify the recommended import path for 0.1.0 (docs + examples)

#### ndarray_ext: broadcasting and shape utilities
- [x] Broadcasting compatibility checks (see `src/ndarray_ext/broadcasting.rs`)
- [x] `broadcastshape` utilities (see `src/ndarray_ext/broadcasting.rs`)
- [x] `broadcast_arrays` helpers (see `src/ndarray_ext/broadcasting.rs`)
- [x] `broadcast_apply` helpers (see `src/ndarray_ext/broadcasting.rs`)
- [ ] Add explicit docs/examples for multi-array broadcasting edge cases

#### ndarray_ext: array manipulation/ops
- [x] Core ops module exists (see `src/ndarray_ext/ops.rs`)
- [x] `reshape` helpers (see `src/ndarray_ext/ops.rs`)
- [x] `stack` helpers (see `src/ndarray_ext/ops.rs`)
- [x] `split` helpers (see `src/ndarray_ext/ops.rs`)
- [x] `swapaxes` helpers (see `src/ndarray_ext/ops.rs`)
- [x] 2D argmin/argmax helpers exist (see `src/ndarray_ext/manipulation.rs`)
- [x] Views module documents zero-copy transformations (see `src/ndarray_ext/views.rs`)
- [ ] Confirm behavior on empty inputs, singleton dimensions, and axis handling

#### ndarray_ext: SIMD reductions (1D)
- [x] SIMD reduction module exists (see `src/ndarray_ext/reduction.rs`)
- [x] `sum_simd` (see `src/ndarray_ext/reduction.rs`)
- [x] `mean_simd` (see `src/ndarray_ext/reduction.rs`)
- [x] `min_simd` / `max_simd` (see `src/ndarray_ext/reduction.rs`)
- [x] `variance_simd` / `std_simd` with `ddof` (see `src/ndarray_ext/reduction.rs`)
- [x] `argmin_simd` / `argmax_simd` (see `src/ndarray_ext/reduction.rs`)
- [x] `cumsum_simd` / `cumprod_simd` (see `src/ndarray_ext/reduction.rs`)
- [ ] Document numerical expectations (NaN/Inf handling, stable vs unstable reduction)

#### ndarray_ext: preprocessing (SIMD)
- [x] Preprocessing module exists (see `src/ndarray_ext/preprocessing.rs`)
- [x] `normalize_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [x] `standardize_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [x] `clip_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [x] `softmax_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [x] `relu_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [x] `leaky_relu_simd` (see `src/ndarray_ext/preprocessing.rs`)
- [ ] Confirm softmax behavior across dtypes and extreme values
- [ ] Provide one canonical example per preprocessing function

#### ndarray_ext: statistics
- [x] Correlation utilities exist (see `src/ndarray_ext/stats/correlation.rs`)
- [ ] Ensure stats modules have consistent naming and error behavior

### SIMD operations (core)

#### Core traits and organization
- [x] SIMD ops trait exists: `SimdUnifiedOps` (see `src/simd_ops/functions.rs`)
- [x] SIMD infrastructure exists (see `src/simd/`, `src/simd_impl.rs`, `src/simd_ops/`)
- [x] SIMD test module exists (see `src/simd_ops_tests.rs`)
- [ ] Split/organize very large modules where it improves maintainability (no behavior change)

#### Unary operations
- [x] `simd_abs_f32` / `simd_abs_f64` (see `src/simd/unary.rs`)
- [x] `simd_sqrt_f32` / `simd_sqrt_f64` (see `src/simd/unary.rs`)
- [x] `simd_sign_f32` / `simd_sign_f64` (see `src/simd/unary.rs`)
- [x] Integer-power ops `simd_powi_f32` / `simd_powi_f64` (see `src/simd/unary_powi.rs`)

#### Rounding
- [x] `simd_floor_f32` / `simd_floor_f64` (see `src/simd/rounding.rs`)
- [x] `simd_ceil_f32` / `simd_ceil_f64` (see `src/simd/rounding.rs`)
- [x] `simd_round_f32` / `simd_round_f64` (see `src/simd/rounding.rs`)

#### Transcendentals (vectorized)
- [x] `simd_exp_f32` / `simd_exp_f64` (see `src/simd/transcendental/functions.rs`)
- [x] `simd_exp_fast_f32` (see `src/simd/transcendental/functions.rs`)
- [x] `simd_ln_f32` / `simd_ln_f64` (see `src/simd/transcendental/functions_5.rs`)
- [x] `simd_log2_f32` / `simd_log2_f64` (see `src/simd/transcendental/functions_6.rs`)
- [x] `simd_log10_f32` / `simd_log10_f64` (see `src/simd/transcendental/functions_6.rs`)
- [x] `simd_sin_f32` / `simd_sin_f64` (see `src/simd/transcendental/functions_5.rs`, `functions_6.rs`)
- [x] `simd_cos_f32` / `simd_cos_f64` (see `src/simd/transcendental/functions_6.rs`)
- [x] `simd_tanh_f32` / `simd_tanh_f64` (see `src/simd/transcendental/functions_4.rs`)
- [x] Polynomial approximations exist for several functions (see `src/simd_ops_polynomial.rs`)
- [ ] Clarify which transcendentals are "core-stable" vs "best-effort fast math"

#### Similarity
- [x] Cosine similarity for f32/f64 exists (see `src/simd/similarity.rs`)

### Memory efficiency and out-of-core

#### Module surface
- [x] `memory_efficient` module is exported (see `src/lib.rs`)
- [x] Memory-efficient docs exist (see `docs/memory_efficient.md`)

#### Memory mapped arrays
- [x] `MemoryMappedArray` exists (see `src/memory_efficient/memmap.rs`)
- [x] `open_mmap` exists (see `src/memory_efficient/memmap.rs`)
- [x] `create_mmap` exists (see `src/memory_efficient/memmap.rs`)
- [ ] Verify portability and failure modes for mmap across supported platforms

#### Chunked / lazy / out-of-core
- [x] `ChunkedArray` exists (see `src/memory_efficient/chunked.rs`)
- [x] `chunk_wise_op` exists (see `src/memory_efficient/chunked.rs`)
- [x] `chunk_wise_reduce` exists (see `src/memory_efficient/chunked.rs`)
- [x] `LazyArray` exists (see `src/memory_efficient/lazy_array.rs`)
- [x] `OutOfCoreArray` exists (see `src/memory_efficient/out_of_core.rs`)
- [x] Cross-file prefetcher exists (see `src/memory_efficient/cross_file_prefetch.rs`)
- [ ] Define/verify thread-safety and aliasing rules for all out-of-core types
- [ ] Add stress tests for chunking boundaries and extremely large shapes

### Performance utilities
- [x] Performance optimization utilities exist (see `src/performance_optimization.rs`)
- [x] Cache optimization utilities exist (see `src/performance/cache_optimization.rs`)
- [ ] Define "fast path" guarantees (what triggers them, what is fallback)
- [ ] Keep a small, stable baseline benchmark suite for regression detection

### Parallelism
- [x] Parallel module exists (see `src/parallel/`)
- [x] Parallel ops entrypoints exist (see `src/parallel_ops.rs`, `src/parallel_redirect.rs`)
- [ ] Confirm defaults and determinism expectations (ordering, reductions)
- [ ] Add targeted tests for parallel reductions and chunked iterators

### GPU (core surface)
- [x] GPU module exists (see `src/gpu/`)
- [x] GPU registry exists (see `src/gpu_registry.rs`)
- [ ] Ensure any GPU APIs exposed by core are clearly feature-gated and documented
- [ ] Provide one minimal example for any GPU-exposed public API

### Error handling and diagnostics
- [x] Core error types exist (see `src/error/error.rs`)
- [x] Error recovery utilities exist (see `src/error/recovery.rs`)
- [x] Diagnostics utilities exist (see `src/error/diagnostics.rs`)
- [ ] Ensure error messages are consistent and actionable across modules
- [ ] Prefer `Result` over panic in all public APIs; audit panic paths

### Validation and testing support
- [x] Validation module exists (see `src/validation/`)
- [x] Cross-platform SIMD validation exists (see `src/validation/cross_platform.rs`)
- [x] Testing infrastructure exists (see `src/testing/`)
- [ ] Ensure the core crate’s own tests cover feature-gated modules appropriately

### Logging, profiling, and configuration
- [x] Logging module exists (see `src/logging.rs`, `src/logging/`)
- [x] Profiling module exists (see `src/profiling/`)
- [x] Config module exists (see `src/config.rs`, `src/config/`)
- [ ] Ensure logging/profiling APIs are consistent and minimally invasive

### Documentation
- [x] Getting started exists (see `docs/getting_started.md`)
- [x] Examples overview exists (see `docs/examples.md`)
- [x] Error handling guide exists (see `docs/error_handling.md`)
- [x] Performance characteristics exist (see `docs/PERFORMANCE_CHARACTERISTICS.md`)
- [x] SIMD optimization notes exist (see `docs/SIMD_ULTRA_OPTIMIZATION.md`)
- [x] Production operation docs exist (see `docs/PRODUCTION_OPERATIONS.md`)
- [x] Production deployment docs exist (see `docs/PRODUCTION_DEPLOYMENT.md`)
- [x] Security audit preparation exists (see `docs/SECURITY_AUDIT_PREPARATION.md`)
- [ ] Audit docs for user-facing consistency in 0.1.0 (remove narrative-only phrasing)
- [ ] Document feature flags and their tradeoffs in one place

## Backlog (keep short, non-timeline)

- [ ] Reduce accidental public API surface (where feasible)
- [ ] Add more property-based tests for shape/stride/broadcast corner cases
- [ ] Add compatibility tests for mmap + out-of-core on all supported platforms
- [ ] Expand benchmarks only where they catch real regressions
