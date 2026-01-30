//! Auto-generated module
//!
//! 🤖 Generated with [SplitRS](https://github.com/cool-japan/splitrs)

use super::types::{Dwt2dConfig, Dwt2dResult, MemoryPool, ThresholdMethod};
use crate::dwt::{self, Wavelet};
use crate::error::{SignalError, SignalResult};
use scirs2_core::ndarray::Array2;
use scirs2_core::parallel_ops::*;
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

use super::types::{Dwt2dResult, ThresholdMethod};
use super::functions_3::apply_threshold;

/// Advanced denoising using 2D wavelet thresholding with adaptive threshold selection
///
/// This function automatically estimates optimal thresholds for each subband based on
/// noise characteristics and applies adaptive thresholding for improved denoising.
#[allow(dead_code)]
pub fn denoise_dwt2d_adaptive(
    noisy_image: &Array2<f64>,
    wavelet: Wavelet,
    noise_variance: Option<f64>,
    method: ThresholdMethod,
) -> SignalResult<Array2<f64>> {
    if noisy_image.is_empty() {
        return Err(SignalError::ValueError("Input array is empty".to_string()));
    }
    if let Some(data_slice) = noisy_image.as_slice() {}
    let mut decomposition = dwt2d_decompose_adaptive(noisy_image, wavelet, None)?;
    let sigma = if let Some(var) = noise_variance {
        var.sqrt()
    } else {
        estimate_noise_variance(&decomposition)
    };
    let threshold_h = sigma * (2.0 * (noisy_image.len() as f64).ln()).sqrt() * 0.8;
    let threshold_v = sigma * (2.0 * (noisy_image.len() as f64).ln()).sqrt() * 0.8;
    let threshold_d = sigma * (2.0 * (noisy_image.len() as f64).ln()).sqrt() * 1.2;
    apply_adaptive_thresholding(&mut decomposition.detail_h, threshold_h, method);
    apply_adaptive_thresholding(&mut decomposition.detail_v, threshold_v, method);
    apply_adaptive_thresholding(&mut decomposition.detail_d, threshold_d, method);
    dwt2d_reconstruct(&decomposition, wavelet, None)
}
/// Multi-level adaptive denoising
#[allow(dead_code)]
pub fn denoise_wavedec2_adaptive(
    noisy_image: &Array2<f64>,
    wavelet: Wavelet,
    levels: usize,
    noise_variance: Option<f64>,
    method: ThresholdMethod,
) -> SignalResult<Array2<f64>> {
    if noisy_image.is_empty() {
        return Err(SignalError::ValueError("Input array is empty".to_string()));
    }
    let mut coeffs = wavedec2_enhanced(noisy_image, wavelet, levels, None)?;
    let sigma = if let Some(var) = noise_variance {
        var.sqrt()
    } else {
        estimate_noise_variance(&coeffs[coeffs.len() - 1])
    };
    let mut thresholds = Vec::with_capacity(levels);
    for level in 0..levels {
        let level_factor = 2.0_f64.powi((levels - level - 1) as i32).sqrt();
        let base_threshold = sigma * (2.0 * (noisy_image.len() as f64).ln()).sqrt();
        thresholds.push(base_threshold * level_factor);
    }
    for (level, coeffs_level) in coeffs.iter_mut().enumerate() {
        let threshold = thresholds[level];
        apply_adaptive_thresholding(&mut coeffs_level.detail_h, threshold * 0.8, method);
        apply_adaptive_thresholding(&mut coeffs_level.detail_v, threshold * 0.8, method);
        apply_adaptive_thresholding(&mut coeffs_level.detail_d, threshold * 1.2, method);
    }
    waverec2(&coeffs, wavelet, None)
}
/// Estimate noise variance from wavelet coefficients (using robust MAD estimator)
#[allow(dead_code)]
fn estimate_noise_variance(decomp: &Dwt2dResult) -> f64 {
    let mut diagonal_coeffs: Vec<f64> = decomp.detail_d.iter().cloned().collect();
    if diagonal_coeffs.is_empty() {
        return 1.0;
    }
    diagonal_coeffs
        .sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let n = diagonal_coeffs.len();
    let median = if n % 2 == 0 {
        (diagonal_coeffs[n / 2 - 1] + diagonal_coeffs[n / 2]) / 2.0
    } else {
        diagonal_coeffs[n / 2]
    };
    let mut abs_deviations: Vec<f64> = diagonal_coeffs
        .iter()
        .map(|&x| (x - median).abs())
        .collect();
    abs_deviations.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let mad = if n % 2 == 0 {
        (abs_deviations[n / 2 - 1] + abs_deviations[n / 2]) / 2.0
    } else {
        abs_deviations[n / 2]
    };
    mad / 0.6745
}
/// Apply adaptive thresholding to a 2D array
#[allow(dead_code)]
fn apply_adaptive_thresholding(
    data: &mut Array2<f64>,
    threshold: f64,
    method: ThresholdMethod,
) {
    if let Some(data_slice) = data.as_slice_mut() {
        simd_threshold_coefficients(data_slice, threshold, method);
    } else {
        for val in data.iter_mut() {
            *val = apply_threshold(*val, threshold, method);
        }
    }
}
/// Calculate compression ratio after thresholding
#[allow(dead_code)]
pub fn calculate_compression_ratio(
    original: &Dwt2dResult,
    compressed: &Dwt2dResult,
) -> f64 {
    let (_, original_counts) = count_nonzeros(_original, true);
    let (_, compressed_counts) = count_nonzeros(compressed, true);
    let original_total = original_counts.approx + original_counts.detail_h
        + original_counts.detail_v + original_counts.detail_d;
    let compressed_total = compressed_counts.approx + compressed_counts.detail_h
        + compressed_counts.detail_v + compressed_counts.detail_d;
    if compressed_total == 0 {
        f64::INFINITY
    } else {
        original_total as f64 / compressed_total as f64
    }
}
/// Calculate Peak Signal-to-Noise Ratio (PSNR) between original and reconstructed images
#[allow(dead_code)]
pub fn calculate_psnr(
    original: &Array2<f64>,
    reconstructed: &Array2<f64>,
) -> SignalResult<f64> {
    if original.shape() != reconstructed.shape() {
        return Err(
            SignalError::ValueError("Arrays must have the same shape".to_string()),
        );
    }
    let max_val = original.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
    if max_val <= 0.0 {
        return Err(
            SignalError::ValueError(
                "Maximum value must be positive for PSNR calculation".to_string(),
            ),
        );
    }
    let mut mse = 0.0;
    let mut count = 0;
    for (orig, recon) in original.iter().zip(reconstructed.iter()) {
        let diff = orig - recon;
        mse += diff * diff;
        count += 1;
    }
    if count == 0 {
        return Err(SignalError::ValueError("Arrays are empty".to_string()));
    }
    mse /= count as f64;
    if mse == 0.0 {
        Ok(f64::INFINITY)
    } else {
        Ok(20.0 * (max_val * max_val / mse).log10())
    }
}
/// Calculate Structural Similarity Index (SSIM) between two images
#[allow(dead_code)]
pub fn calculate_ssim(
    original: &Array2<f64>,
    reconstructed: &Array2<f64>,
    window_size: usize,
) -> SignalResult<f64> {
    if original.shape() != reconstructed.shape() {
        return Err(
            SignalError::ValueError("Arrays must have the same shape".to_string()),
        );
    }
    if window_size < 3 || window_size % 2 == 0 {
        return Err(
            SignalError::ValueError(
                "Window _size must be odd and at least 3".to_string(),
            ),
        );
    }
    let (rows, cols) = original.dim();
    if rows < window_size || cols < window_size {
        return Err(
            SignalError::ValueError(
                "Image dimensions must be larger than window _size".to_string(),
            ),
        );
    }
    let k1 = 0.01;
    let k2 = 0.03;
    let dynamic_range = original.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b))
        - original.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let c1 = (k1 * dynamic_range).powi(2);
    let c2 = (k2 * dynamic_range).powi(2);
    let mut ssim_sum = 0.0;
    let mut window_count = 0;
    let half_window = window_size / 2;
    for i in half_window..(rows - half_window) {
        for j in half_window..(cols - half_window) {
            let mut window1 = Vec::new();
            let mut window2 = Vec::new();
            for di in 0..window_size {
                for dj in 0..window_size {
                    let ri = i - half_window + di;
                    let rj = j - half_window + dj;
                    window1.push(original[[ri, rj]]);
                    window2.push(reconstructed[[ri, rj]]);
                }
            }
            let n = window1.len() as f64;
            let mean1 = window1.iter().sum::<f64>() / n;
            let mean2 = window2.iter().sum::<f64>() / n;
            let var1 = window1.iter().map(|&x| (x - mean1).powi(2)).sum::<f64>()
                / (n - 1.0);
            let var2 = window2.iter().map(|&x| (x - mean2).powi(2)).sum::<f64>()
                / (n - 1.0);
            let covar = window1
                .iter()
                .zip(window2.iter())
                .map(|(&x1, &x2)| (x1 - mean1) * (x2 - mean2))
                .sum::<f64>() / (n - 1.0);
            let numerator = (2.0 * mean1 * mean2 + c1) * (2.0 * covar + c2);
            let denominator = (mean1.powi(2) + mean2.powi(2) + c1) * (var1 + var2 + c2);
            if denominator > 1e-15 {
                ssim_sum += numerator / denominator;
                window_count += 1;
            }
        }
    }
    if window_count == 0 { Ok(0.0) } else { Ok(ssim_sum / window_count as f64) }
}
