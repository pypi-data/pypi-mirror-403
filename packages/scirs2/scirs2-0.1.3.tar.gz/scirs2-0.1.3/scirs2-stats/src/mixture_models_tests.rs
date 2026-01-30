use super::*;

#[cfg(test)]
mod tests {
    use super::*;
    use scirs2_core::ndarray::array;

    #[test]
    fn test_advanced_gmm_basic() {
        let data = array![
            [1.0, 2.0],
            [1.1, 2.1],
            [0.9, 1.9],
            [5.0, 6.0],
            [5.1, 6.1],
            [4.9, 5.9]
        ];

        let config = GMMConfig {
            max_iter: 50,
            tolerance: 1e-4,
            n_init: 2,
            ..Default::default()
        };

        let mut gmm = GaussianMixtureModel::new(2, config).expect("Test: operation failed");
        let params = gmm.fit(&data.view()).expect("Test: operation failed");

        assert_eq!(params.weights.len(), 2);
        assert!(params.converged);
        assert!(params.log_likelihood.is_finite());
    }

    #[test]
    fn test_robust_gmm() {
        let data = array![
            [1.0, 2.0],
            [1.1, 2.1],
            [0.9, 1.9],
            [100.0, 100.0], // Outlier
            [5.0, 6.0],
            [5.1, 6.1]
        ];

        let mut robust_gmm = RobustGMM::new(2, 0.1f64, 0.2f64, GMMConfig::default())
            .expect("Test: operation failed");

        let params = robust_gmm
            .fit(&data.view())
            .expect("Test: operation failed");
        assert!(params.outlier_scores.is_some());

        let outliers = robust_gmm
            .detect_outliers(&data.view())
            .expect("Test: operation failed");
        assert_eq!(outliers.len(), data.nrows());
    }

    #[test]
    fn test_streaming_gmm() {
        let batch1 = array![[1.0, 2.0], [1.1, 2.1], [0.9, 1.9]];

        let batch2 = array![[5.0, 6.0], [5.1, 6.1], [4.9, 5.9]];

        let mut streaming_gmm = StreamingGMM::new(2, 0.1f64, 0.9f64, GMMConfig::default())
            .expect("Test: operation failed");

        streaming_gmm
            .partial_fit(&batch1.view())
            .expect("Test: operation failed");
        streaming_gmm
            .partial_fit(&batch2.view())
            .expect("Test: operation failed");

        let params = streaming_gmm
            .get_parameters()
            .expect("Test: operation failed");
        assert_eq!(params.weights.len(), 2);
    }

    #[test]
    fn test_gmm_model_selection() {
        let data = array![
            [1.0, 2.0],
            [1.1, 2.1],
            [0.9, 1.9],
            [5.0, 6.0],
            [5.1, 6.1],
            [4.9, 5.9],
            [3.0, 3.0],
            [3.1, 3.1],
            [2.9, 2.9]
        ];

        let (best_n, params) = gmm_model_selection(
            &data.view(),
            2,
            4,
            Some(GMMConfig {
                max_iter: 20,
                ..Default::default()
            }),
        )
        .expect("Test: operation failed");

        assert!(best_n >= 2 && best_n <= 4);
        assert!(params.model_selection.bic.is_finite());
    }

    #[test]
    fn test_variational_gmm() {
        let data = array![
            [1.0, 2.0],
            [1.1, 2.1],
            [0.9, 1.9],
            [5.0, 6.0],
            [5.1, 6.1],
            [4.9, 5.9]
        ];

        let mut vgmm = VariationalGMM::new(2, VariationalGMMConfig::default());
        let result = vgmm.fit(&data.view()).expect("Test: operation failed");

        assert!(result.lower_bound > f64::NEG_INFINITY);
        assert!(result.effective_components > 0);
    }
}

/// Variational Bayesian Gaussian Mixture Model
pub struct VariationalGMM<F> {
    /// Maximum number of components
    pub max_components: usize,
    /// Configuration
    pub config: VariationalGMMConfig,
    /// Fitted parameters
    pub parameters: Option<VariationalGMMParameters<F>>,
    /// Lower bound history
    pub lower_bound_history: Vec<F>,
    _phantom: PhantomData<F>,
}

/// Configuration for Variational GMM
#[derive(Debug, Clone)]
pub struct VariationalGMMConfig {
    /// Maximum iterations
    pub max_iter: usize,
    /// Convergence tolerance
    pub tolerance: f64,
    /// Concentration parameter for Dirichlet prior
    pub alpha: f64,
    /// Degrees of freedom for Wishart prior
    pub nu: f64,
    /// Prior mean
    pub mean_prior: Option<Vec<f64>>,
    /// Prior precision matrix
    pub precision_prior: Option<Vec<Vec<f64>>>,
    /// Enable automatic relevance determination
    pub ard: bool,
    /// Random seed
    pub seed: Option<u64>,
}

impl Default for VariationalGMMConfig {
    fn default() -> Self {
        Self {
            max_iter: 100,
            tolerance: 1e-6,
            alpha: 1.0,
            nu: 1.0,
            mean_prior: None,
            precision_prior: None,
            ard: true,
            seed: None,
        }
    }
}

/// Variational GMM parameters
#[derive(Debug, Clone)]
pub struct VariationalGMMParameters<F> {
    /// Component weights (posterior Dirichlet parameters)
    pub weight_concentration: Array1<F>,
    /// Component means (posterior normal parameters)
    pub mean_precision: Array1<F>,
    pub means: Array2<F>,
    /// Component precisions (posterior Wishart parameters)
    pub degrees_of_freedom: Array1<F>,
    pub scale_matrices: Array3<F>,
    /// Lower bound
    pub lower_bound: F,
    /// Effective number of components
    pub effective_components: usize,
    /// Number of iterations
    pub n_iter: usize,
    /// Converged flag
    pub converged: bool,
}

/// Variational GMM result
#[derive(Debug, Clone)]
pub struct VariationalGMMResult<F> {
    /// Lower bound value
    pub lower_bound: F,
    /// Effective number of components
    pub effective_components: usize,
    /// Predictive probabilities
    pub responsibilities: Array2<F>,
    /// Component weights
    pub weights: Array1<F>,
}

impl<F> VariationalGMM<F>
where
    F: Float
        + FromPrimitive
        + SimdUnifiedOps
        + Send
        + Sync
        + std::fmt::Debug
        + std::fmt::Display
        + std::iter::Sum<F>,
{
    /// Create new Variational GMM
    pub fn new(_maxcomponents: usize, config: VariationalGMMConfig) -> Self {
        Self {
            max_components: _maxcomponents,
            config,
            parameters: None,
            lower_bound_history: Vec::new(),
            _phantom: PhantomData,
        }
    }

    /// Fit Variational GMM to data
    pub fn fit(&mut self, data: &ArrayView2<F>) -> StatsResult<VariationalGMMResult<F>> {
        let (_n_samples_, n_features) = data.dim();

        // Initialize parameters
        let mut weight_concentration = Array1::from_elem(
            self.max_components,
            F::from(self.config.alpha).expect("Failed to convert to float"),
        );
        let mut mean_precision = Array1::from_elem(self.max_components, F::one());
        let mut means = self.initialize_means(data)?;
        let mut degrees_of_freedom = Array1::from_elem(
            self.max_components,
            F::from(self.config.nu + n_features as f64).expect("Failed to convert to float"),
        );
        let mut scale_matrices = Array3::zeros((self.max_components, n_features, n_features));

        // Initialize scale matrices as identity
        for k in 0..self.max_components {
            for i in 0..n_features {
                scale_matrices[[k, i, i]] = F::one();
            }
        }

        let mut lower_bound = F::neg_infinity();
        let mut converged = false;

        for iteration in 0..self.config.max_iter {
            // E-step: Update responsibilities
            let responsibilities = self.compute_responsibilities(
                data,
                &means,
                &scale_matrices,
                &degrees_of_freedom,
                &weight_concentration,
            )?;

            // M-step: Update parameters
            let (
                new_weight_concentration,
                new_mean_precision,
                new_means,
                new_degrees_of_freedom,
                new_scale_matrices,
            ) = self.update_parameters(data, &responsibilities)?;

            // Compute lower bound
            let new_lower_bound = self.compute_lower_bound(
                data,
                &responsibilities,
                &new_weight_concentration,
                &new_means,
                &new_scale_matrices,
            )?;

            // Check convergence
            if iteration > 0
                && (new_lower_bound - lower_bound).abs()
                    < F::from(self.config.tolerance).expect("Failed to convert to float")
            {
                converged = true;
            }

            // Update parameters
            weight_concentration = new_weight_concentration;
            mean_precision = new_mean_precision;
            means = new_means;
            degrees_of_freedom = new_degrees_of_freedom;
            scale_matrices = new_scale_matrices;
            lower_bound = new_lower_bound;

            self.lower_bound_history.push(lower_bound);

            if converged {
                break;
            }
        }

        // Compute effective number of components
        let effective_components = self.compute_effective_components(&weight_concentration);

        // Compute final responsibilities and weights
        let responsibilities = self.compute_responsibilities(
            data,
            &means,
            &scale_matrices,
            &degrees_of_freedom,
            &weight_concentration,
        )?;
        let weights = self.compute_weights(&weight_concentration);

        let parameters = VariationalGMMParameters {
            weight_concentration,
            mean_precision,
            means,
            degrees_of_freedom,
            scale_matrices,
            lower_bound,
            effective_components,
            n_iter: self.lower_bound_history.len(),
            converged,
        };

        self.parameters = Some(parameters);

        Ok(VariationalGMMResult {
            lower_bound,
            effective_components,
            responsibilities,
            weights,
        })
    }

    /// Initialize means for variational GMM
    fn initialize_means(&self, data: &ArrayView2<F>) -> StatsResult<Array2<F>> {
        let (n_samples_, n_features) = data.dim();
        let mut means = Array2::zeros((self.max_components, n_features));

        use scirs2_core::random::Random;
        let mut init_rng = scirs2_core::random::thread_rng();
        let mut rng = match self.config.seed {
            Some(seed) => Random::seed(seed),
            None => Random::seed(init_rng.random()),
        };

        for i in 0..self.max_components {
            let idx = rng.random_range(0..n_samples_);
            means.row_mut(i).assign(&data.row(idx));
        }

        Ok(means)
    }

    /// Compute responsibilities (E-step)
    fn compute_responsibilities(
        &self,
        data: &ArrayView2<F>,
        means: &Array2<F>,
        scale_matrices: &Array3<F>,
        degrees_of_freedom: &Array1<F>,
        weight_concentration: &Array1<F>,
    ) -> StatsResult<Array2<F>> {
        let n_samples_ = data.shape()[0];
        let mut responsibilities = Array2::zeros((n_samples_, self.max_components));

        for i in 0..n_samples_ {
            let mut log_probs = Array1::zeros(self.max_components);

            for k in 0..self.max_components {
                // Compute log probability for component k
                let log_weight = self.compute_log_weight(weight_concentration[k]);
                let log_likelihood = self.compute_log_likelihood_component(
                    &data.row(i),
                    &means.row(k),
                    &scale_matrices.slice(s![k, .., ..]),
                    degrees_of_freedom[k],
                )?;
                log_probs[k] = log_weight + log_likelihood;
            }

            // Normalize responsibilities
            let log_sum = self.log_sum_exp(&log_probs);
            for k in 0..self.max_components {
                responsibilities[[i, k]] = (log_probs[k] - log_sum).exp();
            }
        }

        Ok(responsibilities)
    }

    /// Update parameters (M-step)
    fn update_parameters(
        &self,
        data: &ArrayView2<F>,
        responsibilities: &Array2<F>,
    ) -> StatsResult<(Array1<F>, Array1<F>, Array2<F>, Array1<F>, Array3<F>)> {
        let (n_samples_, n_features) = data.dim();

        // Update weight concentration
        let mut weight_concentration = Array1::from_elem(
            self.max_components,
            F::from(self.config.alpha).expect("Failed to convert to float"),
        );
        for k in 0..self.max_components {
            let nk: F = responsibilities.column(k).sum();
            weight_concentration[k] = weight_concentration[k] + nk;
        }

        // Update means and precisions
        let mean_precision = Array1::ones(self.max_components);
        let mut means = Array2::zeros((self.max_components, n_features));
        let mut degrees_of_freedom = Array1::from_elem(
            self.max_components,
            F::from(self.config.nu + n_features as f64).expect("Failed to convert to float"),
        );
        let mut scale_matrices = Array3::zeros((self.max_components, n_features, n_features));

        for k in 0..self.max_components {
            let nk: F = responsibilities.column(k).sum();

            if nk > F::zero() {
                // Update mean
                for j in 0..n_features {
                    let mut weighted_sum = F::zero();
                    for i in 0..n_samples_ {
                        weighted_sum = weighted_sum + responsibilities[[i, k]] * data[[i, j]];
                    }
                    means[[k, j]] = weighted_sum / nk;
                }

                // Update degrees of freedom
                degrees_of_freedom[k] =
                    F::from(self.config.nu).expect("Failed to convert to float") + nk;

                // Update scale matrix (simplified)
                for i in 0..n_features {
                    scale_matrices[[k, i, i]] =
                        F::one() + F::from(0.1).expect("Failed to convert constant to float") * nk;
                }
            }
        }

        Ok((
            weight_concentration,
            mean_precision,
            means,
            degrees_of_freedom,
            scale_matrices,
        ))
    }

    /// Compute lower bound
    fn compute_lower_bound(
        &self,
        data: &ArrayView2<F>,
        responsibilities: &Array2<F>,
        weight_concentration: &Array1<F>,
        means: &Array2<F>,
        scale_matrices: &Array3<F>,
    ) -> StatsResult<F> {
        let n_samples_ = data.shape()[0];
        let mut lower_bound = F::zero();

        // Expected log likelihood
        for i in 0..n_samples_ {
            for k in 0..self.max_components {
                if responsibilities[[i, k]] > F::zero() {
                    let log_likelihood = self.compute_log_likelihood_component(
                        &data.row(i),
                        &means.row(k),
                        &scale_matrices.slice(s![k, .., ..]),
                        F::from(10.0).expect("Failed to convert constant to float"), // simplified
                    )?;
                    lower_bound = lower_bound + responsibilities[[i, k]] * log_likelihood;
                }
            }
        }

        // KL divergence terms (simplified)
        for k in 0..self.max_components {
            let weight_contrib = weight_concentration[k] * weight_concentration[k].ln();
            lower_bound = lower_bound
                - weight_contrib * F::from(0.01).expect("Failed to convert constant to float");
        }

        Ok(lower_bound)
    }

    /// Compute effective number of components
    fn compute_effective_components(&self, weightconcentration: &Array1<F>) -> usize {
        let total: F = weightconcentration.sum();
        let mut effective = 0;

        for &weight in weightconcentration.iter() {
            let proportion = weight / total;
            if proportion > F::from(0.01).expect("Failed to convert constant to float") {
                // 1% threshold
                effective += 1;
            }
        }

        effective
    }

    /// Compute component weights
    fn compute_weights(&self, weightconcentration: &Array1<F>) -> Array1<F> {
        let total: F = weightconcentration.sum();
        weightconcentration.mapv(|w| w / total)
    }

    /// Compute log weight
    fn compute_log_weight(&self, concentration: F) -> F {
        concentration.ln()
    }

    /// Compute log likelihood for a component (simplified)
    fn compute_log_likelihood_component(
        &self,
        point: &ArrayView1<F>,
        mean: &ArrayView1<F>,
        _scale_matrix: &scirs2_core::ndarray::ArrayBase<
            scirs2_core::ndarray::ViewRepr<&F>,
            scirs2_core::ndarray::Dim<[usize; 2]>,
        >,
        _degrees_of_freedom: F,
    ) -> StatsResult<F> {
        // Simplified Gaussian log likelihood
        let mut sum_sq = F::zero();
        for (x, m) in point.iter().zip(mean.iter()) {
            let diff = *x - *m;
            sum_sq = sum_sq + diff * diff;
        }

        let log_likelihood = -F::from(0.5).expect("Failed to convert constant to float") * sum_sq;
        Ok(log_likelihood)
    }

    /// Log-sum-exp for numerical stability
    fn log_sum_exp(&self, logvalues: &Array1<F>) -> F {
        let max_val = logvalues.iter().fold(F::neg_infinity(), |a, &b| a.max(b));
        if max_val == F::neg_infinity() {
            return F::neg_infinity();
        }

        let sum: F = logvalues.iter().map(|&x| (x - max_val).exp()).sum();

        max_val + sum.ln()
    }
}
