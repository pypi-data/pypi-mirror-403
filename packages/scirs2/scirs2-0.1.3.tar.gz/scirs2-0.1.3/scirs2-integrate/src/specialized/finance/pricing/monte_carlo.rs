//! Monte Carlo methods for option pricing

use crate::error::IntegrateResult;
use crate::specialized::finance::models::VolatilityModel;
use crate::specialized::finance::solvers::StochasticPDESolver;
use crate::specialized::finance::types::{FinancialOption, OptionStyle, OptionType};
use scirs2_core::random::{Rng, StandardNormal};

/// Monte Carlo pricing implementation with variance reduction techniques
pub fn price_monte_carlo(
    solver: &StochasticPDESolver,
    option: &FinancialOption,
    n_paths: usize,
    antithetic: bool,
) -> IntegrateResult<f64> {
    match &solver.volatility_model {
        VolatilityModel::Constant(sigma) => {
            monte_carlo_black_scholes(option, *sigma, n_paths, antithetic)
        }
        VolatilityModel::Heston {
            v0,
            theta,
            kappa,
            sigma,
            rho,
        } => monte_carlo_heston(
            option, *v0, *theta, *kappa, *sigma, *rho, n_paths, antithetic,
        ),
        _ => Err(crate::error::IntegrateError::ValueError(
            "Monte Carlo not implemented for this volatility model yet".to_string(),
        )),
    }
}

/// Monte Carlo pricing for Black-Scholes model
fn monte_carlo_black_scholes(
    option: &FinancialOption,
    sigma: f64,
    n_paths: usize,
    antithetic: bool,
) -> IntegrateResult<f64> {
    let mut rng = scirs2_core::random::thread_rng();
    let normal = StandardNormal;

    let dt = option.maturity / 252.0; // Daily time steps
    let n_steps = 252;
    let drift = (option.risk_free_rate - option.dividend_yield - 0.5 * sigma * sigma) * dt;
    let vol_sqrt_dt = sigma * dt.sqrt();

    let mut payoff_sum = 0.0;
    let effective_paths = if antithetic { n_paths / 2 } else { n_paths };

    for _ in 0..effective_paths {
        // Standard path
        let mut s = option.spot;
        let mut path_sum = 0.0; // For Asian options

        for _ in 0..n_steps {
            let z: f64 = rng.sample(normal);
            s *= (drift + vol_sqrt_dt * z).exp();
            path_sum += s;
        }

        let payoff = calculate_payoff(option, s, path_sum / n_steps as f64);
        payoff_sum += payoff;

        // Antithetic path (use -z)
        if antithetic {
            let mut s_anti = option.spot;
            let mut path_sum_anti = 0.0;

            for _ in 0..n_steps {
                let z: f64 = rng.sample(normal);
                s_anti *= (drift - vol_sqrt_dt * z).exp(); // Note: -z
                path_sum_anti += s_anti;
            }

            let payoff_anti = calculate_payoff(option, s_anti, path_sum_anti / n_steps as f64);
            payoff_sum += payoff_anti;
        }
    }

    let actual_paths = if antithetic { n_paths } else { effective_paths };
    let discounted_payoff =
        (payoff_sum / actual_paths as f64) * (-option.risk_free_rate * option.maturity).exp();

    Ok(discounted_payoff)
}

/// Monte Carlo pricing for Heston stochastic volatility model
fn monte_carlo_heston(
    option: &FinancialOption,
    v0: f64,
    theta: f64,
    kappa: f64,
    sigma: f64,
    rho: f64,
    n_paths: usize,
    antithetic: bool,
) -> IntegrateResult<f64> {
    let mut rng = scirs2_core::random::thread_rng();
    let normal = StandardNormal;

    let dt = option.maturity / 252.0;
    let n_steps = 252;
    let sqrt_dt = dt.sqrt();
    let sqrt_1_minus_rho2 = (1.0 - rho * rho).sqrt();

    let mut payoff_sum = 0.0;
    let effective_paths = if antithetic { n_paths / 2 } else { n_paths };

    for _ in 0..effective_paths {
        // Standard path
        let mut s = option.spot;
        let mut v = v0.max(0.0);
        let mut path_sum = 0.0;

        for _ in 0..n_steps {
            let z1: f64 = rng.sample(normal);
            let z2: f64 = rng.sample(normal);

            // Correlated Brownian motions
            let dw_s = z1;
            let dw_v = rho * z1 + sqrt_1_minus_rho2 * z2;

            // Update variance (Euler-Maruyama with full truncation)
            let sqrt_v = v.sqrt();
            v += kappa * (theta - v) * dt + sigma * sqrt_v * sqrt_dt * dw_v;
            v = v.max(0.0); // Ensure non-negative variance

            // Update stock price
            let drift = (option.risk_free_rate - option.dividend_yield - 0.5 * v) * dt;
            s *= (drift + sqrt_v * sqrt_dt * dw_s).exp();
            path_sum += s;
        }

        let payoff = calculate_payoff(option, s, path_sum / n_steps as f64);
        payoff_sum += payoff;

        // Antithetic path
        if antithetic {
            let mut s_anti = option.spot;
            let mut v_anti = v0.max(0.0);
            let mut path_sum_anti = 0.0;

            for _ in 0..n_steps {
                let z1: f64 = rng.sample(normal);
                let z2: f64 = rng.sample(normal);

                let dw_s = -z1; // Antithetic
                let dw_v = -rho * z1 - sqrt_1_minus_rho2 * z2; // Antithetic

                let sqrt_v = v_anti.sqrt();
                v_anti += kappa * (theta - v_anti) * dt + sigma * sqrt_v * sqrt_dt * dw_v;
                v_anti = v_anti.max(0.0);

                let drift = (option.risk_free_rate - option.dividend_yield - 0.5 * v_anti) * dt;
                s_anti *= (drift + sqrt_v * sqrt_dt * dw_s).exp();
                path_sum_anti += s_anti;
            }

            let payoff_anti = calculate_payoff(option, s_anti, path_sum_anti / n_steps as f64);
            payoff_sum += payoff_anti;
        }
    }

    let actual_paths = if antithetic { n_paths } else { effective_paths };
    let discounted_payoff =
        (payoff_sum / actual_paths as f64) * (-option.risk_free_rate * option.maturity).exp();

    Ok(discounted_payoff)
}

/// Calculate payoff based on option style
fn calculate_payoff(option: &FinancialOption, final_price: f64, average_price: f64) -> f64 {
    match option.option_style {
        OptionStyle::European | OptionStyle::American => match option.option_type {
            OptionType::Call => (final_price - option.strike).max(0.0),
            OptionType::Put => (option.strike - final_price).max(0.0),
        },
        OptionStyle::Asian => match option.option_type {
            OptionType::Call => (average_price - option.strike).max(0.0),
            OptionType::Put => (option.strike - average_price).max(0.0),
        },
        OptionStyle::Barrier {
            barrier,
            is_up,
            is_knock_in,
        } => {
            // Simplified barrier check (only checks final price)
            let barrier_hit = if is_up {
                final_price >= barrier
            } else {
                final_price <= barrier
            };

            let barrier_active = if is_knock_in {
                barrier_hit
            } else {
                !barrier_hit
            };

            if barrier_active {
                match option.option_type {
                    OptionType::Call => (final_price - option.strike).max(0.0),
                    OptionType::Put => (option.strike - final_price).max(0.0),
                }
            } else {
                0.0
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::specialized::finance::models::VolatilityModel;
    use crate::specialized::finance::types::{FinanceMethod, OptionType};

    #[test]
    fn test_monte_carlo_european_call() {
        let option = FinancialOption {
            option_type: OptionType::Call,
            option_style: OptionStyle::European,
            strike: 100.0,
            maturity: 1.0,
            spot: 100.0,
            risk_free_rate: 0.05,
            dividend_yield: 0.0,
        };

        let solver = StochasticPDESolver::new(
            100,
            50,
            VolatilityModel::Constant(0.2),
            FinanceMethod::MonteCarlo {
                n_paths: 10000,
                antithetic: true,
            },
        );

        let price = price_monte_carlo(&solver, &option, 10000, true).expect("Operation failed");

        // Black-Scholes reference: ~10.45
        assert!(price > 8.0 && price < 13.0, "Price: {}", price);
    }

    #[test]
    fn test_monte_carlo_european_put() {
        let option = FinancialOption {
            option_type: OptionType::Put,
            option_style: OptionStyle::European,
            strike: 100.0,
            maturity: 1.0,
            spot: 100.0,
            risk_free_rate: 0.05,
            dividend_yield: 0.0,
        };

        let solver = StochasticPDESolver::new(
            100,
            50,
            VolatilityModel::Constant(0.2),
            FinanceMethod::MonteCarlo {
                n_paths: 10000,
                antithetic: true,
            },
        );

        let price = price_monte_carlo(&solver, &option, 10000, true).expect("Operation failed");

        // Black-Scholes reference: ~5.57
        assert!(price > 4.0 && price < 7.5, "Price: {}", price);
    }

    #[test]
    fn test_monte_carlo_asian_call() {
        let option = FinancialOption {
            option_type: OptionType::Call,
            option_style: OptionStyle::Asian,
            strike: 100.0,
            maturity: 1.0,
            spot: 100.0,
            risk_free_rate: 0.05,
            dividend_yield: 0.0,
        };

        let solver = StochasticPDESolver::new(
            100,
            50,
            VolatilityModel::Constant(0.2),
            FinanceMethod::MonteCarlo {
                n_paths: 10000,
                antithetic: true,
            },
        );

        let price = price_monte_carlo(&solver, &option, 10000, true).expect("Operation failed");

        // Asian options are cheaper than European
        assert!(price > 3.0 && price < 8.0, "Price: {}", price);
    }
}
