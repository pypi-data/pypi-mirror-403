#!/usr/bin/env python
"""
Real-world demo using Apple OHLCV data.

Downloads a sample dataset from https://github.com/plotly/datasets
(`finance-charts-apple.csv`, MIT licensed), converts it to Qrucible's schema,
and runs a simple moving-average crossover backtest.
"""

from __future__ import annotations

import csv
import datetime as dt
import pathlib
import urllib.request
from typing import Tuple

import numpy as np

from qrucible import StrategyConfig, run_backtest

DATA_URL = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
DATA_PATH = pathlib.Path("data/finance-charts-apple.csv")


def download_dataset(path: pathlib.Path = DATA_PATH) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    print(f"Downloading sample data to {path} ...")
    urllib.request.urlretrieve(DATA_URL, path)
    return path


def load_ohlcv(path: pathlib.Path) -> Tuple[np.ndarray, np.ndarray]:
    timestamps = []
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row["Date"]
            dt_obj = dt.datetime.fromisoformat(date_str)
            ts_us = int(dt_obj.timestamp() * 1_000_000)
            timestamps.append(ts_us)
            rows.append(
                [
                    float(row["AAPL.Open"]),
                    float(row["AAPL.High"]),
                    float(row["AAPL.Low"]),
                    float(row["AAPL.Close"]),
                    float(row["AAPL.Volume"]),
                ]
            )
    ohlcv = np.array(rows, dtype=np.float64)
    ts = np.array(timestamps, dtype=np.float64)
    return ts, ohlcv


def to_bars(ts: np.ndarray, ohlcv: np.ndarray) -> np.ndarray:
    asset_ids = np.zeros(len(ts), dtype=np.float64)
    return np.column_stack([ts, asset_ids, ohlcv]).astype(np.float64)


def main() -> None:
    csv_path = download_dataset()
    ts, ohlcv = load_ohlcv(csv_path)
    bars = to_bars(ts, ohlcv)

    cfg = StrategyConfig(
        strategy_type="MA_CROSS",
        fast_window=10,
        slow_window=30,
        stop_loss=0.02,
        take_profit=0.04,
        risk_per_trade=0.01,
        initial_cash=1_000_000.0,
    )

    result = run_backtest(bars, cfg)
    print("Data points:", len(bars))
    print("Result:", result)
    print("As dict:", result.as_dict())


if __name__ == "__main__":
    main()
