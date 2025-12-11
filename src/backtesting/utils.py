"""
TokemFX Backtesting Utilities
=============================
Helper functions and utilities for backtesting operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting operations"""
    parallel_processing: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    validation_enabled: bool = True
    statistical_testing: bool = True
    data_quality_checks: bool = True


def setup_backtest_environment(config: Optional[BacktestConfig] = None) -> BacktestConfig:
    """
    Setup and validate backtesting environment.

    Args:
        config: Optional configuration override

    Returns:
        Validated configuration object
    """
    if config is None:
        config = BacktestConfig()

    # Validate configuration
    if config.max_workers < 1:
        config.max_workers = 4
        logger.warning("Invalid max_workers, setting to 4")

    if config.max_workers > 8:
        logger.warning("High worker count may cause system instability")

    logger.info(f"Backtesting environment configured: {config}")
    return config


def validate_data_compatibility(strategy_class, data_sample: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate data compatibility with strategy requirements.

    Args:
        strategy_class: The strategy class to validate against
        data_sample: Sample DataFrame to check

    Returns:
        Validation results dictionary
    """
    required_columns = ['time', 'open', 'high', 'low', 'close']
    missing_columns = []

    for col in required_columns:
        if col not in data_sample.columns:
            missing_columns.append(col)

    has_time_column = any(col in data_sample.columns for col in ['time', 'timestamp', 'datetime'])
    has_ohlc = all(col in data_sample.columns for col in ['open', 'high', 'low', 'close'])

    validation_result = {
        'is_valid': len(missing_columns) == 0 and has_time_column and has_ohlc,
        'missing_columns': missing_columns,
        'data_points': len(data_sample),
        'time_range': None,
        'warnings': []
    }

    # Check time range if available
    if has_time_column:
        time_col = [col for col in data_sample.columns if col in ['time', 'timestamp', 'datetime']][0]
        if pd.api.types.is_datetime64_any_dtype(data_sample[time_col]):
            validation_result['time_range'] = {
                'start': data_sample[time_col].min(),
                'end': data_sample[time_col].max(),
                'duration': data_sample[time_col].max() - data_sample[time_col].min()
            }

    # Check for potential data quality issues
    if len(data_sample) > 0:
        # Check for gaps in time series
        if has_time_column and len(data_sample) > 1:
            time_col = [col for col in data_sample.columns if col in ['time', 'timestamp', 'datetime']][0]
            time_series = pd.to_datetime(data_sample[time_col]).sort_values()
            expected_periods = pd.date_range(start=time_series.min(), end=time_series.max(), freq='1min')
            gap_percentage = 1 - (len(time_series) / len(expected_periods))
            if gap_percentage > 0.1:  # More than 10% gaps
                validation_result['warnings'].append(".1f")

        # Check for unrealistic price movements
        if has_ohlc:
            returns = data_sample['close'].pct_change().dropna()
            outliers = len(returns[abs(returns) > 0.1])  # More than 10% change
            if outliers > len(returns) * 0.05:  # More than 5% of bars are outliers
                validation_result['warnings'].append(f"High volatility detected: {outliers} outlier price movements")

    return validation_result


def calculate_progress_percentage(current: int, total: int, decimals: int = 2) -> float:
    """
    Calculate progress percentage with proper handling of edge cases.

    Args:
        current: Current progress value
        total: Total value to reach
        decimals: Decimal places to round to

    Returns:
        Progress percentage (0.0 to 100.0)
    """
    if total <= 0:
        return 100.0 if current > 0 else 0.0

    percentage = min(100.0, (current / total) * 100)
    return round(percentage, decimals)


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in seconds to human readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return "02.1f"
    elif seconds < 3600:
        return "02.1f"
    elif seconds < 86400:
        hours = seconds / 3600
        return "02.1f"
    else:
        days = seconds / 86400
        return "02.1f"


def safe_divide(numerator: Union[int, float],
               denominator: Union[int, float],
               default: Union[int, float] = 0.0) -> float:
    """
    Safe division that handles division by zero.

    Args:
        numerator: Dividend
        denominator: Divisor
        default: Default value when denominator is zero

    Returns:
        Division result or default value
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (ZeroDivisionError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.

    Args:
        text: String to truncate
        max_length: Maximum allowed length
        suffix: Suffix to append if truncated

    Returns:
        Truncated string or original if short enough
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def generate_parameter_combinations(parameter_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    Generate all parameter combinations from parameter ranges.

    Args:
        parameter_ranges: Dictionary of parameter names to lists of values

    Returns:
        List of parameter combination dictionaries
    """
    from itertools import product

    param_names = list(parameter_ranges.keys())
    param_values = list(parameter_ranges.values())

    combinations = []
    for combination in product(*param_values):
        param_dict = dict(zip(param_names, combination))
        combinations.append(param_dict)

    return combinations


def validate_parameter_ranges(parameters: Dict[str, Any],
                            strategy_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate parameter ranges against strategy requirements.

    Args:
        parameters: Parameter dictionary to validate
        strategy_requirements: Optional strategy-specific requirements

    Returns:
        Validation results dictionary
    """
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }

    # General validation rules
    validations = {
        'fast_period': lambda x: isinstance(x, int) and 1 <= x <= 200,
        'slow_period': lambda x: isinstance(x, int) and 1 <= x <= 500,
        'rsi_period': lambda x: isinstance(x, int) and 2 <= x <= 100,
        'rsi_oversold': lambda x: isinstance(x, (int, float)) and 1 <= x <= 50,
        'rsi_overbought': lambda x: isinstance(x, (int, float)) and 50 <= x <= 99,
        'size': lambda x: isinstance(x, (int, float)) and x > 0,
        'stop_loss': lambda x: isinstance(x, (int, float)) and 0 < x <= 1,
        'take_profit': lambda x: isinstance(x, (int, float)) and x >= 1
    }

    for param_name, param_value in parameters.items():
        if param_name in validations:
            if not validations[param_name](param_value):
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Invalid value for {param_name}: {param_value}")
        else:
            # Unknown parameter - issue warning but don't fail
            validation_results['warnings'].append(f"Unknown parameter: {param_name}")

    # Cross-parameter validation
    if 'fast_period' in parameters and 'slow_period' in parameters:
        if parameters['fast_period'] >= parameters['slow_period']:
            validation_results['is_valid'] = False
            validation_results['errors'].append("Fast period must be shorter than slow period")

    if 'rsi_oversold' in parameters and 'rsi_overbought' in parameters:
        if parameters['rsi_oversold'] >= parameters['rsi_overbought']:
            validation_results['is_valid'] = False
            validation_results['errors'].append("RSI oversold level must be below overbought level")

    return validation_results


def create_strategy_comparison_table(results_list: List[Dict[str, Any]],
                                   metrics: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Create a comparison table for multiple strategy results.

    Args:
        results_list: List of backtest result dictionaries
        metrics: Specific metrics to include in comparison

    Returns:
        Comparison DataFrame
    """
    if metrics is None:
        metrics = [
            'strategy_class', 'sharpe_ratio', 'total_return_pct',
            'win_rate', 'max_drawdown', 'total_trades', 'net_profit'
        ]

    comparison_data = []
    for result in results_list:
        row = {}
        for metric in metrics:
            row[metric] = result.get(metric)

        # Extract parameters for comparison
        params = result.get('parameters', {})
        for param_key, param_value in params.items():
            if param_key in ['fast_period', 'slow_period', 'rsi_period']:  # Common params
                row[f'param_{param_key}'] = param_value

        comparison_data.append(row)

    return pd.DataFrame(comparison_data)


def calculate_confidence_intervals(returns: pd.Series,
                                 confidence_level: float = 0.95) -> Dict[str, float]:
    """
    Calculate confidence intervals for returns distribution.

    Args:
        returns: Series of period returns
        confidence_level: Statistical confidence level

    Returns:
        Dictionary with confidence interval bounds
    """
    if returns.empty:
        return {'lower': 0.0, 'upper': 0.0, 'confidence_level': confidence_level}

    mean_return = returns.mean()
    std_return = returns.std()
    n = len(returns)

    # Critical value from t-distribution
    from scipy import stats
    critical_value = stats.t.ppf((1 + confidence_level) / 2, n - 1)

    # Standard error
    standard_error = std_return / np.sqrt(n)

    # Confidence interval
    lower_bound = mean_return - critical_value * standard_error
    upper_bound = mean_return + critical_value * standard_error

    return {
        'lower': lower_bound,
        'upper': upper_bound,
        'confidence_level': confidence_level,
        'mean': mean_return,
        'std_error': standard_error
    }


def optimize_ram_usage() -> Dict[str, Any]:
    """
    Perform garbage collection and memory optimization.

    Returns:
        Memory optimization results
    """
    import gc
    import psutil

    try:
        # Get memory before GC
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Run garbage collection
        collected = gc.collect()

        # Get memory after GC
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = memory_before - memory_after

        return {
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_freed_mb': memory_freed,
            'objects_collected': collected,
            'success': True
        }

    except ImportError:
        # psutil not available
        collected = gc.collect()
        return {
            'objects_collected': collected,
            'success': True,
            'note': 'psutil not available for memory monitoring'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_system_resource_usage() -> Dict[str, Any]:
    """
    Get current system resource usage.

    Returns:
        System resource information
    """
    try:
        import psutil
        process = psutil.Process()

        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'num_threads': process.num_threads(),
            'open_files': len(process.open_files()),
            'success': True
        }

    except ImportError:
        return {
            'success': False,
            'error': 'psutil not available',
            'fallback': 'Install psutil for resource monitoring'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def create_performance_benchmark(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create performance benchmark for comparison against known standards.

    Args:
        results: Backtest results to benchmark

    Returns:
        Benchmark comparison data
    """
    sharpe_ratio = results.get('sharpe_ratio', 0)
    max_drawdown = results.get('max_drawdown', 0)
    win_rate = results.get('win_rate', 0)

    # Risk-adjusted return benchmarks
    benchmark = {
        'sharpe_ratio': {
            'value': sharpe_ratio,
            'excellent': sharpe_ratio > 3.0,
            'good': sharpe_ratio > 1.5,
            'poor': sharpe_ratio < 0.5,
            'benchmark': 'Sharpe Ratio: >1.5 = Good, >3.0 = Excellent'
        },
        'max_drawdown': {
            'value': max_drawdown,
            'excellent': max_drawdown < 5.0,
            'good': max_drawdown < 15.0,
            'poor': max_drawdown > 30.0,
            'benchmark': 'Max Drawdown: <5% = Excellent, <15% = Good'
        },
        'win_rate': {
            'value': win_rate,
            'excellent': win_rate > 0.75,
            'good': win_rate > 0.60,
            'poor': win_rate < 0.45,
            'benchmark': 'Win Rate: >60% = Good, >75% = Excellent'
        }
    }

    # Overall grade
    scores = [
        2 if benchmark['sharpe_ratio']['excellent'] else 1 if benchmark['sharpe_ratio']['good'] else 0,
        2 if benchmark['max_drawdown']['excellent'] else 1 if benchmark['max_drawdown']['good'] else 0,
        2 if benchmark['win_rate']['excellent'] else 1 if benchmark['win_rate']['good'] else 0
    ]

    avg_score = sum(scores) / len(scores)
    if avg_score >= 1.8:
        grade = 'A'
        description = 'Excellent Performance'
    elif avg_score >= 1.3:
        grade = 'B'
        description = 'Good Performance'
    elif avg_score >= 0.8:
        grade = 'C'
        description = 'Fair Performance'
    elif avg_score >= 0.3:
        grade = 'D'
        description = 'Poor Performance'
    else:
        grade = 'F'
        description = 'Very Poor Performance'

    benchmark['overall'] = {
        'grade': grade,
        'description': description,
        'score': avg_score,
        'max_score': 2.0
    }

    return benchmark
