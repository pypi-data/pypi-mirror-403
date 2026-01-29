# Qrucible

Hybrid, stateful backtester with a Rust hot path and a clean Python API. Qrucible executes path-dependent logic (position sizing that reacts to wins/losses, stops, and exits) at vectorized speeds by keeping the critical loop in Rust and fanning out parameter grids with `rayon`.

**430x faster** than equivalent Python code. See [Benchmarks](benchmarks.md) for methodology and results.

## Key Features

- **Install in seconds**: `pip install qrucible` (prebuilt wheels for Linux/macOS/Windows)
- **Fast**: 430x speedup over Python, 1,000+ configs/second grid search throughput
- **Stateful**: Risk sizing, stop-loss/take-profit, reduce-after-loss, margin tracking
- **Realistic**: Transaction costs (commission, slippage, spread) for trustworthy results
- **Extensible**: External signal mode for user-defined strategies with Rust-speed execution
- **Diagnostic**: Optional trade ledger and equity curve output for analysis
- **Flexible inputs**: CSV and Parquet (ts, asset_id, OHLCV), multi-asset support

## Quickstart

```bash
pip install qrucible
python - <<'PY'
import numpy as np
from qrucible import StrategyConfig, run_backtest

rows = 50_000
ohlcv = np.random.lognormal(mean=0.0, sigma=0.02, size=(rows, 5)).astype(np.float64)
ohlcv[:, 2] = np.minimum(ohlcv[:, 0], ohlcv[:, 3])
ohlcv[:, 1] = np.maximum(ohlcv[:, 0], ohlcv[:, 3])
timestamps = (np.arange(rows, dtype=np.int64) * 1_000_000).astype(np.float64)
asset_ids = np.zeros(rows, dtype=np.float64)
bars = np.column_stack([timestamps, asset_ids, ohlcv]).astype(np.float64)

cfg = StrategyConfig(
    fast_window=10,
    slow_window=30,
    stop_loss=0.02,
    take_profit=0.04,
    risk_per_trade=0.01,
)

result = run_backtest(bars, cfg)
print(result)
PY
```

Next steps:

- See [Install](install.md) for local builds and `maturin` usage.
- See [Data](data.md) for bar schema and loaders.
- See [Strategy Config](config.md) for parameters and recipes.
- See [Benchmarks](benchmarks.md) for methodology and reporting.
