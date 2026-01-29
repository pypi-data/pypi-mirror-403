//! Strategy configuration and validation.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Strategy type enumeration for internal use.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StrategyKind {
    MaCross,
    Rsi,
    Bollinger,
    Macd,
    Stochastic,
    Adx,
    Atr,
    Cci,
    Obv,
    Vwap,
    Keltner,
    Donchian,
    Ichimoku,
    SuperTrend,
    Williams,
    Aroon,
    Mfi,
    Roc,
    Tsi,
    UltimateOscillator,
    External,
}

/// Order type for position management.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum OrderType {
    #[default]
    Market,
    StopLoss,
    TakeProfit,
    TrailingStop,
    TrailingTakeProfit,
    TimeStop,
    BreakEvenStop,
}

/// Configuration for trailing stop behavior.
#[pyclass]
#[derive(Clone, Debug)]
pub struct TrailingStopConfig {
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub trail_pct: f64,           // Trail by percentage (e.g., 0.02 = 2%)
    #[pyo3(get, set)]
    pub trail_atr_mult: f64,      // Trail by ATR multiple (0 = disabled)
    #[pyo3(get, set)]
    pub activation_pct: f64,      // Only activate after this profit % (0 = immediate)
}

#[pymethods]
impl TrailingStopConfig {
    #[new]
    #[pyo3(signature = (enabled = false, trail_pct = 0.02, trail_atr_mult = 0.0, activation_pct = 0.0))]
    fn new(enabled: bool, trail_pct: f64, trail_atr_mult: f64, activation_pct: f64) -> Self {
        Self {
            enabled,
            trail_pct,
            trail_atr_mult,
            activation_pct,
        }
    }
}

impl Default for TrailingStopConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            trail_pct: 0.02,
            trail_atr_mult: 0.0,
            activation_pct: 0.0,
        }
    }
}

/// Configuration for break-even stop behavior.
#[pyclass]
#[derive(Clone, Debug)]
pub struct BreakEvenConfig {
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub trigger_pct: f64,         // Move to break-even after this profit %
    #[pyo3(get, set)]
    pub offset_pct: f64,          // Offset from entry (e.g., 0.001 = 0.1% profit locked)
}

#[pymethods]
impl BreakEvenConfig {
    #[new]
    #[pyo3(signature = (enabled = false, trigger_pct = 0.01, offset_pct = 0.001))]
    fn new(enabled: bool, trigger_pct: f64, offset_pct: f64) -> Self {
        Self {
            enabled,
            trigger_pct,
            offset_pct,
        }
    }
}

impl Default for BreakEvenConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            trigger_pct: 0.01,
            offset_pct: 0.001,
        }
    }
}

/// Configuration for time-based stops.
#[pyclass]
#[derive(Clone, Debug)]
pub struct TimeStopConfig {
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub max_bars: usize,          // Maximum bars to hold a position
    #[pyo3(get, set)]
    pub max_duration_us: i64,     // Maximum duration in microseconds (0 = disabled)
}

#[pymethods]
impl TimeStopConfig {
    #[new]
    #[pyo3(signature = (enabled = false, max_bars = 100, max_duration_us = 0))]
    fn new(enabled: bool, max_bars: usize, max_duration_us: i64) -> Self {
        Self {
            enabled,
            max_bars,
            max_duration_us,
        }
    }
}

impl Default for TimeStopConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            max_bars: 100,
            max_duration_us: 0,
        }
    }
}

/// Configuration for partial exits (scaling out).
#[pyclass]
#[derive(Clone, Debug)]
pub struct PartialExitConfig {
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub exit_pct: f64,            // Percentage of position to exit (e.g., 0.5 = 50%)
    #[pyo3(get, set)]
    pub trigger_pct: f64,         // Profit % to trigger partial exit
    #[pyo3(get, set)]
    pub move_stop_to_entry: bool, // Move stop to entry after partial exit
}

#[pymethods]
impl PartialExitConfig {
    #[new]
    #[pyo3(signature = (enabled = false, exit_pct = 0.5, trigger_pct = 0.02, move_stop_to_entry = true))]
    fn new(enabled: bool, exit_pct: f64, trigger_pct: f64, move_stop_to_entry: bool) -> Self {
        Self {
            enabled,
            exit_pct,
            trigger_pct,
            move_stop_to_entry,
        }
    }
}

impl Default for PartialExitConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            exit_pct: 0.5,
            trigger_pct: 0.02,
            move_stop_to_entry: true,
        }
    }
}

/// Configuration for pyramiding (scaling in).
#[pyclass]
#[derive(Clone, Debug)]
pub struct PyramidConfig {
    #[pyo3(get, set)]
    pub enabled: bool,
    #[pyo3(get, set)]
    pub max_entries: usize,       // Maximum number of entries
    #[pyo3(get, set)]
    pub entry_spacing_pct: f64,   // Minimum price move before adding (e.g., 0.01 = 1%)
    #[pyo3(get, set)]
    pub size_multiplier: f64,     // Size of each add relative to initial (e.g., 0.5 = half size)
}

#[pymethods]
impl PyramidConfig {
    #[new]
    #[pyo3(signature = (enabled = false, max_entries = 3, entry_spacing_pct = 0.01, size_multiplier = 0.5))]
    fn new(enabled: bool, max_entries: usize, entry_spacing_pct: f64, size_multiplier: f64) -> Self {
        Self {
            enabled,
            max_entries,
            entry_spacing_pct,
            size_multiplier,
        }
    }
}

impl Default for PyramidConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            max_entries: 3,
            entry_spacing_pct: 0.01,
            size_multiplier: 0.5,
        }
    }
}

/// Main strategy configuration.
#[pyclass]
#[derive(Clone, Debug)]
pub struct StrategyConfig {
    // === Strategy Selection ===
    #[pyo3(get, set)]
    pub strategy_type: String,

    // === Moving Average Parameters ===
    #[pyo3(get, set)]
    pub fast_window: usize,
    #[pyo3(get, set)]
    pub slow_window: usize,
    #[pyo3(get, set)]
    pub ma_type: String,          // SMA, EMA, WMA, DEMA, TEMA, KAMA, HMA, VWMA

    // === RSI Parameters ===
    #[pyo3(get, set)]
    pub rsi_period: usize,
    #[pyo3(get, set)]
    pub rsi_upper: f64,
    #[pyo3(get, set)]
    pub rsi_lower: f64,

    // === Bollinger Bands Parameters ===
    #[pyo3(get, set)]
    pub bollinger_period: usize,
    #[pyo3(get, set)]
    pub bollinger_std: f64,

    // === MACD Parameters ===
    #[pyo3(get, set)]
    pub macd_fast: usize,
    #[pyo3(get, set)]
    pub macd_slow: usize,
    #[pyo3(get, set)]
    pub macd_signal: usize,

    // === Stochastic Parameters ===
    #[pyo3(get, set)]
    pub stoch_k_period: usize,
    #[pyo3(get, set)]
    pub stoch_d_period: usize,
    #[pyo3(get, set)]
    pub stoch_upper: f64,
    #[pyo3(get, set)]
    pub stoch_lower: f64,

    // === ADX Parameters ===
    #[pyo3(get, set)]
    pub adx_period: usize,
    #[pyo3(get, set)]
    pub adx_threshold: f64,       // Minimum ADX for trend confirmation

    // === ATR Parameters ===
    #[pyo3(get, set)]
    pub atr_period: usize,
    #[pyo3(get, set)]
    pub atr_multiplier: f64,      // For ATR-based stops

    // === CCI Parameters ===
    #[pyo3(get, set)]
    pub cci_period: usize,
    #[pyo3(get, set)]
    pub cci_upper: f64,
    #[pyo3(get, set)]
    pub cci_lower: f64,

    // === Keltner Channel Parameters ===
    #[pyo3(get, set)]
    pub keltner_period: usize,
    #[pyo3(get, set)]
    pub keltner_atr_mult: f64,

    // === Donchian Channel Parameters ===
    #[pyo3(get, set)]
    pub donchian_period: usize,

    // === Ichimoku Parameters ===
    #[pyo3(get, set)]
    pub ichimoku_tenkan: usize,
    #[pyo3(get, set)]
    pub ichimoku_kijun: usize,
    #[pyo3(get, set)]
    pub ichimoku_senkou_b: usize,

    // === SuperTrend Parameters ===
    #[pyo3(get, set)]
    pub supertrend_period: usize,
    #[pyo3(get, set)]
    pub supertrend_mult: f64,

    // === Williams %R Parameters ===
    #[pyo3(get, set)]
    pub williams_period: usize,
    #[pyo3(get, set)]
    pub williams_upper: f64,
    #[pyo3(get, set)]
    pub williams_lower: f64,

    // === Aroon Parameters ===
    #[pyo3(get, set)]
    pub aroon_period: usize,
    #[pyo3(get, set)]
    pub aroon_threshold: f64,

    // === MFI Parameters ===
    #[pyo3(get, set)]
    pub mfi_period: usize,
    #[pyo3(get, set)]
    pub mfi_upper: f64,
    #[pyo3(get, set)]
    pub mfi_lower: f64,

    // === ROC Parameters ===
    #[pyo3(get, set)]
    pub roc_period: usize,
    #[pyo3(get, set)]
    pub roc_threshold: f64,

    // === TSI Parameters ===
    #[pyo3(get, set)]
    pub tsi_long_period: usize,
    #[pyo3(get, set)]
    pub tsi_short_period: usize,
    #[pyo3(get, set)]
    pub tsi_signal_period: usize,

    // === Ultimate Oscillator Parameters ===
    #[pyo3(get, set)]
    pub uo_period1: usize,
    #[pyo3(get, set)]
    pub uo_period2: usize,
    #[pyo3(get, set)]
    pub uo_period3: usize,
    #[pyo3(get, set)]
    pub uo_upper: f64,
    #[pyo3(get, set)]
    pub uo_lower: f64,

    // === OBV Parameters ===
    #[pyo3(get, set)]
    pub obv_ma_period: usize,     // For OBV MA crossover signals

    // === VWAP Parameters ===
    #[pyo3(get, set)]
    pub vwap_std_mult: f64,       // Standard deviation bands

    // === Risk Management ===
    #[pyo3(get, set)]
    pub stop_loss: f64,
    #[pyo3(get, set)]
    pub take_profit: f64,
    #[pyo3(get, set)]
    pub risk_per_trade: f64,
    #[pyo3(get, set)]
    pub initial_cash: f64,
    #[pyo3(get, set)]
    pub reduce_after_loss: bool,
    #[pyo3(get, set)]
    pub loss_size_factor: f64,
    #[pyo3(get, set)]
    pub margin_factor: f64,
    #[pyo3(get, set)]
    pub max_position_size: f64,   // Maximum position size as fraction of equity
    #[pyo3(get, set)]
    pub max_drawdown_exit: f64,   // Exit all positions if drawdown exceeds this

    // === Execution Realism ===
    #[pyo3(get, set)]
    pub commission: f64,
    #[pyo3(get, set)]
    pub slippage_bps: f64,
    #[pyo3(get, set)]
    pub spread_bps: f64,

    // === Advanced Order Types ===
    #[pyo3(get, set)]
    pub use_atr_stops: bool,      // Use ATR-based stops instead of percentage

    // === Metrics ===
    #[pyo3(get, set)]
    pub periods_per_year: f64,

    // === Diagnostics ===
    #[pyo3(get, set)]
    pub record_trades: bool,
    #[pyo3(get, set)]
    pub record_equity_curve: bool,

    // === Nested Configs (stored as Option for PyO3 compatibility) ===
    pub trailing_stop: TrailingStopConfig,
    pub break_even: BreakEvenConfig,
    pub time_stop: TimeStopConfig,
    pub partial_exit: PartialExitConfig,
    pub pyramid: PyramidConfig,
}

#[pymethods]
impl StrategyConfig {
    #[new]
    #[pyo3(signature = (
        fast_window = 10,
        slow_window = 30,
        strategy_type = "MA_CROSS".to_string(),
        ma_type = "SMA".to_string(),
        rsi_period = 14,
        rsi_upper = 70.0,
        rsi_lower = 30.0,
        bollinger_period = 20,
        bollinger_std = 2.0,
        macd_fast = 12,
        macd_slow = 26,
        macd_signal = 9,
        stoch_k_period = 14,
        stoch_d_period = 3,
        stoch_upper = 80.0,
        stoch_lower = 20.0,
        adx_period = 14,
        adx_threshold = 25.0,
        atr_period = 14,
        atr_multiplier = 2.0,
        cci_period = 20,
        cci_upper = 100.0,
        cci_lower = -100.0,
        keltner_period = 20,
        keltner_atr_mult = 2.0,
        donchian_period = 20,
        ichimoku_tenkan = 9,
        ichimoku_kijun = 26,
        ichimoku_senkou_b = 52,
        supertrend_period = 10,
        supertrend_mult = 3.0,
        williams_period = 14,
        williams_upper = -20.0,
        williams_lower = -80.0,
        aroon_period = 25,
        aroon_threshold = 70.0,
        mfi_period = 14,
        mfi_upper = 80.0,
        mfi_lower = 20.0,
        roc_period = 12,
        roc_threshold = 0.0,
        tsi_long_period = 25,
        tsi_short_period = 13,
        tsi_signal_period = 13,
        uo_period1 = 7,
        uo_period2 = 14,
        uo_period3 = 28,
        uo_upper = 70.0,
        uo_lower = 30.0,
        obv_ma_period = 20,
        vwap_std_mult = 2.0,
        stop_loss = 0.02,
        take_profit = 0.04,
        risk_per_trade = 0.01,
        initial_cash = 1_000_000.0,
        reduce_after_loss = true,
        loss_size_factor = 0.5,
        margin_factor = 1.0,
        max_position_size = 1.0,
        max_drawdown_exit = 0.0,
        commission = 0.0,
        slippage_bps = 0.0,
        spread_bps = 0.0,
        use_atr_stops = false,
        periods_per_year = 252.0,
        record_trades = false,
        record_equity_curve = false,
        trailing_stop = None,
        break_even = None,
        time_stop = None,
        partial_exit = None,
        pyramid = None,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        fast_window: usize,
        slow_window: usize,
        strategy_type: String,
        ma_type: String,
        rsi_period: usize,
        rsi_upper: f64,
        rsi_lower: f64,
        bollinger_period: usize,
        bollinger_std: f64,
        macd_fast: usize,
        macd_slow: usize,
        macd_signal: usize,
        stoch_k_period: usize,
        stoch_d_period: usize,
        stoch_upper: f64,
        stoch_lower: f64,
        adx_period: usize,
        adx_threshold: f64,
        atr_period: usize,
        atr_multiplier: f64,
        cci_period: usize,
        cci_upper: f64,
        cci_lower: f64,
        keltner_period: usize,
        keltner_atr_mult: f64,
        donchian_period: usize,
        ichimoku_tenkan: usize,
        ichimoku_kijun: usize,
        ichimoku_senkou_b: usize,
        supertrend_period: usize,
        supertrend_mult: f64,
        williams_period: usize,
        williams_upper: f64,
        williams_lower: f64,
        aroon_period: usize,
        aroon_threshold: f64,
        mfi_period: usize,
        mfi_upper: f64,
        mfi_lower: f64,
        roc_period: usize,
        roc_threshold: f64,
        tsi_long_period: usize,
        tsi_short_period: usize,
        tsi_signal_period: usize,
        uo_period1: usize,
        uo_period2: usize,
        uo_period3: usize,
        uo_upper: f64,
        uo_lower: f64,
        obv_ma_period: usize,
        vwap_std_mult: f64,
        stop_loss: f64,
        take_profit: f64,
        risk_per_trade: f64,
        initial_cash: f64,
        reduce_after_loss: bool,
        loss_size_factor: f64,
        margin_factor: f64,
        max_position_size: f64,
        max_drawdown_exit: f64,
        commission: f64,
        slippage_bps: f64,
        spread_bps: f64,
        use_atr_stops: bool,
        periods_per_year: f64,
        record_trades: bool,
        record_equity_curve: bool,
        trailing_stop: Option<TrailingStopConfig>,
        break_even: Option<BreakEvenConfig>,
        time_stop: Option<TimeStopConfig>,
        partial_exit: Option<PartialExitConfig>,
        pyramid: Option<PyramidConfig>,
    ) -> PyResult<Self> {
        let config = Self {
            strategy_type: strategy_type.trim().to_uppercase(),
            fast_window,
            slow_window,
            ma_type: ma_type.trim().to_uppercase(),
            rsi_period,
            rsi_upper,
            rsi_lower,
            bollinger_period,
            bollinger_std,
            macd_fast,
            macd_slow,
            macd_signal,
            stoch_k_period,
            stoch_d_period,
            stoch_upper,
            stoch_lower,
            adx_period,
            adx_threshold,
            atr_period,
            atr_multiplier,
            cci_period,
            cci_upper,
            cci_lower,
            keltner_period,
            keltner_atr_mult,
            donchian_period,
            ichimoku_tenkan,
            ichimoku_kijun,
            ichimoku_senkou_b,
            supertrend_period,
            supertrend_mult,
            williams_period,
            williams_upper,
            williams_lower,
            aroon_period,
            aroon_threshold,
            mfi_period,
            mfi_upper,
            mfi_lower,
            roc_period,
            roc_threshold,
            tsi_long_period,
            tsi_short_period,
            tsi_signal_period,
            uo_period1,
            uo_period2,
            uo_period3,
            uo_upper,
            uo_lower,
            obv_ma_period,
            vwap_std_mult,
            stop_loss,
            take_profit,
            risk_per_trade,
            initial_cash,
            reduce_after_loss,
            loss_size_factor,
            margin_factor,
            max_position_size,
            max_drawdown_exit,
            commission,
            slippage_bps,
            spread_bps,
            use_atr_stops,
            periods_per_year,
            record_trades,
            record_equity_curve,
            trailing_stop: trailing_stop.unwrap_or_default(),
            break_even: break_even.unwrap_or_default(),
            time_stop: time_stop.unwrap_or_default(),
            partial_exit: partial_exit.unwrap_or_default(),
            pyramid: pyramid.unwrap_or_default(),
        };
        validate_config(&config)?;
        Ok(config)
    }

    // Getters for nested configs
    #[getter]
    fn get_trailing_stop(&self, py: Python<'_>) -> PyResult<Py<TrailingStopConfig>> {
        Py::new(py, self.trailing_stop.clone())
    }

    #[getter]
    fn get_break_even(&self, py: Python<'_>) -> PyResult<Py<BreakEvenConfig>> {
        Py::new(py, self.break_even.clone())
    }

    #[getter]
    fn get_time_stop(&self, py: Python<'_>) -> PyResult<Py<TimeStopConfig>> {
        Py::new(py, self.time_stop.clone())
    }

    #[getter]
    fn get_partial_exit(&self, py: Python<'_>) -> PyResult<Py<PartialExitConfig>> {
        Py::new(py, self.partial_exit.clone())
    }

    #[getter]
    fn get_pyramid(&self, py: Python<'_>) -> PyResult<Py<PyramidConfig>> {
        Py::new(py, self.pyramid.clone())
    }
}

/// Parse strategy type string to StrategyKind enum.
pub fn strategy_kind(strategy_type: &str) -> Option<StrategyKind> {
    let value = strategy_type.trim();
    if value.eq_ignore_ascii_case("MA_CROSS")
        || value.eq_ignore_ascii_case("MA")
        || value.eq_ignore_ascii_case("MACROSS")
    {
        Some(StrategyKind::MaCross)
    } else if value.eq_ignore_ascii_case("RSI") {
        Some(StrategyKind::Rsi)
    } else if value.eq_ignore_ascii_case("BOLLINGER")
        || value.eq_ignore_ascii_case("BOLL")
        || value.eq_ignore_ascii_case("BBANDS")
    {
        Some(StrategyKind::Bollinger)
    } else if value.eq_ignore_ascii_case("MACD") {
        Some(StrategyKind::Macd)
    } else if value.eq_ignore_ascii_case("STOCHASTIC")
        || value.eq_ignore_ascii_case("STOCH")
    {
        Some(StrategyKind::Stochastic)
    } else if value.eq_ignore_ascii_case("ADX") {
        Some(StrategyKind::Adx)
    } else if value.eq_ignore_ascii_case("ATR") {
        Some(StrategyKind::Atr)
    } else if value.eq_ignore_ascii_case("CCI") {
        Some(StrategyKind::Cci)
    } else if value.eq_ignore_ascii_case("OBV") {
        Some(StrategyKind::Obv)
    } else if value.eq_ignore_ascii_case("VWAP") {
        Some(StrategyKind::Vwap)
    } else if value.eq_ignore_ascii_case("KELTNER") {
        Some(StrategyKind::Keltner)
    } else if value.eq_ignore_ascii_case("DONCHIAN") {
        Some(StrategyKind::Donchian)
    } else if value.eq_ignore_ascii_case("ICHIMOKU") {
        Some(StrategyKind::Ichimoku)
    } else if value.eq_ignore_ascii_case("SUPERTREND") {
        Some(StrategyKind::SuperTrend)
    } else if value.eq_ignore_ascii_case("WILLIAMS")
        || value.eq_ignore_ascii_case("WILLIAMS_R")
        || value.eq_ignore_ascii_case("WILLR")
    {
        Some(StrategyKind::Williams)
    } else if value.eq_ignore_ascii_case("AROON") {
        Some(StrategyKind::Aroon)
    } else if value.eq_ignore_ascii_case("MFI") {
        Some(StrategyKind::Mfi)
    } else if value.eq_ignore_ascii_case("ROC") {
        Some(StrategyKind::Roc)
    } else if value.eq_ignore_ascii_case("TSI") {
        Some(StrategyKind::Tsi)
    } else if value.eq_ignore_ascii_case("ULTIMATE")
        || value.eq_ignore_ascii_case("ULTIMATE_OSCILLATOR")
        || value.eq_ignore_ascii_case("UO")
    {
        Some(StrategyKind::UltimateOscillator)
    } else if value.eq_ignore_ascii_case("EXTERNAL")
        || value.eq_ignore_ascii_case("SIGNALS")
    {
        Some(StrategyKind::External)
    } else {
        None
    }
}

/// Validate configuration parameters.
pub fn validate_config(config: &StrategyConfig) -> PyResult<StrategyKind> {
    let strategy = strategy_kind(&config.strategy_type).ok_or_else(|| {
        PyValueError::new_err(
            "strategy_type must be one of: MA_CROSS, RSI, BOLLINGER, MACD, STOCHASTIC, ADX, ATR, \
             CCI, OBV, VWAP, KELTNER, DONCHIAN, ICHIMOKU, SUPERTREND, WILLIAMS, AROON, MFI, ROC, \
             TSI, ULTIMATE, EXTERNAL"
        )
    })?;

    // Validate cost parameters
    if config.commission < 0.0 || !config.commission.is_finite() {
        return Err(PyValueError::new_err("commission must be >= 0 and finite"));
    }
    if config.slippage_bps < 0.0 || !config.slippage_bps.is_finite() {
        return Err(PyValueError::new_err("slippage_bps must be >= 0 and finite"));
    }
    if config.spread_bps < 0.0 || !config.spread_bps.is_finite() {
        return Err(PyValueError::new_err("spread_bps must be >= 0 and finite"));
    }

    // Validate risk parameters
    if config.risk_per_trade <= 0.0 || config.risk_per_trade > 1.0 {
        return Err(PyValueError::new_err("risk_per_trade must be in (0, 1]"));
    }
    if config.stop_loss <= 0.0 {
        return Err(PyValueError::new_err(
            "stop_loss must be > 0 for risk_per_trade sizing",
        ));
    }
    if config.take_profit < 0.0 {
        return Err(PyValueError::new_err("take_profit must be >= 0"));
    }
    if config.initial_cash <= 0.0 {
        return Err(PyValueError::new_err("initial_cash must be positive"));
    }
    if !(0.0..=1.0).contains(&config.loss_size_factor) {
        return Err(PyValueError::new_err(
            "loss_size_factor must be between 0 and 1",
        ));
    }
    if config.margin_factor <= 0.0 || config.margin_factor > 1.0 {
        return Err(PyValueError::new_err("margin_factor must be in (0, 1]"));
    }
    if config.periods_per_year <= 0.0 {
        return Err(PyValueError::new_err("periods_per_year must be > 0"));
    }
    if config.max_position_size <= 0.0 || config.max_position_size > 10.0 {
        return Err(PyValueError::new_err("max_position_size must be in (0, 10]"));
    }
    if config.max_drawdown_exit < 0.0 || config.max_drawdown_exit > 1.0 {
        return Err(PyValueError::new_err("max_drawdown_exit must be in [0, 1]"));
    }

    // Strategy-specific validation
    match strategy {
        StrategyKind::MaCross => {
            if config.fast_window == 0 || config.slow_window == 0 {
                return Err(PyValueError::new_err(
                    "fast_window and slow_window must be > 0 for MA_CROSS",
                ));
            }
        }
        StrategyKind::Rsi => {
            if config.rsi_period < 2 {
                return Err(PyValueError::new_err("rsi_period must be >= 2"));
            }
            if !(0.0..=100.0).contains(&config.rsi_lower)
                || !(0.0..=100.0).contains(&config.rsi_upper)
                || config.rsi_upper <= config.rsi_lower
            {
                return Err(PyValueError::new_err(
                    "rsi_lower/rsi_upper must be in [0, 100] with rsi_upper > rsi_lower",
                ));
            }
        }
        StrategyKind::Bollinger => {
            if config.bollinger_period < 2 {
                return Err(PyValueError::new_err("bollinger_period must be >= 2"));
            }
            if config.bollinger_std <= 0.0 {
                return Err(PyValueError::new_err("bollinger_std must be > 0"));
            }
        }
        StrategyKind::Macd => {
            if config.macd_fast == 0 || config.macd_slow == 0 || config.macd_signal == 0 {
                return Err(PyValueError::new_err(
                    "macd_fast, macd_slow, and macd_signal must be > 0",
                ));
            }
            if config.macd_fast >= config.macd_slow {
                return Err(PyValueError::new_err("macd_fast must be < macd_slow"));
            }
        }
        StrategyKind::Stochastic => {
            if config.stoch_k_period < 2 || config.stoch_d_period < 1 {
                return Err(PyValueError::new_err(
                    "stoch_k_period must be >= 2 and stoch_d_period must be >= 1",
                ));
            }
        }
        StrategyKind::Adx => {
            if config.adx_period < 2 {
                return Err(PyValueError::new_err("adx_period must be >= 2"));
            }
        }
        StrategyKind::Atr => {
            if config.atr_period < 1 {
                return Err(PyValueError::new_err("atr_period must be >= 1"));
            }
        }
        StrategyKind::Cci => {
            if config.cci_period < 2 {
                return Err(PyValueError::new_err("cci_period must be >= 2"));
            }
        }
        StrategyKind::Keltner => {
            if config.keltner_period < 2 {
                return Err(PyValueError::new_err("keltner_period must be >= 2"));
            }
        }
        StrategyKind::Donchian => {
            if config.donchian_period < 2 {
                return Err(PyValueError::new_err("donchian_period must be >= 2"));
            }
        }
        StrategyKind::Ichimoku => {
            if config.ichimoku_tenkan < 2 || config.ichimoku_kijun < 2 || config.ichimoku_senkou_b < 2 {
                return Err(PyValueError::new_err(
                    "ichimoku periods must be >= 2",
                ));
            }
        }
        StrategyKind::SuperTrend => {
            if config.supertrend_period < 1 {
                return Err(PyValueError::new_err("supertrend_period must be >= 1"));
            }
            if config.supertrend_mult <= 0.0 {
                return Err(PyValueError::new_err("supertrend_mult must be > 0"));
            }
        }
        StrategyKind::Williams => {
            if config.williams_period < 2 {
                return Err(PyValueError::new_err("williams_period must be >= 2"));
            }
        }
        StrategyKind::Aroon => {
            if config.aroon_period < 2 {
                return Err(PyValueError::new_err("aroon_period must be >= 2"));
            }
        }
        StrategyKind::Mfi => {
            if config.mfi_period < 2 {
                return Err(PyValueError::new_err("mfi_period must be >= 2"));
            }
        }
        StrategyKind::Roc => {
            if config.roc_period < 1 {
                return Err(PyValueError::new_err("roc_period must be >= 1"));
            }
        }
        StrategyKind::Tsi => {
            if config.tsi_long_period < 2 || config.tsi_short_period < 2 {
                return Err(PyValueError::new_err("tsi periods must be >= 2"));
            }
        }
        StrategyKind::UltimateOscillator => {
            if config.uo_period1 < 1 || config.uo_period2 < 1 || config.uo_period3 < 1 {
                return Err(PyValueError::new_err("ultimate oscillator periods must be >= 1"));
            }
        }
        StrategyKind::Obv | StrategyKind::Vwap | StrategyKind::External => {}
    }

    // Validate trailing stop config
    if config.trailing_stop.enabled {
        if config.trailing_stop.trail_pct <= 0.0 && config.trailing_stop.trail_atr_mult <= 0.0 {
            return Err(PyValueError::new_err(
                "trailing_stop requires either trail_pct > 0 or trail_atr_mult > 0",
            ));
        }
    }

    // Validate break-even config
    if config.break_even.enabled {
        if config.break_even.trigger_pct <= 0.0 {
            return Err(PyValueError::new_err(
                "break_even.trigger_pct must be > 0",
            ));
        }
    }

    // Validate time stop config
    if config.time_stop.enabled {
        if config.time_stop.max_bars == 0 && config.time_stop.max_duration_us <= 0 {
            return Err(PyValueError::new_err(
                "time_stop requires either max_bars > 0 or max_duration_us > 0",
            ));
        }
    }

    // Validate partial exit config
    if config.partial_exit.enabled {
        if config.partial_exit.exit_pct <= 0.0 || config.partial_exit.exit_pct >= 1.0 {
            return Err(PyValueError::new_err(
                "partial_exit.exit_pct must be in (0, 1)",
            ));
        }
        if config.partial_exit.trigger_pct <= 0.0 {
            return Err(PyValueError::new_err(
                "partial_exit.trigger_pct must be > 0",
            ));
        }
    }

    // Validate pyramid config
    if config.pyramid.enabled {
        if config.pyramid.max_entries < 2 {
            return Err(PyValueError::new_err(
                "pyramid.max_entries must be >= 2",
            ));
        }
        if config.pyramid.entry_spacing_pct <= 0.0 {
            return Err(PyValueError::new_err(
                "pyramid.entry_spacing_pct must be > 0",
            ));
        }
        if config.pyramid.size_multiplier <= 0.0 {
            return Err(PyValueError::new_err(
                "pyramid.size_multiplier must be > 0",
            ));
        }
    }

    Ok(strategy)
}
