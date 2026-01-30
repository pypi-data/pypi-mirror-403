//! Auto-generated module
//!
//! 🤖 Generated with [SplitRS](https://github.com/cool-japan/splitrs)

use crate::error::{Result, TransformError};
use scirs2_core::ndarray::{Array1, ArrayStatCompat, ArrayView1, ArrayView2};
use scirs2_core::validation::check_not_empty;
use std::collections::HashMap;
#[cfg(feature = "auto-feature-engineering")]
use std::collections::VecDeque;
#[cfg(feature = "auto-feature-engineering")]
use tch::{nn, Device, Tensor};

/// Performance record for historical analysis
#[cfg(feature = "auto-feature-engineering")]
#[derive(Debug, Clone)]
pub struct PerformanceRecord {
    /// Dataset meta-features
    meta_features: DatasetMetaFeatures,
    /// Applied transformations
    transformations: Vec<TransformationConfig>,
    /// Performance metrics
    metrics: PerformanceMetrics,
    /// Computational cost
    computational_cost: f64,
    /// Timestamp
    timestamp: u64,
}
/// Experience tuple for reinforcement learning
#[cfg(feature = "auto-feature-engineering")]
#[derive(Debug, Clone)]
pub struct Experience {
    /// State representation (meta-features)
    state: Vec<f64>,
    /// Action taken (transformation choice)
    action: usize,
    /// Reward received (performance improvement)
    reward: f64,
    /// Next state
    next_state: Vec<f64>,
    /// Whether episode terminated
    done: bool,
}
/// Available transformation types for automated selection
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum TransformationType {
    /// Standardization (Z-score normalization)
    StandardScaler,
    /// Min-max scaling
    MinMaxScaler,
    /// Robust scaling using median and IQR
    RobustScaler,
    /// Power transformation (Box-Cox/Yeo-Johnson)
    PowerTransformer,
    /// Polynomial feature generation
    PolynomialFeatures,
    /// Principal Component Analysis
    PCA,
    /// Feature selection based on variance
    VarianceThreshold,
    /// Quantile transformation
    QuantileTransformer,
    /// Binary encoding for categorical features
    BinaryEncoder,
    /// Target encoding
    TargetEncoder,
}
/// Multi-objective optimization weights
#[cfg(feature = "auto-feature-engineering")]
#[derive(Debug, Clone)]
pub struct FeatureOptimizationWeights {
    /// Weight for prediction performance
    pub performance_weight: f64,
    /// Weight for computational efficiency
    pub efficiency_weight: f64,
    /// Weight for model interpretability
    pub interpretability_weight: f64,
    /// Weight for robustness
    pub robustness_weight: f64,
}
/// Performance metrics for multi-objective optimization
#[cfg(feature = "auto-feature-engineering")]
#[derive(Debug, Clone)]
pub struct PerformanceMetrics {
    /// Prediction accuracy/score
    accuracy: f64,
    /// Training time in seconds
    training_time: f64,
    /// Memory usage in MB
    memory_usage: f64,
    /// Model complexity score
    complexity_score: f64,
    /// Cross-validation score
    cv_score: f64,
}
/// Multi-objective recommendation system (placeholder)
pub struct MultiObjectiveRecommendation;
/// Advanced meta-learning system for feature engineering (placeholder)
pub struct AdvancedMetaLearningSystem;
/// Enhanced meta-features for advanced analysis (placeholder)
pub struct EnhancedMetaFeatures;
/// Configuration for a transformation with its parameters
#[derive(Debug, Clone)]
pub struct TransformationConfig {
    /// Type of transformation to apply
    pub transformation_type: TransformationType,
    /// Parameters for the transformation
    pub parameters: HashMap<String, f64>,
    /// Expected performance score for this transformation
    pub expected_performance: f64,
}
/// Meta-learning model for transformation selection
#[cfg(feature = "auto-feature-engineering")]
pub struct MetaLearningModel {
    /// Neural network for predicting transformation performance
    model: nn::Sequential,
    /// Variable store for parameters
    vs: nn::VarStore,
    /// Device for computation (CPU/GPU)
    device: Device,
    /// Training data cache
    training_cache: Vec<(DatasetMetaFeatures, Vec<TransformationConfig>)>,
}
#[cfg(feature = "auto-feature-engineering")]
impl MetaLearningModel {
    /// Create a new meta-learning model
    pub fn new() -> Result<Self> {
        let device = Device::cuda_if_available();
        let vs = nn::VarStore::new(device);
        let root = vs.root();
        let model = nn::seq()
            .add(nn::linear(&root / "layer1", 10, 64, Default::default()))
            .add_fn(|xs| xs.relu())
            .add(nn::linear(&root / "layer2", 64, 32, Default::default()))
            .add_fn(|xs| xs.relu())
            .add(nn::linear(&root / "layer3", 32, 16, Default::default()))
            .add_fn(|xs| xs.relu())
            .add(nn::linear(&root / "output", 16, 10, Default::default()))
            .add_fn(|xs| xs.softmax(-1, tch::Kind::Float));
        Ok(MetaLearningModel {
            model,
            vs,
            device,
            training_cache: Vec::new(),
        })
    }
    /// Train the meta-learning model on historical transformation performance data
    pub fn train(
        &mut self,
        training_data: Vec<(DatasetMetaFeatures, Vec<TransformationConfig>)>,
    ) -> Result<()> {
        self.training_cache.extend(training_data.clone());
        let (input_features, target_scores) = self.prepare_training_data(&training_data)?;
        for epoch in 0..100 {
            let predicted = input_features.apply(&self.model);
            let loss = predicted.mse_loss(&target_scores, tch::Reduction::Mean);
            if epoch % 20 == 0 {
                println!("Epoch {epoch}: Loss = {:.4}", loss.double_value(&[]));
            }
        }
        Ok(())
    }
    /// Predict optimal transformations for a given dataset
    pub fn predict_transformations(
        &self,
        meta_features: &DatasetMetaFeatures,
    ) -> Result<Vec<TransformationConfig>> {
        let input_tensor = self.meta_features_to_tensor(meta_features)?;
        let prediction = input_tensor.apply(&self.model);
        self.tensor_to_transformations(&prediction)
    }
    fn prepare_training_data(
        &self,
        training_data: &[(DatasetMetaFeatures, Vec<TransformationConfig>)],
    ) -> Result<(Tensor, Tensor)> {
        if training_data.is_empty() {
            return Err(TransformError::InvalidInput(
                "Training _data cannot be empty".to_string(),
            ));
        }
        let n_samples = training_data.len();
        let mut input_features = Vec::with_capacity(n_samples * 10);
        let mut target_scores = Vec::with_capacity(n_samples * 10);
        for (meta_features, transformations) in training_data {
            let features = vec![
                (meta_features.n_samples as f64).ln().max(0.0),
                (meta_features.n_features as f64).ln().max(0.0),
                meta_features.sparsity.clamp(0.0, 1.0),
                meta_features.mean_correlation.clamp(-1.0, 1.0),
                meta_features.std_correlation.max(0.0),
                meta_features.mean_skewness.clamp(-10.0, 10.0),
                meta_features.mean_kurtosis.clamp(-10.0, 10.0),
                meta_features.missing_ratio.clamp(0.0, 1.0),
                meta_features.variance_ratio.max(0.0),
                meta_features.outlier_ratio.clamp(0.0, 1.0),
            ];
            if features.iter().any(|&f| !f.is_finite()) {
                return Err(TransformError::ComputationError(
                    "Non-finite values detected in meta-features".to_string(),
                ));
            }
            input_features.extend(features);
            let mut scores = vec![0.0f64; 10];
            for config in transformations {
                let idx = self.transformation_type_to_index(&config.transformation_type);
                let performance = config.expected_performance.clamp(0.0, 1.0);
                scores[idx] = scores[idx].max(performance as f64);
            }
            target_scores.extend(scores);
        }
        let input_tensor = Tensor::from_slice(&input_features)
            .reshape(&[n_samples as i64, 10])
            .to_device(self.device);
        let target_tensor = Tensor::from_slice(&target_scores)
            .reshape(&[n_samples as i64, 10])
            .to_device(self.device);
        Ok((input_tensor, target_tensor))
    }
    fn meta_features_to_tensor(&self, meta_features: &DatasetMetaFeatures) -> Result<Tensor> {
        let features = vec![
            (meta_features.n_samples as f64).ln().max(0.0),
            (meta_features.n_features as f64).ln().max(0.0),
            meta_features.sparsity.clamp(0.0, 1.0),
            meta_features.mean_correlation.clamp(-1.0, 1.0),
            meta_features.std_correlation.max(0.0),
            meta_features.mean_skewness.clamp(-10.0, 10.0),
            meta_features.mean_kurtosis.clamp(-10.0, 10.0),
            meta_features.missing_ratio.clamp(0.0, 1.0),
            meta_features.variance_ratio.max(0.0),
            meta_features.outlier_ratio.clamp(0.0, 1.0),
        ];
        if features.iter().any(|&f| !f.is_finite()) {
            return Err(TransformError::ComputationError(
                "Non-finite values detected in meta-features".to_string(),
            ));
        }
        Ok(Tensor::from_slice(&features)
            .reshape(&[1, 10])
            .to_device(self.device))
    }
    fn tensor_to_transformations(&self, prediction: &Tensor) -> Result<Vec<TransformationConfig>> {
        let scores: Vec<f64> = prediction.try_into().map_err(|e| {
            TransformError::ComputationError(format!("Failed to extract tensor data: {:?}", e))
        })?;
        if scores.len() != 10 {
            return Err(TransformError::ComputationError(format!(
                "Expected 10 prediction scores, got {}",
                scores.len()
            )));
        }
        let mut transformations = Vec::new();
        let max_score = scores.iter().fold(0.0f64, |a, &b| a.max(b));
        let mean_score = scores.iter().sum::<f64>() / scores.len() as f64;
        let threshold = (max_score * 0.7 + mean_score * 0.3).max(0.3);
        for (i, &score) in scores.iter().enumerate() {
            if score > threshold && score.is_finite() {
                let transformation_type = self.index_to_transformation_type(i);
                let config = TransformationConfig {
                    transformation_type: transformation_type.clone(),
                    parameters: self.get_default_parameters_for_type(&transformation_type),
                    expected_performance: score.clamp(0.0, 1.0),
                };
                transformations.push(config);
            }
        }
        if transformations.is_empty() {
            let mut score_indices: Vec<(usize, f64)> = scores
                .iter()
                .enumerate()
                .filter(|(_, &score)| score.is_finite())
                .map(|(i, &score)| (i, score))
                .collect();
            score_indices
                .sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
            for (i, score) in score_indices.into_iter().take(3) {
                let transformation_type = self.index_to_transformation_type(i);
                let config = TransformationConfig {
                    transformation_type: transformation_type.clone(),
                    parameters: self.get_default_parameters_for_type(&transformation_type),
                    expected_performance: score.clamp(0.0, 1.0),
                };
                transformations.push(config);
            }
        }
        transformations.sort_by(|a, b| {
            b.expected_performance
                .partial_cmp(&a.expected_performance)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        Ok(transformations)
    }
    fn transformation_type_to_index(&self, t_type: &TransformationType) -> usize {
        match t_type {
            TransformationType::StandardScaler => 0,
            TransformationType::MinMaxScaler => 1,
            TransformationType::RobustScaler => 2,
            TransformationType::PowerTransformer => 3,
            TransformationType::PolynomialFeatures => 4,
            TransformationType::PCA => 5,
            TransformationType::VarianceThreshold => 6,
            TransformationType::QuantileTransformer => 7,
            TransformationType::BinaryEncoder => 8,
            TransformationType::TargetEncoder => 9,
        }
    }
    fn index_to_transformation_type(&self, index: usize) -> TransformationType {
        match index {
            0 => TransformationType::StandardScaler,
            1 => TransformationType::MinMaxScaler,
            2 => TransformationType::RobustScaler,
            3 => TransformationType::PowerTransformer,
            4 => TransformationType::PolynomialFeatures,
            5 => TransformationType::PCA,
            6 => TransformationType::VarianceThreshold,
            7 => TransformationType::QuantileTransformer,
            8 => TransformationType::BinaryEncoder,
            _ => TransformationType::StandardScaler,
        }
    }
    fn get_default_parameters_for_type(&self, t_type: &TransformationType) -> HashMap<String, f64> {
        let mut params = HashMap::new();
        match t_type {
            TransformationType::PCA => {
                params.insert("n_components".to_string(), 0.95);
            }
            TransformationType::PolynomialFeatures => {
                params.insert("degree".to_string(), 2.0);
                params.insert("include_bias".to_string(), 0.0);
            }
            TransformationType::VarianceThreshold => {
                params.insert("threshold".to_string(), 0.01);
            }
            _ => {}
        }
        params
    }
}
/// Reinforcement learning agent for transformation selection
#[cfg(feature = "auto-feature-engineering")]
pub struct RLAgent {
    /// Q-network for value estimation
    q_network: nn::Sequential,
    /// Target network for stable training
    target_network: nn::Sequential,
    /// Experience replay buffer
    replay_buffer: VecDeque<Experience>,
    /// Epsilon for exploration
    epsilon: f64,
    /// Learning rate
    learning_rate: f64,
    /// Discount factor
    gamma: f64,
}
/// Meta-features extracted from datasets for transformation selection
#[derive(Debug, Clone)]
pub struct DatasetMetaFeatures {
    /// Number of samples
    pub n_samples: usize,
    /// Number of features
    pub n_features: usize,
    /// Sparsity ratio (fraction of zero values)
    pub sparsity: f64,
    /// Mean of feature correlations
    pub mean_correlation: f64,
    /// Standard deviation of feature correlations
    pub std_correlation: f64,
    /// Skewness statistics
    pub mean_skewness: f64,
    /// Kurtosis statistics
    pub mean_kurtosis: f64,
    /// Number of missing values
    pub missing_ratio: f64,
    /// Feature variance statistics
    pub variance_ratio: f64,
    /// Outlier ratio
    pub outlier_ratio: f64,
    /// Whether the dataset has missing values
    pub has_missing: bool,
}
/// Automated feature engineering pipeline
pub struct AutoFeatureEngineer {
    #[cfg(feature = "auto-feature-engineering")]
    meta_model: MetaLearningModel,
    /// Historical transformation performance data
    #[cfg(feature = "auto-feature-engineering")]
    transformation_history: Vec<(DatasetMetaFeatures, Vec<TransformationConfig>, f64)>,
}
impl AutoFeatureEngineer {
    /// Expose pearson_correlation as a public method for external use
    #[allow(dead_code)]
    pub fn pearson_correlation(&self, x: &ArrayView1<f64>, y: &ArrayView1<f64>) -> Result<f64> {
        self.pearson_correlation_internal(x, y)
    }
    /// Create a new automated feature engineer
    pub fn new() -> Result<Self> {
        #[cfg(feature = "auto-feature-engineering")]
        let meta_model = MetaLearningModel::new()?;
        Ok(AutoFeatureEngineer {
            #[cfg(feature = "auto-feature-engineering")]
            meta_model,
            #[cfg(feature = "auto-feature-engineering")]
            transformation_history: Vec::new(),
        })
    }
    /// Extract meta-features from a dataset
    pub fn extract_meta_features(&self, x: &ArrayView2<f64>) -> Result<DatasetMetaFeatures> {
        check_not_empty(x, "x")?;
        for &val in x.iter() {
            if !val.is_finite() {
                return Err(crate::error::TransformError::DataValidationError(
                    "Data contains non-finite values".to_string(),
                ));
            }
        }
        let (n_samples, n_features) = x.dim();
        if n_samples < 2 || n_features < 1 {
            return Err(TransformError::InvalidInput(
                "Dataset must have at least 2 samples and 1 feature".to_string(),
            ));
        }
        let zeros = x.iter().filter(|&&val| val == 0.0).count();
        let sparsity = zeros as f64 / (n_samples * n_features) as f64;
        let correlations = self.compute_feature_correlations(x)?;
        let mean_correlation = correlations.mean().unwrap_or(0.0);
        let std_correlation = 0.0;
        let (mean_skewness, mean_kurtosis) = self.compute_distribution_stats(x)?;
        let missing_count = x.iter().filter(|val| val.is_nan()).count();
        let missing_ratio = missing_count as f64 / (n_samples * n_features) as f64;
        let has_missing = missing_count > 0;
        let variances: Array1<f64> = x.var_axis(scirs2_core::ndarray::Axis(0), 0.0);
        let finite_variances: Vec<f64> = variances
            .iter()
            .filter(|&&v| v.is_finite() && v >= 0.0)
            .copied()
            .collect();
        let variance_ratio = if finite_variances.is_empty() {
            0.0
        } else {
            let mean_var = finite_variances.iter().sum::<f64>() / finite_variances.len() as f64;
            if mean_var < f64::EPSILON {
                0.0
            } else {
                let var_of_vars = finite_variances
                    .iter()
                    .map(|&v| (v - mean_var).powi(2))
                    .sum::<f64>()
                    / finite_variances.len() as f64;
                (var_of_vars.sqrt() / mean_var).min(100.0)
            }
        };
        let outlier_ratio = self.compute_outlier_ratio(x)?;
        Ok(DatasetMetaFeatures {
            n_samples,
            n_features,
            sparsity,
            mean_correlation,
            std_correlation,
            mean_skewness,
            mean_kurtosis,
            missing_ratio,
            variance_ratio,
            outlier_ratio,
            has_missing,
        })
    }
    /// Recommend optimal transformations for a dataset
    #[cfg(feature = "auto-feature-engineering")]
    pub fn recommend_transformations(
        &self,
        x: &ArrayView2<f64>,
    ) -> Result<Vec<TransformationConfig>> {
        let meta_features = self.extract_meta_features(x)?;
        self.meta_model.predict_transformations(&meta_features)
    }
    /// Recommend optimal transformations for a dataset (fallback implementation)
    #[cfg(not(feature = "auto-feature-engineering"))]
    pub fn recommend_transformations(
        &self,
        x: &ArrayView2<f64>,
    ) -> Result<Vec<TransformationConfig>> {
        self.rule_based_recommendations(x)
    }
    /// Rule-based transformation recommendations (fallback)
    fn rule_based_recommendations(&self, x: &ArrayView2<f64>) -> Result<Vec<TransformationConfig>> {
        let meta_features = self.extract_meta_features(x)?;
        let mut recommendations = Vec::new();
        if meta_features.mean_skewness.abs() > 1.0 {
            recommendations.push(TransformationConfig {
                transformation_type: TransformationType::PowerTransformer,
                parameters: HashMap::new(),
                expected_performance: 0.8,
            });
        }
        if meta_features.n_features > 100 {
            let mut params = HashMap::new();
            params.insert("n_components".to_string(), 0.95);
            recommendations.push(TransformationConfig {
                transformation_type: TransformationType::PCA,
                parameters: params,
                expected_performance: 0.75,
            });
        }
        if meta_features.variance_ratio > 1.0 {
            recommendations.push(TransformationConfig {
                transformation_type: TransformationType::StandardScaler,
                parameters: HashMap::new(),
                expected_performance: 0.9,
            });
        }
        if meta_features.outlier_ratio > 0.1 {
            recommendations.push(TransformationConfig {
                transformation_type: TransformationType::RobustScaler,
                parameters: HashMap::new(),
                expected_performance: 0.85,
            });
        }
        recommendations.sort_by(|a, b| {
            b.expected_performance
                .partial_cmp(&a.expected_performance)
                .expect("Operation failed")
        });
        Ok(recommendations)
    }
    /// Train the meta-learning model with new data
    #[cfg(feature = "auto-feature-engineering")]
    pub fn update_model(
        &mut self,
        meta_features: DatasetMetaFeatures,
        transformations: Vec<TransformationConfig>,
        performance: f64,
    ) -> Result<()> {
        self.transformation_history.push((
            meta_features.clone(),
            transformations.clone(),
            performance,
        ));
        if self.transformation_history.len() % 10 == 0 {
            let training_data: Vec<_> = self
                .transformation_history
                .iter()
                .map(|(meta, trans, _perf)| (meta.clone(), trans.clone()))
                .collect();
            self.meta_model.train(training_data)?;
        }
        Ok(())
    }
    fn compute_feature_correlations(&self, x: &ArrayView2<f64>) -> Result<Array1<f64>> {
        let n_features = x.ncols();
        if n_features < 2 {
            return Ok(Array1::zeros(0));
        }
        let mut correlations = Vec::with_capacity((n_features * (n_features - 1)) / 2);
        for i in 0..n_features {
            for j in i + 1..n_features {
                let col_i = x.column(i);
                let col_j = x.column(j);
                let correlation = self.pearson_correlation_internal(&col_i, &col_j)?;
                correlations.push(correlation);
            }
        }
        Ok(Array1::from_vec(correlations))
    }
    fn pearson_correlation_internal(
        &self,
        x: &ArrayView1<f64>,
        y: &ArrayView1<f64>,
    ) -> Result<f64> {
        if x.len() != y.len() {
            return Err(TransformError::InvalidInput(
                "Arrays must have the same length for correlation calculation".to_string(),
            ));
        }
        if x.len() < 2 {
            return Ok(0.0);
        }
        let _n = x.len() as f64;
        let mean_x = x.mean_or(0.0);
        let mean_y = y.mean_or(0.0);
        let numerator: f64 = x
            .iter()
            .zip(y.iter())
            .map(|(&xi, &yi)| (xi - mean_x) * (yi - mean_y))
            .sum();
        let sum_sq_x: f64 = x.iter().map(|&xi| (xi - mean_x).powi(2)).sum();
        let sum_sq_y: f64 = y.iter().map(|&yi| (yi - mean_y).powi(2)).sum();
        let denominator = (sum_sq_x * sum_sq_y).sqrt();
        if denominator < f64::EPSILON {
            Ok(0.0)
        } else {
            let correlation = numerator / denominator;
            Ok(correlation.clamp(-1.0, 1.0))
        }
    }
    fn compute_distribution_stats(&self, x: &ArrayView2<f64>) -> Result<(f64, f64)> {
        let mut skewness_values = Vec::new();
        let mut kurtosis_values = Vec::new();
        for col in x.columns() {
            let finite_values: Vec<f64> = col
                .iter()
                .filter(|&&val| val.is_finite())
                .copied()
                .collect();
            if finite_values.len() < 3 {
                continue;
            }
            let n = finite_values.len() as f64;
            let mean = finite_values.iter().sum::<f64>() / n;
            let variance = finite_values
                .iter()
                .map(|&val| (val - mean).powi(2))
                .sum::<f64>()
                / (n - 1.0);
            let std = variance.sqrt();
            if std > f64::EPSILON * 1000.0 {
                let m3: f64 = finite_values
                    .iter()
                    .map(|&val| ((val - mean) / std).powi(3))
                    .sum::<f64>()
                    / n;
                let skew = if n > 2.0 {
                    m3 * (n * (n - 1.0)).sqrt() / (n - 2.0)
                } else {
                    m3
                };
                let m4: f64 = finite_values
                    .iter()
                    .map(|&val| ((val - mean) / std).powi(4))
                    .sum::<f64>()
                    / n;
                let kurt = if n > 3.0 {
                    let numerator = (n - 1.0) * ((n + 1.0) * m4 - 3.0 * (n - 1.0));
                    let denominator = (n - 2.0) * (n - 3.0);
                    numerator / denominator
                } else {
                    m4 - 3.0
                };
                skewness_values.push(skew.clamp(-20.0, 20.0));
                kurtosis_values.push(kurt.clamp(-20.0, 20.0));
            }
        }
        let mean_skewness = if skewness_values.is_empty() {
            0.0
        } else {
            skewness_values.iter().sum::<f64>() / skewness_values.len() as f64
        };
        let mean_kurtosis = if kurtosis_values.is_empty() {
            0.0
        } else {
            kurtosis_values.iter().sum::<f64>() / kurtosis_values.len() as f64
        };
        Ok((mean_skewness, mean_kurtosis))
    }
    fn compute_outlier_ratio(&self, x: &ArrayView2<f64>) -> Result<f64> {
        let mut total_outliers = 0;
        let mut total_values = 0;
        for col in x.columns() {
            let mut sorted_col: Vec<f64> = col
                .iter()
                .filter(|&&val| val.is_finite())
                .copied()
                .collect();
            if sorted_col.is_empty() {
                continue;
            }
            sorted_col.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            let n = sorted_col.len();
            if n < 4 {
                continue;
            }
            let q1_idx = (n as f64 * 0.25) as usize;
            let q3_idx = (n as f64 * 0.75) as usize;
            let q1 = sorted_col[q1_idx.min(n - 1)];
            let q3 = sorted_col[q3_idx.min(n - 1)];
            let iqr = q3 - q1;
            if iqr < f64::EPSILON {
                continue;
            }
            let lower_bound = q1 - 1.5 * iqr;
            let upper_bound = q3 + 1.5 * iqr;
            let outliers = col
                .iter()
                .filter(|&&val| val.is_finite() && (val < lower_bound || val > upper_bound))
                .count();
            total_outliers += outliers;
            total_values += col.len();
        }
        if total_values == 0 {
            Ok(0.0)
        } else {
            Ok(total_outliers as f64 / total_values as f64)
        }
    }
}
