//! Result types for backtesting output.

use crate::config::StrategyConfig;
use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Individual trade record for the trade ledger.
#[pyclass]
#[derive(Clone, Debug)]
pub struct Trade {
    #[pyo3(get)]
    pub asset_id: u32,
    #[pyo3(get)]
    pub entry_ts: i64,
    #[pyo3(get)]
    pub exit_ts: i64,
    #[pyo3(get)]
    pub side: String, // "long" or "short"
    #[pyo3(get)]
    pub qty: f64,
    #[pyo3(get)]
    pub entry_price: f64,
    #[pyo3(get)]
    pub exit_price: f64,
    #[pyo3(get)]
    pub gross_pnl: f64, // PnL before costs
    #[pyo3(get)]
    pub net_pnl: f64, // PnL after commission and execution costs
    #[pyo3(get)]
    pub commission_paid: f64,
    #[pyo3(get)]
    pub execution_cost: f64, // Slippage + spread cost combined
    #[pyo3(get)]
    pub bars_held: usize, // Number of bars position was held
    #[pyo3(get)]
    pub mae: f64, // Maximum Adverse Excursion (worst drawdown during trade)
    #[pyo3(get)]
    pub mfe: f64, // Maximum Favorable Excursion (best profit during trade)
    #[pyo3(get)]
    pub exit_reason: String, // "signal", "stop_loss", "take_profit", "trailing_stop", "time_stop", etc.
}

#[pymethods]
impl Trade {
    pub fn as_dict(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new_bound(py);
        dict.set_item("asset_id", self.asset_id)?;
        dict.set_item("entry_ts", self.entry_ts)?;
        dict.set_item("exit_ts", self.exit_ts)?;
        dict.set_item("side", &self.side)?;
        dict.set_item("qty", self.qty)?;
        dict.set_item("entry_price", self.entry_price)?;
        dict.set_item("exit_price", self.exit_price)?;
        dict.set_item("gross_pnl", self.gross_pnl)?;
        dict.set_item("net_pnl", self.net_pnl)?;
        dict.set_item("commission_paid", self.commission_paid)?;
        dict.set_item("execution_cost", self.execution_cost)?;
        dict.set_item("bars_held", self.bars_held)?;
        dict.set_item("mae", self.mae)?;
        dict.set_item("mfe", self.mfe)?;
        dict.set_item("exit_reason", &self.exit_reason)?;
        Ok(dict.into_py(py))
    }

    fn __repr__(&self) -> String {
        format!(
            "Trade({} {} @ {:.4} -> {:.4}, gross_pnl={:.2}, net_pnl={:.2}, exit={})",
            self.side, self.qty, self.entry_price, self.exit_price, self.gross_pnl, self.net_pnl, self.exit_reason
        )
    }
}

/// Equity curve point for diagnostics.
#[pyclass]
#[derive(Clone, Debug)]
pub struct EquityPoint {
    #[pyo3(get)]
    pub ts: i64,
    #[pyo3(get)]
    pub equity: f64,
    #[pyo3(get)]
    pub cash: f64,
    #[pyo3(get)]
    pub drawdown: f64,
    #[pyo3(get)]
    pub position_value: f64,
    #[pyo3(get)]
    pub unrealized_pnl: f64,
}

#[pymethods]
impl EquityPoint {
    pub fn as_dict(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new_bound(py);
        dict.set_item("ts", self.ts)?;
        dict.set_item("equity", self.equity)?;
        dict.set_item("cash", self.cash)?;
        dict.set_item("drawdown", self.drawdown)?;
        dict.set_item("position_value", self.position_value)?;
        dict.set_item("unrealized_pnl", self.unrealized_pnl)?;
        Ok(dict.into_py(py))
    }
}

/// Complete backtest results.
#[pyclass]
#[derive(Clone)]
pub struct BacktestResult {
    // === Returns & Risk Metrics ===
    #[pyo3(get)]
    pub total_return: f64,
    #[pyo3(get)]
    pub sharpe: f64,
    #[pyo3(get)]
    pub sortino: f64,
    #[pyo3(get)]
    pub max_drawdown: f64,
    #[pyo3(get)]
    pub calmar: f64,
    #[pyo3(get)]
    pub annualized_return: f64,
    #[pyo3(get)]
    pub annualized_volatility: f64,

    // === Trade Statistics ===
    #[pyo3(get)]
    pub trades: usize,
    #[pyo3(get)]
    pub wins: usize,
    #[pyo3(get)]
    pub losses: usize,
    #[pyo3(get)]
    pub win_pct: f64,
    #[pyo3(get)]
    pub expectancy: f64,
    #[pyo3(get)]
    pub avg_win: f64,
    #[pyo3(get)]
    pub avg_loss: f64,
    #[pyo3(get)]
    pub profit_factor: f64,
    #[pyo3(get)]
    pub payoff_ratio: f64,
    #[pyo3(get)]
    pub max_consecutive_wins: usize,
    #[pyo3(get)]
    pub max_consecutive_losses: usize,
    #[pyo3(get)]
    pub avg_bars_held: f64,

    // === Risk Metrics ===
    #[pyo3(get)]
    pub var_95: f64, // Value at Risk (95%)
    #[pyo3(get)]
    pub cvar_95: f64, // Conditional VaR (95%)
    #[pyo3(get)]
    pub recovery_factor: f64,
    #[pyo3(get)]
    pub ulcer_index: f64,
    #[pyo3(get)]
    pub kelly_criterion: f64,

    // === Portfolio State ===
    #[pyo3(get)]
    pub final_equity: f64,
    #[pyo3(get)]
    pub cash: f64,
    #[pyo3(get)]
    pub realized_pnl: f64,
    #[pyo3(get)]
    pub unrealized_pnl: f64,
    #[pyo3(get)]
    pub margin_used: f64,

    // === Cost Analysis ===
    #[pyo3(get)]
    pub total_commission: f64,
    #[pyo3(get)]
    pub total_execution_cost: f64,
    #[pyo3(get)]
    pub total_slippage: f64,
    #[pyo3(get)]
    pub total_spread_cost: f64,

    // === Advanced Order Stats ===
    #[pyo3(get)]
    pub stop_loss_exits: usize,
    #[pyo3(get)]
    pub take_profit_exits: usize,
    #[pyo3(get)]
    pub trailing_stop_exits: usize,
    #[pyo3(get)]
    pub time_stop_exits: usize,
    #[pyo3(get)]
    pub signal_exits: usize,
    #[pyo3(get)]
    pub partial_exits: usize,
    #[pyo3(get)]
    pub pyramid_entries: usize,

    // === Nested Data ===
    pub config: StrategyConfig,
    pub trade_ledger: Vec<Trade>,
    pub equity_curve: Vec<EquityPoint>,
}

#[pymethods]
impl BacktestResult {
    #[getter]
    fn config(&self, py: Python<'_>) -> PyResult<Py<StrategyConfig>> {
        Py::new(py, self.config.clone())
    }

    #[getter]
    fn trade_ledger(&self, py: Python<'_>) -> PyResult<Vec<Py<Trade>>> {
        self.trade_ledger
            .iter()
            .map(|t| Py::new(py, t.clone()))
            .collect()
    }

    #[getter]
    fn equity_curve(&self, py: Python<'_>) -> PyResult<Vec<Py<EquityPoint>>> {
        self.equity_curve
            .iter()
            .map(|e| Py::new(py, e.clone()))
            .collect()
    }

    pub fn as_dict(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let dict = PyDict::new_bound(py);

        // Returns & Risk Metrics
        dict.set_item("total_return", self.total_return)?;
        dict.set_item("sharpe", self.sharpe)?;
        dict.set_item("sortino", self.sortino)?;
        dict.set_item("max_drawdown", self.max_drawdown)?;
        dict.set_item("calmar", self.calmar)?;
        dict.set_item("annualized_return", self.annualized_return)?;
        dict.set_item("annualized_volatility", self.annualized_volatility)?;

        // Trade Statistics
        dict.set_item("trades", self.trades)?;
        dict.set_item("wins", self.wins)?;
        dict.set_item("losses", self.losses)?;
        dict.set_item("win_pct", self.win_pct)?;
        dict.set_item("expectancy", self.expectancy)?;
        dict.set_item("avg_win", self.avg_win)?;
        dict.set_item("avg_loss", self.avg_loss)?;
        dict.set_item("profit_factor", self.profit_factor)?;
        dict.set_item("payoff_ratio", self.payoff_ratio)?;
        dict.set_item("max_consecutive_wins", self.max_consecutive_wins)?;
        dict.set_item("max_consecutive_losses", self.max_consecutive_losses)?;
        dict.set_item("avg_bars_held", self.avg_bars_held)?;

        // Risk Metrics
        dict.set_item("var_95", self.var_95)?;
        dict.set_item("cvar_95", self.cvar_95)?;
        dict.set_item("recovery_factor", self.recovery_factor)?;
        dict.set_item("ulcer_index", self.ulcer_index)?;
        dict.set_item("kelly_criterion", self.kelly_criterion)?;

        // Portfolio State
        dict.set_item("final_equity", self.final_equity)?;
        dict.set_item("cash", self.cash)?;
        dict.set_item("realized_pnl", self.realized_pnl)?;
        dict.set_item("unrealized_pnl", self.unrealized_pnl)?;
        dict.set_item("margin_used", self.margin_used)?;

        // Cost Analysis
        dict.set_item("total_commission", self.total_commission)?;
        dict.set_item("total_execution_cost", self.total_execution_cost)?;
        dict.set_item("total_slippage", self.total_slippage)?;
        dict.set_item("total_spread_cost", self.total_spread_cost)?;

        // Advanced Order Stats
        dict.set_item("stop_loss_exits", self.stop_loss_exits)?;
        dict.set_item("take_profit_exits", self.take_profit_exits)?;
        dict.set_item("trailing_stop_exits", self.trailing_stop_exits)?;
        dict.set_item("time_stop_exits", self.time_stop_exits)?;
        dict.set_item("signal_exits", self.signal_exits)?;
        dict.set_item("partial_exits", self.partial_exits)?;
        dict.set_item("pyramid_entries", self.pyramid_entries)?;

        // Config
        dict.set_item("config", Py::new(py, self.config.clone())?)?;

        // Trade ledger as list of dicts
        let trades_list: Vec<_> = self
            .trade_ledger
            .iter()
            .map(|t| t.as_dict(py))
            .collect::<PyResult<_>>()?;
        dict.set_item("trade_ledger", trades_list)?;

        // Equity curve as list of dicts
        let equity_list: Vec<_> = self
            .equity_curve
            .iter()
            .map(|e| e.as_dict(py))
            .collect::<PyResult<_>>()?;
        dict.set_item("equity_curve", equity_list)?;

        Ok(dict.into_py(py))
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "BacktestResult(total_return={:.4}, sharpe={:.3}, sortino={:.3}, max_drawdown={:.3}, \
             trades={}, wins={}, losses={}, final_equity={:.2})",
            self.total_return,
            self.sharpe,
            self.sortino,
            self.max_drawdown,
            self.trades,
            self.wins,
            self.losses,
            self.final_equity
        ))
    }
}

impl Default for BacktestResult {
    fn default() -> Self {
        Self {
            total_return: 0.0,
            sharpe: 0.0,
            sortino: 0.0,
            max_drawdown: 0.0,
            calmar: 0.0,
            annualized_return: 0.0,
            annualized_volatility: 0.0,
            trades: 0,
            wins: 0,
            losses: 0,
            win_pct: 0.0,
            expectancy: 0.0,
            avg_win: 0.0,
            avg_loss: 0.0,
            profit_factor: 0.0,
            payoff_ratio: 0.0,
            max_consecutive_wins: 0,
            max_consecutive_losses: 0,
            avg_bars_held: 0.0,
            var_95: 0.0,
            cvar_95: 0.0,
            recovery_factor: 0.0,
            ulcer_index: 0.0,
            kelly_criterion: 0.0,
            final_equity: 0.0,
            cash: 0.0,
            realized_pnl: 0.0,
            unrealized_pnl: 0.0,
            margin_used: 0.0,
            total_commission: 0.0,
            total_execution_cost: 0.0,
            total_slippage: 0.0,
            total_spread_cost: 0.0,
            stop_loss_exits: 0,
            take_profit_exits: 0,
            trailing_stop_exits: 0,
            time_stop_exits: 0,
            signal_exits: 0,
            partial_exits: 0,
            pyramid_entries: 0,
            config: StrategyConfig {
                strategy_type: String::new(),
                fast_window: 0,
                slow_window: 0,
                ma_type: String::new(),
                rsi_period: 0,
                rsi_upper: 0.0,
                rsi_lower: 0.0,
                bollinger_period: 0,
                bollinger_std: 0.0,
                macd_fast: 0,
                macd_slow: 0,
                macd_signal: 0,
                stoch_k_period: 0,
                stoch_d_period: 0,
                stoch_upper: 0.0,
                stoch_lower: 0.0,
                adx_period: 0,
                adx_threshold: 0.0,
                atr_period: 0,
                atr_multiplier: 0.0,
                cci_period: 0,
                cci_upper: 0.0,
                cci_lower: 0.0,
                keltner_period: 0,
                keltner_atr_mult: 0.0,
                donchian_period: 0,
                ichimoku_tenkan: 0,
                ichimoku_kijun: 0,
                ichimoku_senkou_b: 0,
                supertrend_period: 0,
                supertrend_mult: 0.0,
                williams_period: 0,
                williams_upper: 0.0,
                williams_lower: 0.0,
                aroon_period: 0,
                aroon_threshold: 0.0,
                mfi_period: 0,
                mfi_upper: 0.0,
                mfi_lower: 0.0,
                roc_period: 0,
                roc_threshold: 0.0,
                tsi_long_period: 0,
                tsi_short_period: 0,
                tsi_signal_period: 0,
                uo_period1: 0,
                uo_period2: 0,
                uo_period3: 0,
                uo_upper: 0.0,
                uo_lower: 0.0,
                obv_ma_period: 0,
                vwap_std_mult: 0.0,
                stop_loss: 0.0,
                take_profit: 0.0,
                risk_per_trade: 0.0,
                initial_cash: 0.0,
                reduce_after_loss: false,
                loss_size_factor: 0.0,
                margin_factor: 0.0,
                max_position_size: 0.0,
                max_drawdown_exit: 0.0,
                commission: 0.0,
                slippage_bps: 0.0,
                spread_bps: 0.0,
                use_atr_stops: false,
                periods_per_year: 0.0,
                record_trades: false,
                record_equity_curve: false,
                trailing_stop: Default::default(),
                break_even: Default::default(),
                time_stop: Default::default(),
                partial_exit: Default::default(),
                pyramid: Default::default(),
            },
            trade_ledger: Vec::new(),
            equity_curve: Vec::new(),
        }
    }
}
