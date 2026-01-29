//! Backtesting simulation engine.

use std::cmp::Ordering;
use std::sync::Arc;

use numpy::PyReadonlyArray1;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rayon::prelude::*;

use crate::config::{validate_config, StrategyConfig, StrategyKind};
use crate::data::{extract_bar_data, BarData};
use crate::indicators::{BarInput, IndicatorState, Signal};
use crate::metrics::{
    annualized_return, calmar_ratio, checked_equity, conditional_var, ensure_finite,
    kelly_criterion, metric_value, payoff_ratio, profit_factor, recovery_factor, sharpe_ratio,
    sortino_ratio, ulcer_index, value_at_risk,
};
use crate::portfolio::{
    check_partial_exit, check_time_stop, close_position, create_trade_record, enter_long,
    enter_short, mark_to_price, pyramid_position, update_break_even, update_trailing_stop,
    AssetState, ExitReason, Portfolio,
};
use crate::result::{BacktestResult, EquityPoint, Trade};

/// Run a backtest with built-in strategy signals.
#[pyfunction]
#[pyo3(signature = (data, config))]
pub fn run_backtest(data: &Bound<'_, PyAny>, config: StrategyConfig) -> PyResult<BacktestResult> {
    let strategy = validate_config(&config)?;
    if matches!(strategy, StrategyKind::External) {
        return Err(PyValueError::new_err(
            "strategy_type='EXTERNAL' requires run_backtest_with_signals(); \
             use that function to provide your signals array",
        ));
    }
    let bar_data = extract_bar_data(data)?;

    // Validate minimum data requirements
    validate_minimum_data(&bar_data, &config, strategy)?;

    simulate(&bar_data, &config, strategy, None).map_err(PyValueError::new_err)
}

/// Calculate minimum bars required for a strategy's indicator warm-up period.
fn get_minimum_bars(config: &StrategyConfig, strategy: StrategyKind) -> usize {
    match strategy {
        StrategyKind::MaCross => config.slow_window.max(config.fast_window) + 1,
        StrategyKind::Rsi => config.rsi_period + 1,
        StrategyKind::Bollinger => config.bollinger_period + 1,
        StrategyKind::Macd => config.macd_slow + config.macd_signal,
        StrategyKind::Stochastic => config.stoch_k_period + config.stoch_d_period,
        StrategyKind::Adx => config.adx_period * 2 + 1,
        StrategyKind::Atr => config.atr_period + 1,
        StrategyKind::Cci => config.cci_period + 1,
        StrategyKind::Keltner => config.keltner_period + config.atr_period,
        StrategyKind::Donchian => config.donchian_period + 1,
        StrategyKind::Ichimoku => config.ichimoku_senkou_b + 1,
        StrategyKind::SuperTrend => config.supertrend_period + 1,
        StrategyKind::Williams => config.williams_period + 1,
        StrategyKind::Aroon => config.aroon_period + 1,
        StrategyKind::Mfi => config.mfi_period + 1,
        StrategyKind::Roc => config.roc_period + 1,
        StrategyKind::Tsi => config.tsi_long_period + config.tsi_short_period + config.tsi_signal_period,
        StrategyKind::UltimateOscillator => config.uo_period3 + 1,
        StrategyKind::Obv => config.obv_ma_period + 1,
        StrategyKind::Vwap => 2,
        StrategyKind::External => 1,
    }
}

/// Validate that the data has enough bars for indicator warm-up.
fn validate_minimum_data(data: &BarData, config: &StrategyConfig, strategy: StrategyKind) -> PyResult<()> {
    if data.rows == 0 {
        return Err(PyValueError::new_err(
            "data is empty; cannot run backtest with zero rows"
        ));
    }

    let min_bars = get_minimum_bars(config, strategy);
    if data.rows < min_bars {
        let strategy_name = format!("{:?}", strategy);
        return Err(PyValueError::new_err(format!(
            "insufficient data: {} strategy requires at least {} bars for indicator warm-up, but only {} provided. \
             Consider using more historical data or reducing indicator periods.",
            strategy_name, min_bars, data.rows
        )));
    }

    Ok(())
}

/// Run a backtest with user-provided signals (External Signal Mode).
#[pyfunction]
#[pyo3(signature = (data, signals, config))]
pub fn run_backtest_with_signals(
    data: &Bound<'_, PyAny>,
    signals: PyReadonlyArray1<'_, i8>,
    config: StrategyConfig,
) -> PyResult<BacktestResult> {
    let mut config_for_validation = config.clone();
    config_for_validation.strategy_type = "EXTERNAL".to_string();
    validate_config(&config_for_validation)?;

    let bar_data = extract_bar_data(data)?;
    let signals_vec: Vec<i8> = signals.as_array().to_vec();

    if signals_vec.len() != bar_data.rows {
        return Err(PyValueError::new_err(format!(
            "signals length ({}) must match data rows ({})",
            signals_vec.len(),
            bar_data.rows
        )));
    }

    for (i, &s) in signals_vec.iter().enumerate() {
        if s < -1 || s > 1 {
            return Err(PyValueError::new_err(format!(
                "signals[{}] = {} is invalid; must be -1, 0, or 1",
                i, s
            )));
        }
    }

    simulate(&bar_data, &config, StrategyKind::External, Some(signals_vec))
        .map_err(PyValueError::new_err)
}

/// Run a grid search over multiple configurations.
#[pyfunction]
#[pyo3(signature = (data, configs, metric = "total_return", top_n = 10))]
pub fn grid_search(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    configs: Vec<StrategyConfig>,
    metric: &str,
    top_n: usize,
) -> PyResult<Vec<BacktestResult>> {
    if configs.is_empty() {
        return Ok(vec![]);
    }
    let bar_data = extract_bar_data(data)?;
    let shared = Arc::new(bar_data);
    let mut kinds = Vec::with_capacity(configs.len());
    for (i, cfg) in configs.iter().enumerate() {
        let kind = validate_config(cfg)?;
        if matches!(kind, StrategyKind::External) {
            return Err(PyValueError::new_err(format!(
                "configs[{}] has strategy_type='EXTERNAL' which is not supported in grid_search; \
                 use run_backtest_with_signals() instead",
                i
            )));
        }
        kinds.push(kind);
    }

    let metric_key = metric.to_lowercase();
    let results: Result<Vec<_>, String> = py.allow_threads(|| {
        configs
            .par_iter()
            .zip(kinds.par_iter())
            .map(|(cfg, kind)| simulate(shared.as_ref(), cfg, *kind, None))
            .collect()
    });
    let mut results = results.map_err(PyValueError::new_err)?;

    results.par_sort_by(|a, b| {
        let a_metric = metric_value(
            a.total_return,
            a.sharpe,
            a.sortino,
            a.max_drawdown,
            a.calmar,
            a.win_pct,
            a.expectancy,
            &metric_key,
        );
        let b_metric = metric_value(
            b.total_return,
            b.sharpe,
            b.sortino,
            b.max_drawdown,
            b.calmar,
            b.win_pct,
            b.expectancy,
            &metric_key,
        );
        b_metric.partial_cmp(&a_metric).unwrap_or(Ordering::Equal)
    });

    let capped = top_n.min(results.len());
    results.truncate(capped);
    Ok(results)
}

/// Core simulation loop.
pub fn simulate(
    data: &BarData,
    cfg: &StrategyConfig,
    strategy: StrategyKind,
    external_signals: Option<Vec<i8>>,
) -> Result<BacktestResult, String> {
    let asset_cap = data.max_asset_id as usize + 1;
    let mut assets: Vec<Option<AssetState>> = Vec::with_capacity(asset_cap);
    assets.resize_with(asset_cap, || None);

    let mut portfolio = Portfolio::new(cfg.initial_cash);

    let mut prev_equity = cfg.initial_cash;
    let mut peak_equity = cfg.initial_cash;
    let mut max_drawdown = 0.0;
    let mut returns = Vec::new();
    let mut equity_history = Vec::new();
    let mut current_ts: Option<i64> = None;
    let mut final_equity = cfg.initial_cash;

    // Cost tracking
    let mut total_commission = 0.0;
    let mut total_slippage = 0.0;
    let mut total_spread_cost = 0.0;
    let commission = cfg.commission;
    let slippage_bps = cfg.slippage_bps;
    let spread_bps = cfg.spread_bps;

    // Order type statistics
    let mut stop_loss_exits = 0usize;
    let mut take_profit_exits = 0usize;
    let mut trailing_stop_exits = 0usize;
    let mut time_stop_exits = 0usize;
    let mut signal_exits = 0usize;
    let mut partial_exit_count = 0usize;
    let mut pyramid_entry_count = 0usize;

    // Diagnostics output
    let record_trades = cfg.record_trades;
    let record_equity_curve = cfg.record_equity_curve;
    let mut trade_ledger: Vec<Trade> = Vec::new();
    let mut equity_curve: Vec<EquityPoint> = Vec::new();

    let stop_loss = cfg.stop_loss;
    let take_profit = cfg.take_profit;

    // Global bar index for external signals
    let mut global_bar_idx = 0usize;

    for chunk in &data.chunks {
        let len = chunk.len;
        let ts_values = chunk.ts.values();
        let asset_values = chunk.asset_id.values();
        let open_values = chunk.open.values();
        let high_values = chunk.high.values();
        let low_values = chunk.low.values();
        let close_values = chunk.close.values();
        let volume_values = chunk.volume.values();

        for i in 0..len {
            let ts = ts_values[i];

            // Handle timestamp change (new bar period)
            if let Some(prev_ts) = current_ts {
                if ts != prev_ts {
                    let equity = checked_equity(portfolio.cash, portfolio.marked_value)?;
                    if prev_equity > 0.0 {
                        let step = (equity - prev_equity) / prev_equity;
                        ensure_finite(step, "step_return")?;
                        returns.push(step);
                    }
                    prev_equity = equity;
                    final_equity = equity;
                    equity_history.push(equity);

                    if equity > peak_equity {
                        peak_equity = equity;
                        ensure_finite(peak_equity, "peak_equity")?;
                    }
                    let drawdown = if peak_equity > 0.0 {
                        (peak_equity - equity) / peak_equity
                    } else {
                        0.0
                    };
                    ensure_finite(drawdown, "drawdown")?;
                    if drawdown > max_drawdown {
                        max_drawdown = drawdown;
                    }

                    // Check max drawdown exit
                    if cfg.max_drawdown_exit > 0.0 && drawdown >= cfg.max_drawdown_exit {
                        // Close all positions
                        for asset_opt in assets.iter_mut() {
                            if let Some(state) = asset_opt {
                                if state.position.qty != 0.0 {
                                    let (_pnl, _bars_held) = close_position(
                                        &mut portfolio,
                                        state,
                                        state.last_price,
                                        None,
                                        global_bar_idx,
                                    )?;
                                    // Positions closed due to max drawdown exit
                                }
                            }
                        }
                    }

                    if record_equity_curve {
                        equity_curve.push(EquityPoint {
                            ts: prev_ts,
                            equity,
                            cash: portfolio.cash,
                            drawdown,
                            position_value: portfolio.marked_value,
                            unrealized_pnl: portfolio.unrealized,
                        });
                    }
                    current_ts = Some(ts);
                }
            } else {
                current_ts = Some(ts);
            }

            let asset_id_u32 = asset_values[i];
            let asset_id = asset_id_u32 as usize;
            let open = open_values[i];
            let high = high_values[i];
            let low = low_values[i];
            let close = close_values[i];
            let volume = volume_values[i];

            let state = assets[asset_id]
                .get_or_insert_with(|| AssetState::new(IndicatorState::new(strategy, cfg)));

            mark_to_price(&mut portfolio, state, close)?;

            // Get ATR for ATR-based features
            let atr = state.indicator.get_atr();

            // Get signal from indicator or external signals
            let bar_input = BarInput {
                open,
                high,
                low,
                close,
                volume,
            };
            let signal = if matches!(strategy, StrategyKind::External) {
                if let Some(ref signals) = external_signals {
                    let sig = signals[global_bar_idx];
                    Signal {
                        long: sig == 1,
                        short: sig == -1,
                    }
                } else {
                    Signal::default()
                }
            } else {
                state.indicator.update(bar_input)
            };

            let qty = state.position.qty;

            // Handle existing position
            if qty != 0.0 {
                let is_long = qty > 0.0;
                let mut exit = false;
                let mut exit_price = close;
                let mut exit_reason = ExitReason::Signal;

                // Update position tracking
                if is_long {
                    state.position.highest_price = state.position.highest_price.max(high);
                    state.position.lowest_price = state.position.lowest_price.min(low);
                } else {
                    state.position.highest_price = state.position.highest_price.max(high);
                    state.position.lowest_price = state.position.lowest_price.min(low);
                }

                // Check trailing stop
                if update_trailing_stop(state, high, low, close, cfg, atr) {
                    exit = true;
                    exit_price = state.position.trailing_stop_price;
                    exit_reason = ExitReason::TrailingStop;
                }

                // Check break-even stop
                if !exit {
                    if let Some(be_stop) = update_break_even(state, close, cfg) {
                        if is_long && low <= be_stop {
                            exit = true;
                            exit_price = be_stop;
                            exit_reason = ExitReason::BreakEven;
                        } else if !is_long && high >= be_stop {
                            exit = true;
                            exit_price = be_stop;
                            exit_reason = ExitReason::BreakEven;
                        }
                    }
                }

                // Check time stop
                if !exit && check_time_stop(state, ts, global_bar_idx, cfg) {
                    exit = true;
                    exit_reason = ExitReason::TimeStop;
                }

                // Check stop loss and take profit
                if !exit {
                    let effective_stop = if cfg.use_atr_stops {
                        atr.map(|a| a * cfg.atr_multiplier / state.position.entry_price)
                            .unwrap_or(stop_loss)
                    } else {
                        stop_loss
                    };

                    if is_long {
                        let stop_price = state.position.entry_price * (1.0 - effective_stop);
                        if low <= stop_price {
                            exit = true;
                            exit_price = stop_price;
                            exit_reason = ExitReason::StopLoss;
                        }
                        if !exit && take_profit > 0.0 {
                            let tp_price = state.position.entry_price * (1.0 + take_profit);
                            if high >= tp_price {
                                exit = true;
                                exit_price = tp_price;
                                exit_reason = ExitReason::TakeProfit;
                            }
                        }
                        if !exit && signal.short {
                            exit = true;
                            exit_reason = ExitReason::Signal;
                        }
                    } else {
                        let stop_price = state.position.entry_price * (1.0 + effective_stop);
                        if high >= stop_price {
                            exit = true;
                            exit_price = stop_price;
                            exit_reason = ExitReason::StopLoss;
                        }
                        if !exit && take_profit > 0.0 {
                            let tp_price = state.position.entry_price * (1.0 - take_profit);
                            if low <= tp_price {
                                exit = true;
                                exit_price = tp_price;
                                exit_reason = ExitReason::TakeProfit;
                            }
                        }
                        if !exit && signal.long {
                            exit = true;
                            exit_reason = ExitReason::Signal;
                        }
                    }
                }

                // Check partial exit
                if !exit && check_partial_exit(state, close, cfg) {
                    let partial_qty = state.position.qty.abs() * cfg.partial_exit.exit_pct;

                    // Calculate costs
                    let exit_slippage = exit_price * partial_qty * (slippage_bps / 10000.0);
                    let exit_spread = exit_price * partial_qty * (spread_bps / 10000.0 / 2.0);
                    total_slippage += exit_slippage;
                    total_spread_cost += exit_spread;
                    total_commission += commission;
                    portfolio.cash -= commission + exit_slippage + exit_spread;

                    let (_pnl, _bars_held) =
                        close_position(&mut portfolio, state, close, Some(partial_qty), global_bar_idx)?;

                    if cfg.partial_exit.move_stop_to_entry {
                        state.position.trailing_stop_price = state.position.entry_price;
                        state.position.trailing_stop_active = true;
                    }

                    partial_exit_count += 1;
                }

                // Execute exit
                if exit {
                    // Calculate costs
                    let exit_slippage = exit_price * qty.abs() * (slippage_bps / 10000.0);
                    let exit_spread = exit_price * qty.abs() * (spread_bps / 10000.0 / 2.0);
                    total_slippage += exit_slippage;
                    total_spread_cost += exit_spread;
                    total_commission += commission;
                    portfolio.cash -= commission + exit_slippage + exit_spread;

                    // Create trade record before closing
                    let gross_pnl = (exit_price - state.position.entry_price) * qty;

                    if record_trades {
                        trade_ledger.push(create_trade_record(
                            state,
                            asset_id_u32,
                            exit_price,
                            ts,
                            global_bar_idx.saturating_sub(state.position.entry_bar_idx),
                            gross_pnl,
                            commission,
                            exit_slippage + exit_spread,
                            exit_reason,
                        ));
                    }

                    close_position(&mut portfolio, state, exit_price, None, global_bar_idx)?;

                    // Update exit statistics
                    match exit_reason {
                        ExitReason::StopLoss => stop_loss_exits += 1,
                        ExitReason::TakeProfit => take_profit_exits += 1,
                        ExitReason::TrailingStop => trailing_stop_exits += 1,
                        ExitReason::TimeStop => time_stop_exits += 1,
                        ExitReason::Signal => signal_exits += 1,
                        _ => {}
                    }
                }

                // Check for pyramid opportunity
                if !exit && state.position.qty != 0.0 {
                    let should_pyramid = if is_long { signal.long } else { signal.short };
                    if should_pyramid && pyramid_position(&mut portfolio, state, close, cfg, atr)? {
                        pyramid_entry_count += 1;
                    }
                }
            }

            // Enter new position
            if state.position.qty == 0.0 {
                if signal.long {
                    let entry_slippage = close * (slippage_bps / 10000.0);
                    let entry_spread = close * (spread_bps / 10000.0 / 2.0);

                    if enter_long(&mut portfolio, state, close, cfg, ts, global_bar_idx, atr)? {
                        let entry_cost = close * state.position.qty * (entry_slippage + entry_spread) / close;
                        total_slippage += entry_cost * (slippage_bps / (slippage_bps + spread_bps / 2.0));
                        total_spread_cost += entry_cost * ((spread_bps / 2.0) / (slippage_bps + spread_bps / 2.0));
                        total_commission += commission;
                        portfolio.cash -= commission + entry_cost;

                        state.position.entry_commission = commission;
                        state.position.entry_slippage = entry_cost;
                    }
                } else if signal.short {
                    let entry_slippage = close * (slippage_bps / 10000.0);
                    let entry_spread = close * (spread_bps / 10000.0 / 2.0);

                    if enter_short(&mut portfolio, state, close, cfg, ts, global_bar_idx, atr)? {
                        let entry_cost = close * state.position.qty.abs() * (entry_slippage + entry_spread) / close;
                        total_slippage += entry_cost * (slippage_bps / (slippage_bps + spread_bps / 2.0));
                        total_spread_cost += entry_cost * ((spread_bps / 2.0) / (slippage_bps + spread_bps / 2.0));
                        total_commission += commission;
                        portfolio.cash -= commission + entry_cost;

                        state.position.entry_commission = commission;
                        state.position.entry_slippage = entry_cost;
                    }
                }
            }

            global_bar_idx += 1;
        }
    }

    // Final equity calculation
    if let Some(final_ts) = current_ts {
        let equity = checked_equity(portfolio.cash, portfolio.marked_value)?;
        if prev_equity > 0.0 {
            let step = (equity - prev_equity) / prev_equity;
            ensure_finite(step, "step_return")?;
            returns.push(step);
        }
        final_equity = equity;
        equity_history.push(equity);

        if equity > peak_equity {
            peak_equity = equity;
            ensure_finite(peak_equity, "peak_equity")?;
        }
        let drawdown = if peak_equity > 0.0 {
            (peak_equity - equity) / peak_equity
        } else {
            0.0
        };
        ensure_finite(drawdown, "drawdown")?;
        if drawdown > max_drawdown {
            max_drawdown = drawdown;
        }

        if record_equity_curve {
            equity_curve.push(EquityPoint {
                ts: final_ts,
                equity,
                cash: portfolio.cash,
                drawdown,
                position_value: portfolio.marked_value,
                unrealized_pnl: portfolio.unrealized,
            });
        }
    }

    // Calculate final metrics
    let total_return = (final_equity / cfg.initial_cash) - 1.0;
    ensure_finite(total_return, "total_return")?;

    let sharpe = sharpe_ratio(&returns, cfg.periods_per_year);
    let sortino = sortino_ratio(&returns, cfg.periods_per_year);
    let ann_return = annualized_return(total_return, returns.len(), cfg.periods_per_year);
    let calmar = calmar_ratio(ann_return, max_drawdown);

    // Trade statistics
    let trades = portfolio.trades;
    let wins = portfolio.wins;
    let losses = portfolio.losses;
    let win_pct = if trades > 0 {
        wins as f64 / trades as f64
    } else {
        0.0
    };
    let expectancy = if trades > 0 {
        portfolio.realized_pnl / trades as f64
    } else {
        0.0
    };
    let avg_win = if wins > 0 {
        portfolio.win_pnl_sum / wins as f64
    } else {
        0.0
    };
    let avg_loss = if losses > 0 {
        portfolio.loss_pnl_sum.abs() / losses as f64
    } else {
        0.0
    };
    let pf = profit_factor(portfolio.gross_profit, portfolio.gross_loss);
    let pr = payoff_ratio(avg_win, avg_loss);
    let avg_bars = if trades > 0 {
        portfolio.total_bars_held as f64 / trades as f64
    } else {
        0.0
    };

    // Risk metrics
    let var_95 = value_at_risk(&returns, 0.95);
    let cvar_95 = conditional_var(&returns, 0.95);
    let rf = recovery_factor(portfolio.realized_pnl, max_drawdown * cfg.initial_cash);
    let ui = ulcer_index(&equity_history);
    let kelly = kelly_criterion(win_pct, pr);

    // Volatility
    let ann_vol = if returns.len() >= 2 {
        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>()
            / (returns.len() - 1) as f64;
        variance.sqrt() * cfg.periods_per_year.sqrt()
    } else {
        0.0
    };

    let total_execution_cost = total_slippage + total_spread_cost;

    Ok(BacktestResult {
        total_return,
        sharpe,
        sortino,
        max_drawdown,
        calmar,
        annualized_return: ann_return,
        annualized_volatility: ann_vol,
        trades,
        wins,
        losses,
        win_pct,
        expectancy,
        avg_win,
        avg_loss,
        profit_factor: pf,
        payoff_ratio: pr,
        max_consecutive_wins: portfolio.max_consecutive_wins,
        max_consecutive_losses: portfolio.max_consecutive_losses,
        avg_bars_held: avg_bars,
        var_95,
        cvar_95,
        recovery_factor: rf,
        ulcer_index: ui,
        kelly_criterion: kelly,
        final_equity,
        cash: portfolio.cash,
        realized_pnl: portfolio.realized_pnl,
        unrealized_pnl: portfolio.unrealized,
        margin_used: portfolio.margin_used,
        total_commission,
        total_execution_cost,
        total_slippage,
        total_spread_cost,
        stop_loss_exits,
        take_profit_exits,
        trailing_stop_exits,
        time_stop_exits,
        signal_exits,
        partial_exits: partial_exit_count,
        pyramid_entries: pyramid_entry_count,
        config: cfg.clone(),
        trade_ledger,
        equity_curve,
    })
}
