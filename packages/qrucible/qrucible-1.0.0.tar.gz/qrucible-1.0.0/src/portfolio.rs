//! Portfolio and position management.

use crate::config::StrategyConfig;
use crate::indicators::IndicatorState;
use crate::metrics::{checked_equity, ensure_finite};
use crate::result::Trade;

/// Position state for a single asset.
#[derive(Clone, Copy, Debug)]
pub struct Position {
    pub qty: f64,
    pub entry_price: f64,
    pub avg_entry_price: f64, // For pyramiding
    pub margin_used: f64,
    pub last_trade_loss: bool,
    pub entry_ts: i64,
    pub entry_bar_idx: usize,
    pub trailing_stop_price: f64, // Current trailing stop price
    pub trailing_stop_active: bool,
    pub break_even_triggered: bool,
    pub partial_exit_triggered: bool,
    pub pyramid_count: usize, // Number of pyramid entries
    pub highest_price: f64, // For MAE/MFE tracking
    pub lowest_price: f64, // For MAE/MFE tracking
    pub entry_commission: f64,
    pub entry_slippage: f64,
}

impl Default for Position {
    fn default() -> Self {
        Self {
            qty: 0.0,
            entry_price: 0.0,
            avg_entry_price: 0.0,
            margin_used: 0.0,
            last_trade_loss: false,
            entry_ts: 0,
            entry_bar_idx: 0,
            trailing_stop_price: 0.0,
            trailing_stop_active: false,
            break_even_triggered: false,
            partial_exit_triggered: false,
            pyramid_count: 0,
            highest_price: 0.0,
            lowest_price: f64::MAX,
            entry_commission: 0.0,
            entry_slippage: 0.0,
        }
    }
}

/// Asset state including indicator and position.
pub struct AssetState {
    pub indicator: IndicatorState,
    pub position: Position,
    pub last_price: f64,
    pub has_price: bool,
}

impl AssetState {
    pub fn new(indicator: IndicatorState) -> Self {
        Self {
            indicator,
            position: Position::default(),
            last_price: 0.0,
            has_price: false,
        }
    }
}

/// Portfolio state across all assets.
pub struct Portfolio {
    pub cash: f64,
    pub realized_pnl: f64,
    pub margin_used: f64,
    pub marked_value: f64,
    pub unrealized: f64,
    pub trades: usize,
    pub wins: usize,
    pub losses: usize,
    pub win_pnl_sum: f64,
    pub loss_pnl_sum: f64,
    pub gross_profit: f64,
    pub gross_loss: f64,
    pub total_bars_held: usize,
    pub consecutive_wins: usize,
    pub consecutive_losses: usize,
    pub max_consecutive_wins: usize,
    pub max_consecutive_losses: usize,
    pub trade_results: Vec<bool>, // true = win, false = loss
}

impl Portfolio {
    pub fn new(initial_cash: f64) -> Self {
        Self {
            cash: initial_cash,
            realized_pnl: 0.0,
            margin_used: 0.0,
            marked_value: 0.0,
            unrealized: 0.0,
            trades: 0,
            wins: 0,
            losses: 0,
            win_pnl_sum: 0.0,
            loss_pnl_sum: 0.0,
            gross_profit: 0.0,
            gross_loss: 0.0,
            total_bars_held: 0,
            consecutive_wins: 0,
            consecutive_losses: 0,
            max_consecutive_wins: 0,
            max_consecutive_losses: 0,
            trade_results: Vec::new(),
        }
    }
}

/// Exit reason for trade logging.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExitReason {
    Signal,
    StopLoss,
    TakeProfit,
    TrailingStop,
    TimeStop,
    BreakEven,
    PartialExit,
    MaxDrawdown,
}

impl ExitReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            ExitReason::Signal => "signal",
            ExitReason::StopLoss => "stop_loss",
            ExitReason::TakeProfit => "take_profit",
            ExitReason::TrailingStop => "trailing_stop",
            ExitReason::TimeStop => "time_stop",
            ExitReason::BreakEven => "break_even",
            ExitReason::PartialExit => "partial_exit",
            ExitReason::MaxDrawdown => "max_drawdown",
        }
    }
}

/// Mark position to current price.
pub fn mark_to_price(
    portfolio: &mut Portfolio,
    state: &mut AssetState,
    price: f64,
) -> Result<(), String> {
    if state.position.qty != 0.0 && state.has_price {
        let delta = state.position.qty * (price - state.last_price);
        portfolio.marked_value += delta;
        portfolio.unrealized += delta;
        ensure_finite(portfolio.marked_value, "marked_value")?;
        ensure_finite(portfolio.unrealized, "unrealized_pnl")?;

        // Update MAE/MFE tracking
        if state.position.qty > 0.0 {
            state.position.highest_price = state.position.highest_price.max(price);
            state.position.lowest_price = state.position.lowest_price.min(price);
        } else {
            state.position.highest_price = state.position.highest_price.max(price);
            state.position.lowest_price = state.position.lowest_price.min(price);
        }
    }
    state.last_price = price;
    state.has_price = true;
    Ok(())
}

/// Calculate position size based on risk.
pub fn calculate_position_size(
    portfolio: &Portfolio,
    state: &AssetState,
    price: f64,
    stop_distance: f64,
    cfg: &StrategyConfig,
) -> f64 {
    let size_multiplier = if cfg.reduce_after_loss && state.position.last_trade_loss {
        cfg.loss_size_factor
    } else {
        1.0
    };

    let equity = match checked_equity(portfolio.cash, portfolio.marked_value) {
        Ok(e) => e,
        Err(_) => return 0.0,
    };

    let risk_budget = (equity * cfg.risk_per_trade * size_multiplier).max(0.0);
    let risk_per_unit = price * stop_distance;

    if risk_budget <= 0.0 || risk_per_unit <= 0.0 || price <= 0.0 {
        return 0.0;
    }

    let mut qty = risk_budget / risk_per_unit;

    // Apply max position size constraint
    let max_qty = (equity * cfg.max_position_size) / price;
    qty = qty.min(max_qty);

    qty
}

/// Enter a long position.
pub fn enter_long(
    portfolio: &mut Portfolio,
    state: &mut AssetState,
    price: f64,
    cfg: &StrategyConfig,
    ts: i64,
    bar_idx: usize,
    atr: Option<f64>,
) -> Result<bool, String> {
    let stop_distance = if cfg.use_atr_stops {
        atr.unwrap_or(price * cfg.stop_loss) * cfg.atr_multiplier / price
    } else {
        cfg.stop_loss
    };

    let qty = calculate_position_size(portfolio, state, price, stop_distance, cfg);

    let available_cash = (portfolio.cash - portfolio.margin_used).max(0.0);
    let max_qty = available_cash / price;
    let qty = qty.min(max_qty);

    if !qty.is_finite() || qty <= 0.0 {
        return Ok(false);
    }

    let cost = qty * price;
    portfolio.cash -= cost;
    ensure_finite(portfolio.cash, "cash")?;

    state.position.qty = qty;
    state.position.entry_price = price;
    state.position.avg_entry_price = price;
    state.position.margin_used = 0.0;
    state.position.entry_ts = ts;
    state.position.entry_bar_idx = bar_idx;
    state.position.pyramid_count = 1;
    state.position.highest_price = price;
    state.position.lowest_price = price;
    state.position.trailing_stop_active = false;
    state.position.break_even_triggered = false;
    state.position.partial_exit_triggered = false;

    // Initialize trailing stop if enabled
    if cfg.trailing_stop.enabled && cfg.trailing_stop.activation_pct == 0.0 {
        let trail = if cfg.trailing_stop.trail_atr_mult > 0.0 {
            atr.map(|a| a * cfg.trailing_stop.trail_atr_mult)
                .unwrap_or(price * cfg.trailing_stop.trail_pct)
        } else {
            price * cfg.trailing_stop.trail_pct
        };
        state.position.trailing_stop_price = price - trail;
        state.position.trailing_stop_active = true;
    }

    portfolio.marked_value += cost;
    ensure_finite(portfolio.marked_value, "marked_value")?;

    Ok(true)
}

/// Enter a short position.
pub fn enter_short(
    portfolio: &mut Portfolio,
    state: &mut AssetState,
    price: f64,
    cfg: &StrategyConfig,
    ts: i64,
    bar_idx: usize,
    atr: Option<f64>,
) -> Result<bool, String> {
    let stop_distance = if cfg.use_atr_stops {
        atr.unwrap_or(price * cfg.stop_loss) * cfg.atr_multiplier / price
    } else {
        cfg.stop_loss
    };

    let qty = calculate_position_size(portfolio, state, price, stop_distance, cfg);

    let available_cash = (portfolio.cash - portfolio.margin_used).max(0.0);
    let mut notional = qty * price;
    let max_notional = available_cash / cfg.margin_factor;

    if notional > max_notional {
        notional = max_notional;
    }
    let qty = notional / price;

    if !qty.is_finite() || qty <= 0.0 {
        return Ok(false);
    }

    let margin_required = notional * cfg.margin_factor;
    portfolio.cash += notional;
    portfolio.margin_used += margin_required;
    ensure_finite(portfolio.cash, "cash")?;
    ensure_finite(portfolio.margin_used, "margin_used")?;

    state.position.qty = -qty;
    state.position.entry_price = price;
    state.position.avg_entry_price = price;
    state.position.margin_used = margin_required;
    state.position.entry_ts = ts;
    state.position.entry_bar_idx = bar_idx;
    state.position.pyramid_count = 1;
    state.position.highest_price = price;
    state.position.lowest_price = price;
    state.position.trailing_stop_active = false;
    state.position.break_even_triggered = false;
    state.position.partial_exit_triggered = false;

    // Initialize trailing stop if enabled
    if cfg.trailing_stop.enabled && cfg.trailing_stop.activation_pct == 0.0 {
        let trail = if cfg.trailing_stop.trail_atr_mult > 0.0 {
            atr.map(|a| a * cfg.trailing_stop.trail_atr_mult)
                .unwrap_or(price * cfg.trailing_stop.trail_pct)
        } else {
            price * cfg.trailing_stop.trail_pct
        };
        state.position.trailing_stop_price = price + trail;
        state.position.trailing_stop_active = true;
    }

    portfolio.marked_value += state.position.qty * price;
    ensure_finite(portfolio.marked_value, "marked_value")?;

    Ok(true)
}

/// Add to an existing position (pyramid).
pub fn pyramid_position(
    portfolio: &mut Portfolio,
    state: &mut AssetState,
    price: f64,
    cfg: &StrategyConfig,
    atr: Option<f64>,
) -> Result<bool, String> {
    if !cfg.pyramid.enabled {
        return Ok(false);
    }

    if state.position.pyramid_count >= cfg.pyramid.max_entries {
        return Ok(false);
    }

    // Check spacing requirement
    let price_move_pct = if state.position.qty > 0.0 {
        (price - state.position.avg_entry_price) / state.position.avg_entry_price
    } else {
        (state.position.avg_entry_price - price) / state.position.avg_entry_price
    };

    if price_move_pct < cfg.pyramid.entry_spacing_pct {
        return Ok(false);
    }

    let stop_distance = if cfg.use_atr_stops {
        atr.unwrap_or(price * cfg.stop_loss) * cfg.atr_multiplier / price
    } else {
        cfg.stop_loss
    };

    let base_qty = calculate_position_size(portfolio, state, price, stop_distance, cfg);
    let add_qty = base_qty * cfg.pyramid.size_multiplier;

    if !add_qty.is_finite() || add_qty <= 0.0 {
        return Ok(false);
    }

    let is_long = state.position.qty > 0.0;

    if is_long {
        let available_cash = (portfolio.cash - portfolio.margin_used).max(0.0);
        let max_add = available_cash / price;
        let add_qty = add_qty.min(max_add);

        if add_qty <= 0.0 {
            return Ok(false);
        }

        let cost = add_qty * price;
        portfolio.cash -= cost;
        portfolio.marked_value += cost;

        // Update average entry price
        let total_cost = state.position.qty * state.position.avg_entry_price + cost;
        let new_qty = state.position.qty + add_qty;
        state.position.avg_entry_price = total_cost / new_qty;
        state.position.qty = new_qty;
    } else {
        let available_cash = (portfolio.cash - portfolio.margin_used).max(0.0);
        let max_notional = available_cash / cfg.margin_factor;
        let add_notional = (add_qty * price).min(max_notional);
        let add_qty = add_notional / price;

        if add_qty <= 0.0 {
            return Ok(false);
        }

        let margin_required = add_notional * cfg.margin_factor;
        portfolio.cash += add_notional;
        portfolio.margin_used += margin_required;

        // Update average entry price
        let total_notional =
            state.position.qty.abs() * state.position.avg_entry_price + add_notional;
        let new_qty = state.position.qty.abs() + add_qty;
        state.position.avg_entry_price = total_notional / new_qty;
        state.position.qty = -new_qty;
        state.position.margin_used += margin_required;

        portfolio.marked_value -= add_notional;
    }

    state.position.pyramid_count += 1;
    ensure_finite(portfolio.cash, "cash")?;
    ensure_finite(portfolio.marked_value, "marked_value")?;

    Ok(true)
}

/// Close a position (full or partial).
pub fn close_position(
    portfolio: &mut Portfolio,
    state: &mut AssetState,
    exit_price: f64,
    exit_qty: Option<f64>, // None = full exit
    bar_idx: usize,
) -> Result<(f64, usize), String> {
    // Returns (pnl, bars_held)
    let qty = state.position.qty;
    if qty == 0.0 {
        return Ok((0.0, 0));
    }

    let exit_qty = exit_qty.unwrap_or(qty.abs()).min(qty.abs());
    let is_full_exit = (exit_qty - qty.abs()).abs() < 1e-10;
    let exit_qty_signed = if qty > 0.0 { exit_qty } else { -exit_qty };

    let mark_value = exit_qty_signed * state.last_price;
    portfolio.marked_value -= mark_value;
    portfolio.unrealized -= exit_qty_signed * (state.last_price - state.position.entry_price);
    ensure_finite(portfolio.marked_value, "marked_value")?;
    ensure_finite(portfolio.unrealized, "unrealized_pnl")?;

    let pnl = (exit_price - state.position.entry_price) * exit_qty_signed;
    portfolio.cash += exit_qty_signed * exit_price;
    portfolio.realized_pnl += pnl;

    if is_full_exit {
        portfolio.trades += 1;
        if pnl >= 0.0 {
            portfolio.wins += 1;
            portfolio.win_pnl_sum += pnl;
            portfolio.gross_profit += pnl;
            state.position.last_trade_loss = false;
            portfolio.consecutive_wins += 1;
            portfolio.consecutive_losses = 0;
            portfolio.max_consecutive_wins =
                portfolio.max_consecutive_wins.max(portfolio.consecutive_wins);
        } else {
            portfolio.losses += 1;
            portfolio.loss_pnl_sum += pnl;
            portfolio.gross_loss += pnl.abs();
            state.position.last_trade_loss = true;
            portfolio.consecutive_losses += 1;
            portfolio.consecutive_wins = 0;
            portfolio.max_consecutive_losses =
                portfolio.max_consecutive_losses.max(portfolio.consecutive_losses);
        }
        portfolio.trade_results.push(pnl >= 0.0);
    }

    let bars_held = bar_idx.saturating_sub(state.position.entry_bar_idx);
    portfolio.total_bars_held += bars_held;

    ensure_finite(portfolio.cash, "cash")?;
    ensure_finite(portfolio.realized_pnl, "realized_pnl")?;

    // Release margin for shorts
    if qty < 0.0 {
        let margin_to_release = state.position.margin_used * (exit_qty / qty.abs());
        portfolio.margin_used -= margin_to_release;
        state.position.margin_used -= margin_to_release;
        ensure_finite(portfolio.margin_used, "margin_used")?;
    }

    if is_full_exit {
        state.position.qty = 0.0;
        state.position.entry_price = 0.0;
        state.position.avg_entry_price = 0.0;
        state.position.margin_used = 0.0;
        state.position.pyramid_count = 0;
    } else {
        state.position.qty -= exit_qty_signed;
    }

    Ok((pnl, bars_held))
}

/// Check and update trailing stop.
pub fn update_trailing_stop(
    state: &mut AssetState,
    high: f64,
    low: f64,
    close: f64,
    cfg: &StrategyConfig,
    atr: Option<f64>,
) -> bool {
    if !cfg.trailing_stop.enabled || state.position.qty == 0.0 {
        return false;
    }

    let is_long = state.position.qty > 0.0;
    let profit_pct = if is_long {
        (close - state.position.entry_price) / state.position.entry_price
    } else {
        (state.position.entry_price - close) / state.position.entry_price
    };

    // Check if trailing stop should be activated
    if !state.position.trailing_stop_active {
        if profit_pct >= cfg.trailing_stop.activation_pct {
            state.position.trailing_stop_active = true;
            let trail = if cfg.trailing_stop.trail_atr_mult > 0.0 {
                atr.map(|a| a * cfg.trailing_stop.trail_atr_mult)
                    .unwrap_or(close * cfg.trailing_stop.trail_pct)
            } else {
                close * cfg.trailing_stop.trail_pct
            };

            if is_long {
                state.position.trailing_stop_price = close - trail;
            } else {
                state.position.trailing_stop_price = close + trail;
            }
        }
        return false;
    }

    // Update trailing stop
    let trail = if cfg.trailing_stop.trail_atr_mult > 0.0 {
        atr.map(|a| a * cfg.trailing_stop.trail_atr_mult)
            .unwrap_or(close * cfg.trailing_stop.trail_pct)
    } else {
        close * cfg.trailing_stop.trail_pct
    };

    if is_long {
        let new_stop = high - trail;
        if new_stop > state.position.trailing_stop_price {
            state.position.trailing_stop_price = new_stop;
        }
        // Check if stop is hit
        low <= state.position.trailing_stop_price
    } else {
        let new_stop = low + trail;
        if new_stop < state.position.trailing_stop_price {
            state.position.trailing_stop_price = new_stop;
        }
        // Check if stop is hit
        high >= state.position.trailing_stop_price
    }
}

/// Check and update break-even stop.
pub fn update_break_even(state: &mut AssetState, close: f64, cfg: &StrategyConfig) -> Option<f64> {
    if !cfg.break_even.enabled
        || state.position.qty == 0.0
        || state.position.break_even_triggered
    {
        return None;
    }

    let is_long = state.position.qty > 0.0;
    let profit_pct = if is_long {
        (close - state.position.entry_price) / state.position.entry_price
    } else {
        (state.position.entry_price - close) / state.position.entry_price
    };

    if profit_pct >= cfg.break_even.trigger_pct {
        state.position.break_even_triggered = true;
        let new_stop = if is_long {
            state.position.entry_price * (1.0 + cfg.break_even.offset_pct)
        } else {
            state.position.entry_price * (1.0 - cfg.break_even.offset_pct)
        };
        Some(new_stop)
    } else {
        None
    }
}

/// Check time-based stop.
pub fn check_time_stop(
    state: &AssetState,
    current_ts: i64,
    bar_idx: usize,
    cfg: &StrategyConfig,
) -> bool {
    if !cfg.time_stop.enabled || state.position.qty == 0.0 {
        return false;
    }

    let bars_held = bar_idx.saturating_sub(state.position.entry_bar_idx);
    if cfg.time_stop.max_bars > 0 && bars_held >= cfg.time_stop.max_bars {
        return true;
    }

    if cfg.time_stop.max_duration_us > 0 {
        let duration = current_ts - state.position.entry_ts;
        if duration >= cfg.time_stop.max_duration_us {
            return true;
        }
    }

    false
}

/// Check partial exit conditions.
pub fn check_partial_exit(state: &mut AssetState, close: f64, cfg: &StrategyConfig) -> bool {
    if !cfg.partial_exit.enabled
        || state.position.qty == 0.0
        || state.position.partial_exit_triggered
    {
        return false;
    }

    let is_long = state.position.qty > 0.0;
    let profit_pct = if is_long {
        (close - state.position.entry_price) / state.position.entry_price
    } else {
        (state.position.entry_price - close) / state.position.entry_price
    };

    if profit_pct >= cfg.partial_exit.trigger_pct {
        state.position.partial_exit_triggered = true;
        true
    } else {
        false
    }
}

/// Create trade record for logging.
pub fn create_trade_record(
    state: &AssetState,
    asset_id: u32,
    exit_price: f64,
    exit_ts: i64,
    bars_held: usize,
    gross_pnl: f64,
    commission: f64,
    execution_cost: f64,
    exit_reason: ExitReason,
) -> Trade {
    let is_long = state.position.qty > 0.0;

    // Calculate MAE and MFE
    let (mae, mfe) = if is_long {
        let mae = (state.position.entry_price - state.position.lowest_price)
            / state.position.entry_price;
        let mfe = (state.position.highest_price - state.position.entry_price)
            / state.position.entry_price;
        (mae, mfe)
    } else {
        let mae = (state.position.highest_price - state.position.entry_price)
            / state.position.entry_price;
        let mfe = (state.position.entry_price - state.position.lowest_price)
            / state.position.entry_price;
        (mae, mfe)
    };

    let total_commission = state.position.entry_commission + commission;
    let total_execution_cost = state.position.entry_slippage + execution_cost;
    let net_pnl = gross_pnl - total_commission - total_execution_cost;

    Trade {
        asset_id,
        entry_ts: state.position.entry_ts,
        exit_ts,
        side: if is_long {
            "long".to_string()
        } else {
            "short".to_string()
        },
        qty: state.position.qty.abs(),
        entry_price: state.position.entry_price,
        exit_price,
        gross_pnl,
        net_pnl,
        commission_paid: total_commission,
        execution_cost: total_execution_cost,
        bars_held,
        mae,
        mfe,
        exit_reason: exit_reason.as_str().to_string(),
    }
}
