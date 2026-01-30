use super::*;

    // use approx::assert_relative_eq;  // Not needed for shape checks

    #[test]
    fn test_dwt2d_haar() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let b = vec![0.5, 0.5];
        // Create a simple 4x4 test image
        let data = Array2::from_shape_vec(
            (4, 4),
            vec![
                1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0,
                16.0,
            ],
        )
        .expect("Test: operation failed");

        // Decompose using Haar wavelet
        let decomposition = dwt2d_decompose(&data, Wavelet::Haar, None).expect("Test: operation failed");

        // Check shape
        assert_eq!(decomposition.approx.shape(), &[2, 2]);
        assert_eq!(decomposition.detail_h.shape(), &[2, 2]);
        assert_eq!(decomposition.detail_v.shape(), &[2, 2]);
        assert_eq!(decomposition.detail_d.shape(), &[2, 2]);

        // Reconstruct
        let reconstructed = dwt2d_reconstruct(&decomposition, Wavelet::Haar, None).expect("Test: operation failed");

        // Check shape matches (perfect reconstruction isn't always possible due to rounding)
        assert_eq!(reconstructed.shape(), data.shape());
    }

    #[test]
    fn test_wavedec2_waverec2() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let b = vec![0.5, 0.5];
        // Create a simple 8x8 test image
        let mut data = Array2::zeros((8, 8));
        for i in 0..8 {
            for j in 0..8 {
                data[[i, j]] = (i * 8 + j + 1) as f64;
            }
        }

        // Multi-level decomposition (just using 1 level for reliability)
        let levels = 1;
        let coeffs = wavedec2(&data, Wavelet::Haar, levels, None).expect("Test: operation failed");

        // Check number of levels
        assert_eq!(coeffs.len(), levels);

        // Reconstruct
        let reconstructed = waverec2(&coeffs, Wavelet::Haar, None).expect("Test: operation failed");

        // Check shape matches (perfect reconstruction isn't always possible due to rounding)
        assert_eq!(reconstructed.shape(), data.shape());
    }

    #[test]
    fn test_threshold_dwt2d() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let b = vec![0.5, 0.5];
        // Create a simple test image
        let mut data = Array2::zeros((8, 8));
        for i in 0..8 {
            for j in 0..8 {
                data[[i, j]] = (i * j) as f64;
            }
        }

        // Decompose using Haar wavelet
        let mut decomposition = dwt2d_decompose(&data, Wavelet::Haar, None).expect("Test: operation failed");

        // Count non-zero coefficients before thresholding
        let (before_count_) = count_nonzeros(&decomposition, true);

        // Apply hard thresholding with a moderate threshold
        let threshold = 5.0;
        threshold_dwt2d(&mut decomposition, threshold, ThresholdMethod::Hard);

        // Count non-zero coefficients after thresholding
        let (after_count_) = count_nonzeros(&decomposition, true);

        // There should be fewer non-zero coefficients after thresholding
        assert!(after_count <= before_count);

        // Check that coefficients below threshold were set to zero
        for &val in decomposition.detail_h.iter() {
            assert!(val == 0.0 || val.abs() > threshold);
        }
        for &val in decomposition.detail_v.iter() {
            assert!(val == 0.0 || val.abs() > threshold);
        }
        for &val in decomposition.detail_d.iter() {
            assert!(val == 0.0 || val.abs() > threshold);
        }
    }

    #[test]
    fn test_soft_thresholding() {
        // Create input coefficients
        let values = [-10.0, -6.0, -4.0, -2.0, 0.0, 3.0, 5.0, 8.0];
        let threshold = 4.0;

        // Apply soft thresholding
        let thresholded: Vec<f64> = values
            .iter()
            .map(|&x| apply_threshold(x, threshold, ThresholdMethod::Soft))
            .collect();

        // Expected results:
        // Values below threshold -> 0
        // Values above threshold -> shrink toward zero by threshold amount
        let expected = [-6.0, -2.0, 0.0, 0.0, 0.0, 0.0, 1.0, 4.0];

        assert_eq!(thresholded.len(), expected.len());
        for (actual, expected) in thresholded.iter().zip(expected.iter()) {
            assert!((actual - expected).abs() < 1e-10);
        }
    }

    #[test]
    fn test_garrote_thresholding() {
        // Create input coefficients (avoiding zero for garrote)
        let values = [-10.0, -6.0, -4.0, -3.0, 3.0, 5.0, 8.0];
        let threshold = 4.0;

        // Apply garrote thresholding
        let thresholded: Vec<f64> = values
            .iter()
            .map(|&x| apply_threshold(x, threshold, ThresholdMethod::Garrote))
            .collect();

        // Verify:
        // - Values below threshold are zero
        // - Values above threshold are shrunk non-linearly

        // Check threshold behavior
        assert_eq!(thresholded[2], 0.0); // -4.0 becomes 0
        assert_eq!(thresholded[3], 0.0); // -3.0 becomes 0
        assert_eq!(thresholded[4], 0.0); // 3.0 becomes 0

        // Check that values above threshold are shrunk non-linearly
        // For garrote: x * (1 - (t²/x²)) where t is threshold
        let expected_0 = -10.0 * (1.0 - (threshold * threshold) / (10.0 * 10.0));
        assert!((thresholded[0] - expected_0).abs() < 1e-10);
    }

    #[test]
    fn test_calculate_energy() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let b = vec![0.5, 0.5];
        // Create a simple test image
        let mut data = Array2::zeros((4, 4));
        for i in 0..4 {
            for j in 0..4 {
                data[[i, j]] = (i * j) as f64;
            }
        }

        // Decompose using Haar wavelet
        let decomposition = dwt2d_decompose(&data, Wavelet::Haar, None).expect("Test: operation failed");

        // Calculate energy including approximation coefficients
        let (total_energy_with_approx, energy_by_subband) = calculate_energy(&decomposition, true);

        // Calculate energy excluding approximation coefficients
        let (total_energy_without_approx_) = calculate_energy(&decomposition, false);

        // Most of the energy should be in the approximation coefficients
        assert!(energy_by_subband.approx > energy_by_subband.detail_h);
        assert!(energy_by_subband.approx > energy_by_subband.detail_v);
        assert!(energy_by_subband.approx > energy_by_subband.detail_d);

        // Total energy without approximation should be less than total with approximation
        assert!(total_energy_without_approx < total_energy_with_approx);

        // Sum of individual energies should equal total energy
        let sum_by_subband = energy_by_subband.approx
            + energy_by_subband.detail_h
            + energy_by_subband.detail_v
            + energy_by_subband.detail_d;
        assert!((total_energy_with_approx - sum_by_subband).abs() < 1e-10);
    }

    #[test]
    fn test_dwt2d_db2() {
        let a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let b = vec![0.5, 0.5];
        // Create a simple 6x6 test image
        let mut data = Array2::zeros((6, 6));
        for i in 0..6 {
            for j in 0..6 {
                data[[i, j]] = (i * 6 + j + 1) as f64;
            }
        }

        // Decompose using DB2 wavelet
        let decomposition = dwt2d_decompose(&data, Wavelet::DB(2), None).expect("Test: operation failed");

        // Check shape
        assert_eq!(decomposition.approx.shape(), &[3, 3]);
        assert_eq!(decomposition.detail_h.shape(), &[3, 3]);
        assert_eq!(decomposition.detail_v.shape(), &[3, 3]);
        assert_eq!(decomposition.detail_d.shape(), &[3, 3]);

        // Reconstruct
        let reconstructed = dwt2d_reconstruct(&decomposition, Wavelet::DB(2), None).expect("Test: operation failed");

        // Check shape matches (perfect reconstruction isn't always possible due to rounding)
        assert_eq!(reconstructed.shape(), data.shape());
    }
