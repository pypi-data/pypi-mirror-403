import math
import platform
import time
from dataclasses import asdict, dataclass
from typing import List

from importlib import metadata
import os

try:
    import numpy as np
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: numpy\n"
        "Install it in your venv, then rerun:\n"
        "  python -m pip install -U numpy\n"
    ) from e

try:
    from qrucible import StrategyConfig, grid_search, run_backtest
except ModuleNotFoundError:  # pragma: no cover
    StrategyConfig = None  # type: ignore[assignment]
    grid_search = None  # type: ignore[assignment]
    run_backtest = None  # type: ignore[assignment]


@dataclass
class PyResult:
    total_return: float
    sharpe: float
    trades: int
    wins: int
    losses: int
    final_equity: float


def make_synthetic_intraday(
    minutes: int,
    assets: int = 1,
    seed: int = 42,
    start_ts_us: int = 1_700_000_000_000_000,
) -> np.ndarray:
    """
    Generate synthetic intraday bars (equity-like microstructure, not a market model).

    Schema: [ts_epoch_us, asset_id, open, high, low, close, volume]

    Notes:
    - This is designed for repeatable performance benchmarking.
    - For Python-vs-Rust parity comparisons, keep assets=1 (the Python reference loop is single-asset).
    """
    rng = np.random.default_rng(seed)

    # Equity-like minute returns: small drift, small noise.
    drift = 0.00002
    vol = 0.0015

    total = minutes * assets
    ts = np.repeat(
        (start_ts_us + (np.arange(minutes, dtype=np.int64) * 60_000_000)).astype(np.float64),
        assets,
    )
    asset_id = np.tile(np.arange(assets, dtype=np.int64), minutes).astype(np.float64)

    # Start each asset around $100 with small dispersion.
    start_prices = 100.0 * rng.lognormal(mean=0.0, sigma=0.05, size=assets)
    log_rets = rng.normal(loc=drift, scale=vol, size=total)
    # Build per-asset price paths in a single vector.
    closes = np.empty(total, dtype=np.float64)
    for a in range(assets):
        idx = slice(a, total, assets)
        prices = start_prices[a] * np.exp(np.cumsum(log_rets[idx]))
        closes[idx] = prices
    opens = np.empty_like(closes)
    opens[:assets] = closes[:assets]
    opens[assets:] = closes[:-assets]

    # Approximate OHLC around open/close.
    intrabar_spread = rng.uniform(0.0, 0.0025, size=total)
    highs = np.maximum(opens, closes) * (1 + intrabar_spread)
    lows = np.minimum(opens, closes) * (1 - intrabar_spread)
    volume = rng.lognormal(mean=12.0, sigma=0.5, size=total)

    return np.column_stack([ts, asset_id, opens, highs, lows, closes, volume]).astype(np.float64)


def compute_sharpe(returns: List[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = float(np.mean(returns))
    std = float(np.std(returns, ddof=1))
    if std <= 0.0:
        return 0.0
    return mean / std * math.sqrt(252.0)


def python_backtest(bars: np.ndarray, cfg: StrategyConfig) -> PyResult:
    """Reference implementation of the Rust loop in pure Python."""
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
                if cfg.stop_loss > 0.0:
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
                if cfg.stop_loss > 0.0:
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
    sharpe = compute_sharpe(step_returns)
    return PyResult(
        total_return=total_return,
        sharpe=sharpe,
        trades=trades,
        wins=wins,
        losses=losses,
        final_equity=prev_equity,
    )


def main() -> None:
    if StrategyConfig is None or grid_search is None or run_backtest is None:
        raise SystemExit(
            "Missing dependency: qrucible\n"
            "Build/install the extension, then rerun:\n"
            "  maturin develop --release\n"
            "or:\n"
            "  pip install qrucible\n"
        )
    minutes = int(os.environ.get("QRUCIBLE_BENCH_MINUTES", "200000"))
    assets = int(os.environ.get("QRUCIBLE_BENCH_ASSETS", "1"))
    bars = make_synthetic_intraday(minutes=minutes, assets=assets, seed=42)
    base_cfg = StrategyConfig(
        strategy_type="RSI",
        rsi_period=14,
        rsi_upper=70.0,
        rsi_lower=30.0,
        stop_loss=0.01,
        take_profit=0.03,
        risk_per_trade=0.01,
        initial_cash=1_000_000.0,
        reduce_after_loss=True,
        loss_size_factor=0.5,
    )

    # Sanity check: Python loop vs Rust loop parity on a single config
    if assets == 1:
        python_result = python_backtest(bars, base_cfg)
        rust_result = run_backtest(bars, base_cfg)
        print("Parity check (Python vs Rust):")
        print(f"  Python: {asdict(python_result)}")
        print(
            "  Rust  : "
            f"{{'total_return': {rust_result.total_return:.6f}, 'sharpe': {rust_result.sharpe:.6f}, "
            f"'trades': {rust_result.trades}, 'wins': {rust_result.wins}, 'losses': {rust_result.losses}, "
            f"'final_equity': {rust_result.final_equity:.2f}}}"
        )
    else:
        rust_result = run_backtest(bars, base_cfg)
        print("Parity check: skipped (assets > 1; Python reference loop is single-asset)")
        print(
            "  Rust  : "
            f"{{'total_return': {rust_result.total_return:.6f}, 'sharpe': {rust_result.sharpe:.6f}, "
            f"'trades': {rust_result.trades}, 'wins': {rust_result.wins}, 'losses': {rust_result.losses}, "
            f"'final_equity': {rust_result.final_equity:.2f}}}"
        )

    def bar(label: str, value: float, max_value: float, width: int = 32) -> None:
        scale = 0 if max_value <= 0 else min(value / max_value, 1.0)
        filled = int(round(scale * width))
        bar_str = "#" * filled + "-" * (width - filled)
        print(f"  {label:<12} [{bar_str}] {value:.2f}s")

    # Build a modest RSI grid to make the gap obvious without taking forever
    rsi_periods = range(10, 31)

    grid = [
        StrategyConfig(
            strategy_type="RSI",
            rsi_period=period,
            rsi_upper=70.0,
            rsi_lower=30.0,
            stop_loss=0.01,
            take_profit=0.03,
            risk_per_trade=0.01,
            initial_cash=1_000_000.0,
            reduce_after_loss=True,
            loss_size_factor=0.5,
        )
        for period in rsi_periods
    ]

    start = time.perf_counter()
    if assets == 1:
        python_results = [python_backtest(bars, cfg) for cfg in grid]
        python_time = time.perf_counter() - start
    else:
        python_results = []
        python_time = 0.0

    start = time.perf_counter()
    rust_results = grid_search(bars, grid, metric="sharpe", top_n=len(grid))
    rust_time = time.perf_counter() - start

    best_rust = rust_results[0]
    best_python = max(python_results, key=lambda r: r.sharpe) if python_results else None

    print("\nGrid search timing:")
    if assets == 1:
        print(f"  Python loop: {python_time:.2f}s for {len(grid)} configs")
    print(f"  Rust loop  : {rust_time:.4f}s for {len(grid)} configs")
    if assets == 1 and rust_time > 0:
        print(f"  Speedup    : {python_time / rust_time:,.1f}x")

    print("\nSpeed visual:")
    max_time = max(python_time, rust_time) if assets == 1 else rust_time
    if assets == 1:
        bar("Python", python_time, max_time)
    bar("Rust", rust_time, max_time)

    print("\nTop Sharpe (Rust):", best_rust)
    if best_python is not None:
        print("Top Sharpe (Python):", asdict(best_python))

    print_markdown_summary(len(grid), python_time, rust_time, minutes=minutes, assets=assets)
    print_environment()


def throughput(count: int, seconds: float) -> float:
    return 0.0 if seconds <= 0 else count / seconds


def print_markdown_summary(
    configs: int,
    python_time: float,
    rust_time: float,
    minutes: int,
    assets: int,
) -> None:
    py_throughput = throughput(configs, python_time) if python_time > 0 else 0.0
    rust_throughput = throughput(configs, rust_time)
    speedup = (python_time / rust_time) if (python_time > 0 and rust_time > 0) else 0.0
    print("\n## Benchmark (copy/paste)")
    print(f"- Dataset: synthetic intraday (minutes={minutes}, assets={assets}, rows={minutes * assets:,})")
    print("| Impl | Configs | Time (s) | Throughput (cfg/s) | Speedup vs Python |")
    print("| --- | --- | --- | --- | --- |")
    if python_time > 0:
        print(f"| Python loop | {configs} | {python_time:.3f} | {py_throughput:,.1f} | 1.0x |")
        print(f"| Rust loop | {configs} | {rust_time:.3f} | {rust_throughput:,.1f} | {speedup:,.1f}x |")
    else:
        print(f"| Rust loop | {configs} | {rust_time:.3f} | {rust_throughput:,.1f} | n/a |")


def print_environment() -> None:
    cpu = platform.processor() or platform.machine()
    try:
        qrucible_version = metadata.version("qrucible")
    except metadata.PackageNotFoundError:
        qrucible_version = "editable (not installed from wheel)"

    print("\n### Environment")
    print(f"- OS: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"- Python: {platform.python_version()}")
    print(f"- NumPy: {np.__version__}")
    print(f"- Qrucible: {qrucible_version}")
    print(f"- CPU: {cpu}")


if __name__ == "__main__":
    main()
