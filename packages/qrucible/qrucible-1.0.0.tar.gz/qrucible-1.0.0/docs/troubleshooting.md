# Troubleshooting Guide

This guide covers common issues and their solutions when using Qrucible.

## Installation Issues

### `pip install qrucible` fails

**Problem:** Installation fails with compilation errors.

**Solution:** Qrucible provides prebuilt wheels for most platforms. If you're seeing compilation errors:

1. Make sure you have a recent pip version:
   ```bash
   pip install --upgrade pip
   ```

2. Try specifying the wheel directly:
   ```bash
   pip install qrucible --prefer-binary
   ```

3. If building from source, ensure you have the Rust toolchain installed:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

### Module not found: `qrucible`

**Problem:** After installation, `import qrucible` fails.

**Solution:**

1. Verify the installation:
   ```bash
   pip show qrucible
   ```

2. Ensure you're using the same Python environment:
   ```bash
   which python
   pip list | grep qrucible
   ```

3. If using virtual environments, make sure it's activated:
   ```bash
   source .venv/bin/activate
   ```

---

## Data Loading Issues

### "ndarray must have 7 columns"

**Problem:** Loading data fails with column count error.

**Solution:** Qrucible expects data in this format:

```
[ts_epoch_us, asset_id, open, high, low, close, volume]
```

Ensure your data has exactly 7 columns in this order. Example:

```python
import numpy as np

# Correct format
bars = np.column_stack([
    timestamps,    # column 0: microsecond timestamps
    asset_ids,     # column 1: asset identifier (0 for single asset)
    opens,         # column 2: open prices
    highs,         # column 3: high prices
    lows,          # column 4: low prices
    closes,        # column 5: close prices
    volumes,       # column 6: volume
]).astype(np.float64)
```

### "high must be >= low" or similar OHLC errors

**Problem:** Data validation fails due to inconsistent OHLC data.

**Solution:** Qrucible validates that your bar data is internally consistent:

- `high` must be >= `open`, `low`, and `close`
- `low` must be <= `open`, `low`, and `close`
- All prices must be positive (> 0)
- Volume must be non-negative (>= 0)

Check your data for:

```python
# Find problematic rows
mask = bars[:, 3] < bars[:, 4]  # high < low
problem_rows = np.where(mask)[0]
print(f"Rows with high < low: {problem_rows}")
```

### "timestamp is before previous timestamp"

**Problem:** Data is not sorted chronologically.

**Solution:** Sort your data by timestamp before passing to Qrucible:

```python
# Sort by timestamp (column 0)
sorted_indices = np.argsort(bars[:, 0])
bars = bars[sorted_indices]
```

### "price must be positive"

**Problem:** Zero or negative prices in data.

**Solution:** Filter out invalid bars:

```python
# Remove rows with zero or negative prices
valid_mask = (bars[:, 2] > 0) & (bars[:, 3] > 0) & (bars[:, 4] > 0) & (bars[:, 5] > 0)
bars = bars[valid_mask]
```

---

## Configuration Errors

### "strategy_type must be one of: ..."

**Problem:** Invalid strategy type specified.

**Solution:** Use one of these supported strategy types:

- `MA_CROSS` - Moving Average Crossover
- `RSI` - Relative Strength Index
- `BOLLINGER` - Bollinger Bands
- `MACD` - Moving Average Convergence Divergence
- `STOCHASTIC` - Stochastic Oscillator
- `ADX` - Average Directional Index
- `ATR` - Average True Range
- `CCI` - Commodity Channel Index
- `OBV` - On-Balance Volume
- `VWAP` - Volume Weighted Average Price
- `KELTNER` - Keltner Channels
- `DONCHIAN` - Donchian Channels
- `ICHIMOKU` - Ichimoku Cloud
- `SUPERTREND` - SuperTrend Indicator
- `WILLIAMS` - Williams %R
- `AROON` - Aroon Indicator
- `MFI` - Money Flow Index
- `ROC` - Rate of Change
- `TSI` - True Strength Index
- `ULTIMATE` - Ultimate Oscillator
- `EXTERNAL` - External Signals (use with `run_backtest_with_signals`)

### "stop_loss must be > 0"

**Problem:** Invalid stop loss value.

**Solution:** Stop loss must be a positive fraction:

```python
# Correct: 2% stop loss
config = StrategyConfig(strategy_type="MA_CROSS", stop_loss=0.02)

# Incorrect
config = StrategyConfig(strategy_type="MA_CROSS", stop_loss=0)  # Error!
config = StrategyConfig(strategy_type="MA_CROSS", stop_loss=-0.02)  # Error!
```

### "risk_per_trade must be in (0, 1]"

**Problem:** Invalid risk per trade value.

**Solution:** Risk per trade should be between 0 and 1 (exclusive/inclusive):

```python
# Correct: Risk 1% of equity per trade
config = StrategyConfig(strategy_type="MA_CROSS", risk_per_trade=0.01)

# Incorrect
config = StrategyConfig(strategy_type="MA_CROSS", risk_per_trade=1.5)  # > 100%!
config = StrategyConfig(strategy_type="MA_CROSS", risk_per_trade=0)    # No risk!
```

---

## Backtest Errors

### "insufficient data: ... requires at least N bars"

**Problem:** Not enough data for indicator warm-up period.

**Solution:** Each strategy requires a minimum amount of data:

| Strategy | Minimum Bars Needed |
|----------|---------------------|
| MA_CROSS | slow_window + 1 |
| RSI | rsi_period + 1 |
| BOLLINGER | bollinger_period + 1 |
| MACD | macd_slow + macd_signal |
| ICHIMOKU | ichimoku_senkou_b + 1 |

Options:
1. Use more historical data
2. Reduce indicator periods

```python
# If you only have 50 bars, use smaller periods
config = StrategyConfig(
    strategy_type="MA_CROSS",
    fast_window=5,   # Instead of default 10
    slow_window=15,  # Instead of default 30
)
```

### "EXTERNAL requires run_backtest_with_signals()"

**Problem:** Using `run_backtest()` with strategy_type="EXTERNAL".

**Solution:** External signals require the `run_backtest_with_signals()` function:

```python
import numpy as np
from qrucible import StrategyConfig, run_backtest_with_signals

signals = np.zeros(len(bars), dtype=np.int8)
signals[10] = 1   # Go long at bar 10
signals[50] = -1  # Go short at bar 50

config = StrategyConfig(strategy_type="EXTERNAL")
result = run_backtest_with_signals(bars, signals, config)
```

### "signals length must match data rows"

**Problem:** Signal array length doesn't match data length.

**Solution:** Ensure signals array has exactly the same number of elements as data rows:

```python
signals = np.zeros(len(bars), dtype=np.int8)  # Same length as bars
```

### "signals[i] is invalid; must be -1, 0, or 1"

**Problem:** Invalid signal values.

**Solution:** Signals must be -1 (short), 0 (hold), or 1 (long):

```python
signals = np.zeros(len(bars), dtype=np.int8)
signals[signals > 0.5] = 1    # Long
signals[signals < -0.5] = -1  # Short
# Everything else stays 0    # Hold
```

---

## Performance Issues

### Backtest is slow

**Problem:** Backtest takes longer than expected.

**Solutions:**

1. **Use grid_search for multiple configs:** Grid search uses parallel processing:
   ```python
   # Faster than running individually
   results = grid_search(bars, configs, metric="sharpe", top_n=10)
   ```

2. **Reduce recording overhead:**
   ```python
   config = StrategyConfig(
       strategy_type="MA_CROSS",
       record_trades=False,       # Disable trade logging
       record_equity_curve=False, # Disable equity curve
   )
   ```

3. **Use appropriate data types:**
   ```python
   # Ensure data is float64
   bars = bars.astype(np.float64)
   ```

### Memory issues with large datasets

**Problem:** Out of memory errors with large datasets.

**Solutions:**

1. **Process in chunks:**
   ```python
   chunk_size = 100_000
   for i in range(0, len(bars), chunk_size):
       chunk = bars[i:i+chunk_size]
       result = run_backtest(chunk, config)
   ```

2. **Use Parquet files:** Qrucible streams Parquet files efficiently:
   ```python
   bars = load_bars("large_dataset.parquet")
   ```

---

## Common Pitfalls

### No trades executed

**Problem:** Backtest completes but shows 0 trades.

**Possible causes:**

1. **Indicator warm-up:** Early bars don't generate signals. Check if you have enough data.

2. **Signal thresholds:** RSI/Stochastic might never hit overbought/oversold levels:
   ```python
   # More sensitive thresholds
   config = StrategyConfig(
       strategy_type="RSI",
       rsi_upper=60.0,  # Instead of 70
       rsi_lower=40.0,  # Instead of 30
   )
   ```

3. **Risk sizing:** Position size might round to zero if risk budget is too small:
   ```python
   config = StrategyConfig(
       strategy_type="MA_CROSS",
       risk_per_trade=0.02,   # Increase from 0.01
       initial_cash=100000.0, # Increase capital
   )
   ```

### Unexpected results

**Problem:** Results don't match expectations.

**Debugging steps:**

1. **Enable trade recording:**
   ```python
   config = StrategyConfig(
       strategy_type="MA_CROSS",
       record_trades=True,
   )
   result = run_backtest(bars, config)
   
   # Inspect individual trades
   for trade in result.trade_ledger[:10]:
       print(f"{trade.side}: {trade.entry_price} -> {trade.exit_price}, reason: {trade.exit_reason}")
   ```

2. **Check exit statistics:**
   ```python
   print(f"Stop Loss Exits: {result.stop_loss_exits}")
   print(f"Take Profit Exits: {result.take_profit_exits}")
   print(f"Signal Exits: {result.signal_exits}")
   ```

3. **Verify data integrity:**
   ```python
   print(f"Data rows: {len(bars)}")
   print(f"Price range: {bars[:, 5].min():.2f} - {bars[:, 5].max():.2f}")
   print(f"Date range: {bars[0, 0]} - {bars[-1, 0]}")
   ```

---

## Getting Help

If you can't resolve your issue:

1. **Check the documentation:** https://charlesfreidenreich.github.io/Qrucible/

2. **Search existing issues:** https://github.com/charlesfreidenreich/Qrucible/issues

3. **Open a new issue** with:
   - Qrucible version (`pip show qrucible`)
   - Python version (`python --version`)
   - Operating system
   - Minimal code to reproduce the issue
   - Full error message/traceback

4. **Community support:**
   - GitHub Discussions
   - Stack Overflow (tag: `qrucible`)
