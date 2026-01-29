# Strategy config

`StrategyConfig` controls the trading logic and sizing rules passed to `run_backtest` or `grid_search`.

## Strategy types

- `MA_CROSS` (alias: `MA`, `MACROSS`): fast vs slow moving average crossover.
- `RSI`: RSI with upper/lower bands.
- `BOLLINGER` (alias: `BOLL`, `BBANDS`): Bollinger Bands breakout/mean reversion.
- `EXTERNAL` (alias: `SIGNALS`): User-provided signals via `run_backtest_with_signals()`.

## Fields (with defaults)

| Field | Default | Notes |
| --- | --- | --- |
| `strategy_type` | `"MA_CROSS"` | One of the strategy types above. |
| `fast_window` | `10` | For MA cross; must be > 0. |
| `slow_window` | `30` | For MA cross; must be > 0. |
| `rsi_period` | `14` | For RSI; must be >= 2. |
| `rsi_upper` | `70.0` | For RSI; must be in [0, 100] and > `rsi_lower`. |
| `rsi_lower` | `30.0` | For RSI; must be in [0, 100] and < `rsi_upper`. |
| `bollinger_period` | `20` | For Bollinger; must be >= 2. |
| `bollinger_std` | `2.0` | Std-dev multiplier for Bollinger. |
| `stop_loss` | `0.02` | Fractional stop. Must be > 0 for sizing to work. |
| `take_profit` | `0.04` | Fractional take-profit; can be 0 to disable. |
| `risk_per_trade` | `0.01` | Fraction of equity risked per position (0, 1]. |
| `initial_cash` | `1_000_000.0` | Starting equity. |
| `reduce_after_loss` | `True` | If true, shrink next trade after a loss by `loss_size_factor`. |
| `loss_size_factor` | `0.5` | Multiplier for next trade after a loss (0 to 1]. |
| `margin_factor` | `1.0` | Short margin requirement (0, 1]. |
| `periods_per_year` | `252.0` | Used for annualizing Sharpe/Sortino. |
| `commission` | `0.0` | Fixed commission per trade (entry + exit). |
| `slippage_bps` | `0.0` | Slippage in basis points (1 bp = 0.01%). |
| `spread_bps` | `0.0` | Bid-ask spread in basis points. |
| `record_trades` | `False` | Enable trade ledger output. |
| `record_equity_curve` | `False` | Enable equity curve output. |

## Recipes

### Fast MA crossover
```python
cfg = StrategyConfig(strategy_type="MA_CROSS", fast_window=5, slow_window=20, stop_loss=0.01, take_profit=0.02)
```

### RSI mean reversion
```python
cfg = StrategyConfig(strategy_type="RSI", rsi_period=14, rsi_lower=35.0, rsi_upper=65.0, stop_loss=0.01)
```

### Bollinger breakout with tighter bands
```python
cfg = StrategyConfig(strategy_type="BOLLINGER", bollinger_period=20, bollinger_std=1.0, stop_loss=0.01, take_profit=0.03)
```

### Grid search example
```python
grid = [
    StrategyConfig(strategy_type="RSI", rsi_period=period, rsi_lower=30.0, rsi_upper=70.0, stop_loss=0.01)
    for period in range(10, 31)
]
results = grid_search(bars, grid, metric="sharpe", top_n=5)
```

### Realistic backtest with costs
```python
cfg = StrategyConfig(
    strategy_type="RSI",
    rsi_period=14,
    stop_loss=0.02,
    commission=10.0,      # $10 per trade
    slippage_bps=5.0,     # 5 basis points slippage
    spread_bps=10.0,      # 10 basis points spread
)
result = run_backtest(bars, cfg)
print(f"Total commission: ${result.total_commission:.2f}")
print(f"Total execution cost (slippage+spread): ${result.total_execution_cost:.2f}")
```

### Trade ledger and equity curve
```python
cfg = StrategyConfig(
    strategy_type="MA_CROSS",
    fast_window=10,
    slow_window=30,
    commission=5.0,
    record_trades=True,
    record_equity_curve=True,
)
result = run_backtest(bars, cfg)

# Access individual trades
for trade in result.trade_ledger:
    print(f"{trade.side} {trade.qty:.2f} @ {trade.entry_price:.2f} -> {trade.exit_price:.2f}")
    print(f"  gross_pnl: {trade.gross_pnl:.2f}, net_pnl: {trade.net_pnl:.2f}")
    print(f"  commission: {trade.commission_paid:.2f}, execution_cost: {trade.execution_cost:.2f}")

# Access equity curve
for point in result.equity_curve[-5:]:  # Last 5 points
    print(f"ts={point.ts}, equity={point.equity:.2f}, drawdown={point.drawdown:.4f}")
```

**Trade fields:**
- `gross_pnl`: PnL before costs (consistent with `result.realized_pnl`)
- `net_pnl`: PnL after commission and execution costs
- `commission_paid`: Commission for this trade (entry + exit)
- `execution_cost`: Slippage + spread cost combined

## Cost accounting convention

Qrucible uses a **gross PnL** convention for portfolio-level metrics:

| Field | Convention | Notes |
| --- | --- | --- |
| `realized_pnl` | Gross | Sum of trade P&L before costs |
| `expectancy` | Gross | `realized_pnl / trades` |
| `avg_win` / `avg_loss` | Gross | Average winning/losing trade P&L |
| `final_equity` | Net | Reflects actual cash after all costs |
| `total_return` | Net | Based on `final_equity / initial_cash` |
| `Trade.gross_pnl` | Gross | Individual trade P&L before costs |
| `Trade.net_pnl` | Net | Individual trade P&L after costs |

This means `realized_pnl` will be higher than actual profits when costs are enabled.
To compute net realized P&L: `realized_pnl - total_commission - total_execution_cost`

### External signals mode
```python
import numpy as np
from qrucible import StrategyConfig, run_backtest_with_signals

# Generate your own signals: 1=long, -1=short, 0=hold
# Note: 0 means "hold current position" (no new entry)
# Positions exit via stop-loss, take-profit, or opposite signal
signals = np.zeros(len(bars), dtype=np.int8)
signals[my_long_mask] = 1
signals[my_short_mask] = -1

# Qrucible handles sizing, stops, TP, and metrics
cfg = StrategyConfig(
    strategy_type="EXTERNAL",  # Used with run_backtest_with_signals
    stop_loss=0.02,
    take_profit=0.04,
    risk_per_trade=0.01,
)
result = run_backtest_with_signals(bars, signals, cfg)
```
