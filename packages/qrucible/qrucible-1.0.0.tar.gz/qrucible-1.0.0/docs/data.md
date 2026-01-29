# Data format

Qrucible works with wide OHLCV arrays or pre-parsed `BarData`.

## Schema

Expected column order (float64):

1. `ts_epoch_us` (int-like, microseconds since epoch)
2. `asset_id` (int-like)
3. `open`
4. `high`
5. `low`
6. `close`
7. `volume`

All numeric values must be finite. `asset_id` must be non-negative integers. `ts_epoch_us` must be integer-valued microseconds.

## Loading data

### From NumPy (fastest for synthetic data)

Pass a `numpy.ndarray` shaped `(rows, 7)`:
```python
from qrucible import run_backtest, StrategyConfig
result = run_backtest(bars, StrategyConfig(...))
```

### From CSV

```python
from qrucible import load_bars_csv
bars = load_bars_csv("data/bars.csv", has_header=True)
```

CSV parser expects numeric fields only; set `has_header=True` if a header row exists (auto-detected otherwise).

### From Parquet

```python
from qrucible import load_bars_parquet
bars = load_bars_parquet("data/bars.parquet")
```

Required columns (case-insensitive): `ts_epoch_us`, `asset_id`, `open`, `high`, `low`, `close`, `volume`. Wheels include codecs for brotli, gzip, lz4, snappy, and zstd.

### Mixed / multi-asset

Multi-asset data is supported; `asset_id` groups rows by asset. You can pass either raw arrays or `BarData` from loaders to `run_backtest` or `grid_search`.

## Real-data demo

Run `python scripts/demo_real_data.py` to download a public Apple OHLCV sample and execute a moving-average crossover backtest.
