"""
Qrucible Test Suite
==================

This module contains comprehensive tests for the Qrucible backtesting engine:
- Python/Rust parity tests for core strategies
- Edge case tests for error handling
- Validation tests for data integrity
- Strategy coverage tests for all 20+ strategy types
"""
import math
from dataclasses import dataclass
from typing import List

import numpy as np
import pytest

from qrucible import (
    StrategyConfig,
    grid_search,
    run_backtest,
    run_backtest_with_signals,
    load_bars,
    BarData,
    TrailingStopConfig,
    BreakEvenConfig,
    TimeStopConfig,
    PartialExitConfig,
    PyramidConfig,
)


@dataclass
class PyResult:
    total_return: float
    sharpe: float
    trades: int
    wins: int
    losses: int
    final_equity: float


def make_bars(rows: int = 300) -> np.ndarray:
    t = np.linspace(0.0, 12.0 * math.pi, rows)
    closes = 100.0 + np.sin(t) + 0.1 * np.cos(3.0 * t)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    spread = 0.001
    highs = np.maximum(opens, closes) * (1.0 + spread)
    lows = np.minimum(opens, closes) * (1.0 - spread)
    volume = np.full(rows, 1_000.0)
    ohlcv = np.column_stack([opens, highs, lows, closes, volume]).astype(np.float64)
    timestamps = (np.arange(rows, dtype=np.int64) * 1_000_000).astype(np.float64)
    asset_ids = np.zeros(rows, dtype=np.float64)
    return np.column_stack([timestamps, asset_ids, ohlcv]).astype(np.float64)


def compute_sharpe(returns: List[float], periods_per_year: float) -> float:
    if len(returns) < 2:
        return 0.0
    mean = float(np.mean(returns))
    std = float(np.std(returns, ddof=1))
    if std <= 0.0:
        return 0.0
    return mean / std * math.sqrt(periods_per_year)


def python_backtest(bars: np.ndarray, cfg: StrategyConfig) -> PyResult:
    strategy = str(cfg.strategy_type).strip().upper()
    cash = cfg.initial_cash
    position = 0.0
    entry_price = 0.0
    margin_used = 0.0
    last_trade_loss = False
    trades = wins = losses = 0
    fast_sum = slow_sum = 0.0
    rsi_prev_close = None
    rsi_gain_sum = rsi_loss_sum = 0.0
    rsi_avg_gain = rsi_avg_loss = 0.0
    rsi_count = 0
    boll_period = cfg.bollinger_period
    boll_buf = [0.0] * boll_period
    boll_sum = boll_sumsq = 0.0
    boll_count = boll_idx = 0
    prev_equity = cash
    step_returns: List[float] = []

    closes = bars[:, 5]
    highs = bars[:, 3]
    lows = bars[:, 4]

    for i in range(len(bars)):
        close = closes[i]
        high = highs[i]
        low = lows[i]

        signal_long = False
        signal_short = False

        if strategy in {"MA_CROSS", "MA", "MACROSS"}:
            fast_sum += close
            if i >= cfg.fast_window:
                fast_sum -= closes[i - cfg.fast_window]
            slow_sum += close
            if i >= cfg.slow_window:
                slow_sum -= closes[i - cfg.slow_window]

            fast_ready = i + 1 >= cfg.fast_window
            slow_ready = i + 1 >= cfg.slow_window
            if fast_ready and slow_ready:
                fast_ma = fast_sum / cfg.fast_window
                slow_ma = slow_sum / cfg.slow_window
                signal_long = fast_ma > slow_ma
                signal_short = fast_ma < slow_ma
        elif strategy == "RSI":
            if rsi_prev_close is not None:
                delta = close - rsi_prev_close
                gain = max(delta, 0.0)
                loss = max(-delta, 0.0)
                if rsi_count < cfg.rsi_period:
                    rsi_gain_sum += gain
                    rsi_loss_sum += loss
                    rsi_count += 1
                    if rsi_count == cfg.rsi_period:
                        rsi_avg_gain = rsi_gain_sum / cfg.rsi_period
                        rsi_avg_loss = rsi_loss_sum / cfg.rsi_period
                else:
                    rsi_avg_gain = (rsi_avg_gain * (cfg.rsi_period - 1) + gain) / cfg.rsi_period
                    rsi_avg_loss = (rsi_avg_loss * (cfg.rsi_period - 1) + loss) / cfg.rsi_period
            rsi_prev_close = close
            if rsi_count >= cfg.rsi_period:
                if rsi_avg_loss == 0.0:
                    rsi = 100.0
                else:
                    rs = rsi_avg_gain / rsi_avg_loss
                    rsi = 100.0 - (100.0 / (1.0 + rs))
                signal_long = rsi < cfg.rsi_lower
                signal_short = rsi > cfg.rsi_upper
        elif strategy in {"BOLLINGER", "BOLL", "BBANDS"}:
            if boll_count < boll_period:
                boll_buf[boll_count] = close
                boll_sum += close
                boll_sumsq += close * close
                boll_count += 1
                boll_ready = boll_count >= boll_period
            else:
                old = boll_buf[boll_idx]
                boll_sum -= old
                boll_sumsq -= old * old
                boll_buf[boll_idx] = close
                boll_sum += close
                boll_sumsq += close * close
                boll_idx = (boll_idx + 1) % boll_period
                boll_ready = True

            if boll_ready:
                mean = boll_sum / boll_period
                variance = (boll_sumsq / boll_period) - (mean * mean)
                if variance < 0.0:
                    variance = 0.0
                std = math.sqrt(variance)
                upper = mean + cfg.bollinger_std * std
                lower = mean - cfg.bollinger_std * std
                signal_long = close < lower
                signal_short = close > upper
        else:
            raise ValueError(f"Unknown strategy_type: {cfg.strategy_type}")

        if position != 0.0:
            exit_trade = False
            exit_price = close

            if position > 0.0:
                stop_price = entry_price * (1.0 - cfg.stop_loss)
                if low <= stop_price:
                    exit_trade = True
                    exit_price = stop_price

                if not exit_trade and cfg.take_profit > 0.0:
                    tp_price = entry_price * (1.0 + cfg.take_profit)
                    if high >= tp_price:
                        exit_trade = True
                        exit_price = tp_price

                if not exit_trade and signal_short:
                    exit_trade = True
            else:
                stop_price = entry_price * (1.0 + cfg.stop_loss)
                if high >= stop_price:
                    exit_trade = True
                    exit_price = stop_price

                if not exit_trade and cfg.take_profit > 0.0:
                    tp_price = entry_price * (1.0 - cfg.take_profit)
                    if low <= tp_price:
                        exit_trade = True
                        exit_price = tp_price

                if not exit_trade and signal_long:
                    exit_trade = True

            if exit_trade:
                pnl = (exit_price - entry_price) * position
                cash += position * exit_price
                position = 0.0
                margin_used = 0.0
                trades += 1
                if pnl >= 0.0:
                    wins += 1
                    last_trade_loss = False
                else:
                    losses += 1
                    last_trade_loss = True

        if position == 0.0 and (signal_long or signal_short):
            size_mult = cfg.loss_size_factor if cfg.reduce_after_loss and last_trade_loss else 1.0
            available_cash = max(0.0, cash - margin_used)
            equity = cash + position * close
            risk_budget = max(0.0, equity * cfg.risk_per_trade * size_mult)
            risk_per_unit = close * cfg.stop_loss
            if risk_budget > 0.0 and risk_per_unit > 0.0 and close > 0.0:
                qty = risk_budget / risk_per_unit
                if signal_long:
                    max_qty = available_cash / close
                    qty = min(qty, max_qty)
                    if np.isfinite(qty) and qty > 0.0:
                        cash -= qty * close
                        position = qty
                        entry_price = close
                elif signal_short:
                    notional = qty * close
                    max_notional = available_cash / cfg.margin_factor
                    notional = min(notional, max_notional)
                    qty = notional / close
                    if np.isfinite(qty) and qty > 0.0:
                        cash += notional
                        margin_used += notional * cfg.margin_factor
                        position = -qty
                        entry_price = close

        equity = cash + position * close
        if prev_equity > 0.0:
            step_returns.append((equity - prev_equity) / prev_equity)
        prev_equity = equity

    total_return = (prev_equity / cfg.initial_cash) - 1.0
    sharpe = compute_sharpe(step_returns, cfg.periods_per_year)
    return PyResult(
        total_return=total_return,
        sharpe=sharpe,
        trades=trades,
        wins=wins,
        losses=losses,
        final_equity=prev_equity,
    )


@pytest.mark.parametrize(
    "strategy_type,kwargs",
    [
        ("MA_CROSS", dict(fast_window=3, slow_window=7)),
        ("RSI", dict(rsi_period=6, rsi_lower=45.0, rsi_upper=55.0)),
        ("BOLLINGER", dict(bollinger_period=10, bollinger_std=0.5)),
    ],
)
def test_python_rust_parity(strategy_type: str, kwargs: dict) -> None:
    bars = make_bars()
    cfg = StrategyConfig(
        strategy_type=strategy_type,
        stop_loss=0.01,
        take_profit=0.02,
        risk_per_trade=0.02,
        initial_cash=100_000.0,
        reduce_after_loss=True,
        loss_size_factor=0.5,
        margin_factor=1.0,
        **kwargs,
    )

    py = python_backtest(bars, cfg)
    rust = run_backtest(bars, cfg)

    assert rust.trades == py.trades
    assert rust.wins == py.wins
    assert rust.losses == py.losses
    assert rust.total_return == pytest.approx(py.total_return, rel=1e-9, abs=1e-9)
    assert rust.final_equity == pytest.approx(py.final_equity, rel=1e-9, abs=1e-6)
    assert rust.sharpe == pytest.approx(py.sharpe, rel=1e-6, abs=1e-6)


def test_grid_search_orders_and_matches_single_runs() -> None:
    bars = make_bars()
    base_kwargs = dict(
        stop_loss=0.01,
        take_profit=0.03,
        risk_per_trade=0.02,
        initial_cash=250_000.0,
        reduce_after_loss=True,
        loss_size_factor=0.5,
        margin_factor=1.0,
    )
    configs = [
        StrategyConfig(strategy_type="MA_CROSS", fast_window=3, slow_window=8, **base_kwargs),
        StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=12, **base_kwargs),
        StrategyConfig(strategy_type="MA_CROSS", fast_window=8, slow_window=20, **base_kwargs),
    ]

    grid_results = grid_search(bars, configs, metric="total_return", top_n=2)
    single_runs = [run_backtest(bars, cfg) for cfg in configs]
    single_sorted = sorted(single_runs, key=lambda r: r.total_return, reverse=True)[:2]

    assert len(grid_results) == 2
    for got, expected in zip(grid_results, single_sorted):
        assert got.total_return == pytest.approx(expected.total_return, rel=1e-9, abs=1e-9)
        assert got.trades == expected.trades
        assert got.wins == expected.wins
        assert got.losses == expected.losses


# =============================================================================
# EDGE CASE TESTS - Error Handling
# =============================================================================

class TestEdgeCases:
    """Test error handling and edge cases."""

    def test_empty_data_raises_error(self) -> None:
        """Empty data should raise a clear error."""
        empty_bars = np.zeros((0, 7), dtype=np.float64)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=3, slow_window=7)
        with pytest.raises(ValueError, match="empty|zero rows"):
            run_backtest(empty_bars, cfg)

    def test_insufficient_data_for_indicator(self) -> None:
        """Data with fewer bars than indicator period should raise clear error."""
        # Create only 5 bars, but slow_window=20 needs at least 20
        small_bars = make_bars(rows=5)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=3, slow_window=20)
        with pytest.raises(ValueError, match="insufficient data|warm-up"):
            run_backtest(small_bars, cfg)

    def test_invalid_strategy_type(self) -> None:
        """Invalid strategy type should raise clear error."""
        with pytest.raises(ValueError, match="strategy_type"):
            StrategyConfig(strategy_type="INVALID_STRATEGY")

    def test_invalid_stop_loss_zero(self) -> None:
        """Zero stop_loss should raise error."""
        with pytest.raises(ValueError, match="stop_loss"):
            StrategyConfig(strategy_type="MA_CROSS", stop_loss=0.0)

    def test_invalid_stop_loss_negative(self) -> None:
        """Negative stop_loss should raise error."""
        with pytest.raises(ValueError, match="stop_loss"):
            StrategyConfig(strategy_type="MA_CROSS", stop_loss=-0.01)

    def test_invalid_risk_per_trade(self) -> None:
        """Invalid risk_per_trade should raise error."""
        with pytest.raises(ValueError, match="risk_per_trade"):
            StrategyConfig(strategy_type="MA_CROSS", risk_per_trade=1.5)

    def test_invalid_initial_cash(self) -> None:
        """Non-positive initial_cash should raise error."""
        with pytest.raises(ValueError, match="initial_cash"):
            StrategyConfig(strategy_type="MA_CROSS", initial_cash=0.0)

    def test_invalid_rsi_bounds(self) -> None:
        """RSI bounds where upper <= lower should raise error."""
        with pytest.raises(ValueError, match="rsi"):
            StrategyConfig(strategy_type="RSI", rsi_upper=30.0, rsi_lower=70.0)

    def test_invalid_macd_periods(self) -> None:
        """MACD with fast >= slow should raise error."""
        with pytest.raises(ValueError, match="macd"):
            StrategyConfig(strategy_type="MACD", macd_fast=26, macd_slow=12)

    def test_external_strategy_without_signals(self) -> None:
        """EXTERNAL strategy with run_backtest should raise error."""
        bars = make_bars()
        cfg = StrategyConfig(strategy_type="EXTERNAL")
        with pytest.raises(ValueError, match="EXTERNAL|signals"):
            run_backtest(bars, cfg)


# =============================================================================
# DATA VALIDATION TESTS
# =============================================================================

class TestDataValidation:
    """Test OHLC data validation."""

    def test_invalid_ohlc_high_less_than_low(self) -> None:
        """High < Low should raise clear error."""
        bars = make_bars()
        # Make high < low for one bar
        bars[10, 3] = 50.0  # high = 50
        bars[10, 4] = 60.0  # low = 60 (invalid)
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="high.*low|must be >="):
            run_backtest(bars, cfg)

    def test_invalid_ohlc_negative_price(self) -> None:
        """Negative prices should raise clear error."""
        bars = make_bars()
        bars[5, 5] = -10.0  # negative close
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="positive|negative"):
            run_backtest(bars, cfg)

    def test_invalid_ohlc_zero_price(self) -> None:
        """Zero prices should raise clear error."""
        bars = make_bars()
        bars[5, 2] = 0.0  # zero open
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="positive"):
            run_backtest(bars, cfg)

    def test_invalid_volume_negative(self) -> None:
        """Negative volume should raise clear error."""
        bars = make_bars()
        bars[5, 6] = -100.0  # negative volume
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="volume|non-negative"):
            run_backtest(bars, cfg)

    def test_nan_in_data(self) -> None:
        """NaN values in data should raise clear error."""
        bars = make_bars()
        bars[5, 5] = float('nan')  # NaN close
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="finite|nan"):
            run_backtest(bars, cfg)

    def test_inf_in_data(self) -> None:
        """Infinity values in data should raise clear error."""
        bars = make_bars()
        bars[5, 5] = float('inf')  # Inf close
        cfg = StrategyConfig(strategy_type="MA_CROSS")
        with pytest.raises(ValueError, match="finite|inf"):
            run_backtest(bars, cfg)


# =============================================================================
# STRATEGY COVERAGE TESTS - All 20+ Strategy Types
# =============================================================================

class TestAllStrategies:
    """Test that all strategy types can execute without errors."""

    BASE_KWARGS = dict(
        stop_loss=0.02,
        take_profit=0.04,
        risk_per_trade=0.01,
        initial_cash=100_000.0,
    )

    @pytest.mark.parametrize("strategy_type,extra_kwargs,min_bars", [
        ("MA_CROSS", dict(fast_window=5, slow_window=10), 15),
        ("RSI", dict(rsi_period=7), 20),
        ("BOLLINGER", dict(bollinger_period=10), 15),
        ("MACD", dict(macd_fast=8, macd_slow=17, macd_signal=5), 30),
        ("STOCHASTIC", dict(stoch_k_period=7, stoch_d_period=3), 15),
        ("ADX", dict(adx_period=7), 30),
        ("ATR", dict(atr_period=7), 15),
        ("CCI", dict(cci_period=10), 15),
        ("KELTNER", dict(keltner_period=10), 25),
        ("DONCHIAN", dict(donchian_period=10), 15),
        ("ICHIMOKU", dict(ichimoku_tenkan=5, ichimoku_kijun=13, ichimoku_senkou_b=26), 35),
        ("SUPERTREND", dict(supertrend_period=7, supertrend_mult=2.0), 15),
        ("WILLIAMS", dict(williams_period=7), 15),
        ("AROON", dict(aroon_period=12), 20),
        ("MFI", dict(mfi_period=7), 15),
        ("ROC", dict(roc_period=6), 15),
        ("TSI", dict(tsi_long_period=13, tsi_short_period=7, tsi_signal_period=7), 40),
        ("ULTIMATE", dict(uo_period1=4, uo_period2=7, uo_period3=14), 20),
        ("OBV", dict(obv_ma_period=10), 15),
        ("VWAP", dict(vwap_std_mult=2.0), 10),
    ])
    def test_strategy_executes(self, strategy_type: str, extra_kwargs: dict, min_bars: int) -> None:
        """Each strategy type should execute without errors."""
        bars = make_bars(rows=max(100, min_bars * 3))
        cfg = StrategyConfig(strategy_type=strategy_type, **self.BASE_KWARGS, **extra_kwargs)
        result = run_backtest(bars, cfg)

        # Basic sanity checks
        assert result is not None
        assert result.trades >= 0
        assert result.wins >= 0
        assert result.losses >= 0
        assert result.wins + result.losses <= result.trades
        assert result.final_equity > 0


# =============================================================================
# EXTERNAL SIGNALS TESTS
# =============================================================================

class TestExternalSignals:
    """Test external signal mode."""

    def test_external_signals_basic(self) -> None:
        """External signals should work correctly."""
        bars = make_bars(rows=100)
        signals = np.zeros(100, dtype=np.int8)
        # Go long on bar 10, exit on bar 50
        signals[10] = 1
        signals[50] = -1

        cfg = StrategyConfig(strategy_type="EXTERNAL")
        result = run_backtest_with_signals(bars, signals, cfg)

        assert result is not None
        assert result.trades >= 0

    def test_external_signals_wrong_length(self) -> None:
        """Signals array with wrong length should raise error."""
        bars = make_bars(rows=100)
        signals = np.zeros(50, dtype=np.int8)  # Wrong length

        cfg = StrategyConfig(strategy_type="EXTERNAL")
        with pytest.raises(ValueError, match="length|match"):
            run_backtest_with_signals(bars, signals, cfg)

    def test_external_signals_invalid_values(self) -> None:
        """Invalid signal values should raise error."""
        bars = make_bars(rows=100)
        signals = np.zeros(100, dtype=np.int8)
        signals[10] = 5  # Invalid value

        cfg = StrategyConfig(strategy_type="EXTERNAL")
        with pytest.raises(ValueError, match="invalid|must be -1, 0, or 1"):
            run_backtest_with_signals(bars, signals, cfg)


# =============================================================================
# ADVANCED ORDER TYPES TESTS
# =============================================================================

class TestAdvancedOrderTypes:
    """Test advanced order types (trailing stop, break-even, etc.)."""

    def test_trailing_stop_config(self) -> None:
        """Trailing stop should execute without errors."""
        bars = make_bars(rows=200)
        trailing_stop = TrailingStopConfig(
            enabled=True,
            trail_pct=0.02,
            activation_pct=0.01,
        )
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            trailing_stop=trailing_stop,
        )
        result = run_backtest(bars, cfg)
        assert result is not None

    def test_break_even_config(self) -> None:
        """Break-even stop should execute without errors."""
        bars = make_bars(rows=200)
        break_even = BreakEvenConfig(
            enabled=True,
            trigger_pct=0.01,
            offset_pct=0.001,
        )
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            break_even=break_even,
        )
        result = run_backtest(bars, cfg)
        assert result is not None

    def test_time_stop_config(self) -> None:
        """Time-based stop should execute without errors."""
        bars = make_bars(rows=200)
        time_stop = TimeStopConfig(
            enabled=True,
            max_bars=20,
        )
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            time_stop=time_stop,
        )
        result = run_backtest(bars, cfg)
        assert result is not None

    def test_partial_exit_config(self) -> None:
        """Partial exit should execute without errors."""
        bars = make_bars(rows=200)
        partial_exit = PartialExitConfig(
            enabled=True,
            exit_pct=0.5,
            trigger_pct=0.02,
        )
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            partial_exit=partial_exit,
        )
        result = run_backtest(bars, cfg)
        assert result is not None

    def test_pyramid_config(self) -> None:
        """Pyramiding should execute without errors."""
        bars = make_bars(rows=200)
        pyramid = PyramidConfig(
            enabled=True,
            max_entries=3,
            entry_spacing_pct=0.01,
            size_multiplier=0.5,
        )
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            pyramid=pyramid,
        )
        result = run_backtest(bars, cfg)
        assert result is not None


# =============================================================================
# RESULT CONSISTENCY TESTS
# =============================================================================

class TestResultConsistency:
    """Test that results are consistent and make sense."""

    def test_wins_plus_losses_equals_trades(self) -> None:
        """wins + losses should equal trades."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15)
        result = run_backtest(bars, cfg)
        assert result.wins + result.losses == result.trades

    def test_win_pct_range(self) -> None:
        """Win percentage should be between 0 and 1."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15)
        result = run_backtest(bars, cfg)
        assert 0.0 <= result.win_pct <= 1.0

    def test_max_drawdown_range(self) -> None:
        """Max drawdown should be between 0 and 1."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15)
        result = run_backtest(bars, cfg)
        assert 0.0 <= result.max_drawdown <= 1.0

    def test_final_equity_positive(self) -> None:
        """Final equity should be positive."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15)
        result = run_backtest(bars, cfg)
        assert result.final_equity > 0

    def test_trade_recording(self) -> None:
        """Trade recording should produce valid trade records."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            record_trades=True,
        )
        result = run_backtest(bars, cfg)
        assert len(result.trade_ledger) == result.trades
        for trade in result.trade_ledger:
            assert trade.qty > 0
            assert trade.entry_price > 0
            assert trade.exit_price > 0

    def test_equity_curve_recording(self) -> None:
        """Equity curve recording should produce valid data points."""
        bars = make_bars(rows=300)
        cfg = StrategyConfig(
            strategy_type="MA_CROSS",
            fast_window=5,
            slow_window=15,
            record_equity_curve=True,
        )
        result = run_backtest(bars, cfg)
        assert len(result.equity_curve) > 0
        for point in result.equity_curve:
            assert point.equity > 0
            assert 0.0 <= point.drawdown <= 1.0


# =============================================================================
# GRID SEARCH TESTS
# =============================================================================

class TestGridSearch:
    """Test grid search functionality."""

    def test_grid_search_empty_configs(self) -> None:
        """Grid search with empty configs should return empty list."""
        bars = make_bars()
        results = grid_search(bars, [], metric="total_return", top_n=5)
        assert results == []

    def test_grid_search_top_n_larger_than_configs(self) -> None:
        """Grid search with top_n > len(configs) should return all results."""
        bars = make_bars()
        configs = [
            StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15),
            StrategyConfig(strategy_type="MA_CROSS", fast_window=7, slow_window=20),
        ]
        results = grid_search(bars, configs, metric="total_return", top_n=10)
        assert len(results) == 2

    def test_grid_search_different_metrics(self) -> None:
        """Grid search should work with different optimization metrics."""
        bars = make_bars()
        configs = [
            StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=15),
            StrategyConfig(strategy_type="MA_CROSS", fast_window=7, slow_window=20),
            StrategyConfig(strategy_type="MA_CROSS", fast_window=10, slow_window=30),
        ]

        for metric in ["total_return", "sharpe", "sortino", "calmar", "win_pct"]:
            results = grid_search(bars, configs, metric=metric, top_n=2)
            assert len(results) == 2
