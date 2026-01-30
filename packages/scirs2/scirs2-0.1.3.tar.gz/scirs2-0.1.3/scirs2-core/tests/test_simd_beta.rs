//! Beta function SIMD tests

use scirs2_core::ndarray::{array, Array1};
#[cfg(feature = "random")]
use scirs2_core::random::{thread_rng, Distribution, Uniform};

// =============================================================================
// =============================================================================
// Beta Function Tests (Phase 60)
// =============================================================================

use scirs2_core::ndarray_ext::elementwise::{beta_simd, ln_beta_simd};

// -----------------------------------------------------------------------------
// beta (Beta Function) Tests
// -----------------------------------------------------------------------------

/// Test beta basic f64
#[test]
fn test_beta_simd_basic_f64() {
    let a = array![1.0_f64, 2.0, 3.0];
    let b = array![1.0_f64, 2.0, 3.0];
    let result = beta_simd(&a.view(), &b.view());

    // B(1, 1) = 1
    assert!(
        (result[0] - 1.0).abs() < 1e-10,
        "B(1, 1) should be 1, got {}",
        result[0]
    );

    // B(2, 2) = Γ(2)Γ(2)/Γ(4) = 1*1/6 = 1/6
    assert!(
        (result[1] - 1.0 / 6.0).abs() < 1e-10,
        "B(2, 2) should be 1/6, got {}",
        result[1]
    );

    // B(3, 3) = Γ(3)Γ(3)/Γ(6) = 2*2/120 = 1/30
    assert!(
        (result[2] - 1.0 / 30.0).abs() < 1e-10,
        "B(3, 3) should be 1/30, got {}",
        result[2]
    );
}

/// Test beta basic f32
#[test]
fn test_beta_simd_basic_f32() {
    let a = array![1.0_f32, 2.0, 3.0];
    let b = array![1.0_f32, 2.0, 3.0];
    let result = beta_simd(&a.view(), &b.view());

    assert!(
        (result[0] - 1.0).abs() < 1e-5,
        "B(1, 1) should be 1, got {}",
        result[0]
    );
    assert!(
        (result[1] - 1.0 / 6.0).abs() < 1e-5,
        "B(2, 2) should be 1/6, got {}",
        result[1]
    );
}

/// Test beta empty array
#[test]
fn test_beta_simd_empty() {
    let a: Array1<f64> = array![];
    let b: Array1<f64> = array![];
    let result = beta_simd(&a.view(), &b.view());
    assert_eq!(result.len(), 0, "Empty input should give empty output");
}

/// Test beta large array (SIMD path)
#[test]
fn test_beta_simd_large_array() {
    let n = 1000;
    let a: Array1<f64> = Array1::linspace(1.0, 5.0, n);
    let b: Array1<f64> = Array1::linspace(1.0, 5.0, n);
    let result = beta_simd(&a.view(), &b.view());

    assert_eq!(result.len(), n);
    for (i, &v) in result.iter().enumerate() {
        assert!(
            v.is_finite() && v > 0.0,
            "Beta should be finite positive at index {}, got {}",
            i,
            v
        );
    }
}

/// Test beta symmetry B(a, b) = B(b, a)
#[test]
fn test_beta_simd_symmetry() {
    let a = array![1.5_f64, 2.5, 3.5, 0.5];
    let b = array![2.0_f64, 1.0, 4.0, 3.0];

    let result1 = beta_simd(&a.view(), &b.view());
    let result2 = beta_simd(&b.view(), &a.view());

    for i in 0..a.len() {
        assert!(
            (result1[i] - result2[i]).abs() < 1e-10,
            "B(a, b) should equal B(b, a) at index {}",
            i
        );
    }
}

/// Test beta special value B(0.5, 0.5) = π
#[test]
fn test_beta_simd_half_half() {
    let a = array![0.5_f64];
    let b = array![0.5_f64];
    let result = beta_simd(&a.view(), &b.view());

    assert!(
        (result[0] - std::f64::consts::PI).abs() < 1e-8,
        "B(0.5, 0.5) should be π, got {}",
        result[0]
    );
}

/// Test beta B(a, 1) = 1/a
#[test]
fn test_beta_simd_a_one() {
    let a = array![2.0_f64, 3.0, 4.0, 5.0];
    let b = array![1.0_f64, 1.0, 1.0, 1.0];
    let result = beta_simd(&a.view(), &b.view());

    for i in 0..a.len() {
        let expected = 1.0 / a[i];
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "B({}, 1) should be 1/{} = {}, got {}",
            a[i],
            a[i],
            expected,
            result[i]
        );
    }
}

/// Test beta for Beta distribution use case
#[test]
fn test_beta_simd_distribution_use_case() {
    // Beta distribution parameters
    let alpha = array![2.0_f64, 5.0, 1.0, 0.5];
    let beta_param = array![5.0_f64, 2.0, 1.0, 0.5];
    let beta_val = beta_simd(&alpha.view(), &beta_param.view());

    // All beta values should be positive for valid parameters
    for (i, &b) in beta_val.iter().enumerate() {
        assert!(
            b > 0.0 && b.is_finite(),
            "Beta function should be positive for valid params, got {} at index {}",
            b,
            i
        );
    }
}

// -----------------------------------------------------------------------------
// ln_beta (Log-Beta Function) Tests
// -----------------------------------------------------------------------------

/// Test ln_beta basic f64
#[test]
fn test_ln_beta_simd_basic_f64() {
    let a = array![1.0_f64, 2.0, 3.0];
    let b = array![1.0_f64, 2.0, 3.0];
    let result = ln_beta_simd(&a.view(), &b.view());

    // ln(B(1, 1)) = ln(1) = 0
    assert!(
        result[0].abs() < 1e-10,
        "ln(B(1, 1)) should be 0, got {}",
        result[0]
    );

    // ln(B(2, 2)) = ln(1/6)
    let expected_ln_b22 = (1.0_f64 / 6.0).ln();
    assert!(
        (result[1] - expected_ln_b22).abs() < 1e-10,
        "ln(B(2, 2)) should be ln(1/6), got {}",
        result[1]
    );
}

/// Test ln_beta basic f32
#[test]
fn test_ln_beta_simd_basic_f32() {
    let a = array![1.0_f32, 2.0];
    let b = array![1.0_f32, 2.0];
    let result = ln_beta_simd(&a.view(), &b.view());

    assert!(
        result[0].abs() < 1e-5,
        "ln(B(1, 1)) should be 0, got {}",
        result[0]
    );
}

/// Test ln_beta empty array
#[test]
fn test_ln_beta_simd_empty() {
    let a: Array1<f64> = array![];
    let b: Array1<f64> = array![];
    let result = ln_beta_simd(&a.view(), &b.view());
    assert_eq!(result.len(), 0, "Empty input should give empty output");
}

/// Test ln_beta large array (SIMD path)
#[test]
fn test_ln_beta_simd_large_array() {
    let n = 1000;
    let a: Array1<f64> = Array1::linspace(1.0, 10.0, n);
    let b: Array1<f64> = Array1::linspace(1.0, 10.0, n);
    let result = ln_beta_simd(&a.view(), &b.view());

    assert_eq!(result.len(), n);
    for (i, &v) in result.iter().enumerate() {
        assert!(
            v.is_finite(),
            "ln(Beta) should be finite at index {}, got {}",
            i,
            v
        );
    }
}

/// Test ln_beta symmetry
#[test]
fn test_ln_beta_simd_symmetry() {
    let a = array![1.5_f64, 2.5, 3.5];
    let b = array![2.0_f64, 1.0, 4.0];

    let result1 = ln_beta_simd(&a.view(), &b.view());
    let result2 = ln_beta_simd(&b.view(), &a.view());

    for i in 0..a.len() {
        assert!(
            (result1[i] - result2[i]).abs() < 1e-10,
            "ln(B(a, b)) should equal ln(B(b, a)) at index {}",
            i
        );
    }
}

/// Test ln_beta consistency with beta: exp(ln_beta) = beta
#[test]
fn test_ln_beta_simd_consistency() {
    let a = array![1.0_f64, 2.0, 3.0, 0.5, 1.5];
    let b = array![1.0_f64, 2.0, 3.0, 0.5, 2.5];

    let ln_beta_val = ln_beta_simd(&a.view(), &b.view());
    let beta_val = beta_simd(&a.view(), &b.view());

    for i in 0..a.len() {
        let exp_ln_beta = ln_beta_val[i].exp();
        assert!(
            (exp_ln_beta - beta_val[i]).abs() < 1e-10,
            "exp(ln(B(a,b))) should equal B(a,b), got {} vs {} at index {}",
            exp_ln_beta,
            beta_val[i],
            i
        );
    }
}

/// Test ln_beta numerical stability for large arguments
#[test]
fn test_ln_beta_simd_large_args() {
    // For large arguments, beta would overflow but ln_beta should be stable
    let a = array![100.0_f64, 200.0, 500.0];
    let b = array![100.0_f64, 200.0, 500.0];
    let result = ln_beta_simd(&a.view(), &b.view());

    // Results should be finite (very negative for large symmetric args)
    for (i, &v) in result.iter().enumerate() {
        assert!(
            v.is_finite(),
            "ln(Beta) should be finite for large args at index {}, got {}",
            i,
            v
        );
        assert!(
            v < 0.0,
            "ln(Beta) should be negative for large args, got {}",
            v
        );
    }
}

/// Test ln_beta for Bayesian inference use case
#[test]
fn test_ln_beta_simd_bayesian_use_case() {
    // Common Beta distribution parameters for A/B testing
    // Prior: Beta(1, 1) = uniform
    // Posterior after observations: Beta(alpha + successes, beta + failures)
    let alpha = array![1.0_f64, 10.0, 50.0, 100.0]; // Prior + successes
    let beta_param = array![1.0_f64, 10.0, 50.0, 100.0]; // Prior + failures

    let ln_beta_val = ln_beta_simd(&alpha.view(), &beta_param.view());

    // All log-beta values should be finite
    for (i, &lb) in ln_beta_val.iter().enumerate() {
        assert!(
            lb.is_finite(),
            "ln(Beta) should be finite for Bayesian params at index {}",
            i
        );
    }

    // ln(Beta) should decrease as parameters increase (normalizing constant gets smaller)
    for i in 0..ln_beta_val.len() - 1 {
        assert!(
            ln_beta_val[i] > ln_beta_val[i + 1],
            "ln(Beta) should decrease as params increase"
        );
    }
}

// ============================================================================
// Phase 61: SIMD lerp (linear interpolation) tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::lerp_simd;
use scirs2_core::ndarray_ext::elementwise::smoothstep_simd;

/// Test lerp basic f32 correctness
#[test]
fn test_lerp_simd_f32_basic() {
    let a = array![0.0_f32, 10.0, -5.0, 100.0];
    let b = array![10.0_f32, 20.0, 5.0, 200.0];

    // t = 0: should return a
    let result = lerp_simd(&a.view(), &b.view(), 0.0_f32);
    assert!((result[0] - 0.0).abs() < 1e-6);
    assert!((result[1] - 10.0).abs() < 1e-6);
    assert!((result[2] - (-5.0)).abs() < 1e-6);
    assert!((result[3] - 100.0).abs() < 1e-6);

    // t = 1: should return b
    let result = lerp_simd(&a.view(), &b.view(), 1.0_f32);
    assert!((result[0] - 10.0).abs() < 1e-6);
    assert!((result[1] - 20.0).abs() < 1e-6);
    assert!((result[2] - 5.0).abs() < 1e-6);
    assert!((result[3] - 200.0).abs() < 1e-6);

    // t = 0.5: should return midpoint
    let result = lerp_simd(&a.view(), &b.view(), 0.5_f32);
    assert!((result[0] - 5.0).abs() < 1e-6);
    assert!((result[1] - 15.0).abs() < 1e-6);
    assert!((result[2] - 0.0).abs() < 1e-6);
    assert!((result[3] - 150.0).abs() < 1e-6);
}

/// Test lerp basic f64 correctness
#[test]
fn test_lerp_simd_f64_basic() {
    let a = array![0.0_f64, 100.0, -50.0];
    let b = array![100.0_f64, 200.0, 50.0];

    // t = 0.25
    let result = lerp_simd(&a.view(), &b.view(), 0.25_f64);
    assert!((result[0] - 25.0).abs() < 1e-14);
    assert!((result[1] - 125.0).abs() < 1e-14);
    assert!((result[2] - (-25.0)).abs() < 1e-14);

    // t = 0.75
    let result = lerp_simd(&a.view(), &b.view(), 0.75_f64);
    assert!((result[0] - 75.0).abs() < 1e-14);
    assert!((result[1] - 175.0).abs() < 1e-14);
    assert!((result[2] - 25.0).abs() < 1e-14);
}

/// Test lerp empty array
#[test]
fn test_lerp_simd_empty() {
    let a: Array1<f64> = array![];
    let b: Array1<f64> = array![];
    let result = lerp_simd(&a.view(), &b.view(), 0.5_f64);
    assert_eq!(result.len(), 0);
}

/// Test lerp large array (SIMD path)
#[test]
fn test_lerp_simd_large_array() {
    let n = 10000;
    let a = Array1::from_vec((0..n).map(|i| i as f64).collect());
    let b = Array1::from_vec((0..n).map(|i| (i * 2) as f64).collect());

    let result = lerp_simd(&a.view(), &b.view(), 0.5_f64);
    assert_eq!(result.len(), n);

    // Check a few values: lerp(i, 2*i, 0.5) = i + 0.5*(2i - i) = i + 0.5*i = 1.5*i
    for i in [0, 100, 1000, 5000, 9999] {
        let expected = 1.5 * i as f64;
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "lerp[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test lerp extrapolation (t outside [0, 1])
#[test]
fn test_lerp_simd_extrapolation() {
    let a = array![0.0_f64, 0.0];
    let b = array![10.0_f64, 20.0];

    // t = -1: extrapolate backward
    let result = lerp_simd(&a.view(), &b.view(), -1.0_f64);
    assert!((result[0] - (-10.0)).abs() < 1e-14);
    assert!((result[1] - (-20.0)).abs() < 1e-14);

    // t = 2: extrapolate forward
    let result = lerp_simd(&a.view(), &b.view(), 2.0_f64);
    assert!((result[0] - 20.0).abs() < 1e-14);
    assert!((result[1] - 40.0).abs() < 1e-14);
}

/// Test lerp property: lerp(a, b, t) = a + t*(b-a)
#[test]
fn test_lerp_simd_formula_verification() {
    let a = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];
    let b = array![11.0_f64, 12.0, 13.0, 14.0, 15.0];
    let t = 0.3_f64;

    let result = lerp_simd(&a.view(), &b.view(), t);

    for i in 0..a.len() {
        let expected = a[i] + t * (b[i] - a[i]);
        assert!(
            (result[i] - expected).abs() < 1e-14,
            "Formula verification failed at index {}",
            i
        );
    }
}

/// Test lerp with same values (a == b)
#[test]
fn test_lerp_simd_same_values() {
    let a = array![5.0_f64, 5.0, 5.0];
    let b = array![5.0_f64, 5.0, 5.0];

    for t in [0.0, 0.25, 0.5, 0.75, 1.0] {
        let result = lerp_simd(&a.view(), &b.view(), t);
        for i in 0..a.len() {
            assert!(
                (result[i] - 5.0).abs() < 1e-14,
                "lerp of identical values should be the same value"
            );
        }
    }
}

/// Test lerp animation blending use case
#[test]
fn test_lerp_simd_animation_blending() {
    // Simulating position interpolation between keyframes
    let keyframe_0 = array![0.0_f64, 0.0, 0.0]; // Position at t=0
    let keyframe_1 = array![10.0_f64, 5.0, 2.0]; // Position at t=1

    // Interpolate at various animation times
    for time in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] {
        let position = lerp_simd(&keyframe_0.view(), &keyframe_1.view(), time);
        for i in 0..3 {
            let expected = keyframe_0[i] + time * (keyframe_1[i] - keyframe_0[i]);
            assert!(
                (position[i] - expected).abs() < 1e-14,
                "Animation interpolation at t={} failed",
                time
            );
        }
    }
}

// ============================================================================
// Phase 61: SIMD smoothstep tests
// ============================================================================

/// Test smoothstep basic f32 correctness
#[test]
fn test_smoothstep_simd_f32_basic() {
    let x = array![0.0_f32, 0.25, 0.5, 0.75, 1.0];

    let result = smoothstep_simd(0.0_f32, 1.0_f32, &x.view());

    // smoothstep(0) = 0
    assert!((result[0] - 0.0).abs() < 1e-6);
    // smoothstep(0.5) = 0.5 (symmetric about midpoint)
    assert!((result[2] - 0.5).abs() < 1e-6);
    // smoothstep(1) = 1
    assert!((result[4] - 1.0).abs() < 1e-6);

    // Values should be monotonically increasing
    for i in 0..result.len() - 1 {
        assert!(result[i] <= result[i + 1], "smoothstep should be monotonic");
    }
}

/// Test smoothstep basic f64 correctness
#[test]
fn test_smoothstep_simd_f64_basic() {
    let x = array![0.0_f64, 0.25, 0.5, 0.75, 1.0];

    let result = smoothstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Verify the Hermite polynomial: 3t² - 2t³
    for i in 0..x.len() {
        let t = x[i];
        let expected = t * t * (3.0 - 2.0 * t);
        assert!(
            (result[i] - expected).abs() < 1e-14,
            "smoothstep[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test smoothstep empty array
#[test]
fn test_smoothstep_simd_empty() {
    let x: Array1<f64> = array![];
    let result = smoothstep_simd(0.0_f64, 1.0_f64, &x.view());
    assert_eq!(result.len(), 0);
}

/// Test smoothstep clamping at edges
#[test]
fn test_smoothstep_simd_clamping() {
    let x = array![-1.0_f64, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0];

    let result = smoothstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Values below edge0 should be 0
    assert!((result[0] - 0.0).abs() < 1e-14); // x = -1
    assert!((result[1] - 0.0).abs() < 1e-14); // x = -0.5
    assert!((result[2] - 0.0).abs() < 1e-14); // x = 0

    // Values above edge1 should be 1
    assert!((result[4] - 1.0).abs() < 1e-14); // x = 1
    assert!((result[5] - 1.0).abs() < 1e-14); // x = 1.5
    assert!((result[6] - 1.0).abs() < 1e-14); // x = 2
}

/// Test smoothstep with custom edges
#[test]
fn test_smoothstep_simd_custom_edges() {
    let x = array![0.0_f64, 2.5, 5.0, 7.5, 10.0];

    // Edges at [0, 10]
    let result = smoothstep_simd(0.0_f64, 10.0_f64, &x.view());

    // x=0: t=0, smoothstep=0
    assert!((result[0] - 0.0).abs() < 1e-14);
    // x=5: t=0.5, smoothstep=0.5
    assert!((result[2] - 0.5).abs() < 1e-14);
    // x=10: t=1, smoothstep=1
    assert!((result[4] - 1.0).abs() < 1e-14);
}

/// Test smoothstep large array (SIMD path)
#[test]
fn test_smoothstep_simd_large_array() {
    let n = 10000;
    let x = Array1::linspace(0.0, 1.0, n);

    let result = smoothstep_simd(0.0_f64, 1.0_f64, &x.view());
    assert_eq!(result.len(), n);

    // Verify first, middle, and last values
    assert!((result[0] - 0.0).abs() < 1e-14);
    let mid = n / 2;
    let t_mid = x[mid];
    let expected_mid = t_mid * t_mid * (3.0 - 2.0 * t_mid);
    assert!((result[mid] - expected_mid).abs() < 1e-10);
    assert!((result[n - 1] - 1.0).abs() < 1e-14);
}

/// Test smoothstep property: derivative at edges is zero
#[test]
fn test_smoothstep_simd_derivative_at_edges() {
    // The derivative of 3t² - 2t³ is 6t - 6t² = 6t(1-t)
    // At t=0: derivative = 0, at t=1: derivative = 0

    // Approximate derivative at boundaries with very small epsilon
    let eps = 1e-8_f64;
    let x_near_0 = array![0.0, eps];
    let x_near_1 = array![1.0 - eps, 1.0];

    let result_0 = smoothstep_simd(0.0_f64, 1.0_f64, &x_near_0.view());
    let result_1 = smoothstep_simd(0.0_f64, 1.0_f64, &x_near_1.view());

    // Derivative near 0 should be very small
    let deriv_near_0 = (result_0[1] - result_0[0]) / eps;
    assert!(
        deriv_near_0.abs() < 1e-5,
        "Derivative at edge0 should be near 0, got {}",
        deriv_near_0
    );

    // Derivative near 1 should be very small
    let deriv_near_1 = (result_1[1] - result_1[0]) / eps;
    assert!(
        deriv_near_1.abs() < 1e-5,
        "Derivative at edge1 should be near 0, got {}",
        deriv_near_1
    );
}

/// Test smoothstep with reversed edges (edge0 > edge1)
#[test]
fn test_smoothstep_simd_reversed_edges() {
    let x = array![0.0_f64, 0.5, 1.0];

    // Reversed: edge0=1, edge1=0
    let result = smoothstep_simd(1.0_f64, 0.0_f64, &x.view());

    // With reversed edges, x=0 maps to t=(0-1)/(0-1)=1, x=1 maps to t=0
    // smoothstep(1.0, 0.0, 0) should be 1 (since x < edge1)
    // smoothstep(1.0, 0.0, 1) should be 0 (since x > edge0)
    assert!((result[0] - 1.0).abs() < 1e-14); // x=0 gives smoothstep=1
    assert!((result[2] - 0.0).abs() < 1e-14); // x=1 gives smoothstep=0
}

/// Test smoothstep shader use case: soft shadow transition
#[test]
fn test_smoothstep_simd_shadow_transition() {
    // Simulating soft shadow from light source
    // Shadow starts at distance 2.0, fully dark at 5.0
    let distances = array![0.0_f64, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
    let shadow_start = 2.0_f64;
    let shadow_end = 5.0_f64;

    let shadow_factor = smoothstep_simd(shadow_start, shadow_end, &distances.view());

    // Before shadow_start: no shadow (0)
    assert!((shadow_factor[0] - 0.0).abs() < 1e-14);
    assert!((shadow_factor[1] - 0.0).abs() < 1e-14);
    assert!((shadow_factor[2] - 0.0).abs() < 1e-14);

    // After shadow_end: full shadow (1)
    assert!((shadow_factor[5] - 1.0).abs() < 1e-14);
    assert!((shadow_factor[6] - 1.0).abs() < 1e-14);
    assert!((shadow_factor[7] - 1.0).abs() < 1e-14);

    // Middle region: smooth transition
    assert!(shadow_factor[3] > 0.0 && shadow_factor[3] < 1.0);
    assert!(shadow_factor[4] > 0.0 && shadow_factor[4] < 1.0);
}

// ============================================================================
// Phase 62: SIMD hypot (hypotenuse) tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::copysign_simd;
use scirs2_core::ndarray_ext::elementwise::hypot_simd;

/// Test hypot basic f32 correctness with Pythagorean triples
#[test]
fn test_hypot_simd_f32_basic() {
    // Well-known Pythagorean triples
    let x = array![3.0_f32, 5.0, 8.0, 7.0];
    let y = array![4.0_f32, 12.0, 15.0, 24.0];

    let result = hypot_simd(&x.view(), &y.view());

    assert!((result[0] - 5.0).abs() < 1e-5); // 3-4-5
    assert!((result[1] - 13.0).abs() < 1e-5); // 5-12-13
    assert!((result[2] - 17.0).abs() < 1e-5); // 8-15-17
    assert!((result[3] - 25.0).abs() < 1e-5); // 7-24-25
}

/// Test hypot basic f64 correctness
#[test]
fn test_hypot_simd_f64_basic() {
    let x = array![3.0_f64, 5.0, 8.0, 7.0];
    let y = array![4.0_f64, 12.0, 15.0, 24.0];

    let result = hypot_simd(&x.view(), &y.view());

    assert!((result[0] - 5.0).abs() < 1e-14);
    assert!((result[1] - 13.0).abs() < 1e-14);
    assert!((result[2] - 17.0).abs() < 1e-14);
    assert!((result[3] - 25.0).abs() < 1e-14);
}

/// Test hypot empty array
#[test]
fn test_hypot_simd_empty() {
    let x: Array1<f64> = array![];
    let y: Array1<f64> = array![];
    let result = hypot_simd(&x.view(), &y.view());
    assert_eq!(result.len(), 0);
}

/// Test hypot large array (SIMD path)
#[test]
fn test_hypot_simd_large_array() {
    let n = 10000;
    // Generate values that form 3-4-5 scaled triangles
    let x = Array1::from_vec((0..n).map(|i| 3.0 * i as f64).collect());
    let y = Array1::from_vec((0..n).map(|i| 4.0 * i as f64).collect());

    let result = hypot_simd(&x.view(), &y.view());
    assert_eq!(result.len(), n);

    // Check: hypot(3i, 4i) = 5i
    for i in [0, 100, 1000, 5000, 9999] {
        let expected = 5.0 * i as f64;
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "hypot[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test hypot with zeros
#[test]
fn test_hypot_simd_zeros() {
    let x = array![0.0_f64, 5.0, 0.0];
    let y = array![3.0_f64, 0.0, 0.0];

    let result = hypot_simd(&x.view(), &y.view());

    assert!((result[0] - 3.0).abs() < 1e-14); // hypot(0, 3) = 3
    assert!((result[1] - 5.0).abs() < 1e-14); // hypot(5, 0) = 5
    assert!((result[2] - 0.0).abs() < 1e-14); // hypot(0, 0) = 0
}

/// Test hypot with negative values
#[test]
fn test_hypot_simd_negative_values() {
    let x = array![-3.0_f64, -5.0, 3.0, -3.0];
    let y = array![4.0_f64, -12.0, -4.0, -4.0];

    let result = hypot_simd(&x.view(), &y.view());

    // hypot should always return positive values regardless of input signs
    assert!((result[0] - 5.0).abs() < 1e-14);
    assert!((result[1] - 13.0).abs() < 1e-14);
    assert!((result[2] - 5.0).abs() < 1e-14);
    assert!((result[3] - 5.0).abs() < 1e-14);
}

/// Test hypot overflow protection
#[test]
fn test_hypot_simd_overflow_protection() {
    // Large values that would overflow with naive x*x + y*y
    let large = 1e150_f64;
    let x = array![large, large];
    let y = array![large, large];

    let result = hypot_simd(&x.view(), &y.view());

    // Result should be finite, approximately large * sqrt(2)
    assert!(result[0].is_finite(), "hypot should handle large values");
    let expected = large * std::f64::consts::SQRT_2;
    let relative_error = ((result[0] - expected) / expected).abs();
    assert!(
        relative_error < 1e-10,
        "hypot({}, {}) = {}, expected {}",
        large,
        large,
        result[0],
        expected
    );
}

/// Test hypot underflow protection
#[test]
fn test_hypot_simd_underflow_protection() {
    // Small values that would underflow with naive x*x + y*y
    let small = 1e-200_f64;
    let x = array![small, small];
    let y = array![small, small];

    let result = hypot_simd(&x.view(), &y.view());

    // Result should be finite and non-zero
    assert!(result[0].is_finite(), "hypot should handle small values");
    assert!(result[0] > 0.0, "hypot should not underflow to zero");
    let expected = small * std::f64::consts::SQRT_2;
    let relative_error = ((result[0] - expected) / expected).abs();
    assert!(
        relative_error < 1e-10,
        "hypot({}, {}) = {}, expected {}",
        small,
        small,
        result[0],
        expected
    );
}

/// Test hypot property: hypot(x, 0) = |x|
#[test]
fn test_hypot_simd_identity_property() {
    let x = array![5.0_f64, -5.0, 0.0, std::f64::consts::PI];
    let zeros = Array1::zeros(4);

    let result = hypot_simd(&x.view(), &zeros.view());

    for i in 0..x.len() {
        assert!(
            (result[i] - x[i].abs()).abs() < 1e-14,
            "hypot(x, 0) should equal |x|"
        );
    }
}

/// Test hypot distance calculation use case
#[test]
fn test_hypot_simd_distance_calculation() {
    // Calculate distances from origin to various 2D points
    let points_x = array![1.0_f64, 1.0, 2.0, 3.0];
    let points_y = array![0.0_f64, 1.0, 2.0, 4.0];

    let distances = hypot_simd(&points_x.view(), &points_y.view());

    assert!((distances[0] - 1.0).abs() < 1e-14); // Point (1,0)
    assert!((distances[1] - std::f64::consts::SQRT_2).abs() < 1e-14); // Point (1,1)
    assert!((distances[2] - (2.0 * std::f64::consts::SQRT_2)).abs() < 1e-14); // Point (2,2)
    assert!((distances[3] - 5.0).abs() < 1e-14); // Point (3,4) -> 3-4-5 triangle
}

// ============================================================================
// Phase 62: SIMD copysign tests
// ============================================================================

/// Test copysign basic f32 correctness
#[test]
fn test_copysign_simd_f32_basic() {
    let x = array![1.0_f32, -2.0, 3.0, -4.0];
    let y = array![-1.0_f32, 1.0, 1.0, -1.0];

    let result = copysign_simd(&x.view(), &y.view());

    assert!((result[0] - (-1.0)).abs() < 1e-6); // |1| with sign of -1 = -1
    assert!((result[1] - 2.0).abs() < 1e-6); // |-2| with sign of 1 = 2
    assert!((result[2] - 3.0).abs() < 1e-6); // |3| with sign of 1 = 3
    assert!((result[3] - (-4.0)).abs() < 1e-6); // |-4| with sign of -1 = -4
}

/// Test copysign basic f64 correctness
#[test]
fn test_copysign_simd_f64_basic() {
    let x = array![1.0_f64, -2.0, 3.0, -4.0];
    let y = array![-1.0_f64, 1.0, 1.0, -1.0];

    let result = copysign_simd(&x.view(), &y.view());

    assert!((result[0] - (-1.0)).abs() < 1e-14);
    assert!((result[1] - 2.0).abs() < 1e-14);
    assert!((result[2] - 3.0).abs() < 1e-14);
    assert!((result[3] - (-4.0)).abs() < 1e-14);
}

/// Test copysign empty array
#[test]
fn test_copysign_simd_empty() {
    let x: Array1<f64> = array![];
    let y: Array1<f64> = array![];
    let result = copysign_simd(&x.view(), &y.view());
    assert_eq!(result.len(), 0);
}

/// Test copysign large array (SIMD path)
#[test]
fn test_copysign_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((0..n).map(|i| i as f64 + 1.0).collect());
    let y = Array1::from_vec(
        (0..n)
            .map(|i| if i % 2 == 0 { 1.0 } else { -1.0 })
            .collect(),
    );

    let result = copysign_simd(&x.view(), &y.view());
    assert_eq!(result.len(), n);

    // Check: even indices positive, odd indices negative
    for i in [0, 101, 1000, 5001, 9998] {
        if i % 2 == 0 {
            assert!(result[i] > 0.0, "Even index {} should be positive", i);
        } else {
            assert!(result[i] < 0.0, "Odd index {} should be negative", i);
        }
        assert!(
            (result[i].abs() - (i as f64 + 1.0)).abs() < 1e-10,
            "Magnitude should be preserved"
        );
    }
}

/// Test copysign with zeros
#[test]
fn test_copysign_simd_zeros() {
    let x = array![5.0_f64, 0.0, -3.0];
    let y = array![0.0_f64, -1.0, 0.0];

    let result = copysign_simd(&x.view(), &y.view());

    // Zero has positive sign in IEEE 754
    assert!((result[0] - 5.0).abs() < 1e-14); // 5 with sign of +0 = 5
                                              // copysign(0, -1) should be -0
    assert!(result[1] == 0.0 || result[1] == -0.0);
    assert!((result[2] - 3.0).abs() < 1e-14); // -3 with sign of +0 = 3
}

/// Test copysign property: |copysign(x, y)| = |x|
#[test]
fn test_copysign_simd_magnitude_preservation() {
    let x = array![1.5_f64, -2.5, 3.5, -4.5];
    let y = array![-1.0_f64, -1.0, 1.0, 1.0];

    let result = copysign_simd(&x.view(), &y.view());

    for i in 0..x.len() {
        assert!(
            (result[i].abs() - x[i].abs()).abs() < 1e-14,
            "copysign should preserve magnitude"
        );
    }
}

/// Test copysign property: sign(copysign(x, y)) = sign(y)
#[test]
fn test_copysign_simd_sign_transfer() {
    let x = array![1.0_f64, -2.0, 3.0, -4.0, 5.0];
    let y = array![-10.0_f64, 20.0, -30.0, 40.0, -50.0];

    let result = copysign_simd(&x.view(), &y.view());

    for i in 0..x.len() {
        let result_sign = if result[i] >= 0.0 { 1 } else { -1 };
        let y_sign = if y[i] >= 0.0 { 1 } else { -1 };
        assert_eq!(result_sign, y_sign, "Sign should match y at index {}", i);
    }
}

/// Test copysign use case: implementing absolute value
#[test]
fn test_copysign_simd_abs_implementation() {
    let x = array![-5.0_f64, 3.0, -2.0, 0.0, -0.0];
    let ones = array![1.0_f64, 1.0, 1.0, 1.0, 1.0];

    let result = copysign_simd(&x.view(), &ones.view());

    // copysign(x, 1) = |x|
    for i in 0..x.len() {
        assert!(
            (result[i] - x[i].abs()).abs() < 1e-14,
            "copysign(x, 1) should equal |x|"
        );
    }
}

/// Test copysign use case: implementing negation
#[test]
fn test_copysign_simd_negation_implementation() {
    let x = array![5.0_f64, -3.0, 2.0];
    let neg_ones = array![-1.0_f64, -1.0, -1.0];

    let result = copysign_simd(&x.view(), &neg_ones.view());

    // copysign(x, -1) = -|x|
    for i in 0..x.len() {
        assert!(
            (result[i] - (-x[i].abs())).abs() < 1e-14,
            "copysign(x, -1) should equal -|x|"
        );
    }
}

// ============================================================================
// Phase 63: SIMD smootherstep (Ken Perlin's improved smoothstep) tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::smootherstep_simd;

/// Test smootherstep basic f32 correctness
#[test]
fn test_smootherstep_simd_f32_basic() {
    let x = array![0.0_f32, 0.25, 0.5, 0.75, 1.0];

    let result = smootherstep_simd(0.0_f32, 1.0_f32, &x.view());

    // smootherstep(0) = 0
    assert!((result[0] - 0.0).abs() < 1e-6);
    // smootherstep(0.5) = 0.5 (symmetric about midpoint)
    assert!((result[2] - 0.5).abs() < 1e-6);
    // smootherstep(1) = 1
    assert!((result[4] - 1.0).abs() < 1e-6);

    // Values should be monotonically increasing
    for i in 0..result.len() - 1 {
        assert!(
            result[i] <= result[i + 1],
            "smootherstep should be monotonic"
        );
    }
}

/// Test smootherstep basic f64 correctness
#[test]
fn test_smootherstep_simd_f64_basic() {
    let x = array![0.0_f64, 0.25, 0.5, 0.75, 1.0];

    let result = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Verify the Perlin polynomial: 6t⁵ - 15t⁴ + 10t³
    for i in 0..x.len() {
        let t = x[i];
        let t3 = t * t * t;
        let expected = t3 * (t * (t * 6.0 - 15.0) + 10.0);
        assert!(
            (result[i] - expected).abs() < 1e-14,
            "smootherstep[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test smootherstep empty array
#[test]
fn test_smootherstep_simd_empty() {
    let x: Array1<f64> = array![];
    let result = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());
    assert_eq!(result.len(), 0);
}

/// Test smootherstep clamping at edges
#[test]
fn test_smootherstep_simd_clamping() {
    let x = array![-1.0_f64, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0];

    let result = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Values below edge0 should be 0
    assert!((result[0] - 0.0).abs() < 1e-14); // x = -1
    assert!((result[1] - 0.0).abs() < 1e-14); // x = -0.5
    assert!((result[2] - 0.0).abs() < 1e-14); // x = 0

    // Values above edge1 should be 1
    assert!((result[4] - 1.0).abs() < 1e-14); // x = 1
    assert!((result[5] - 1.0).abs() < 1e-14); // x = 1.5
    assert!((result[6] - 1.0).abs() < 1e-14); // x = 2
}

/// Test smootherstep large array (SIMD path)
#[test]
fn test_smootherstep_simd_large_array() {
    let n = 10000;
    let x = Array1::linspace(0.0, 1.0, n);

    let result = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());
    assert_eq!(result.len(), n);

    // Verify first, middle, and last values
    assert!((result[0] - 0.0).abs() < 1e-14);
    let mid = n / 2;
    let t_mid = x[mid];
    let t3 = t_mid * t_mid * t_mid;
    let expected_mid = t3 * (t_mid * (t_mid * 6.0 - 15.0) + 10.0);
    assert!((result[mid] - expected_mid).abs() < 1e-10);
    assert!((result[n - 1] - 1.0).abs() < 1e-14);
}

/// Test smootherstep property: first derivative at edges is zero
#[test]
fn test_smootherstep_simd_first_derivative_at_edges() {
    // The first derivative of 6t⁵ - 15t⁴ + 10t³ is 30t⁴ - 60t³ + 30t² = 30t²(t-1)²
    // At t=0 and t=1, the derivative is 0

    let eps = 1e-8_f64;
    let x_near_0 = array![0.0, eps];
    let x_near_1 = array![1.0 - eps, 1.0];

    let result_0 = smootherstep_simd(0.0_f64, 1.0_f64, &x_near_0.view());
    let result_1 = smootherstep_simd(0.0_f64, 1.0_f64, &x_near_1.view());

    // Derivative near 0 should be very small
    let deriv_near_0 = (result_0[1] - result_0[0]) / eps;
    assert!(
        deriv_near_0.abs() < 1e-5,
        "First derivative at edge0 should be near 0, got {}",
        deriv_near_0
    );

    // Derivative near 1 should be very small
    let deriv_near_1 = (result_1[1] - result_1[0]) / eps;
    assert!(
        deriv_near_1.abs() < 1e-5,
        "First derivative at edge1 should be near 0, got {}",
        deriv_near_1
    );
}

/// Test smootherstep property: second derivative at edges is zero
#[test]
fn test_smootherstep_simd_second_derivative_at_edges() {
    // The second derivative is 120t³ - 180t² + 60t = 60t(2t-1)(t-1)
    // At t=0 and t=1, the second derivative is 0

    let eps = 1e-6_f64;
    let x = array![0.0, eps, 2.0 * eps];

    let result = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Approximate second derivative at t=0 using central difference
    let d1 = (result[1] - result[0]) / eps;
    let d2 = (result[2] - result[1]) / eps;
    let second_deriv = (d2 - d1) / eps;

    assert!(
        second_deriv.abs() < 1e-2,
        "Second derivative at edge0 should be near 0, got {}",
        second_deriv
    );
}

/// Test smootherstep comparison with smoothstep (should be smoother)
#[test]
fn test_smootherstep_vs_smoothstep() {
    let x = array![0.0_f64, 0.25, 0.5, 0.75, 1.0];

    let result_smoother = smootherstep_simd(0.0_f64, 1.0_f64, &x.view());
    let result_smooth = smoothstep_simd(0.0_f64, 1.0_f64, &x.view());

    // Both should agree at 0, 0.5, and 1
    assert!((result_smoother[0] - result_smooth[0]).abs() < 1e-14);
    assert!((result_smoother[2] - result_smooth[2]).abs() < 1e-14);
    assert!((result_smoother[4] - result_smooth[4]).abs() < 1e-14);

    // At t=0.25 and t=0.75, smootherstep differs from smoothstep
    // smoothstep(0.25) = 3(0.0625) - 2(0.015625) = 0.1875 - 0.03125 = 0.15625
    // smootherstep(0.25) = 6(0.000976...) - 15(0.00390625) + 10(0.015625)
    //                    = 0.005859... - 0.058594... + 0.15625 ≈ 0.103516
    // They should be different
    assert!(
        (result_smoother[1] - result_smooth[1]).abs() > 0.01,
        "smootherstep and smoothstep should differ at t=0.25"
    );
}

/// Test smootherstep Perlin noise use case
#[test]
fn test_smootherstep_simd_perlin_noise_use_case() {
    // In Perlin noise, smootherstep is used for gradient interpolation
    // This tests the fade function behavior that Perlin noise expects

    let t_values = array![0.0_f64, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

    let fade_result = smootherstep_simd(0.0_f64, 1.0_f64, &t_values.view());

    // All values should be in [0, 1]
    for (i, &v) in fade_result.iter().enumerate() {
        assert!(
            (0.0..=1.0).contains(&v),
            "Perlin fade at t={} should be in [0,1], got {}",
            t_values[i],
            v
        );
    }

    // Should be strictly monotonically increasing (except at endpoints)
    for i in 1..fade_result.len() {
        assert!(
            fade_result[i] >= fade_result[i - 1],
            "Perlin fade should be monotonic"
        );
    }

    // The curve should be more "S-shaped" than linear
    // At t=0.5, smootherstep should equal exactly 0.5 (symmetry)
    assert!((fade_result[5] - 0.5).abs() < 1e-14);
}

// ============================================================================
// Phase 64-65: SIMD logaddexp and logit tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::logaddexp_simd;
use scirs2_core::ndarray_ext::elementwise::logit_simd;

/// Test logaddexp basic f32 correctness
#[test]
fn test_logaddexp_simd_f32_basic() {
    let a = array![0.0_f32, 1.0, 2.0, -1.0];
    let b = array![0.0_f32, 1.0, 2.0, 1.0];

    let result = logaddexp_simd(&a.view(), &b.view());

    // log(exp(0) + exp(0)) = log(2)
    assert!((result[0] - 2.0_f32.ln()).abs() < 1e-5);
    // log(exp(1) + exp(1)) = log(2) + 1
    assert!((result[1] - (2.0_f32.ln() + 1.0)).abs() < 1e-5);
    // log(exp(2) + exp(2)) = log(2) + 2
    assert!((result[2] - (2.0_f32.ln() + 2.0)).abs() < 1e-5);
}

/// Test logaddexp basic f64 correctness
#[test]
fn test_logaddexp_simd_f64_basic() {
    let a = array![0.0_f64, 1.0, 2.0, -1.0];
    let b = array![0.0_f64, 1.0, 2.0, 1.0];

    let result = logaddexp_simd(&a.view(), &b.view());

    // log(exp(0) + exp(0)) = log(2)
    assert!((result[0] - 2.0_f64.ln()).abs() < 1e-14);
    // log(exp(1) + exp(1)) = log(2) + 1
    assert!((result[1] - (2.0_f64.ln() + 1.0)).abs() < 1e-14);
    // log(exp(2) + exp(2)) = log(2) + 2
    assert!((result[2] - (2.0_f64.ln() + 2.0)).abs() < 1e-14);
}

/// Test logaddexp empty array
#[test]
fn test_logaddexp_simd_empty() {
    let a: Array1<f64> = array![];
    let b: Array1<f64> = array![];
    let result = logaddexp_simd(&a.view(), &b.view());
    assert_eq!(result.len(), 0);
}

/// Test logaddexp large array (SIMD path)
#[test]
fn test_logaddexp_simd_large_array() {
    let n = 10000;
    // Use smaller values to avoid exp() overflow in the naive verification
    let a = Array1::from_vec((0..n).map(|i| i as f64 * 0.01).collect());
    let b = Array1::from_vec((0..n).map(|i| i as f64 * 0.01 + 0.5).collect());

    let result = logaddexp_simd(&a.view(), &b.view());
    assert_eq!(result.len(), n);

    // Check a few values (keeping values small enough for naive exp())
    for i in [0, 100, 500, 1000] {
        let expected = (a[i].exp() + b[i].exp()).ln();
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "logaddexp[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }

    // For large indices, verify monotonicity and finiteness
    assert!(result[9999].is_finite());
    assert!(result[9999] > result[5000]);
}

/// Test logaddexp numerical stability with large values
#[test]
fn test_logaddexp_simd_large_values() {
    // Large positive values that would overflow with naive exp()
    let a = array![700.0_f64, 700.0, -700.0];
    let b = array![700.0_f64, 500.0, -500.0];

    let result = logaddexp_simd(&a.view(), &b.view());

    // All results should be finite
    for (i, &v) in result.iter().enumerate() {
        assert!(
            v.is_finite(),
            "logaddexp should handle large values, got {} at index {}",
            v,
            i
        );
    }

    // log(exp(700) + exp(700)) = 700 + log(2)
    assert!((result[0] - (700.0 + 2.0_f64.ln())).abs() < 1e-10);
    // log(exp(700) + exp(500)) ≈ 700 (dominated by larger term)
    assert!((result[1] - 700.0).abs() < 1e-10);
}

/// Test logaddexp property: logaddexp(a, a) = a + log(2)
#[test]
fn test_logaddexp_simd_equal_inputs() {
    let a = array![0.0_f64, 1.0, -1.0, 10.0, -10.0];

    let result = logaddexp_simd(&a.view(), &a.view());

    let ln2 = 2.0_f64.ln();
    for i in 0..a.len() {
        let expected = a[i] + ln2;
        assert!(
            (result[i] - expected).abs() < 1e-14,
            "logaddexp(a, a) should be a + log(2)"
        );
    }
}

/// Test logaddexp commutativity: logaddexp(a, b) = logaddexp(b, a)
#[test]
fn test_logaddexp_simd_commutativity() {
    let a = array![1.0_f64, 2.0, -3.0, 4.0];
    let b = array![5.0_f64, -2.0, 3.0, -4.0];

    let result_ab = logaddexp_simd(&a.view(), &b.view());
    let result_ba = logaddexp_simd(&b.view(), &a.view());

    for i in 0..a.len() {
        assert!(
            (result_ab[i] - result_ba[i]).abs() < 1e-14,
            "logaddexp should be commutative"
        );
    }
}

/// Test logaddexp log-probability use case
#[test]
fn test_logaddexp_simd_log_probability() {
    // In log-probability space, logaddexp combines probabilities
    // log(P(A or B)) = logaddexp(log(P(A)), log(P(B))) when A, B are mutually exclusive

    let log_p_a = array![-1.0_f64, -2.0, -3.0]; // P(A) = exp(-1), exp(-2), exp(-3)
    let log_p_b = array![-1.0_f64, -2.0, -3.0]; // P(B) = exp(-1), exp(-2), exp(-3)

    let log_p_union = logaddexp_simd(&log_p_a.view(), &log_p_b.view());

    // P(A or B) = 2 * P(A) when P(A) = P(B), so log(P) = log(2) + log(P(A))
    let ln2 = 2.0_f64.ln();
    for i in 0..log_p_a.len() {
        let expected = log_p_a[i] + ln2;
        assert!(
            (log_p_union[i] - expected).abs() < 1e-14,
            "Log-probability combination failed"
        );
    }
}

// ============================================================================
// Logit tests
// ============================================================================

/// Test logit basic f32 correctness
#[test]
fn test_logit_simd_f32_basic() {
    let p = array![0.5_f32, 0.1, 0.9, 0.01, 0.99];

    let result = logit_simd(&p.view());

    // logit(0.5) = log(1) = 0
    assert!((result[0] - 0.0).abs() < 1e-5);
    // logit(0.1) = log(0.1/0.9)
    assert!((result[1] - (0.1_f32 / 0.9).ln()).abs() < 1e-5);
    // logit(0.9) = log(0.9/0.1)
    assert!((result[2] - (0.9_f32 / 0.1).ln()).abs() < 1e-5);
}

/// Test logit basic f64 correctness
#[test]
fn test_logit_simd_f64_basic() {
    let p = array![0.5_f64, 0.1, 0.9, 0.01, 0.99];

    let result = logit_simd(&p.view());

    // logit(0.5) = log(1) = 0
    assert!((result[0] - 0.0).abs() < 1e-14);
    // logit(0.1) = log(0.1/0.9)
    assert!((result[1] - (0.1_f64 / 0.9).ln()).abs() < 1e-14);
    // logit(0.9) = log(0.9/0.1)
    assert!((result[2] - (0.9_f64 / 0.1).ln()).abs() < 1e-14);
}

/// Test logit empty array
#[test]
fn test_logit_simd_empty() {
    let p: Array1<f64> = array![];
    let result = logit_simd(&p.view());
    assert_eq!(result.len(), 0);
}

/// Test logit large array (SIMD path)
#[test]
fn test_logit_simd_large_array() {
    let n = 10000;
    // Generate probabilities in (0.01, 0.99) range
    let p = Array1::from_vec(
        (0..n)
            .map(|i| 0.01 + 0.98 * (i as f64 / n as f64))
            .collect(),
    );

    let result = logit_simd(&p.view());
    assert_eq!(result.len(), n);

    // Check a few values
    for i in [0, 100, 1000, 5000, 9999] {
        let expected = (p[i] / (1.0 - p[i])).ln();
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "logit[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test logit edge cases
#[test]
fn test_logit_simd_edge_cases() {
    let p = array![0.0_f64, 1.0];

    let result = logit_simd(&p.view());

    // logit(0) = -∞
    assert!(result[0].is_infinite() && result[0] < 0.0);
    // logit(1) = +∞
    assert!(result[1].is_infinite() && result[1] > 0.0);
}

/// Test logit symmetry: logit(p) = -logit(1-p)
#[test]
fn test_logit_simd_symmetry() {
    let p = array![0.1_f64, 0.2, 0.3, 0.4];
    let one_minus_p = p.mapv(|x| 1.0 - x);

    let result_p = logit_simd(&p.view());
    let result_1mp = logit_simd(&one_minus_p.view());

    for i in 0..p.len() {
        assert!(
            (result_p[i] + result_1mp[i]).abs() < 1e-14,
            "logit(p) + logit(1-p) should be 0"
        );
    }
}

/// Test logit as inverse of sigmoid
#[test]
fn test_logit_simd_inverse_of_sigmoid() {
    use scirs2_core::ndarray_ext::elementwise::sigmoid_simd;

    let p = array![0.1_f64, 0.3, 0.5, 0.7, 0.9];

    // logit(p) then sigmoid should return p
    let logit_p = logit_simd(&p.view());
    let sigmoid_logit_p = sigmoid_simd(&logit_p.view());

    for i in 0..p.len() {
        assert!(
            (sigmoid_logit_p[i] - p[i]).abs() < 1e-14,
            "sigmoid(logit(p)) should equal p"
        );
    }
}

/// Test logit logistic regression use case
#[test]
fn test_logit_simd_logistic_regression() {
    // In logistic regression, we model log-odds = β₀ + β₁x₁ + ...
    // Converting predicted probabilities to log-odds should give linear values

    // Simulating probabilities from a logistic model with linear log-odds
    let true_log_odds = array![-2.0_f64, -1.0, 0.0, 1.0, 2.0];
    let probabilities = true_log_odds.mapv(|lo| 1.0 / (1.0 + (-lo).exp()));

    let recovered_log_odds = logit_simd(&probabilities.view());

    for i in 0..true_log_odds.len() {
        assert!(
            (recovered_log_odds[i] - true_log_odds[i]).abs() < 1e-14,
            "Logit should recover log-odds from probabilities"
        );
    }
}

// ============================================================================
// Phase 66-67: SIMD square, rsqrt, sincos tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::rsqrt_simd;
use scirs2_core::ndarray_ext::elementwise::sincos_simd;
use scirs2_core::ndarray_ext::elementwise::square_simd;
use std::f64::consts::PI;

// ============================================================================
// Square tests
// ============================================================================

/// Test square basic f32 correctness
#[test]
fn test_square_simd_f32_basic() {
    let x = array![1.0_f32, 2.0, 3.0, -4.0, 0.5];

    let result = square_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-6); // 1² = 1
    assert!((result[1] - 4.0).abs() < 1e-6); // 2² = 4
    assert!((result[2] - 9.0).abs() < 1e-6); // 3² = 9
    assert!((result[3] - 16.0).abs() < 1e-6); // (-4)² = 16
    assert!((result[4] - 0.25).abs() < 1e-6); // 0.5² = 0.25
}

/// Test square basic f64 correctness
#[test]
fn test_square_simd_f64_basic() {
    let x = array![1.0_f64, 2.0, 3.0, -4.0, 0.5];

    let result = square_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-14); // 1² = 1
    assert!((result[1] - 4.0).abs() < 1e-14); // 2² = 4
    assert!((result[2] - 9.0).abs() < 1e-14); // 3² = 9
    assert!((result[3] - 16.0).abs() < 1e-14); // (-4)² = 16
    assert!((result[4] - 0.25).abs() < 1e-14); // 0.5² = 0.25
}

/// Test square empty array
#[test]
fn test_square_simd_empty() {
    let x: Array1<f64> = array![];
    let result = square_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test square large array (SIMD path)
#[test]
fn test_square_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((0..n).map(|i| (i as f64 - 5000.0) * 0.01).collect());

    let result = square_simd(&x.view());
    assert_eq!(result.len(), n);

    // Check a few values
    for i in [0, 100, 5000, 9999] {
        let expected = x[i] * x[i];
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "square[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test square special values
#[test]
fn test_square_simd_special_values() {
    let x = array![0.0_f64, -0.0, f64::INFINITY, f64::NEG_INFINITY];

    let result = square_simd(&x.view());

    // 0² = 0
    assert_eq!(result[0], 0.0);
    // (-0)² = 0
    assert_eq!(result[1], 0.0);
    // ∞² = ∞
    assert!(result[2].is_infinite() && result[2] > 0.0);
    // (-∞)² = ∞
    assert!(result[3].is_infinite() && result[3] > 0.0);
}

/// Test square always non-negative
#[test]
fn test_square_simd_non_negative() {
    let x = array![-10.0_f64, -5.0, -1.0, -0.1, 0.0, 0.1, 1.0, 5.0, 10.0];

    let result = square_simd(&x.view());

    for (i, &v) in result.iter().enumerate() {
        assert!(
            v >= 0.0,
            "square should always be non-negative, got {} at index {}",
            v,
            i
        );
    }
}

/// Test square vs pow comparison
#[test]
fn test_square_simd_vs_pow() {
    let x = array![1.5_f64, 2.5, 3.5, -4.5, 0.5];

    let result = square_simd(&x.view());
    let pow_result = x.mapv(|v| v.powf(2.0));

    for i in 0..x.len() {
        assert!(
            (result[i] - pow_result[i]).abs() < 1e-14,
            "square should match pow(x, 2)"
        );
    }
}

/// Test square MSE use case
#[test]
fn test_square_simd_mse_use_case() {
    // Computing Mean Squared Error: sum((y - y_hat)²) / n
    let y_true = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];
    let y_pred = array![1.1_f64, 2.2, 2.9, 4.1, 4.9];

    let errors = &y_true - &y_pred;
    let squared_errors = square_simd(&errors.view());
    let mse = squared_errors.sum() / y_true.len() as f64;

    // Manual calculation: (0.1² + 0.2² + 0.1² + 0.1² + 0.1²) / 5 = 0.08 / 5 = 0.016
    let expected_mse = (0.01 + 0.04 + 0.01 + 0.01 + 0.01) / 5.0;
    assert!((mse - expected_mse).abs() < 1e-10, "MSE calculation failed");
}

// ============================================================================
// Rsqrt tests
// ============================================================================

/// Test rsqrt basic f32 correctness
#[test]
fn test_rsqrt_simd_f32_basic() {
    let x = array![1.0_f32, 4.0, 9.0, 16.0, 25.0];

    let result = rsqrt_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-6); // 1/sqrt(1) = 1
    assert!((result[1] - 0.5).abs() < 1e-6); // 1/sqrt(4) = 0.5
    assert!((result[2] - 1.0 / 3.0).abs() < 1e-6); // 1/sqrt(9) = 1/3
    assert!((result[3] - 0.25).abs() < 1e-6); // 1/sqrt(16) = 0.25
    assert!((result[4] - 0.2).abs() < 1e-6); // 1/sqrt(25) = 0.2
}

/// Test rsqrt basic f64 correctness
#[test]
fn test_rsqrt_simd_f64_basic() {
    let x = array![1.0_f64, 4.0, 9.0, 16.0, 25.0];

    let result = rsqrt_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-14); // 1/sqrt(1) = 1
    assert!((result[1] - 0.5).abs() < 1e-14); // 1/sqrt(4) = 0.5
    assert!((result[2] - 1.0 / 3.0).abs() < 1e-14); // 1/sqrt(9) = 1/3
    assert!((result[3] - 0.25).abs() < 1e-14); // 1/sqrt(16) = 0.25
    assert!((result[4] - 0.2).abs() < 1e-14); // 1/sqrt(25) = 0.2
}

/// Test rsqrt empty array
#[test]
fn test_rsqrt_simd_empty() {
    let x: Array1<f64> = array![];
    let result = rsqrt_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test rsqrt large array (SIMD path)
#[test]
fn test_rsqrt_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((1..=n).map(|i| i as f64).collect());

    let result = rsqrt_simd(&x.view());
    assert_eq!(result.len(), n);

    // Check a few values
    for i in [0, 99, 999, 9999] {
        let expected = 1.0 / x[i].sqrt();
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "rsqrt[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test rsqrt special values
#[test]
fn test_rsqrt_simd_special_values() {
    let x = array![0.0_f64, -1.0, f64::INFINITY];

    let result = rsqrt_simd(&x.view());

    // 1/sqrt(0) = ∞
    assert!(result[0].is_infinite() && result[0] > 0.0);
    // 1/sqrt(-1) = NaN
    assert!(result[1].is_nan());
    // 1/sqrt(∞) = 0
    assert_eq!(result[2], 0.0);
}

/// Test rsqrt identity: x * rsqrt(x)² = 1
#[test]
fn test_rsqrt_simd_identity() {
    let x = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];

    let rsqrt_x = rsqrt_simd(&x.view());

    for i in 0..x.len() {
        let product = x[i] * rsqrt_x[i] * rsqrt_x[i];
        assert!(
            (product - 1.0).abs() < 1e-14,
            "x * rsqrt(x)² should be 1, got {}",
            product
        );
    }
}

/// Test rsqrt vs 1/sqrt comparison
#[test]
fn test_rsqrt_simd_vs_one_over_sqrt() {
    let x = array![0.5_f64, 1.5, 2.5, 3.5, 4.5];

    let result = rsqrt_simd(&x.view());
    let manual = x.mapv(|v| 1.0 / v.sqrt());

    for i in 0..x.len() {
        assert!(
            (result[i] - manual[i]).abs() < 1e-14,
            "rsqrt should match 1/sqrt"
        );
    }
}

/// Test rsqrt vector normalization use case
#[test]
fn test_rsqrt_simd_vector_normalization() {
    // Vector normalization: v_normalized = v * rsqrt(dot(v, v))
    // This is the primary use case in graphics

    // 3D vectors
    let vx = array![3.0_f64, 1.0, 0.0];
    let vy = array![4.0_f64, 1.0, 1.0];
    let vz = array![0.0_f64, 1.0, 0.0];

    // Compute squared magnitudes
    let mag_squared = &vx * &vx + &vy * &vy + &vz * &vz;
    // Get inverse magnitudes
    let inv_mag = rsqrt_simd(&mag_squared.view());

    // Normalize
    let nx = &vx * &inv_mag;
    let ny = &vy * &inv_mag;
    let nz = &vz * &inv_mag;

    // Check normalized vector magnitudes are 1
    for i in 0..vx.len() {
        let norm = (nx[i] * nx[i] + ny[i] * ny[i] + nz[i] * nz[i]).sqrt();
        assert!(
            (norm - 1.0).abs() < 1e-14,
            "Normalized vector magnitude should be 1, got {}",
            norm
        );
    }
}

/// Test rsqrt quaternion normalization use case
#[test]
fn test_rsqrt_simd_quaternion_normalization() {
    // Quaternion normalization: q / |q|
    // Given q = (w, x, y, z), |q|² = w² + x² + y² + z²

    let w = array![1.0_f64, 0.5, 0.707];
    let x = array![0.0_f64, 0.5, 0.0];
    let y = array![0.0_f64, 0.5, 0.707];
    let z = array![0.0_f64, 0.5, 0.0];

    let mag_squared = &w * &w + &x * &x + &y * &y + &z * &z;
    let inv_mag = rsqrt_simd(&mag_squared.view());

    let nw = &w * &inv_mag;
    let nx = &x * &inv_mag;
    let ny = &y * &inv_mag;
    let nz = &z * &inv_mag;

    // Check normalized quaternion magnitudes are 1
    for i in 0..w.len() {
        let norm_sq = nw[i] * nw[i] + nx[i] * nx[i] + ny[i] * ny[i] + nz[i] * nz[i];
        assert!(
            (norm_sq - 1.0).abs() < 1e-14,
            "Normalized quaternion magnitude² should be 1, got {}",
            norm_sq
        );
    }
}

// ============================================================================
// Sincos tests
// ============================================================================

/// Test sincos basic f32 correctness
#[test]
fn test_sincos_simd_f32_basic() {
    let x = array![
        0.0_f32,
        PI as f32 / 6.0,
        PI as f32 / 4.0,
        PI as f32 / 2.0,
        PI as f32
    ];

    let (sin_result, cos_result) = sincos_simd(&x.view());

    // sin(0) = 0, cos(0) = 1
    assert!(sin_result[0].abs() < 1e-6);
    assert!((cos_result[0] - 1.0).abs() < 1e-6);
    // sin(π/6) = 0.5, cos(π/6) = √3/2
    assert!((sin_result[1] - 0.5).abs() < 1e-5);
    // sin(π/4) = cos(π/4) = √2/2
    let sqrt2_2 = std::f32::consts::FRAC_1_SQRT_2;
    assert!((sin_result[2] - sqrt2_2).abs() < 1e-5);
    assert!((cos_result[2] - sqrt2_2).abs() < 1e-5);
    // sin(π/2) = 1, cos(π/2) = 0
    assert!((sin_result[3] - 1.0).abs() < 1e-5);
    assert!(cos_result[3].abs() < 1e-5);
}

/// Test sincos basic f64 correctness
#[test]
fn test_sincos_simd_f64_basic() {
    let x = array![0.0_f64, PI / 6.0, PI / 4.0, PI / 2.0, PI];

    let (sin_result, cos_result) = sincos_simd(&x.view());

    // sin(0) = 0, cos(0) = 1
    assert!(sin_result[0].abs() < 1e-14);
    assert!((cos_result[0] - 1.0).abs() < 1e-14);
    // sin(π/6) = 0.5
    assert!((sin_result[1] - 0.5).abs() < 1e-14);
    // sin(π/4) = cos(π/4) = √2/2
    let sqrt2_2 = std::f64::consts::FRAC_1_SQRT_2;
    assert!((sin_result[2] - sqrt2_2).abs() < 1e-14);
    assert!((cos_result[2] - sqrt2_2).abs() < 1e-14);
    // sin(π/2) = 1, cos(π/2) ≈ 0
    assert!((sin_result[3] - 1.0).abs() < 1e-14);
    assert!(cos_result[3].abs() < 1e-14);
    // sin(π) ≈ 0, cos(π) = -1
    assert!(sin_result[4].abs() < 1e-14);
    assert!((cos_result[4] + 1.0).abs() < 1e-14);
}

/// Test sincos empty array
#[test]
fn test_sincos_simd_empty() {
    let x: Array1<f64> = array![];
    let (sin_result, cos_result) = sincos_simd(&x.view());
    assert_eq!(sin_result.len(), 0);
    assert_eq!(cos_result.len(), 0);
}

/// Test sincos large array (SIMD path)
#[test]
fn test_sincos_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((0..n).map(|i| i as f64 * 0.01).collect());

    let (sin_result, cos_result) = sincos_simd(&x.view());
    assert_eq!(sin_result.len(), n);
    assert_eq!(cos_result.len(), n);

    // Check a few values
    for i in [0, 100, 1000, 5000, 9999] {
        let expected_sin = x[i].sin();
        let expected_cos = x[i].cos();
        assert!(
            (sin_result[i] - expected_sin).abs() < 1e-10,
            "sin[{}] = {}, expected {}",
            i,
            sin_result[i],
            expected_sin
        );
        assert!(
            (cos_result[i] - expected_cos).abs() < 1e-10,
            "cos[{}] = {}, expected {}",
            i,
            cos_result[i],
            expected_cos
        );
    }
}

/// Test sincos Pythagorean identity: sin²(x) + cos²(x) = 1
#[test]
fn test_sincos_simd_pythagorean_identity() {
    let x = array![0.0_f64, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, PI, 2.0 * PI];

    let (sin_result, cos_result) = sincos_simd(&x.view());

    for i in 0..x.len() {
        let sum_sq = sin_result[i] * sin_result[i] + cos_result[i] * cos_result[i];
        assert!(
            (sum_sq - 1.0).abs() < 1e-14,
            "sin²(x) + cos²(x) should be 1, got {} at x={}",
            sum_sq,
            x[i]
        );
    }
}

/// Test sincos consistency with separate sin/cos
#[test]
fn test_sincos_simd_consistency() {
    use scirs2_core::ndarray_ext::elementwise::{cos_simd, sin_simd};

    let x = array![0.1_f64, 0.5, 1.0, 2.0, 3.0];

    let (sin_result, cos_result) = sincos_simd(&x.view());
    let sin_separate = sin_simd(&x.view());
    let cos_separate = cos_simd(&x.view());

    for i in 0..x.len() {
        assert!(
            (sin_result[i] - sin_separate[i]).abs() < 1e-14,
            "sincos sin should match sin_simd"
        );
        assert!(
            (cos_result[i] - cos_separate[i]).abs() < 1e-14,
            "sincos cos should match cos_simd"
        );
    }
}

/// Test sincos rotation matrix use case
#[test]
fn test_sincos_simd_rotation_matrix() {
    // 2D rotation matrix: [[cos(θ), -sin(θ)], [sin(θ), cos(θ)]]
    // Rotating point (1, 0) by various angles

    let angles = array![0.0_f64, PI / 4.0, PI / 2.0, PI, 3.0 * PI / 2.0];
    let (sin_theta, cos_theta) = sincos_simd(&angles.view());

    // Point (1, 0) rotated by θ should be at (cos(θ), sin(θ))
    let px = 1.0_f64;
    let py = 0.0_f64;

    for i in 0..angles.len() {
        let rx = cos_theta[i] * px - sin_theta[i] * py;
        let ry = sin_theta[i] * px + cos_theta[i] * py;

        // After rotation, point should be at (cos(θ), sin(θ))
        assert!(
            (rx - cos_theta[i]).abs() < 1e-14,
            "Rotated x should be cos(θ)"
        );
        assert!(
            (ry - sin_theta[i]).abs() < 1e-14,
            "Rotated y should be sin(θ)"
        );

        // Distance from origin should remain 1
        let dist = (rx * rx + ry * ry).sqrt();
        assert!(
            (dist - 1.0).abs() < 1e-14,
            "Rotation should preserve distance from origin"
        );
    }
}

/// Test sincos complex exponential: e^(iθ) = cos(θ) + i*sin(θ)
#[test]
fn test_sincos_simd_euler_formula() {
    // Euler's formula: e^(iθ) = cos(θ) + i*sin(θ)
    // |e^(iθ)| = sqrt(cos²(θ) + sin²(θ)) = 1

    let theta = array![0.0_f64, PI / 4.0, PI / 2.0, PI, 2.0 * PI];
    let (sin_theta, cos_theta) = sincos_simd(&theta.view());

    for i in 0..theta.len() {
        // Magnitude of complex exponential
        let magnitude = (cos_theta[i] * cos_theta[i] + sin_theta[i] * sin_theta[i]).sqrt();
        assert!(
            (magnitude - 1.0).abs() < 1e-14,
            "Complex exponential magnitude should be 1"
        );
    }
}

/// Test sincos wave simulation use case
#[test]
fn test_sincos_simd_wave_simulation() {
    // Simulating a wave: y(t) = A * sin(ωt + φ)
    // Velocity: v(t) = A * ω * cos(ωt + φ)
    // Both need sin and cos

    let amplitude = 2.0_f64;
    let omega = 3.0_f64;
    let phase = PI / 4.0;

    let t = array![0.0_f64, 0.1, 0.2, 0.3, 0.4, 0.5];
    let omega_t_plus_phi = t.mapv(|ti| omega * ti + phase);

    let (sin_result, cos_result) = sincos_simd(&omega_t_plus_phi.view());

    let position = sin_result.mapv(|s| amplitude * s);
    let velocity = cos_result.mapv(|c| amplitude * omega * c);

    // At t=0: position = A*sin(φ), velocity = A*ω*cos(φ)
    let expected_pos_0 = amplitude * (omega * 0.0 + phase).sin();
    let expected_vel_0 = amplitude * omega * (omega * 0.0 + phase).cos();

    assert!((position[0] - expected_pos_0).abs() < 1e-14);
    assert!((velocity[0] - expected_vel_0).abs() < 1e-14);
}

/// Test sincos Fourier transform building block
#[test]
fn test_sincos_simd_fourier_basis() {
    // DFT basis functions: e^(-2πi*k*n/N) = cos(2πkn/N) - i*sin(2πkn/N)
    // For N=8, k=1, compute basis function at each n

    let n = 8;
    let k = 1.0_f64;
    let two_pi_k_over_n = 2.0 * PI * k / (n as f64);

    let indices: Array1<f64> = Array1::from_vec((0..n).map(|i| i as f64).collect());
    let angles = indices.mapv(|i| two_pi_k_over_n * i);

    let (sin_result, cos_result) = sincos_simd(&angles.view());

    // Verify orthogonality property: sum over n should be 0 for k != 0
    let real_sum: f64 = cos_result.iter().sum();
    let imag_sum: f64 = sin_result.iter().sum();

    assert!(
        real_sum.abs() < 1e-14,
        "Sum of cos(2πk*n/N) over n should be 0 for k != 0"
    );
    assert!(
        imag_sum.abs() < 1e-14,
        "Sum of sin(2πk*n/N) over n should be 0 for k != 0"
    );
}

// ============================================================================
// Phase 68: SIMD expm1 and log1p tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::expm1_simd;
use scirs2_core::ndarray_ext::elementwise::log1p_simd;

// ============================================================================
// expm1 tests
// ============================================================================

/// Test expm1 basic f32 correctness
#[test]
fn test_expm1_simd_f32_basic() {
    let x = array![0.0_f32, 1.0, -1.0, 2.0];

    let result = expm1_simd(&x.view());

    // exp(0) - 1 = 0
    assert!((result[0] - 0.0).abs() < 1e-6);
    // exp(1) - 1 ≈ 1.718
    assert!((result[1] - (1.0_f32.exp() - 1.0)).abs() < 1e-5);
    // exp(-1) - 1 ≈ -0.632
    assert!((result[2] - ((-1.0_f32).exp() - 1.0)).abs() < 1e-5);
}

/// Test expm1 basic f64 correctness
#[test]
fn test_expm1_simd_f64_basic() {
    let x = array![0.0_f64, 1.0, -1.0, 2.0];

    let result = expm1_simd(&x.view());

    // exp(0) - 1 = 0
    assert!((result[0] - 0.0).abs() < 1e-14);
    // exp(1) - 1 ≈ 1.718
    assert!((result[1] - (1.0_f64.exp() - 1.0)).abs() < 1e-14);
    // exp(-1) - 1 ≈ -0.632
    assert!((result[2] - ((-1.0_f64).exp() - 1.0)).abs() < 1e-14);
}

/// Test expm1 empty array
#[test]
fn test_expm1_simd_empty() {
    let x: Array1<f64> = array![];
    let result = expm1_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test expm1 large array (SIMD path)
#[test]
fn test_expm1_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((0..n).map(|i| (i as f64 - 5000.0) * 0.001).collect());

    let result = expm1_simd(&x.view());
    assert_eq!(result.len(), n);

    // Check a few values
    for i in [0, 100, 5000, 9999] {
        let expected = x[i].exp_m1();
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "expm1[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test expm1 numerical stability for small values
#[test]
fn test_expm1_simd_small_values() {
    // For very small x, exp(x) - 1 ≈ x (first term of Taylor series)
    // Direct calculation exp(x) - 1 would lose precision here

    let x = array![1e-15_f64, 1e-14, 1e-13, 1e-12, 1e-10];

    let result = expm1_simd(&x.view());

    // For very small x, expm1(x) ≈ x with high precision
    for i in 0..x.len() {
        // The relative error should be very small
        let rel_error = if x[i].abs() > 1e-20 {
            (result[i] - x[i]).abs() / x[i].abs()
        } else {
            (result[i] - x[i]).abs()
        };
        assert!(
            rel_error < 1e-10,
            "expm1 should be numerically stable for small x, relative error = {} at x = {}",
            rel_error,
            x[i]
        );
    }
}

/// Test expm1 vs naive exp(x) - 1 comparison for small values
#[test]
fn test_expm1_simd_vs_naive_small() {
    // This demonstrates the numerical advantage of expm1 over exp(x) - 1

    let x = array![1e-16_f64];
    let result = expm1_simd(&x.view());

    // Naive calculation would give 0 due to floating point precision loss
    let naive = x[0].exp() - 1.0;

    // expm1 should preserve precision
    // For x = 1e-16, expm1(x) should be approximately 1e-16
    // while naive exp(x) - 1 = 0 (precision loss)
    assert!(
        (result[0] - x[0]).abs() < 1e-30,
        "expm1 should preserve precision for tiny values"
    );
    // The naive calculation has lost precision
    assert_eq!(naive, 0.0, "naive exp(x)-1 loses precision for tiny x");
}

/// Test expm1 identity: expm1(-x) = -expm1(x) / (1 + expm1(x))
#[test]
fn test_expm1_simd_identity() {
    let x = array![0.5_f64, 1.0, 1.5, 2.0];

    let result_pos = expm1_simd(&x.view());
    let neg_x = x.mapv(|v| -v);
    let result_neg = expm1_simd(&neg_x.view());

    // expm1(-x) = -expm1(x) / (1 + expm1(x)) = -expm1(x) / exp(x)
    for i in 0..x.len() {
        let expected_neg = -result_pos[i] / (1.0 + result_pos[i]);
        assert!(
            (result_neg[i] - expected_neg).abs() < 1e-14,
            "expm1(-x) identity failed at x = {}",
            x[i]
        );
    }
}

/// Test expm1 financial compound interest use case
#[test]
fn test_expm1_simd_compound_interest() {
    // Continuous compound interest: A = P * e^(rt)
    // Interest earned = P * (e^(rt) - 1) = P * expm1(rt)
    // For small rates, this is critical for accuracy

    let principal = 10000.0_f64;
    let rate = 0.0001_f64; // 0.01% daily rate
    let time = 1.0_f64; // 1 day

    let rt = array![rate * time];
    let growth_factor = expm1_simd(&rt.view());
    let interest = principal * growth_factor[0];

    // For small rates: interest ≈ P * r * t (simple interest approximation)
    let simple_interest = principal * rate * time;

    // The difference between compound and simple interest is very small:
    // compound_interest - simple_interest ≈ P * r² * t² / 2 = 10000 * 1e-8 / 2 = 5e-5
    // So the interest should be very close to simple interest
    let diff = (interest - simple_interest).abs();
    assert!(
        diff < 1e-3,
        "expm1 preserves precision for small compound interest calculations, diff = {}",
        diff
    );

    // Also verify the compound interest is slightly higher than simple interest
    // (due to compounding effect)
    assert!(
        interest >= simple_interest,
        "Compound interest should be >= simple interest"
    );
}

// ============================================================================
// log1p tests
// ============================================================================

/// Test log1p basic f32 correctness
#[test]
fn test_log1p_simd_f32_basic() {
    let x = array![0.0_f32, 1.0, -0.5, 3.0];

    let result = log1p_simd(&x.view());

    // ln(1 + 0) = 0
    assert!((result[0] - 0.0).abs() < 1e-6);
    // ln(1 + 1) = ln(2)
    assert!((result[1] - 2.0_f32.ln()).abs() < 1e-6);
    // ln(1 + (-0.5)) = ln(0.5)
    assert!((result[2] - 0.5_f32.ln()).abs() < 1e-6);
}

/// Test log1p basic f64 correctness
#[test]
fn test_log1p_simd_f64_basic() {
    let x = array![0.0_f64, 1.0, -0.5, 3.0];

    let result = log1p_simd(&x.view());

    // ln(1 + 0) = 0
    assert!((result[0] - 0.0).abs() < 1e-14);
    // ln(1 + 1) = ln(2)
    assert!((result[1] - 2.0_f64.ln()).abs() < 1e-14);
    // ln(1 + (-0.5)) = ln(0.5)
    assert!((result[2] - 0.5_f64.ln()).abs() < 1e-14);
}

/// Test log1p empty array
#[test]
fn test_log1p_simd_empty() {
    let x: Array1<f64> = array![];
    let result = log1p_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test log1p large array (SIMD path)
#[test]
fn test_log1p_simd_large_array() {
    let n = 10000;
    // Use values in (-0.9, 10) to avoid ln of negative numbers
    let x = Array1::from_vec(
        (0..n)
            .map(|i| -0.9 + (i as f64 * 11.0 / n as f64))
            .collect(),
    );

    let result = log1p_simd(&x.view());
    assert_eq!(result.len(), n);

    // Check a few values
    for i in [0, 100, 5000, 9999] {
        let expected = x[i].ln_1p();
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "log1p[{}] = {}, expected {}",
            i,
            result[i],
            expected
        );
    }
}

/// Test log1p numerical stability for small values
#[test]
fn test_log1p_simd_small_values() {
    // For very small x, ln(1 + x) ≈ x (first term of Taylor series)
    // Direct calculation ln(1 + x) would lose precision here

    let x = array![1e-15_f64, 1e-14, 1e-13, 1e-12, 1e-10];

    let result = log1p_simd(&x.view());

    // For very small x, log1p(x) ≈ x with high precision
    for i in 0..x.len() {
        let rel_error = if x[i].abs() > 1e-20 {
            (result[i] - x[i]).abs() / x[i].abs()
        } else {
            (result[i] - x[i]).abs()
        };
        assert!(
            rel_error < 1e-10,
            "log1p should be numerically stable for small x, relative error = {} at x = {}",
            rel_error,
            x[i]
        );
    }
}

/// Test log1p vs naive ln(1 + x) comparison for small values
#[test]
fn test_log1p_simd_vs_naive_small() {
    // This demonstrates the numerical advantage of log1p over ln(1 + x)

    let x = array![1e-16_f64];
    let result = log1p_simd(&x.view());

    // Naive calculation would give 0 due to floating point precision loss
    let naive = (1.0 + x[0]).ln();

    // log1p should preserve precision
    // For x = 1e-16, log1p(x) should be approximately 1e-16
    // while naive ln(1 + x) = 0 (precision loss because 1 + 1e-16 = 1 in f64)
    assert!(
        (result[0] - x[0]).abs() < 1e-30,
        "log1p should preserve precision for tiny values"
    );
    assert_eq!(naive, 0.0, "naive ln(1+x) loses precision for tiny x");
}

/// Test log1p edge cases
#[test]
fn test_log1p_simd_edge_cases() {
    let x = array![-1.0_f64, -2.0];

    let result = log1p_simd(&x.view());

    // ln(1 + (-1)) = ln(0) = -∞
    assert!(result[0].is_infinite() && result[0] < 0.0);
    // ln(1 + (-2)) = ln(-1) = NaN
    assert!(result[1].is_nan());
}

/// Test log1p identity: log1p(x) + log1p(y) = log1p(x + y + xy)
#[test]
fn test_log1p_simd_addition_identity() {
    // log(a) + log(b) = log(ab)
    // log1p(x) + log1p(y) = ln(1+x) + ln(1+y) = ln((1+x)(1+y)) = ln(1 + x + y + xy)
    // = log1p(x + y + xy)

    let x = array![0.1_f64, 0.2, 0.3, 0.5];
    let y = array![0.2_f64, 0.3, 0.1, 0.5];

    let log1p_x = log1p_simd(&x.view());
    let log1p_y = log1p_simd(&y.view());

    let combined = x
        .iter()
        .zip(y.iter())
        .map(|(&xi, &yi)| xi + yi + xi * yi)
        .collect::<Vec<_>>();
    let combined_arr = Array1::from_vec(combined);
    let log1p_combined = log1p_simd(&combined_arr.view());

    for i in 0..x.len() {
        let sum = log1p_x[i] + log1p_y[i];
        assert!(
            (sum - log1p_combined[i]).abs() < 1e-14,
            "log1p addition identity failed at i = {}",
            i
        );
    }
}

/// Test log1p inverse relationship with expm1
#[test]
fn test_log1p_simd_inverse_of_expm1() {
    // log1p(expm1(x)) = x for any x
    // expm1(log1p(x)) = x for x > -1

    let x = array![0.1_f64, 0.5, 1.0, 2.0, -0.5];

    let expm1_x = expm1_simd(&x.view());
    let log1p_expm1_x = log1p_simd(&expm1_x.view());

    for i in 0..x.len() {
        assert!(
            (log1p_expm1_x[i] - x[i]).abs() < 1e-14,
            "log1p(expm1(x)) should equal x"
        );
    }

    // Also test expm1(log1p(x)) = x
    let log1p_x = log1p_simd(&x.view());
    let expm1_log1p_x = expm1_simd(&log1p_x.view());

    for i in 0..x.len() {
        assert!(
            (expm1_log1p_x[i] - x[i]).abs() < 1e-14,
            "expm1(log1p(x)) should equal x"
        );
    }
}

/// Test log1p binary cross-entropy use case
#[test]
fn test_log1p_simd_cross_entropy() {
    // Binary cross-entropy: -y*log(p) - (1-y)*log(1-p)
    // When p is very close to 0 or 1, we need log1p for stability
    // log(1-p) = log1p(-p)

    let p = array![0.99999_f64, 0.9999, 0.999]; // p close to 1
    let neg_p = p.mapv(|v| -v);

    let log_1_minus_p = log1p_simd(&neg_p.view());

    // For p close to 1, log(1-p) should be a large negative number
    for (i, &v) in log_1_minus_p.iter().enumerate() {
        assert!(
            v < 0.0,
            "log(1-p) should be negative for p close to 1, got {} at index {}",
            v,
            i
        );
        assert!(v.is_finite(), "log(1-p) should be finite for p < 1");
    }
}

// ============================================================================
// Phase 69: SIMD clip, cumsum, cumprod, diff tests
// ============================================================================

use scirs2_core::ndarray_ext::elementwise::clip_simd;
use scirs2_core::ndarray_ext::elementwise::cumprod_simd;
use scirs2_core::ndarray_ext::elementwise::cumsum_simd;
use scirs2_core::ndarray_ext::elementwise::diff_simd;

// ============================================================================
// clip tests
// ============================================================================

/// Test clip basic f32 correctness
#[test]
fn test_clip_simd_f32_basic() {
    let x = array![-2.0_f32, -1.0, 0.0, 1.0, 2.0, 3.0];

    let result = clip_simd(&x.view(), 0.0, 1.0);

    assert!((result[0] - 0.0).abs() < 1e-6); // -2 clipped to 0
    assert!((result[1] - 0.0).abs() < 1e-6); // -1 clipped to 0
    assert!((result[2] - 0.0).abs() < 1e-6); // 0 unchanged
    assert!((result[3] - 1.0).abs() < 1e-6); // 1 unchanged
    assert!((result[4] - 1.0).abs() < 1e-6); // 2 clipped to 1
    assert!((result[5] - 1.0).abs() < 1e-6); // 3 clipped to 1
}

/// Test clip basic f64 correctness
#[test]
fn test_clip_simd_f64_basic() {
    let x = array![-2.0_f64, -1.0, 0.0, 1.0, 2.0, 3.0];

    let result = clip_simd(&x.view(), 0.0, 1.0);

    assert!((result[0] - 0.0).abs() < 1e-14); // -2 clipped to 0
    assert!((result[1] - 0.0).abs() < 1e-14); // -1 clipped to 0
    assert!((result[2] - 0.0).abs() < 1e-14); // 0 unchanged
    assert!((result[3] - 1.0).abs() < 1e-14); // 1 unchanged
    assert!((result[4] - 1.0).abs() < 1e-14); // 2 clipped to 1
    assert!((result[5] - 1.0).abs() < 1e-14); // 3 clipped to 1
}

/// Test clip empty array
#[test]
fn test_clip_simd_empty() {
    let x: Array1<f64> = array![];
    let result = clip_simd(&x.view(), 0.0, 1.0);
    assert_eq!(result.len(), 0);
}

/// Test clip large array (SIMD path)
#[test]
fn test_clip_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((0..n).map(|i| (i as f64 - 5000.0) * 0.001).collect());

    let result = clip_simd(&x.view(), -1.0, 1.0);
    assert_eq!(result.len(), n);

    // All values should be in [-1, 1]
    for &v in result.iter() {
        assert!((-1.0..=1.0).contains(&v), "Value {} out of clip range", v);
    }
}

/// Test clip gradient clipping use case
#[test]
fn test_clip_simd_gradient_clipping() {
    // In neural networks, gradients are often clipped to prevent exploding gradients
    let gradients = array![100.0_f64, -50.0, 0.5, -0.1, 200.0];

    let clipped = clip_simd(&gradients.view(), -1.0, 1.0);

    assert!((clipped[0] - 1.0).abs() < 1e-14); // 100 clipped to 1
    assert!((clipped[1] - (-1.0)).abs() < 1e-14); // -50 clipped to -1
    assert!((clipped[2] - 0.5).abs() < 1e-14); // 0.5 unchanged
    assert!((clipped[3] - (-0.1)).abs() < 1e-14); // -0.1 unchanged
    assert!((clipped[4] - 1.0).abs() < 1e-14); // 200 clipped to 1
}

// ============================================================================
// cumsum tests
// ============================================================================

/// Test cumsum basic f32 correctness
#[test]
fn test_cumsum_simd_f32_basic() {
    let x = array![1.0_f32, 2.0, 3.0, 4.0, 5.0];

    let result = cumsum_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-5); // 1
    assert!((result[1] - 3.0).abs() < 1e-5); // 1+2
    assert!((result[2] - 6.0).abs() < 1e-5); // 1+2+3
    assert!((result[3] - 10.0).abs() < 1e-5); // 1+2+3+4
    assert!((result[4] - 15.0).abs() < 1e-5); // 1+2+3+4+5
}

/// Test cumsum basic f64 correctness
#[test]
fn test_cumsum_simd_f64_basic() {
    let x = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];

    let result = cumsum_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-14); // 1
    assert!((result[1] - 3.0).abs() < 1e-14); // 1+2
    assert!((result[2] - 6.0).abs() < 1e-14); // 1+2+3
    assert!((result[3] - 10.0).abs() < 1e-14); // 1+2+3+4
    assert!((result[4] - 15.0).abs() < 1e-14); // 1+2+3+4+5
}

/// Test cumsum empty array
#[test]
fn test_cumsum_simd_empty() {
    let x: Array1<f64> = array![];
    let result = cumsum_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test cumsum large array (SIMD path)
#[test]
fn test_cumsum_simd_large_array() {
    let n = 10000;
    let x = Array1::from_vec((1..=n).map(|i| i as f64).collect());

    let result = cumsum_simd(&x.view());
    assert_eq!(result.len(), n);

    // Last element should be n*(n+1)/2 = 50005000
    let expected_last = (n * (n + 1) / 2) as f64;
    assert!(
        (result[n - 1] - expected_last).abs() < 1e-6,
        "cumsum last element should be {}, got {}",
        expected_last,
        result[n - 1]
    );
}

/// Test cumsum CDF computation use case
#[test]
fn test_cumsum_simd_cdf() {
    // Computing CDF from PDF
    let pdf = array![0.1_f64, 0.2, 0.3, 0.25, 0.15]; // Should sum to 1

    let cdf = cumsum_simd(&pdf.view());

    assert!((cdf[0] - 0.1).abs() < 1e-14);
    assert!((cdf[1] - 0.3).abs() < 1e-14);
    assert!((cdf[2] - 0.6).abs() < 1e-14);
    assert!((cdf[3] - 0.85).abs() < 1e-14);
    assert!((cdf[4] - 1.0).abs() < 1e-14); // CDF should end at 1
}

// ============================================================================
// cumprod tests
// ============================================================================

/// Test cumprod basic f32 correctness
#[test]
fn test_cumprod_simd_f32_basic() {
    let x = array![1.0_f32, 2.0, 3.0, 4.0];

    let result = cumprod_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-5); // 1
    assert!((result[1] - 2.0).abs() < 1e-5); // 1*2
    assert!((result[2] - 6.0).abs() < 1e-5); // 1*2*3
    assert!((result[3] - 24.0).abs() < 1e-5); // 1*2*3*4 = 4!
}

/// Test cumprod basic f64 correctness
#[test]
fn test_cumprod_simd_f64_basic() {
    let x = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];

    let result = cumprod_simd(&x.view());

    assert!((result[0] - 1.0).abs() < 1e-14); // 1
    assert!((result[1] - 2.0).abs() < 1e-14); // 1*2
    assert!((result[2] - 6.0).abs() < 1e-14); // 1*2*3
    assert!((result[3] - 24.0).abs() < 1e-14); // 1*2*3*4 = 4!
    assert!((result[4] - 120.0).abs() < 1e-14); // 1*2*3*4*5 = 5!
}

/// Test cumprod empty array
#[test]
fn test_cumprod_simd_empty() {
    let x: Array1<f64> = array![];
    let result = cumprod_simd(&x.view());
    assert_eq!(result.len(), 0);
}

/// Test cumprod factorial computation
#[test]
fn test_cumprod_simd_factorial() {
    // Computing factorials: cumprod([1,2,3,...,n]) = [1!, 2!, 3!, ..., n!]
    let n = 10;
    let seq = Array1::from_vec((1..=n).map(|i| i as f64).collect());

    let factorials = cumprod_simd(&seq.view());

    // Known factorials
    let expected = [
        1.0, 2.0, 6.0, 24.0, 120.0, 720.0, 5040.0, 40320.0, 362880.0, 3628800.0,
    ];

    for i in 0..n {
        assert!(
            (factorials[i] - expected[i]).abs() < 1e-10,
            "{}! should be {}, got {}",
            i + 1,
            expected[i],
            factorials[i]
        );
    }
}

/// Test cumprod survival probability use case
#[test]
fn test_cumprod_simd_survival() {
    // Computing survival probability from hazard rates
    // Survival at time t = product of (1 - hazard_i) for i < t
    let survival_probs = array![0.99_f64, 0.98, 0.97, 0.96, 0.95];

    let cumulative_survival = cumprod_simd(&survival_probs.view());

    // Cumulative survival should be decreasing
    for i in 1..survival_probs.len() {
        assert!(
            cumulative_survival[i] < cumulative_survival[i - 1],
            "Cumulative survival should be decreasing"
        );
    }

    // Last value should be product of all survival probabilities
    let expected = 0.99 * 0.98 * 0.97 * 0.96 * 0.95;
    assert!(
        (cumulative_survival[4] - expected).abs() < 1e-14,
        "Final survival should be {}",
        expected
    );
}

// ============================================================================
// diff tests
// ============================================================================

/// Test diff basic f32 correctness
#[test]
fn test_diff_simd_f32_basic() {
    let x = array![1.0_f32, 3.0, 6.0, 10.0, 15.0];

    let result = diff_simd(&x.view());
    assert_eq!(result.len(), 4); // n-1 elements

    assert!((result[0] - 2.0).abs() < 1e-5); // 3-1
    assert!((result[1] - 3.0).abs() < 1e-5); // 6-3
    assert!((result[2] - 4.0).abs() < 1e-5); // 10-6
    assert!((result[3] - 5.0).abs() < 1e-5); // 15-10
}

/// Test diff basic f64 correctness
#[test]
fn test_diff_simd_f64_basic() {
    let x = array![1.0_f64, 3.0, 6.0, 10.0, 15.0];

    let result = diff_simd(&x.view());
    assert_eq!(result.len(), 4); // n-1 elements

    assert!((result[0] - 2.0).abs() < 1e-14); // 3-1
    assert!((result[1] - 3.0).abs() < 1e-14); // 6-3
    assert!((result[2] - 4.0).abs() < 1e-14); // 10-6
    assert!((result[3] - 5.0).abs() < 1e-14); // 15-10
}

/// Test diff empty and single element arrays
#[test]
fn test_diff_simd_edge_cases() {
    let x_empty: Array1<f64> = array![];
    let result_empty = diff_simd(&x_empty.view());
    assert_eq!(result_empty.len(), 0);

    let x_single = array![1.0_f64];
    let result_single = diff_simd(&x_single.view());
    assert_eq!(result_single.len(), 0); // Need at least 2 elements
}

/// Test diff large array (SIMD path)
#[test]
fn test_diff_simd_large_array() {
    let n = 10000;
    // Create quadratic sequence: x[i] = i^2
    let x = Array1::from_vec((0..n).map(|i| (i as f64).powi(2)).collect());

    let result = diff_simd(&x.view());
    assert_eq!(result.len(), n - 1);

    // diff of x^2 gives 2x+1 = 1, 3, 5, 7, ... (odd numbers)
    for i in 0..result.len() {
        let expected = (2 * i + 1) as f64;
        assert!(
            (result[i] - expected).abs() < 1e-10,
            "diff[{}] should be {}, got {}",
            i,
            expected,
            result[i]
        );
    }
}

/// Test diff constant array gives zeros
#[test]
fn test_diff_simd_constant() {
    let x = array![5.0_f64, 5.0, 5.0, 5.0, 5.0];

    let result = diff_simd(&x.view());

    for &v in result.iter() {
        assert!((v - 0.0).abs() < 1e-14, "diff of constant should be 0");
    }
}

/// Test diff numerical differentiation use case
#[test]
fn test_diff_simd_numerical_derivative() {
    // Approximate derivative of sin(x) should be cos(x)
    let n = 100;
    let h = 0.01_f64;
    let x = Array1::from_vec((0..n).map(|i| i as f64 * h).collect());
    let sin_x = x.mapv(|xi| xi.sin());

    let diff_sin = diff_simd(&sin_x.view());

    // diff[i] / h ≈ cos(x[i])
    for i in 0..diff_sin.len() {
        let numerical_derivative = diff_sin[i] / h;
        let analytical_derivative = x[i].cos();
        // Should be close (within O(h) error)
        assert!(
            (numerical_derivative - analytical_derivative).abs() < 0.02,
            "Numerical derivative should approximate cos(x)"
        );
    }
}

/// Test diff and cumsum are inverse operations
#[test]
fn test_diff_simd_inverse_of_cumsum() {
    // For a sequence starting from 0: diff(cumsum(x)) = x (except for first element)
    // cumsum(diff(x)) = x - x[0] (offset by first element)

    let x = array![1.0_f64, 2.0, 3.0, 4.0, 5.0];

    let cumsum_x = cumsum_simd(&x.view());
    let diff_cumsum_x = diff_simd(&cumsum_x.view());

    // diff(cumsum(x))[i] should equal x[i+1]
    for i in 0..diff_cumsum_x.len() {
        assert!(
            (diff_cumsum_x[i] - x[i + 1]).abs() < 1e-14,
            "diff(cumsum(x))[{}] should equal x[{}]",
            i,
            i + 1
        );
    }
}

// =============================================================================
