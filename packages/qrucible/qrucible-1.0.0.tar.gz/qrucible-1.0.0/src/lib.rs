//! Qrucible: Hybrid stateful backtesting engine with Rust hot path and Python bindings.
//!
//! This crate provides a high-performance backtesting engine that executes path-dependent
//! logic at vectorized speeds while exposing a clean Python API.
//!
//! # Features
//!
//! - **20+ Technical Indicators**: MA variants (SMA, EMA, WMA, DEMA, TEMA, KAMA, HMA),
//!   momentum (RSI, MACD, Stochastic, Williams %R, MFI, TSI, ROC, Ultimate Oscillator),
//!   volatility (Bollinger, ATR, Keltner, Donchian), trend (ADX, CCI, Aroon, Ichimoku,
//!   SuperTrend, Parabolic SAR), and volume (OBV, VWAP, A/D Line, CMF).
//!
//! - **Advanced Order Types**: Trailing stops (percentage and ATR-based), break-even stops,
//!   time-based stops, partial exits (scaling out), and pyramiding (scaling in).
//!
//! - **Risk Management**: Risk-per-trade sizing, ATR-based stops, max drawdown exit,
//!   reduce-after-loss, margin tracking, and position size limits.
//!
//! - **Execution Realism**: Commission, slippage, and bid-ask spread modeling.
//!
//! - **Comprehensive Metrics**: Sharpe, Sortino, Calmar, VaR, CVaR, profit factor,
//!   Kelly criterion, Ulcer index, MAE/MFE, and more.
//!
//! - **Grid Search**: Parallel parameter sweeps with Rayon.

pub mod config;
pub mod data;
pub mod engine;
pub mod indicators;
pub mod metrics;
pub mod portfolio;
pub mod result;

use pyo3::prelude::*;

// Re-export main types for convenience
pub use config::{
    BreakEvenConfig, PartialExitConfig, PyramidConfig, StrategyConfig, TimeStopConfig,
    TrailingStopConfig,
};
pub use data::{load_bars, load_bars_csv, load_bars_parquet, BarData};
pub use engine::{grid_search, run_backtest, run_backtest_with_signals};
pub use result::{BacktestResult, EquityPoint, Trade};

/// Python module registration.
#[pymodule]
fn qrucible(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Configuration classes
    m.add_class::<StrategyConfig>()?;
    m.add_class::<TrailingStopConfig>()?;
    m.add_class::<BreakEvenConfig>()?;
    m.add_class::<TimeStopConfig>()?;
    m.add_class::<PartialExitConfig>()?;
    m.add_class::<PyramidConfig>()?;

    // Data classes
    m.add_class::<BarData>()?;

    // Result classes
    m.add_class::<BacktestResult>()?;
    m.add_class::<Trade>()?;
    m.add_class::<EquityPoint>()?;

    // Functions
    m.add_function(wrap_pyfunction!(load_bars, m)?)?;
    m.add_function(wrap_pyfunction!(load_bars_csv, m)?)?;
    m.add_function(wrap_pyfunction!(load_bars_parquet, m)?)?;
    m.add_function(wrap_pyfunction!(run_backtest, m)?)?;
    m.add_function(wrap_pyfunction!(run_backtest_with_signals, m)?)?;
    m.add_function(wrap_pyfunction!(grid_search, m)?)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::indicators::moving_averages::*;
    use crate::indicators::momentum::*;
    use crate::indicators::volatility::*;

    #[test]
    fn test_ma_state_signals() {
        let mut state = MaCrossState::new(2, 3, "SMA");
        let signal = state.update(1.0);
        assert!(!signal.long && !signal.short);
        let signal = state.update(2.0);
        assert!(!signal.long && !signal.short);
        let signal = state.update(3.0);
        assert!(signal.long);
        assert!(!signal.short);
        let signal = state.update(0.0);
        assert!(signal.short);
        assert!(!signal.long);
    }

    #[test]
    fn test_rsi_state_signals() {
        let mut rising = RsiState::new(3, 30.0, 70.0);
        assert!(!rising.update(1.0).short);
        assert!(!rising.update(2.0).short);
        assert!(!rising.update(3.0).short);
        let signal = rising.update(4.0);
        assert!(signal.short);
        assert!(!signal.long);

        let mut falling = RsiState::new(3, 30.0, 70.0);
        assert!(!falling.update(4.0).long);
        assert!(!falling.update(3.0).long);
        assert!(!falling.update(2.0).long);
        let signal = falling.update(1.0);
        assert!(signal.long);
        assert!(!signal.short);
    }

    #[test]
    fn test_bollinger_state_signals() {
        let mut short_band = BollingerState::new(2, 0.5);
        assert!(!short_band.update(1.0).short);
        let signal = short_band.update(3.0);
        assert!(signal.short);
        assert!(!signal.long);

        let mut long_band = BollingerState::new(2, 0.5);
        assert!(!long_band.update(3.0).long);
        let signal = long_band.update(1.0);
        assert!(signal.long);
        assert!(!signal.short);
    }

    #[test]
    fn test_ema_calculation() {
        let mut ema = EmaState::new(3);
        assert!(ema.update(1.0).is_none());
        assert!(ema.update(2.0).is_none());
        let result = ema.update(3.0);
        assert!(result.is_some());
        // First EMA value should be SMA
        assert!((result.unwrap() - 2.0).abs() < 0.01);
    }

    #[test]
    fn test_atr_calculation() {
        let mut atr = AtrState::new(3, 2.0);
        atr.update(102.0, 98.0, 100.0);
        atr.update(103.0, 99.0, 101.0);
        atr.update(104.0, 100.0, 102.0);
        assert!(atr.current_atr().is_some());
        assert!(atr.current_atr().unwrap() > 0.0);
    }

    #[test]
    fn test_macd_signals() {
        let mut macd = MacdState::new(3, 5, 2);
        // Feed some rising values
        for i in 0..15 {
            macd.update(100.0 + i as f64);
        }
        assert!(macd.current().is_some());
    }

    #[test]
    fn test_stochastic() {
        let mut stoch = StochasticState::new(5, 3, 20.0, 80.0);
        for _ in 0..10 {
            stoch.update(100.0, 95.0, 98.0);
        }
        let (k, d) = stoch.current().unwrap();
        assert!(k >= 0.0 && k <= 100.0);
        assert!(d >= 0.0 && d <= 100.0);
    }
}
