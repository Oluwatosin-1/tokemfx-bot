"""
Fibonacci Analysis Tools for Technical Analysis
===============================================
Advanced Fibonacci retracements, extensions, projections, and ratios.
TradingView-style Fibonacci tools for professional analysis.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional

# Standard Fibonacci ratios
FIBONACCI_RATIOS = {
    'retracements': {
        'fibonacci': [0.236, 0.382, 0.500, 0.618, 0.786, 1.0, 1.272, 1.618],
        'support': [0.236, 0.382, 0.500, 0.618],
        'resistance': [0.786, 1.0, 1.272, 1.618]
    },
    'extensions': {
        'fibonacci': [0.618, 1.0, 1.272, 1.414, 1.618, 2.0, 2.618],
        'targets': [1.272, 1.618, 2.618]
    },
    'projections': {
        'fibonacci': [0.382, 0.618, 1.0, 1.272, 1.618],
        'harmonic': [0.886, 1.130, 1.272, 2.618, 4.236]
    }
}

class FibonacciCalculator:
    """
    Advanced Fibonacci calculator for multiple analysis types.
    """

    @staticmethod
    def calculate_fibonacci_retracements(high: float, low: float,
                                       ratios: list = None) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels.

        Args:
            high: Highest price point
            low: Lowest price point
            ratios: Custom ratios, defaults to standard Fibonacci

        Returns:
            Dict of level names and price values
        """
        if ratios is None:
            ratios = FIBONACCI_RATIOS['retracements']['fibonacci']

        levels = {}
        range_size = high - low

        for ratio in ratios:
            level_price = high - (range_size * ratio)
            level_name = f"{ratio:.3f}"
            levels[level_name] = level_price

        # Add trend identification
        levels['trend'] = 'bullish' if level_price < high else 'bearish'

        return levels

    @staticmethod
    def calculate_fibonacci_extensions(high: float, low: float, projection_point: float = None,
                                     ratios: list = None) -> Dict[str, float]:
        """
        Calculate Fibonacci extension levels.

        Args:
            high: Original swing high
            low: Original swing low
            projection_point: Point to project from (usually breakout point)
            ratios: Custom ratios for extensions

        Returns:
            Dict of extension level names and price values
        """
        if ratios is None:
            ratios = FIBONACCI_RATIOS['extensions']['fibonacci']

        if projection_point is None:
            projection_point = high

        levels = {}
        range_size = abs(high - low)

        for ratio in ratios:
            if projection_point > high:
                # Bullish extension
                level_price = high + (range_size * ratio)
            else:
                # Bearish extension
                level_price = low - (range_size * ratio)

            level_name = f"ext_{ratio:.3f}"
            levels[level_name] = level_price

        return levels

    @staticmethod
    def calculate_harmonic_patterns(high: float, low: float) -> Dict[str, Dict[str, float]]:
        """
        Calculate harmonic pattern levels (Gartley, Bat, Butterfly, etc.)

        Returns:
            Dict of pattern names with their Fibonacci levels
        """
        patterns = {}

        # Gartley Pattern
        patterns['gartley'] = {
            'x': high,
            'a': low,
            'b': high - (high - low) * 0.618,
            'c': low + (high - low) * 0.382,
            'd': low + (high - low) * 0.786
        }

        # Bat Pattern
        patterns['bat'] = {
            'x': high,
            'a': low,
            'b': high - (high - low) * 0.382,
            'c': low + (high - low) * 0.5,
            'd': low + (high - low) * 0.886
        }

        # Butterfly Pattern
        patterns['butterfly'] = {
            'x': high,
            'a': low,
            'b': high - (high - low) * 0.786,
            'c': low + (high - low) * 0.382,
            'd': low + (high - low) * 1.618
        }

        return patterns

    @staticmethod
    def find_pivot_points(prices: pd.Series, window: int = 5) -> Tuple[float, float]:
        """
        Find significant pivot points for Fibonacci analysis.

        Args:
            prices: Price series
            window: Window size for pivot detection

        Returns:
            Tuple of (swing_high, swing_low)
        """
        if len(prices) < window * 2:
            return prices.max(), prices.min()

        highs = []
        lows = []

        for i in range(window, len(prices) - window):
            current = prices.iloc[i]

            # Check if current is a local high
            is_high = True
            for j in range(max(0, i - window), min(len(prices), i + window + 1)):
                if j != i and prices.iloc[j] > current:
                    is_high = False
                    break

            # Check if current is a local low
            is_low = True
            for j in range(max(0, i - window), min(len(prices), i + window + 1)):
                if j != i and prices.iloc[j] < current:
                    is_low = False
                    break

            if is_high:
                highs.append(current)
            if is_low:
                lows.append(current)

        swing_high = max(highs) if highs else prices.max()
        swing_low = min(lows) if lows else prices.min()

        return swing_high, swing_low

def calculate_fibonacci_retracements(high: float, low: float,
                                   ratios: list = None) -> Dict[str, float]:
    """Convenience function for Fibonacci retracements"""
    return FibonacciCalculator.calculate_fibonacci_retracements(high, low, ratios)

def calculate_fibonacci_extensions(high: float, low: float, projection_point: float = None,
                                ratios: list = None) -> Dict[str, float]:
    """Convenience function for Fibonacci extensions"""
    return FibonacciCalculator.calculate_fibonacci_extensions(high, low, projection_point, ratios)

def get_fibonacci_ratios(type_name: str = 'fibonacci') -> list:
    """
    Get standard Fibonacci ratios for different analysis types.

    Args:
        type_name: 'fibonacci', 'harmonic', or ratio set name

    Returns:
        List of Fibonacci ratios
    """
    return FIBONACCI_RATIOS['retracements'].get(type_name,
                                               FIBONACCI_RATIOS['retracements']['fibonacci'])

def validate_fibonacci_levels(levels: Dict[str, float],
                            current_price: float) -> str:
    """
    Analyze current price relative to Fibonacci levels.

    Returns:
        String describing which Fibonacci level the price is at/near
    """
    tolerance = 0.001  # 0.1% tolerance

    for level_name, level_price in levels.items():
        if level_name == 'trend':
            continue

        price_ratio = abs(current_price - level_price) / current_price

        if price_ratio <= tolerance:
            return f"At Fibonacci {level_name} level"
        elif abs(current_price - level_price) / current_price <= tolerance * 2:
            if current_price > level_price:
                return f"Near Fibonacci {level_name} support"
            else:
                return f"Near Fibonacci {level_name} resistance"

    return "Not at significant Fibonacci level"

def fibonacci_projection_level(start_point: float, end_point: float,
                             projection_ratio: float) -> float:
    """
    Project Fibonacci level from a trend segment.

    Args:
        start_point: Start of trend segment
        end_point: End of trend segment
        projection_ratio: Fibonacci ratio for projection

    Returns:
        Projected price level
    """
    range_size = end_point - start_point
    return start_point + (range_size * projection_ratio)

def find_pivot_points(prices: pd.Series, window: int = 5) -> Tuple[float, float]:
    """
    Find significant pivot points for Fibonacci analysis.

    Args:
        prices: Price series
        window: Window size for pivot detection

    Returns:
        Tuple of (swing_high, swing_low)
    """
    if len(prices) < window * 2:
        return prices.max(), prices.min()

    highs = []
    lows = []

    for i in range(window, len(prices) - window):
        current = prices.iloc[i]

        # Check if current is a local high
        is_high = True
        for j in range(max(0, i - window), min(len(prices), i + window + 1)):
            if j != i and prices.iloc[j] > current:
                is_high = False
                break

        # Check if current is a local low
        is_low = True
        for j in range(max(0, i - window), min(len(prices), i + window + 1)):
            if j != i and prices.iloc[j] < current:
                is_low = False
                break

        if is_high:
            highs.append(current)
        if is_low:
            lows.append(current)

    swing_high = max(highs) if highs else prices.max()
    swing_low = min(lows) if lows else prices.min()

    return swing_high, swing_low
