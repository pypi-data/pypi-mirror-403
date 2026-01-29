#!/usr/bin/env python
"""
Qrucible Quick Start - Your First Backtest

This script shows you everything you need to get started with Qrucible.
Run it with: python scripts/quickstart.py

No prior experience needed!
"""

# First, import the easy-to-use wrapper
import qrucible_easy as ez


def main():
    print("\n" + "=" * 60)
    print("   Welcome to Qrucible - Easy Backtesting for Everyone!")
    print("=" * 60)
    
    # =========================================================================
    # STEP 1: Your first backtest (uses built-in sample data)
    # =========================================================================
    print("\nSTEP 1: Your first backtest")
    print("-" * 40)
    
    result = ez.backtest()
    print(result)
    
    # =========================================================================
    # STEP 2: Try different strategies
    # =========================================================================
    print("\nSTEP 2: Try different strategies")
    print("-" * 40)
    
    # Moving Average Crossover - the classic!
    print("\nMoving Average Crossover:")
    ma_result = ez.backtest_ma(fast=10, slow=30)
    print(f"   {ma_result.summary()}")
    
    # RSI - buy when oversold, sell when overbought
    print("\nRSI Strategy:")
    rsi_result = ez.backtest_rsi(period=14, oversold=30, overbought=70)
    print(f"   {rsi_result.summary()}")
    
    # MACD - follow the momentum
    print("\nMACD Strategy:")
    macd_result = ez.backtest_macd()
    print(f"   {macd_result.summary()}")
    
    # =========================================================================
    # STEP 3: Compare all strategies at once
    # =========================================================================
    print("\nSTEP 3: Compare strategies side-by-side")
    print("-" * 40)
    
    results = ez.compare_strategies()
    
    # =========================================================================
    # STEP 4: Customize parameters
    # =========================================================================
    print("\nSTEP 4: Customize your strategy")
    print("-" * 40)
    
    custom_result = ez.backtest(
        strategy="ma_cross",
        fast_window=5,       # Faster signal
        slow_window=20,      # Shorter lookback
        stop_loss=0.03,      # 3% stop loss
        take_profit=0.06,    # 6% take profit
    )
    print(f"   Custom MA strategy: {custom_result.summary()}")
    
    # =========================================================================
    # STEP 5: Access detailed metrics
    # =========================================================================
    print("\nSTEP 5: Get detailed metrics")
    print("-" * 40)
    
    result = ez.backtest()
    
    print(f"   Total Return:  {result.total_return:.2%}")
    print(f"   Win Rate:      {result.win_rate:.1%}")
    print(f"   Sharpe Ratio:  {result.sharpe_ratio:.2f}")
    print(f"   Max Drawdown:  {result.max_drawdown:.2%}")
    print(f"   Profit Factor: {result.profit_factor:.2f}")
    print(f"   Total Trades:  {result.total_trades}")
    
    # Convert to dictionary for further analysis
    metrics = result.to_dict()
    print(f"\n   As dictionary: {metrics}")
    
    # =========================================================================
    # NEXT STEPS
    # =========================================================================
    print("\n" + "=" * 60)
    print("   You've completed the quick start!")
    print("=" * 60)
    print("""
Next steps:
    
1. Use your own data:
   result = ez.backtest("my_prices.csv")
   result = ez.backtest(my_dataframe)

2. See all available strategies:
   print(ez.list_strategies())

3. Get sample data to play with:
   df = ez.get_sample_data()

4. For advanced features, see the full documentation:
   https://charlesfreidenreich.github.io/Qrucible/
""")


if __name__ == "__main__":
    main()
