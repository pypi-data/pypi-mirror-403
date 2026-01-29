//! Performance metrics calculations.

/// Maximum safe equity value to prevent overflow.
pub const EQUITY_LIMIT: f64 = f64::MAX / 4.0;

/// Calculate Sharpe ratio from period returns.
///
/// Uses sample standard deviation (ddof=1) and annualizes by sqrt(periods_per_year).
pub fn sharpe_ratio(returns: &[f64], periods_per_year: f64) -> f64 {
    if returns.len() < 2 {
        return 0.0;
    }
    let mean = returns.iter().copied().sum::<f64>() / returns.len() as f64;
    let variance = returns
        .iter()
        .map(|r| {
            let diff = r - mean;
            diff * diff
        })
        .sum::<f64>()
        / (returns.len() as f64 - 1.0);
    if variance <= 0.0 {
        return 0.0;
    }
    let std_dev = variance.sqrt();
    mean / std_dev * periods_per_year.sqrt()
}

/// Calculate Sortino ratio from period returns.
///
/// Uses downside deviation (only negative returns) for the denominator.
pub fn sortino_ratio(returns: &[f64], periods_per_year: f64) -> f64 {
    if returns.len() < 2 {
        return 0.0;
    }
    let mean = returns.iter().copied().sum::<f64>() / returns.len() as f64;
    let mut downside_sum = 0.0;
    let mut downside_count = 0usize;
    for r in returns {
        if *r < 0.0 {
            downside_sum += r * r;
            downside_count += 1;
        }
    }
    if downside_count < 2 {
        return 0.0;
    }
    let variance = downside_sum / (downside_count as f64 - 1.0);
    if variance <= 0.0 {
        return 0.0;
    }
    let downside_std = variance.sqrt();
    mean / downside_std * periods_per_year.sqrt()
}

/// Calculate annualized return from total return.
pub fn annualized_return(total_return: f64, periods: usize, periods_per_year: f64) -> f64 {
    if periods == 0 {
        return 0.0;
    }
    if total_return <= -1.0 {
        return -1.0;
    }
    let base = 1.0 + total_return;
    base.powf(periods_per_year / periods as f64) - 1.0
}

/// Calculate Calmar ratio.
///
/// Calmar = Annualized Return / Max Drawdown
pub fn calmar_ratio(annualized: f64, max_drawdown: f64) -> f64 {
    if max_drawdown > 0.0 {
        annualized / max_drawdown
    } else {
        0.0
    }
}

/// Calculate Information Ratio.
///
/// IR = (Portfolio Return - Benchmark Return) / Tracking Error
pub fn information_ratio(
    portfolio_returns: &[f64],
    benchmark_returns: &[f64],
    periods_per_year: f64,
) -> f64 {
    if portfolio_returns.len() != benchmark_returns.len() || portfolio_returns.len() < 2 {
        return 0.0;
    }
    
    let excess_returns: Vec<f64> = portfolio_returns
        .iter()
        .zip(benchmark_returns.iter())
        .map(|(p, b)| p - b)
        .collect();
    
    let mean_excess = excess_returns.iter().sum::<f64>() / excess_returns.len() as f64;
    let variance = excess_returns
        .iter()
        .map(|r| {
            let diff = r - mean_excess;
            diff * diff
        })
        .sum::<f64>()
        / (excess_returns.len() as f64 - 1.0);
    
    if variance <= 0.0 {
        return 0.0;
    }
    
    let tracking_error = variance.sqrt();
    mean_excess / tracking_error * periods_per_year.sqrt()
}

/// Calculate Treynor Ratio.
///
/// Treynor = (Portfolio Return - Risk Free Rate) / Beta
pub fn treynor_ratio(
    portfolio_return: f64,
    risk_free_rate: f64,
    beta: f64,
) -> f64 {
    if beta.abs() < 1e-10 {
        return 0.0;
    }
    (portfolio_return - risk_free_rate) / beta
}

/// Calculate Beta (systematic risk).
///
/// Beta = Cov(Portfolio, Benchmark) / Var(Benchmark)
pub fn calculate_beta(portfolio_returns: &[f64], benchmark_returns: &[f64]) -> f64 {
    if portfolio_returns.len() != benchmark_returns.len() || portfolio_returns.len() < 2 {
        return 1.0;
    }
    
    let port_mean = portfolio_returns.iter().sum::<f64>() / portfolio_returns.len() as f64;
    let bench_mean = benchmark_returns.iter().sum::<f64>() / benchmark_returns.len() as f64;
    
    let mut covariance = 0.0;
    let mut bench_variance = 0.0;
    
    for (p, b) in portfolio_returns.iter().zip(benchmark_returns.iter()) {
        let p_dev = p - port_mean;
        let b_dev = b - bench_mean;
        covariance += p_dev * b_dev;
        bench_variance += b_dev * b_dev;
    }
    
    if bench_variance.abs() < 1e-10 {
        return 1.0;
    }
    
    covariance / bench_variance
}

/// Calculate Alpha (Jensen's Alpha).
///
/// Alpha = Portfolio Return - (Risk Free Rate + Beta * (Benchmark Return - Risk Free Rate))
pub fn calculate_alpha(
    portfolio_return: f64,
    benchmark_return: f64,
    risk_free_rate: f64,
    beta: f64,
) -> f64 {
    portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
}

/// Calculate Value at Risk (VaR) at a given confidence level.
///
/// Uses historical simulation method.
pub fn value_at_risk(returns: &[f64], confidence_level: f64) -> f64 {
    if returns.is_empty() {
        return 0.0;
    }
    
    let mut sorted = returns.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    let index = ((1.0 - confidence_level) * sorted.len() as f64).floor() as usize;
    let index = index.min(sorted.len() - 1);
    
    -sorted[index]  // VaR is typically reported as a positive number
}

/// Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
///
/// Average of returns below the VaR threshold.
pub fn conditional_var(returns: &[f64], confidence_level: f64) -> f64 {
    if returns.is_empty() {
        return 0.0;
    }
    
    let mut sorted = returns.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    let cutoff_index = ((1.0 - confidence_level) * sorted.len() as f64).ceil() as usize;
    let cutoff_index = cutoff_index.max(1).min(sorted.len());
    
    let tail_sum: f64 = sorted[..cutoff_index].iter().sum();
    -tail_sum / cutoff_index as f64
}

/// Calculate maximum consecutive wins.
pub fn max_consecutive_wins(trade_results: &[bool]) -> usize {
    let mut max_wins = 0;
    let mut current_wins = 0;
    
    for &is_win in trade_results {
        if is_win {
            current_wins += 1;
            max_wins = max_wins.max(current_wins);
        } else {
            current_wins = 0;
        }
    }
    
    max_wins
}

/// Calculate maximum consecutive losses.
pub fn max_consecutive_losses(trade_results: &[bool]) -> usize {
    let mut max_losses = 0;
    let mut current_losses = 0;
    
    for &is_win in trade_results {
        if !is_win {
            current_losses += 1;
            max_losses = max_losses.max(current_losses);
        } else {
            current_losses = 0;
        }
    }
    
    max_losses
}

/// Calculate profit factor.
///
/// Profit Factor = Gross Profit / Gross Loss
pub fn profit_factor(gross_profit: f64, gross_loss: f64) -> f64 {
    if gross_loss.abs() < 1e-10 {
        if gross_profit > 0.0 {
            return f64::INFINITY;
        }
        return 0.0;
    }
    gross_profit / gross_loss.abs()
}

/// Calculate recovery factor.
///
/// Recovery Factor = Net Profit / Max Drawdown
pub fn recovery_factor(net_profit: f64, max_drawdown: f64) -> f64 {
    if max_drawdown.abs() < 1e-10 {
        return 0.0;
    }
    net_profit / max_drawdown
}

/// Calculate payoff ratio (average win / average loss).
pub fn payoff_ratio(avg_win: f64, avg_loss: f64) -> f64 {
    if avg_loss.abs() < 1e-10 {
        return 0.0;
    }
    avg_win / avg_loss.abs()
}

/// Calculate Kelly Criterion optimal position size.
///
/// Kelly % = W - (1 - W) / R
/// where W = win probability, R = payoff ratio
pub fn kelly_criterion(win_rate: f64, payoff_ratio: f64) -> f64 {
    if payoff_ratio <= 0.0 {
        return 0.0;
    }
    let kelly = win_rate - (1.0 - win_rate) / payoff_ratio;
    kelly.max(0.0)  // Never recommend negative sizing
}

/// Calculate Ulcer Index (measure of downside volatility).
pub fn ulcer_index(equity_curve: &[f64]) -> f64 {
    if equity_curve.len() < 2 {
        return 0.0;
    }
    
    let mut peak = equity_curve[0];
    let mut sum_sq_dd = 0.0;
    
    for &equity in equity_curve {
        if equity > peak {
            peak = equity;
        }
        let drawdown_pct = (peak - equity) / peak * 100.0;
        sum_sq_dd += drawdown_pct * drawdown_pct;
    }
    
    (sum_sq_dd / equity_curve.len() as f64).sqrt()
}

/// Calculate Ulcer Performance Index (UPI).
///
/// UPI = (Return - Risk Free Rate) / Ulcer Index
pub fn ulcer_performance_index(total_return: f64, risk_free_rate: f64, ulcer_index: f64) -> f64 {
    if ulcer_index.abs() < 1e-10 {
        return 0.0;
    }
    (total_return - risk_free_rate) / ulcer_index
}

/// Calculate Serenity Index.
///
/// Serenity = (CAGR / Max DD) * (Profitable Days / Total Days) * ln(1 + Total Days)
pub fn serenity_index(
    annualized_return: f64,
    max_drawdown: f64,
    win_days: usize,
    total_days: usize,
) -> f64 {
    if max_drawdown.abs() < 1e-10 || total_days == 0 {
        return 0.0;
    }
    
    let return_to_dd = annualized_return / max_drawdown;
    let win_ratio = win_days as f64 / total_days as f64;
    let time_factor = (1.0 + total_days as f64).ln();
    
    return_to_dd * win_ratio * time_factor
}

/// Ensure a value is finite and within safe limits.
pub fn ensure_finite(value: f64, label: &str) -> Result<(), String> {
    if !value.is_finite() || value.abs() > EQUITY_LIMIT {
        return Err(format!("{} overflow", label));
    }
    Ok(())
}

/// Calculate equity checking for overflow.
pub fn checked_equity(cash: f64, marked_value: f64) -> Result<f64, String> {
    let equity = cash + marked_value;
    ensure_finite(equity, "equity")?;
    Ok(equity)
}

/// Get metric value from result for sorting.
pub fn metric_value(
    total_return: f64,
    sharpe: f64,
    sortino: f64,
    max_drawdown: f64,
    calmar: f64,
    win_pct: f64,
    expectancy: f64,
    metric: &str,
) -> f64 {
    match metric {
        "sharpe" => sharpe,
        "sortino" => sortino,
        "max_drawdown" => -max_drawdown,
        "calmar" => calmar,
        "win_pct" => win_pct,
        "expectancy" => expectancy,
        _ => total_return,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sharpe_ratio() {
        let returns = vec![0.01, 0.02, -0.01, 0.015, 0.005];
        let sharpe = sharpe_ratio(&returns, 252.0);
        assert!(sharpe > 0.0);
    }

    #[test]
    fn test_sortino_ratio() {
        // Need at least 2 negative returns for sortino calculation
        let returns = vec![0.01, 0.02, -0.01, 0.015, -0.005, 0.01, -0.02];
        let sortino = sortino_ratio(&returns, 252.0);
        assert!(sortino > 0.0);
    }

    #[test]
    fn test_value_at_risk() {
        let returns = vec![-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07];
        let var_95 = value_at_risk(&returns, 0.95);
        assert!(var_95 > 0.0);
    }

    #[test]
    fn test_profit_factor() {
        assert_eq!(profit_factor(1000.0, 500.0), 2.0);
        assert_eq!(profit_factor(1000.0, 0.0), f64::INFINITY);
    }

    #[test]
    fn test_kelly_criterion() {
        // 60% win rate, 1.5:1 payoff ratio
        let kelly = kelly_criterion(0.6, 1.5);
        assert!(kelly > 0.0 && kelly < 1.0);
    }
}
