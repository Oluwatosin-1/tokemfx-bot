"""
Testing Framework Module
========================
Comprehensive validation frameworks and automated testing capabilities.
"""

from .automated_test_suite import (
    create_sample_ohlc_data,
    get_test_backtest_results,
    simulate_backtest_results,
    generate_strategy_comparison
)
from .indicator_cross_validation import test_all_indicators_mathematical_accuracy as validate_indicators

__all__ = [
    'create_sample_ohlc_data',
    'get_test_backtest_results',
    'simulate_backtest_results',
    'generate_strategy_comparison',
    'validate_indicators'
]
