"""
Qrucible Easy - Beginner-Friendly Backtesting

This module makes Qrucible dead-simple to use. No configuration needed!

Quick Start:
    >>> import qrucible_easy as ez
    >>> 
    >>> # Use built-in sample data
    >>> result = ez.backtest()
    >>> print(result)
    >>>
    >>> # Or use your own data (pandas DataFrame or CSV file)
    >>> result = ez.backtest("my_data.csv")
    >>> result = ez.backtest(my_dataframe)

That's it! No configuration required.
"""

from __future__ import annotations

__all__ = [
    # Main functions
    "backtest",
    "backtest_ma",
    "backtest_rsi",
    "backtest_macd",
    "backtest_bollinger",
    "compare_strategies",
    # Helpers
    "get_sample_data",
    "list_strategies",
    "demo",
    # Classes
    "EasyResult",
]

import datetime
import urllib.request
import pathlib
import csv
from typing import Union, Optional, List, Any
from dataclasses import dataclass

import numpy as np

# Import the core Qrucible module
try:
    import qrucible as _qrucible
except ImportError:
    raise ImportError(
        "Qrucible is not installed. Install it with:\n"
        "  pip install qrucible-backtest\n"
        "Or for development:\n"
        "  maturin develop --release"
    )

# Try to import pandas (optional but recommended)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


# =============================================================================
# SAMPLE DATA - Built-in data so beginners can start immediately
# =============================================================================

SAMPLE_DATA_URL = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
SAMPLE_DATA_PATH = pathlib.Path.home() / ".qrucible" / "sample_data" / "apple.csv"


def _download_sample_data() -> pathlib.Path:
    """Download sample Apple stock data."""
    if SAMPLE_DATA_PATH.exists():
        return SAMPLE_DATA_PATH
    
    SAMPLE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading sample stock data (Apple historical prices)...")
    urllib.request.urlretrieve(SAMPLE_DATA_URL, SAMPLE_DATA_PATH)
    print("Done! Data saved to", SAMPLE_DATA_PATH)
    return SAMPLE_DATA_PATH


def _load_sample_data() -> np.ndarray:
    """Load sample data as numpy array in Qrucible format."""
    path = _download_sample_data()
    return _load_csv_simple(path)


def _load_csv_simple(path: Union[str, pathlib.Path]) -> np.ndarray:
    """Load a CSV file and convert to Qrucible format.
    
    Automatically detects common column names like:
    - Date, date, timestamp, time, ts
    - Open, open, OPEN
    - High, high, HIGH  
    - Low, low, LOW
    - Close, close, CLOSE, Adj Close, adj_close
    - Volume, volume, VOLUME, vol
    """
    path = pathlib.Path(path)
    
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            raise ValueError(f"CSV file {path} appears to be empty")
        
        # Map common column names
        col_map = _detect_columns(headers)
        
        timestamps = []
        rows = []
        
        for row in reader:
            # Parse timestamp
            ts_str = row[col_map["date"]]
            try:
                # Try various date formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        dt_obj = datetime.datetime.strptime(ts_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Try ISO format as last resort
                    dt_obj = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                ts_us = int(dt_obj.timestamp() * 1_000_000)
            except Exception:
                raise ValueError(f"Could not parse date: '{ts_str}'. Expected format: YYYY-MM-DD")
            
            timestamps.append(ts_us)
            
            # Parse OHLCV
            try:
                o = float(row[col_map["open"]])
                h = float(row[col_map["high"]])
                l = float(row[col_map["low"]])
                c = float(row[col_map["close"]])
                v = float(row[col_map["volume"]]) if col_map["volume"] else 0.0
            except (ValueError, KeyError) as e:
                raise ValueError(f"Could not parse numeric values in CSV: {e}")
            
            rows.append([o, h, l, c, v])
    
    ohlcv = np.array(rows, dtype=np.float64)
    ts = np.array(timestamps, dtype=np.float64)
    asset_ids = np.zeros(len(ts), dtype=np.float64)
    
    return np.column_stack([ts, asset_ids, ohlcv]).astype(np.float64)


def _detect_columns(headers: List[str]) -> dict:
    """Auto-detect column names from common variations."""
    headers_lower = {h.lower().strip(): h for h in headers}
    
    def find_col(options: List[str], required: bool = True) -> Optional[str]:
        for opt in options:
            if opt in headers_lower:
                return headers_lower[opt]
        if required:
            raise ValueError(f"Could not find column. Expected one of: {options}. Found: {list(headers)}")
        return None
    
    return {
        "date": find_col(["date", "timestamp", "time", "ts", "datetime", "index"]),
        "open": find_col(["open", "aapl.open", "o", "first"]),
        "high": find_col(["high", "aapl.high", "h", "max"]),
        "low": find_col(["low", "aapl.low", "l", "min"]),
        "close": find_col(["close", "aapl.close", "c", "adj close", "adj_close", "adjusted_close", "last"]),
        "volume": find_col(["volume", "aapl.volume", "vol", "v", "qty"], required=False),
    }


def _dataframe_to_bars(df: "pd.DataFrame") -> np.ndarray:
    """Convert a pandas DataFrame to Qrucible bar format."""
    if not HAS_PANDAS:
        raise ImportError("pandas is required to use DataFrames. Install with: pip install pandas")
    
    # Detect columns
    cols_lower = {c.lower().strip(): c for c in df.columns}
    
    def find_col(options: List[str], required: bool = True) -> Optional[str]:
        for opt in options:
            if opt in cols_lower:
                return cols_lower[opt]
        if required:
            raise ValueError(f"DataFrame missing column. Expected one of: {options}. Found: {list(df.columns)}")
        return None
    
    date_col = find_col(["date", "timestamp", "time", "ts", "datetime"], required=False)
    open_col = find_col(["open", "o", "first"])
    high_col = find_col(["high", "h", "max"])
    low_col = find_col(["low", "l", "min"])
    close_col = find_col(["close", "c", "adj close", "adj_close", "adjusted_close", "last"])
    volume_col = find_col(["volume", "vol", "v", "qty"], required=False)
    
    # Handle dates
    if date_col:
        dates = pd.to_datetime(df[date_col])
    elif isinstance(df.index, pd.DatetimeIndex):
        dates = df.index
    else:
        # Create synthetic timestamps
        dates = pd.date_range(start="2020-01-01", periods=len(df), freq="D")
    
    ts = (dates.astype(np.int64) // 1000).values.astype(np.float64)  # Convert to microseconds
    asset_ids = np.zeros(len(df), dtype=np.float64)
    
    ohlcv = np.column_stack([
        df[open_col].values,
        df[high_col].values,
        df[low_col].values,
        df[close_col].values,
        df[volume_col].values if volume_col else np.zeros(len(df)),
    ]).astype(np.float64)
    
    return np.column_stack([ts, asset_ids, ohlcv]).astype(np.float64)


def _prices_to_bars(prices: Union[List[float], np.ndarray]) -> np.ndarray:
    """Convert a simple list of prices to Qrucible bar format.
    
    Creates synthetic OHLCV data where Open=High=Low=Close=price.
    """
    prices = np.array(prices, dtype=np.float64)
    n = len(prices)
    
    ts = np.arange(n, dtype=np.float64) * 86400_000_000  # Daily timestamps
    asset_ids = np.zeros(n, dtype=np.float64)
    volume = np.ones(n, dtype=np.float64) * 1_000_000  # Synthetic volume
    
    return np.column_stack([
        ts, asset_ids, prices, prices, prices, prices, volume
    ]).astype(np.float64)


# =============================================================================
# PRETTY RESULTS - Easy-to-read output
# =============================================================================

@dataclass
class EasyResult:
    """Beginner-friendly backtest result with pretty printing."""
    
    # Core metrics
    total_return: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Additional details
    profit_factor: float
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    
    # Raw result for advanced users
    _raw: Any
    
    def __str__(self) -> str:
        return self._format_pretty()
    
    def __repr__(self) -> str:
        return self._format_pretty()
    
    def _format_pretty(self) -> str:
        # Determine if profitable
        if self.total_return > 0.05:
            verdict = "Great!"
        elif self.total_return > 0:
            verdict = "Profitable"
        elif self.total_return > -0.05:
            verdict = "Small Loss"
        else:
            verdict = "Loss"
        
        lines = [
            "",
            f"  Backtest Results: {verdict}",
            "  " + "─" * 40,
            f"  Total Return:    {self.total_return:>10.2%}",
            f"  Total Trades:    {self.total_trades:>10}",
            f"  Win Rate:        {self.win_rate:>10.1%}",
            f"  Sharpe Ratio:    {self.sharpe_ratio:>10.2f}",
            f"  Max Drawdown:    {self.max_drawdown:>10.2%}",
            "  " + "─" * 40,
            f"  Profit Factor:   {self.profit_factor:>10.2f}",
            f"  Best Trade:      {self.best_trade:>10.2%}",
            f"  Worst Trade:     {self.worst_trade:>10.2%}",
            "",
        ]
        return "\n".join(lines)
    
    def summary(self) -> str:
        """One-line summary."""
        return f"Return: {self.total_return:.1%} | Win Rate: {self.win_rate:.0%} | Sharpe: {self.sharpe_ratio:.2f} | Trades: {self.total_trades}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for further analysis."""
        return {
            "total_return": self.total_return,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "profit_factor": self.profit_factor,
            "avg_trade_return": self.avg_trade_return,
            "best_trade": self.best_trade,
            "worst_trade": self.worst_trade,
        }
    
    @property
    def raw(self):
        """Access the full Qrucible result object for advanced analysis."""
        return self._raw


def _wrap_result(raw_result) -> EasyResult:
    """Convert raw Qrucible result to beginner-friendly format."""
    # Calculate derived metrics
    avg_trade = raw_result.total_return / raw_result.trades if raw_result.trades > 0 else 0
    
    # Get trade extremes from trade ledger if available
    best_trade = 0.0
    worst_trade = 0.0
    if hasattr(raw_result, 'trade_ledger') and raw_result.trade_ledger:
        pnls = [t.net_pnl / (t.entry_price * t.qty) if t.entry_price * t.qty > 0 else 0 
                for t in raw_result.trade_ledger]
        if pnls:
            best_trade = max(pnls)
            worst_trade = min(pnls)
    
    return EasyResult(
        total_return=raw_result.total_return,
        total_trades=raw_result.trades,
        win_rate=raw_result.win_pct,
        sharpe_ratio=raw_result.sharpe,
        max_drawdown=raw_result.max_drawdown,
        profit_factor=raw_result.profit_factor,
        avg_trade_return=avg_trade,
        best_trade=best_trade,
        worst_trade=worst_trade,
        _raw=raw_result,
    )


# =============================================================================
# MAIN API - Simple functions for beginners
# =============================================================================

def backtest(
    data: Union[str, pathlib.Path, "pd.DataFrame", List[float], np.ndarray, None] = None,
    strategy: str = "ma_cross",
    **kwargs
) -> EasyResult:
    """
    Run a backtest with minimal configuration.
    
    Parameters
    ----------
    data : str, Path, DataFrame, list, or None
        Your price data. Can be:
        - None: Uses built-in Apple stock sample data
        - str/Path: Path to a CSV file
        - DataFrame: Pandas DataFrame with OHLCV columns
        - list: Simple list of prices
        - ndarray: Numpy array (7 columns or just prices)
    
    strategy : str
        Strategy to use. Options:
        - "ma_cross" (default): Moving average crossover
        - "rsi": RSI overbought/oversold
        - "macd": MACD crossover
        - "bollinger": Bollinger band breakout
    
    **kwargs
        Optional strategy parameters (for advanced users).
        Common options:
        - fast_window: Fast MA period (default: 10)
        - slow_window: Slow MA period (default: 30)
        - stop_loss: Stop loss percentage (default: 0.02 = 2%)
        - take_profit: Take profit percentage (default: 0.04 = 4%)
    
    Returns
    -------
    EasyResult
        A result object with pretty printing and easy-to-access metrics.
    
    Examples
    --------
    >>> # Use sample data
    >>> result = backtest()
    >>> print(result)
    
    >>> # Use your own CSV file
    >>> result = backtest("my_prices.csv")
    
    >>> # Use a pandas DataFrame
    >>> result = backtest(df)
    
    >>> # Use a simple list of prices
    >>> result = backtest([100, 102, 101, 105, 103, 108])
    
    >>> # Try different strategies
    >>> result = backtest(strategy="rsi")
    >>> result = backtest(strategy="macd")
    
    >>> # Customize parameters
    >>> result = backtest(fast_window=5, slow_window=20, stop_loss=0.03)
    """
    # Load data
    if data is None:
        bars = _load_sample_data()
    elif isinstance(data, (str, pathlib.Path)):
        bars = _load_csv_simple(data)
    elif HAS_PANDAS and isinstance(data, pd.DataFrame):
        bars = _dataframe_to_bars(data)
    elif isinstance(data, list):
        bars = _prices_to_bars(data)
    elif isinstance(data, np.ndarray):
        if data.ndim == 1:
            bars = _prices_to_bars(data)
        elif data.ndim == 2 and data.shape[1] == 7:
            bars = data.astype(np.float64)
        else:
            raise ValueError(
                f"Numpy array must be 1D (prices) or 2D with 7 columns. Got shape: {data.shape}"
            )
    else:
        raise TypeError(
            f"Unsupported data type: {type(data)}. Use a CSV path, DataFrame, list, or numpy array."
        )
    
    # Build configuration
    config = _build_config(strategy, **kwargs)
    
    # Run backtest
    result = _qrucible.run_backtest(bars, config)
    
    return _wrap_result(result)


def _build_config(strategy: str, **kwargs) -> _qrucible.StrategyConfig:
    """Build a StrategyConfig from simple parameters."""
    strategy = strategy.lower().strip()
    
    # Strategy presets
    presets = {
        "ma_cross": {
            "strategy_type": "MA_CROSS",
            "fast_window": 10,
            "slow_window": 30,
            "ma_type": "EMA",
        },
        "ma": {
            "strategy_type": "MA_CROSS",
            "fast_window": 10,
            "slow_window": 30,
            "ma_type": "EMA",
        },
        "rsi": {
            "strategy_type": "RSI",
            "rsi_period": 14,
            "rsi_upper": 70.0,
            "rsi_lower": 30.0,
        },
        "macd": {
            "strategy_type": "MACD",
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
        },
        "bollinger": {
            "strategy_type": "BOLLINGER",
            "bollinger_period": 20,
            "bollinger_std": 2.0,
        },
        "stochastic": {
            "strategy_type": "STOCHASTIC",
            "stoch_k_period": 14,
            "stoch_d_period": 3,
        },
    }
    
    if strategy not in presets:
        available = ", ".join(presets.keys())
        raise ValueError(f"Unknown strategy: '{strategy}'. Available: {available}")
    
    # Start with preset
    config_dict = presets[strategy].copy()
    
    # Add defaults
    defaults = {
        "stop_loss": 0.02,
        "take_profit": 0.04,
        "risk_per_trade": 0.01,
        "initial_cash": 100_000.0,
        "record_trades": True,
    }
    
    for key, value in defaults.items():
        if key not in config_dict:
            config_dict[key] = value
    
    # Override with user kwargs
    config_dict.update(kwargs)
    
    return _qrucible.StrategyConfig(**config_dict)


# =============================================================================
# CONVENIENCE FUNCTIONS - One-liner strategies
# =============================================================================

def backtest_ma(data=None, fast: int = 10, slow: int = 30, **kwargs) -> EasyResult:
    """
    Backtest a Moving Average Crossover strategy.
    
    Buys when fast MA crosses above slow MA, sells when it crosses below.
    
    Parameters
    ----------
    data : optional
        Price data (CSV path, DataFrame, or list). None uses sample data.
    fast : int
        Fast moving average period (default: 10)
    slow : int
        Slow moving average period (default: 30)
    
    Examples
    --------
    >>> result = backtest_ma()  # Use sample data
    >>> result = backtest_ma("prices.csv", fast=5, slow=20)
    """
    return backtest(data, strategy="ma_cross", fast_window=fast, slow_window=slow, **kwargs)


def backtest_rsi(data=None, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs) -> EasyResult:
    """
    Backtest an RSI (Relative Strength Index) strategy.
    
    Buys when RSI falls below oversold level, sells when above overbought.
    
    Parameters
    ----------
    data : optional
        Price data (CSV path, DataFrame, or list). None uses sample data.
    period : int
        RSI calculation period (default: 14)
    oversold : float
        Buy when RSI below this (default: 30)
    overbought : float
        Sell when RSI above this (default: 70)
    
    Examples
    --------
    >>> result = backtest_rsi()
    >>> result = backtest_rsi(period=7, oversold=25, overbought=75)
    """
    return backtest(data, strategy="rsi", rsi_period=period, rsi_lower=oversold, rsi_upper=overbought, **kwargs)


def backtest_macd(data=None, fast: int = 12, slow: int = 26, signal: int = 9, **kwargs) -> EasyResult:
    """
    Backtest a MACD (Moving Average Convergence Divergence) strategy.
    
    Buys when MACD crosses above signal line, sells when below.
    
    Parameters
    ----------
    data : optional
        Price data (CSV path, DataFrame, or list). None uses sample data.
    fast : int
        Fast EMA period (default: 12)
    slow : int
        Slow EMA period (default: 26)
    signal : int
        Signal line period (default: 9)
    
    Examples
    --------
    >>> result = backtest_macd()
    >>> result = backtest_macd(fast=8, slow=21, signal=5)
    """
    return backtest(data, strategy="macd", macd_fast=fast, macd_slow=slow, macd_signal=signal, **kwargs)


def backtest_bollinger(data=None, period: int = 20, std: float = 2.0, **kwargs) -> EasyResult:
    """
    Backtest a Bollinger Bands strategy.
    
    Buys when price touches lower band, sells when price touches upper band.
    
    Parameters
    ----------
    data : optional
        Price data (CSV path, DataFrame, or list). None uses sample data.
    period : int
        Moving average period (default: 20)
    std : float
        Standard deviation multiplier for bands (default: 2.0)
    
    Examples
    --------
    >>> result = backtest_bollinger()
    >>> result = backtest_bollinger(period=15, std=2.5)
    """
    return backtest(data, strategy="bollinger", bollinger_period=period, bollinger_std=std, **kwargs)


# =============================================================================
# COMPARISON - Test multiple strategies at once
# =============================================================================

def compare_strategies(data=None, strategies: List[str] = None) -> dict:
    """
    Compare multiple strategies on the same data.
    
    Parameters
    ----------
    data : optional
        Price data (CSV path, DataFrame, or list). None uses sample data.
    strategies : list of str, optional
        Strategies to compare. Default: ["ma_cross", "rsi", "macd", "bollinger"]
    
    Returns
    -------
    dict
        Dictionary mapping strategy names to results.
    
    Examples
    --------
    >>> results = compare_strategies()
    >>> for name, result in results.items():
    ...     print(f"{name}: {result.summary()}")
    """
    if strategies is None:
        strategies = ["ma_cross", "rsi", "macd", "bollinger"]
    
    results = {}
    
    print("Comparing strategies...\n")
    
    for strategy in strategies:
        try:
            result = backtest(data, strategy=strategy)
            results[strategy] = result
            print(f"  {strategy:12} | {result.summary()}")
        except Exception as e:
            print(f"  ERROR {strategy:12} | Error: {e}")
    
    # Find best
    if results:
        best = max(results.items(), key=lambda x: x[1].total_return)
        print(f"\n  Best: {best[0]} with {best[1].total_return:.1%} return")
    
    return results


# =============================================================================
# SAMPLE DATA HELPERS
# =============================================================================

def get_sample_data() -> "pd.DataFrame":
    """
    Get sample stock data as a pandas DataFrame.
    
    Returns
    -------
    pd.DataFrame
        Apple historical stock data with Date, Open, High, Low, Close, Volume.
    
    Examples
    --------
    >>> df = get_sample_data()
    >>> print(df.head())
    """
    if not HAS_PANDAS:
        raise ImportError("pandas required. Install with: pip install pandas")
    
    path = _download_sample_data()
    return pd.read_csv(path, parse_dates=["Date"])


def list_strategies() -> List[str]:
    """
    List all available strategies.
    
    Returns
    -------
    list of str
        Available strategy names.
    
    Examples
    --------
    >>> print(list_strategies())
    ['ma_cross', 'rsi', 'macd', 'bollinger', 'stochastic']
    """
    return ["ma_cross", "rsi", "macd", "bollinger", "stochastic"]


# =============================================================================
# QUICK DEMO
# =============================================================================

def demo():
    """
    Run a quick demo to show Qrucible in action.
    
    Examples
    --------
    >>> import qrucible_easy as ez
    >>> ez.demo()
    """
    print("\n" + "=" * 50)
    print("  Welcome to Qrucible - Easy Backtesting!")
    print("=" * 50)
    
    print("\n Loading sample stock data (Apple)...\n")
    
    # Run backtest
    result = backtest()
    print(result)
    
    print("Try these commands:")
    print("   result = ez.backtest()                    # Use sample data")
    print("   result = ez.backtest('my_data.csv')       # Use your CSV")
    print("   result = ez.backtest(my_dataframe)        # Use pandas DataFrame")
    print("   result = ez.backtest_rsi()                # Try RSI strategy")
    print("   results = ez.compare_strategies()         # Compare all strategies")
    print()


# Run demo if executed directly
if __name__ == "__main__":
    demo()
