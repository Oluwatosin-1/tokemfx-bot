"""
TOKEMFX TEST BACKTEST SYSTEM
============================
Test utilities for backtesting simulations and sample data generation.
This module provides mock backtest results and sample OHLC data for testing.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

def create_sample_ohlc_data(instrument: str = "R_10", bars: int = 500) -> pd.DataFrame:
    """
    Create sample OHLC data for testing.

    Args:
        instrument: Trading instrument
        bars: Number of price bars

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)  # For reproducible results

    # Start price based on instrument
    base_prices = {
        'R_10': 0.7, 'R_25': 0.25, 'R_50': 0.20, 'R_75': 0.15, 'R_100': 0.10,
        'frxEURUSD': 1.08, 'frxGBPUSD': 1.27, 'frxUSDJPY': 147.50
    }

    base_price = base_prices.get(instrument, 0.5)
    volatility = {
        'R_10': 0.02, 'R_25': 0.03, 'R_50': 0.04, 'R_75': 0.05, 'R_100': 0.06,
        'frxEURUSD': 0.008, 'frxGBPUSD': 0.009, 'frxUSDJPY': 0.012
    }.get(instrument, 0.01)

    # Generate price series with trend and noise
    trend = 0.0001  # Slight upward trend
    prices = [base_price]

    for _ in range(bars - 1):
        # Random walk with trend
        change = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(0.01, new_price))  # Prevent negative prices

    # Convert to OHLC
    ohlc_data = []
    for i in range(len(prices) - 1):
        current_price = prices[i]
        next_price = prices[i+1]

        # Generate OHLC from current to next price
        range_size = abs(next_price - current_price) * random.uniform(0.3, 0.8)

        if next_price > current_price:  # Bullish bar
            open_p = current_price
            close_p = next_price
            low_p = current_price - random.uniform(0, range_size)
            high_p = next_price + random.uniform(0, range_size)
        else:  # Bearish bar
            open_p = current_price
            close_p = next_price
            high_p = current_price + random.uniform(0, range_size)
            low_p = next_price - random.uniform(0, range_size)

        # Volume (simplified)
        volume = random.randint(1000, 10000)

        ohlc_data.append({
            'time': datetime.now() - timedelta(minutes=(bars - i)),
            'open': round(open_p, 5),
            'high': round(high_p, 5),
            'low': round(low_p, 5),
            'close': round(close_p, 5),
            'volume': volume
        })

    return pd.DataFrame(ohlc_data)

def simulate_backtest_results(instrument: str, strategy: str, timeframe: str,
                            days: int = 365) -> List[Dict[str, Any]]:
    """
    Simulate realistic backtesting results for different strategies.

    Args:
        instrument: Trading instrument
        strategy: Strategy name
        timeframe: Chart timeframe
        days: Backtesting period in days

    Returns:
        List of backtest result dictionaries
    """
    # Base performance metrics by strategy type
    strategy_profiles = {
        'rsi': {'win_rate': 0.65, 'sharpe': 1.4, 'returns': 12.5, 'drawdown': -4.2},
        'macd': {'win_rate': 0.58, 'sharpe': 1.1, 'returns': 8.9, 'drawdown': -3.8},
        'bollinger': {'win_rate': 0.62, 'sharpe': 1.3, 'returns': 15.2, 'drawdown': -5.1},
        'moving_average': {'win_rate': 0.55, 'sharpe': 0.9, 'returns': 6.8, 'drawdown': -2.9},
        'stoch': {'win_rate': 0.60, 'sharpe': 1.2, 'returns': 10.3, 'drawdown': -4.5},
        'default': {'win_rate': 0.52, 'sharpe': 0.8, 'returns': 4.2, 'drawdown': -3.1}
    }

    # Detect strategy type
    strategy_lower = strategy.lower()
    profile = strategy_profiles['default']

    if 'rsi' in strategy_lower:
        profile = strategy_profiles['rsi']
    elif 'macd' in strategy_lower:
        profile = strategy_profiles['macd']
    elif 'bollinger' in strategy_lower:
        profile = strategy_profiles['bollinger']
    elif 'ma' in strategy_lower or 'average' in strategy_lower:
        profile = strategy_profiles['moving_average']
    elif 'stoch' in strategy_lower:
        profile = strategy_profiles['stoch']

    # Generate multiple strategy variations
    variations = [
        f"{strategy} - Aggressive",
        f"{strategy} - Conservative",
        f"{strategy} - Trend Following",
        f"{strategy} - Mean Reversion"
    ]

    results = []
    for i, variation in enumerate(variations):
        # Add some variation to results
        variation_factor = 1 + (random.uniform(-0.2, 0.2))  # ±20% variation

        result = {
            'strategy': variation,
            'instrument': instrument,
            'timeframe': timeframe,
            'total_return': profile['returns'] * variation_factor,
            'sharpe_ratio': profile['sharpe'] + random.uniform(-0.1, 0.1),
            'max_drawdown': profile['drawdown'] * variation_factor,
            'win_rate': profile['win_rate'] + random.uniform(-0.05, 0.05),
            'total_trades': random.randint(120, 250),
            'avg_profit': profile['returns'] / 10 * variation_factor,  # Per trade return
            'period_days': days,
            'start_date': (datetime.now() - timedelta(days=days)).date(),
            'end_date': datetime.now().date(),
            'performance_score': random.uniform(0.6, 0.95)
        }

        # Ensure realistic constraints
        result['win_rate'] = min(0.75, max(0.35, result['win_rate']))
        result['sharpe_ratio'] = max(0.1, result['sharpe_ratio'])
        result['total_return'] = max(-20, min(50, result['total_return']))

        results.append(result)

    return results

def generate_strategy_comparison() -> pd.DataFrame:
    """
    Generate comprehensive strategy comparison data.

    Returns:
        DataFrame with strategy performance metrics
    """
    strategies = [
        "📊 RSI Reversal", "📈 MA Cross", "🎯 Bollinger Breakout",
        "⚡ ATR Breakout", "🔄 EMA + RSI", "🌊 SuperTrend",
        "📉 MACD Cross", "🌀 Fib Retracement"
    ]

    instruments = ["R_10", "R_100", "frxEURUSD", "frxGBPUSD"]

    comparison_data = []

    for strategy in strategies:
        for instrument in instruments:
            # Simulate performance based on instrument volatility
            volatility_bonus = {
                'R_10': 1.0, 'R_100': 1.3,  # Higher volatility = more trades
                'frxEURUSD': 0.8, 'frxGBPUSD': 0.7
            }.get(instrument, 1.0)

            base_performance = {
                "📊 RSI Reversal": [0.68, 1.4, 18.5, 145, 0.13, -4.2],
                "📈 MA Cross": [0.59, 1.1, 12.3, 98, 0.13, -3.5],
                "🎯 Bollinger Breakout": [0.71, 1.6, 22.8, 87, 0.26, -5.8],
                "⚡ ATR Breakout": [0.64, 1.3, 16.2, 156, 0.10, -4.1],
                "🔄 EMA + RSI": [0.67, 1.5, 20.1, 134, 0.15, -4.7],
                "🌊 SuperTrend": [0.62, 1.2, 14.9, 112, 0.13, -3.9],
                "📉 MACD Cross": [0.60, 1.0, 11.8, 89, 0.13, -3.1],
                "🌀 Fib Retracement": [0.69, 1.7, 24.3, 76, 0.32, -6.2]
            }.get(strategy, [0.55, 1.0, 8.5, 120, 0.07, -3.0])

            win_rate, sharpe, total_return, trades, avg_profit, max_drawdown = base_performance

            # Apply volatility adjustment
            adjusted_return = total_return * volatility_bonus
            adjusted_trades = int(trades * volatility_bonus)

            comparison_data.append({
                'Strategy': strategy,
                'Instrument': instrument,
                'Win_Rate': round(win_rate + random.uniform(-0.03, 0.03), 3),
                'Sharpe_Ratio': round(sharpe + random.uniform(-0.1, 0.1), 2),
                'Total_Return_%': round(adjusted_return, 1),
                'Total_Trades': adjusted_trades,
                'Avg_Profit_%': round(avg_profit + random.uniform(-0.02, 0.02), 3),
                'Max_Drawdown_%': round(max_drawdown * (0.9 + random.uniform(0, 0.2)), 1),
                'Profit_Factor': round(1.2 + random.uniform(0, 0.6), 2)
            })

    return pd.DataFrame(comparison_data)

def run_test_backtests() -> Dict[str, Any]:
    """
    Run comprehensive backtesting simulation for all strategies.

    Returns:
        Complete test results
    """
    strategies = [
        "📊 RSI Reversal", "📈 MA Cross", "🎯 Bollinger Breakout",
        "⚡ ATR Breakout", "🔄 EMA + RSI", "🌊 SuperTrend",
        "📉 MACD Cross", "🌀 Fib Retracement"
    ]

    instruments = ["R_10", "R_50", "frxEURUSD"]

    all_results = []
    best_strategies = []

    print("🧪 Running complete backtesting simulation...")

    for instrument in instruments:
        for strategy in strategies:
            results = simulate_backtest_results(instrument, strategy, "1M", days=180)
            all_results.extend(results)

            # Find best strategy for each instrument
            best = max(results, key=lambda x: x.get('performance_score', 0))
            best_strategies.append(best)

    best_strategies.sort(key=lambda x: x.get('performance_score', 0), reverse=True)

    return {
        'all_results': all_results,
        'best_strategies': best_strategies[:3],  # Top 3
        'strategy_comparison': generate_strategy_comparison(),
        'test_data_available': True
    }

# Global test data
test_results = None

def get_test_backtest_results():
    """Lazy load test results"""
    global test_results
    if test_results is None:
        test_results = run_test_backtests()
    return test_results

# Export the required functions
__all__ = [
    'create_sample_ohlc_data',
    'get_test_backtest_results',
    'simulate_backtest_results',
    'generate_strategy_comparison'
]
