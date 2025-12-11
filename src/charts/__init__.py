"""
Advanced Charting Module for TokemFX
=====================================
TradingView-style charts with multiple timeframes and Fibonacci analysis.
"""

from .timeframes import get_available_timeframes, fetch_timeframe_data
from .fibonacci import calculate_fibonacci_retracements, calculate_fibonacci_extensions
from .chart_utils import create_price_chart, add_fibonacci_levels
from .indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_moving_averages, calculate_stochastic, calculate_williams_r,
    calculate_volume_profile, add_indicator_to_chart
)
from .drawing_tools import (
    draw_trend_lines, draw_support_resistance, draw_channels,
    draw_fibonacci_arcs, add_drawing_tools
)
from .patterns import (
    detect_candlestick_patterns, detect_chart_patterns,
    calculate_head_and_shoulders, calculate_double_top_bottom
)

__all__ = [
    # Timeframes
    'get_available_timeframes',
    'fetch_timeframe_data',

    # Fibonacci
    'calculate_fibonacci_retracements',
    'calculate_fibonacci_extensions',

    # Chart utilities
    'create_price_chart',
    'add_fibonacci_levels',

    # Technical indicators
    'calculate_rsi',
    'calculate_macd',
    'calculate_bollinger_bands',
    'calculate_moving_averages',
    'calculate_stochastic',
    'calculate_williams_r',
    'calculate_volume_profile',
    'add_indicator_to_chart',

    # Drawing tools
    'draw_trend_lines',
    'draw_support_resistance',
    'draw_channels',
    'draw_fibonacci_arcs',
    'add_drawing_tools',

    # Pattern recognition
    'detect_candlestick_patterns',
    'detect_chart_patterns',
    'calculate_head_and_shoulders',
    'calculate_double_top_bottom'
]
