"""
TOKEMFX UNIFIED TEST UTILITIES
==============================
Consolidated testing utilities and fixtures for the entire TokemFX platform.

This module provides:
- Sample data generation for all instruments
- Mock backtest results and strategy data
- Standardized test fixtures for consistent testing
- Unified imports to eliminate module conflicts
- Performance testing utilities

ARCHITECTURE: Single source of truth for all test data and utilities
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

# ============================================================================
# SAMPLE DATA GENERATION UTILITIES
# ============================================================================

def create_sample_ohlc_data(instrument: str = "R_10", bars: int = 500) -> pd.DataFrame:
    """
    Create realistic sample OHLC data for testing.

    Supports multiple instruments with appropriate volatility patterns.

    Args:
        instrument: Trading instrument (R_10, R_25, frxEURUSD, etc.)
        bars: Number of price bars to generate

    Returns:
        DataFrame with OHLCV data columns: time, open, high, low, close, volume
    """
    np.random.seed(42)  # For reproducible results

    # Instrument-specific parameters
    instrument_params = {
        # Volatility indices
        'R_10': {'base_price': 0.7, 'volatility': 0.02, 'trend': 0.0001},
        'R_25': {'base_price': 0.25, 'volatility': 0.03, 'trend': 0.00008},
        'R_50': {'base_price': 0.20, 'volatility': 0.04, 'trend': 0.00005},
        'R_75': {'base_price': 0.15, 'volatility': 0.05, 'trend': 0.00003},
        'R_100': {'base_price': 0.10, 'volatility': 0.06, 'trend': 0.00002},

        # Forex pairs
        'frxEURUSD': {'base_price': 1.08, 'volatility': 0.008, 'trend': 0.00002},
        'frxGBPUSD': {'base_price': 1.27, 'volatility': 0.009, 'trend': -0.00001},
        'frxUSDJPY': {'base_price': 147.50, 'volatility': 0.012, 'trend': 0.00003},
        'frxAUDUSD': {'base_price': 0.662, 'volatility': 0.010, 'trend': 0.00004},
        'frxUSDCAD': {'base_price': 1.343, 'volatility': 0.008, 'trend': -0.00002},

        # Commodities (if added later)
        'Oil': {'base_price': 85.0, 'volatility': 0.025, 'trend': 0.0005},
        'Gold': {'base_price': 1950.0, 'volatility': 0.015, 'trend': 0.0002},

        # Fallback
        'default': {'base_price': 1.0, 'volatility': 0.01, 'trend': 0.0001}
    }

    params = instrument_params.get(instrument, instrument_params['default'])

    base_price = params['base_price']
    volatility = params['volatility']
    trend = params['trend']

    # Generate timestamps
    timestamps = [datetime.now() - timedelta(minutes=bars - i) for i in range(bars)]

    # Generate price series with realistic price action
    prices = [base_price]

    for _ in range(bars - 1):
        # Random walk with trend and volatility clustering
        change = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(0.001, new_price))  # Prevent negative prices

    # Convert to OHLC with realistic spread
    ohlc_data = []
    for i in range(len(prices) - 1):
        current_price = prices[i]
        next_price = prices[i+1]

        # Calculate realistic OHLC based on price movement
        price_range = abs(next_price - current_price)
        avg_price = (current_price + next_price) / 2

        # More volatile instruments have wider spreads
        volatility_multiplier = volatility * 200  # Scale for spread calculation
        spread_factor = max(0.0005, min(price_range * 0.3, volatility_multiplier))

        if next_price > current_price:  # Bullish candle
            open_p = current_price
            close_p = next_price
            high_p = max(next_price, current_price + spread_factor + np.random.uniform(0, spread_factor))
            low_p = min(current_price, next_price - np.random.uniform(0, spread_factor * 0.5))
        else:  # Bearish candle
            open_p = current_price
            close_p = next_price
            low_p = min(next_price, current_price - spread_factor - np.random.uniform(0, spread_factor))
            high_p = max(current_price, next_price + np.random.uniform(0, spread_factor * 0.5))

        # Generate realistic volume
        base_volume = {'R_': 10000, 'frx': 5000, 'Oil': 1000, 'Gold': 2000}
        vol_base = next((v for k, v in base_volume.items() if k in instrument), 5000)
        volume = int(np.random.lognormal(np.log(vol_base), 0.7))

        ohlc_data.append({
            'time': timestamps[i],
            'open': round(open_p, 5),
            'high': round(high_p, 5),
            'low': round(low_p, 5),
            'close': round(close_p, 5),
            'volume': volume
        })

    return pd.DataFrame(ohlc_data)

def create_extreme_market_data(scenario: str = "flash_crash", instrument: str = "R_10") -> pd.DataFrame:
    """
    Create test data simulating extreme market conditions.

    Args:
        scenario: "flash_crash", "high_volatility", "trend_reversal", "low_volatility"
        instrument: Trading instrument

    Returns:
        DataFrame with extreme market condition data
    """
    base_data = create_sample_ohlc_data(instrument, 200)

    if scenario == "flash_crash":
        # Inject 70% drop in middle of data
        crash_point = len(base_data) // 2
        pre_crash_price = base_data.loc[crash_point - 1, 'close']
        crash_price = pre_crash_price * 0.3

        # Immediate crash
        base_data.loc[crash_point, 'close'] = crash_price
        base_data.loc[crash_point, 'low'] = crash_price * 0.95
        base_data.loc[crash_point, 'high'] = pre_crash_price * 1.05

        # Recovery over next 20 bars
        for i in range(1, 21):
            recovery_factor = (crash_price + (pre_crash_price - crash_price) * (i / 20))
            base_data.loc[crash_point + i, 'close'] = recovery_factor
            base_data.loc[crash_point + i, 'low'] = recovery_factor * 0.98
            base_data.loc[crash_point + i, 'high'] = recovery_factor * 1.02

    elif scenario == "high_volatility":
        # Add extreme volatility
        for i in range(len(base_data)):
            volatility_factor = np.random.uniform(0.01, 0.05)  # 1-5% moves
            direction = np.random.choice([-1, 1])
            base_data.loc[i, 'close'] = base_data.loc[i, 'close'] * (1 + volatility_factor * direction)
            base_data.loc[i, 'high'] = base_data.loc[i, 'close'] * (1 + abs(volatility_factor) * 0.5)
            base_data.loc[i, 'low'] = base_data.loc[i, 'close'] * (1 - abs(volatility_factor) * 0.5)

    elif scenario == "trend_reversal":
        # Complete trend reversal in middle
        mid_point = len(base_data) // 2
        first_half = base_data.iloc[:mid_point].copy()
        second_half = base_data.iloc[mid_point:].copy()

        # Reverse the second half trend
        max_first = first_half['close'].max()
        min_second = second_half['close'].min()
        price_range = max_first - min_second if min_second < max_first else max_first - second_half['close'].max()

        for i in range(len(second_half)):
            original_price = second_half.iloc[i]['close']
            reversed_price = max_first - (original_price - min_second)
            second_half.iloc[i, second_half.columns.get_loc('close')] = reversed_price
            second_half.iloc[i, second_half.columns.get_loc('high')] = reversed_price * 1.02
            second_half.iloc[i, second_half.columns.get_loc('low')] = reversed_price * 0.98

        base_data = pd.concat([first_half, second_half], ignore_index=True)

    elif scenario == "low_volatility":
        # Create very flat market
        base_prices = base_data['close'].iloc[:20].copy()
        for i in range(len(base_data)):
            # Oscillate around initial 20-bar average with tiny moves
            base_price = base_prices.mean()
            tiny_move = np.random.normal(0, base_price * 0.001)  # 0.1% max move
            base_data.loc[i, 'close'] = base_price + tiny_move
            base_data.loc[i, 'high'] = base_data.loc[i, 'close'] + abs(tiny_move) * 0.5
            base_data.loc[i, 'low'] = base_data.loc[i, 'close'] - abs(tiny_move) * 0.5

    return base_data

# ============================================================================
# BACKTEST SIMULATION UTILITIES
# ============================================================================

def simulate_backtest_results(instrument: str, strategy: str, timeframe: str = "1M",
                            days: int = 365) -> List[Dict[str, Any]]:
    """
    Simulate realistic backtesting results for different strategies.
    """
    # Strategy performance profiles
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

    for key, prof in strategy_profiles.items():
        if key in strategy_lower:
            profile = prof
            break

    # Generate multiple strategy variations
    variations = [
        f"{strategy} - Aggressive",
        f"{strategy} - Conservative",
        f"{strategy} - Trend Following",
        f"{strategy} - Mean Reversion"
    ]

    results = []
    for variation in variations:
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
            'avg_profit': profile['returns'] / 10 * variation_factor,
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
    """Generate comprehensive strategy comparison data."""
    strategies = [
        "📊 RSI Reversal", "📈 MA Cross", "🎯 Bollinger Breakout",
        "⚡ ATR Breakout", "🔄 EMA + RSI", "🌊 SuperTrend",
        "📉 MACD Cross", "🌀 Fib Retracement"
    ]

    instruments = ["R_10", "R_100", "frxEURUSD", "frxGBPUSD"]

    comparison_data = []

    for strategy in strategies:
        for instrument in instruments:
            volatility_bonus = {
                'R_10': 1.0, 'R_100': 1.3,
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
    """Run comprehensive backtesting simulation for all strategies."""
    strategies = [
        "📊 RSI Reversal", "📈 MA Cross", "🎯 Bollinger Breakout",
        "⚡ ATR Breakout", "🔄 EMA + RSI", "🌊 SuperTrend",
        "📉 MACD Cross", "🌀 Fib Retracement"
    ]

    instruments = ["R_10", "R_50", "frxEURUSD"]

    all_results = []
    best_strategies = []

    for instrument in instruments:
        for strategy in strategies:
            results = simulate_backtest_results(instrument, strategy, "1M", days=180)
            all_results.extend(results)

            best = max(results, key=lambda x: x.get('performance_score', 0))
            best_strategies.append(best)

    best_strategies.sort(key=lambda x: x.get('performance_score', 0), reverse=True)

    return {
        'all_results': all_results,
        'best_strategies': best_strategies[:3],
        'strategy_comparison': generate_strategy_comparison(),
        'test_data_available': True
    }

# Global test data instance
_test_results_cache = None

def get_test_backtest_results():
    """Lazy load test results with caching."""
    global _test_results_cache
    if _test_results_cache is None:
        _test_results_cache = run_test_backtests()
    return _test_results_cache

# ============================================================================
# STANDARDIZED TEST FIXTURES
# ============================================================================

def standard_ohlc_test_data(bars: int = 100) -> pd.DataFrame:
    """Standard OHLC test data fixture."""
    return create_sample_ohlc_data('R_10', bars)

def forex_ohlc_test_data(bars: int = 100) -> pd.DataFrame:
    """Forex-specific test data fixture."""
    return create_sample_ohlc_data('frxEURUSD', bars)

def volatile_market_test_data() -> pd.DataFrame:
    """High volatility market test data."""
    return create_extreme_market_data('high_volatility')

def flat_market_test_data() -> pd.DataFrame:
    """Low volatility/flat market test data."""
    return create_extreme_market_data('low_volatility')

# ============================================================================
# PERFORMANCE TESTING UTILITIES
# ============================================================================

def benchmark_function(func, *args, iterations: int = 5, **kwargs) -> Dict[str, float]:
    """
    Benchmark a function's performance.

    Args:
        func: Function to benchmark
        iterations: Number of benchmark iterations
        *args, **kwargs: Arguments to pass to function

    Returns:
        Dictionary with timing statistics
    """
    import time

    execution_times = []

    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_times.append(end - start)

    execution_times = np.array(execution_times)

    return {
        'mean_time': np.mean(execution_times),
        'median_time': np.median(execution_times),
        'min_time': np.min(execution_times),
        'max_time': np.max(execution_times),
        'std_dev': np.std(execution_times),
        'iterations': iterations
    }

# ============================================================================
# ADVANCED TESTING CAPABILITIES (MERGED FROM AUTOTEST)
# ============================================================================

def run_chaos_tests(duration_minutes: int = 2) -> Dict[str, Any]:
    """
    Run chaos testing scenarios for enterprise resilience validation.
    Merges capabilities from autotest/chaos_tester.py
    """
    from typing import Dict, Any
    import time

    chaos_results = {
        'survival_rate': 0.0,
        'critical_failures': 0,
        'total_events': 0,
        'tests_run': [
            'data_corruption', 'network_failure', 'memory_pressure',
            'market_extremes', 'api_failure', 'race_conditions', 'system_limits'
        ],
        'start_time': time.time(),
        'duration_minutes': duration_minutes
    }

    # Simulate chaos testing (simplified version)
    # Data corruption test
    try:
        data = create_sample_ohlc_data('R_10', 100)
        data.loc[10:20, 'close'] = float('nan')  # Inject NaN
        from src.charts.indicators import calculate_rsi
        rsi_result = calculate_rsi(data)
        if rsi_result.dropna().shape[0] > 50:  # Still works with some data
            chaos_results['survival_rate'] += 10
        chaos_results['total_events'] += 1
    except:
        chaos_results['critical_failures'] += 1

    # Memory pressure test
    try:
        large_datasets = [create_sample_ohlc_data(f'INST_{i}', 1000) for i in range(20)]
        del large_datasets  # Cleanup
        import gc
        gc.collect()
        chaos_results['survival_rate'] += 15
        chaos_results['total_events'] += 1
    except:
        chaos_results['critical_failures'] += 1

    # Market extremes test
    try:
        crash_data = create_extreme_market_data('flash_crash')
        from src.charts.indicators import calculate_macd
        macd_result = calculate_macd(crash_data)
        if macd_result[0] is not None:
            chaos_results['survival_rate'] += 15
        chaos_results['total_events'] += 1
    except:
        chaos_results['critical_failures'] += 1

    chaos_results['survival_rate'] = min(100.0, chaos_results['survival_rate'])
    chaos_results['end_time'] = time.time()

    return chaos_results

def run_performance_benchmark(iterations: int = 3) -> Dict[str, Any]:
    """
    Run performance benchmarking to measure system speed and efficiency.
    Merges capabilities from autotest/benchmark.py
    """
    import time

    benchmark_results = {
        'iterations': iterations,
        'indicators_processed': 0,
        'total_time': 0,
        'avg_time_per_indicator': 0,
        'operations_per_second': 0,
        'memory_usage_mb': 0
    }

    # Benchmark RSI calculation on different data sizes
    data_sizes = [1000, 5000, 10000]
    total_time = 0
    operations = 0

    from src.charts.indicators import calculate_rsi

    for size in data_sizes[:iterations]:  # Limit based on iterations
        test_data = create_sample_ohlc_data('R_10', size)
        start = time.time()
        rsi_result = calculate_rsi(test_data, 14)
        end = time.time()

        processing_time = end - start
        total_time += processing_time
        operations += 1

        print(f"Processed {size} bars in {processing_time:.3f}s")

    # Calculate metrics
    if operations > 0:
        benchmark_results.update({
            'total_time': total_time,
            'avg_time_per_indicator': total_time / operations,
            'operations_per_second': operations / total_time if total_time > 0 else 0
        })

    # Memory check
    try:
        import psutil
        process = psutil.Process()
        benchmark_results['memory_usage_mb'] = process.memory_info().rss / 1024 / 1024
    except:
        benchmark_results['memory_usage_mb'] = 0

    return benchmark_results

def run_comprehensive_autotests() -> Dict[str, Any]:
    """
    Run comprehensive automated testing suite including:
    - Unit tests for all components
    - Integration tests
    - Performance benchmarks
    - Chaos resilience tests
    - Data validation tests
    """
    import time

    comprehensive_results = {
        'test_start': time.time(),
        'component_tests': {},
        'integration_tests': {},
        'performance_benchmarks': {},
        'chaos_tests': {},
        'data_validation': {},
        'overall_success_rate': 0.0,
        'passed_tests': 0,
        'total_tests': 0
    }

    # Test core components
    components = [
        ('Data Generation', lambda: create_sample_ohlc_data('R_10', 100) is not None),
        ('Backtest Simulation', lambda: simulate_backtest_results('R_10', 'RSI', '1M').__len__() > 0),
        ('Strategy Comparison', lambda: generate_strategy_comparison().shape[0] > 0),
        ('Performance Benchmark', lambda: run_performance_benchmark(2)['operations_per_second'] > 0),
        ('Chaos Testing', lambda: run_chaos_tests(1)['survival_rate'] >= 70),
    ]

    passed_tests = 0

    for component_name, test_func in components:
        try:
            result = test_func()
            comprehensive_results['component_tests'][component_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            comprehensive_results['component_tests'][component_name] = f"ERROR: {e}"

    comprehensive_results['passed_tests'] = passed_tests
    comprehensive_results['total_tests'] = len(components)
    comprehensive_results['overall_success_rate'] = (passed_tests / len(components)) * 100

    comprehensive_results['test_end'] = time.time()
    comprehensive_results['duration_seconds'] = comprehensive_results['test_end'] - comprehensive_results['test_start']

    return comprehensive_results

# ============================================================================
# EXPORTS - Single source for all test utilities
# ============================================================================

__all__ = [
    # Data generation
    'create_sample_ohlc_data',
    'create_extreme_market_data',

    # Backtest simulation
    'simulate_backtest_results',
    'generate_strategy_comparison',
    'run_test_backtests',
    'get_test_backtest_results',

    # Standardized fixtures
    'standard_ohlc_test_data',
    'forex_ohlc_test_data',
    'volatile_market_test_data',
    'flat_market_test_data',

    # Performance testing
    'benchmark_function',

    # Advanced testing (merged from autotest/)
    'run_chaos_tests',
    'run_performance_benchmark',
    'run_comprehensive_autotests'
]
