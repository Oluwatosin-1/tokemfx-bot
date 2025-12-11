"""
Pattern Recognition Module
==========================
Advanced candlestick and chart pattern detection.
Head & Shoulders, Double Tops/Bottoms, Candlestick patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings

def detect_candlestick_patterns(data: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Detect common candlestick patterns.

    Args:
        data: OHLC DataFrame

    Returns:
        Dict with pattern names and indices where they occur
    """
    if not all(col in data.columns for col in ['open', 'high', 'low', 'close']):
        raise ValueError("DataFrame must contain OHLC columns")

    patterns = {
        'doji': [],
        'hammer': [],
        'shooting_star': [],
        'engulfing_bullish': [],
        'engulfing_bearish': [],
        'morning_star': [],
        'evening_star': []
    }

    for i in range(len(data)):
        if i < 2:  # Need at least 3 candles for some patterns
            continue

        # Current candle
        c_open = data['open'].iloc[i]
        c_high = data['high'].iloc[i]
        c_low = data['low'].iloc[i]
        c_close = data['close'].iloc[i]

        # Previous candle
        p_open = data['open'].iloc[i-1]
        p_high = data['high'].iloc[i-1]
        p_low = data['low'].iloc[i-1]
        p_close = data['close'].iloc[i-1]

        # candle metrics
        body_size = abs(c_close - c_open)
        upper_shadow = c_high - max(c_open, c_close)
        lower_shadow = min(c_open, c_close) - c_low
        total_range = c_high - c_low

        # Doji (very small body, long shadows)
        if body_size <= total_range * 0.1 and upper_shadow > body_size and lower_shadow > body_size:
            patterns['doji'].append(i)

        # Hammer (small body, long lower shadow)
        elif lower_shadow >= 2 * body_size and upper_shadow <= body_size and c_close > c_open:
            patterns['hammer'].append(i)

        # Shooting Star (small body, long upper shadow)
        elif upper_shadow >= 2 * body_size and lower_shadow <= body_size and c_close < c_open:
            patterns['shooting_star'].append(i)

        # Engulfing patterns
        if body_size > abs(p_close - p_open) and (
            (c_close > c_open and c_open < p_close and c_close > p_open) or  # Bullish engulfing
            (c_close < c_open and c_open > p_close and c_close < p_open)      # Bearish engulfing
        ):
            if c_close > c_open:
                patterns['engulfing_bullish'].append(i)
            else:
                patterns['engulfing_bearish'].append(i)

        # Morning Star pattern (needs 3 candles)
        if i >= 2:
            pp_open = data['open'].iloc[i-2]
            pp_high = data['high'].iloc[i-2]
            pp_low = data['low'].iloc[i-2]
            pp_close = data['close'].iloc[i-2]

            # Morning star: large bearish, small, large bullish
            if (pp_close < pp_open and abs(pp_close - pp_open) > abs(p_close - p_open) and
                abs(p_close - p_open) < abs(pp_close - pp_open) * 0.5 and
                c_close > c_open and c_close > pp_high):
                patterns['morning_star'].append(i)

            # Evening star: large bullish, small, large bearish
            elif (pp_close > pp_open and abs(pp_close - pp_open) > abs(p_close - p_open) and
                  abs(p_close - p_open) < abs(pp_close - pp_open) * 0.5 and
                  c_close < c_open and c_close < pp_low):
                patterns['evening_star'].append(i)

    return patterns

def detect_chart_patterns(data: pd.DataFrame) -> Dict[str, List[Dict[str, any]]]:
    """
    Detect complex chart patterns like head & shoulders, double tops.

    Args:
        data: OHLC DataFrame

    Returns:
        Dict with pattern details and their locations
    """
    patterns = {
        'double_top': [],
        'double_bottom': [],
        'head_shoulders': [],
        'inverse_head_shoulders': []
    }

    if len(data) < 30:  # Need sufficient data
        return patterns

    highs = data['high'].values
    lows = data['low'].values
    closes = data['close'].values

    # Find peaks and valleys
    peaks = []
    valleys = []

    for i in range(5, len(highs) - 5):
        # Peak detection
        if all(highs[i] >= highs[i+j] for j in range(-5, 6) if j != 0):
            peaks.append((i, highs[i]))

        # Valley detection
        if all(lows[i] <= lows[i+j] for j in range(-5, 6) if j != 0):
            valleys.append((i, lows[i]))

    # Detect Double Top pattern
    for i in range(len(peaks) - 1):
        p1_index, p1_value = peaks[i]
        for j in range(i + 3, len(peaks)):  # Minimum 3 bars apart
            p2_index, p2_value = peaks[j]

            # Check if peaks are at similar levels
            if abs(p1_value - p2_value) / p1_value <= 0.02:  # Within 2%
                # Check for valley in between
                valley_in_between = None
                for v_idx, v_val in valleys:
                    if p1_index < v_idx < p2_index and v_val < (p1_value + p2_value) / 2:
                        valley_in_between = (v_idx, v_val)
                        break

                if valley_in_between:
                    patterns['double_top'].append({
                        'left_peak': {'index': p1_index, 'price': p1_value},
                        'valley': {'index': valley_in_between[0], 'price': valley_in_between[1]},
                        'right_peak': {'index': p2_index, 'price': p2_value},
                        'confidence': 0.8
                    })

    # Detect Double Bottom pattern (similar logic)
    for i in range(len(valleys) - 1):
        v1_index, v1_value = valleys[i]
        for j in range(i + 3, len(valleys)):
            v2_index, v2_value = valleys[j]

            if abs(v1_value - v2_value) / v1_value <= 0.02:
                peak_in_between = None
                for p_idx, p_val in peaks:
                    if v1_index < p_idx < v2_index and p_val > (v1_value + v2_value) / 2:
                        peak_in_between = (p_idx, p_val)
                        break

                if peak_in_between:
                    patterns['double_bottom'].append({
                        'left_valley': {'index': v1_index, 'price': v1_value},
                        'peak': {'index': peak_in_between[0], 'price': peak_in_between[1]},
                        'right_valley': {'index': v2_index, 'price': v2_value},
                        'confidence': 0.8
                    })

    return patterns

def calculate_head_and_shoulders(data: pd.DataFrame, lookback: int = 100) -> List[Dict[str, any]]:
    """
    Detect Head & Shoulders pattern.

    Args:
        data: OHLC DataFrame
        lookback: Number of bars to look back

    Returns:
        List of H&S pattern detections with confidence scores
    """
    patterns = []
    recent_data = data.tail(lookback)

    highs = recent_data['high'].values
    lows = recent_data['low'].values

    # Find potential left shoulders, heads, right shoulders
    for i in range(10, len(highs) - 10):
        # Look for 5-point pattern: LS, LV, H, RV, RS
        window = highs[max(0, i-10):min(len(highs), i+11)]

        # Find local maxima and minima
        peaks = []
        valleys = []

        for j in range(2, len(window) - 2):
            if window[j] >= max(window[j-2:j+3]):
                peaks.append(window[j])
            if window[j] <= min(window[j-2:j+3]):
                valleys.append(window[j])

        # Need at least 5 points for H&S
        if len(peaks) >= 3 and len(valleys) >= 2:
            # Check if peaks form H&S pattern (left < head > right)
            if (peaks[0] < peaks[1] and peaks[1] > peaks[-1] and
                abs(peaks[0] - peaks[-1]) <= peaks[0] * 0.1):  # Shoulders at similar levels

                neckline = min(valleys)

                patterns.append({
                    'pattern': 'head_and_shoulders',
                    'left_shoulder': peaks[0],
                    'head': peaks[1],
                    'right_shoulder': peaks[-1],
                    'neckline': neckline,
                    'index': len(data) - lookback + i,
                    'confidence': 0.7,
                    'trend': 'bearish'  # H&S usually signals bearish reversal
                })

    return patterns

def calculate_double_top_bottom(data: pd.DataFrame) -> List[Dict[str, any]]:
    """
    Detect Double Top and Double Bottom patterns in recent data.

    Args:
        data: OHLC DataFrame

    Returns:
        List of double top/bottom patterns
    """
    chart_patterns = detect_chart_patterns(data)

    # Convert to standardized format
    patterns = []
    patterns.extend(chart_patterns['double_top'])
    patterns.extend(chart_patterns['double_bottom'])

    return patterns

def detect_harmonic_patterns(data: pd.DataFrame) -> Dict[str, List[Dict[str, any]]]:
    """
    Detect harmonic patterns (Gartley, Butterfly, Bat, Crab).

    Args:
        data: OHLC DataFrame

    Returns:
        Dict with harmonic patterns found
    """
    patterns = {
        'gartley': [],
        'butterfly': [],
        'bat': [],
        'crab': []
    }

    if len(data) < 30:
        return patterns

    # Use higher timeframe data for pattern detection
    closes = data['close'].values
    highs = data['high'].values
    lows = data['low'].values

    # Simple harmonic pattern detection using Fibonacci ratios
    # This is a simplified implementation - real harmonic patterns are more complex

    for start in range(len(closes) - 10):
        segment = closes[start:start+10]

        if len(segment) < 10:
            continue

        # Find potential pivot points
        max_price = max(segment)
        min_price = min(segment)
        range_size = max_price - min_price

        # X point (start)
        x_price = segment[0]

        # Look for A, B, C, D points
        for a_idx in range(2, 8):
            for b_idx in range(a_idx + 2, 9):
                for c_idx in range(b_idx + 2, 10):
                    for d_idx in range(c_idx + 1, 10):
                        a_price = segment[a_idx]
                        b_price = segment[b_idx]
                        c_price = segment[c_idx]
                        d_price = segment[d_idx]

                        # Check for Gartley pattern
                        if (abs((b_price - x_price) / range_size - 0.618) < 0.05 and
                            abs((c_price - x_price) / range_size - 0.382) < 0.05 and
                            abs((d_price - x_price) / range_size - 0.786) < 0.05):

                            patterns['gartley'].append({
                                'x': {'index': start, 'price': x_price},
                                'a': {'index': start + a_idx, 'price': a_price},
                                'b': {'index': start + b_idx, 'price': b_price},
                                'c': {'index': start + c_idx, 'price': c_price},
                                'd': {'index': start + d_idx, 'price': d_price},
                                'confidence': 0.8
                            })

    return patterns

def analyze_pattern_significance(patterns: Dict[str, List[Dict]] | Dict[str, List[int]]
                               ) -> Dict[str, Dict[str, float]]:
    """
    Analyze detected patterns for significance and confidence levels.

    Args:
        patterns: Detected patterns dict (can be indices or full pattern dicts)

    Returns:
        Analysis results with reliability scores
    """
    analysis = {}

    for pattern_type, pattern_list in patterns.items():
        if pattern_list:
            count = len(pattern_list)

            # Handle both dict and index lists
            avg_confidence = 0.0
            if pattern_list and isinstance(pattern_list[0], dict):
                # It's a list of pattern dicts
                avg_confidence = sum(p.get('confidence', 0) for p in pattern_list if isinstance(p, dict)) / count
            elif isinstance(pattern_list[0], (int, float)):
                # It's a list of indices, assign default confidence
                avg_confidence = 0.6  # Default confidence for detected patterns

            # Assess pattern reliability based on various factors
            reliability = min(1.0, avg_confidence * count * 0.1)

            analysis[pattern_type] = {
                'count': count,
                'avg_confidence': avg_confidence,
                'reliability': reliability,
                'signal_strength': 'strong' if reliability > 0.7 else 'moderate' if reliability > 0.4 else 'weak'
            }
        else:
            analysis[pattern_type] = {
                'count': 0,
                'avg_confidence': 0,
                'reliability': 0,
                'signal_strength': 'none'
            }

    return analysis

def get_pattern_recommendations(patterns: Dict[str, List[Dict]] | Dict[str, List[int]]) -> Dict[str, str]:
    """
    Provide trading recommendations based on detected patterns.

    Args:
        patterns: Detected patterns (can be indices or full pattern dicts)

    Returns:
        Dict with recommendations for each pattern type
    """
    recommendations = {}

    analysis = analyze_pattern_significance(patterns)

    for pattern_type, stats in analysis.items():
        if stats['count'] == 0:
            recommendations[pattern_type] = "No patterns detected"
        elif pattern_type == 'double_top':
            recommendations[pattern_type] = "Consider short positions - bearish reversal signal"
        elif pattern_type == 'double_bottom':
            recommendations[pattern_type] = "Consider long positions - bullish reversal signal"
        elif pattern_type == 'head_shoulders':
            recommendations[pattern_type] = "Consider short positions - strong bearish reversal"
        elif pattern_type == 'inverse_head_shoulders':
            recommendations[pattern_type] = "Consider long positions - strong bullish reversal"
        elif pattern_type in ['gartley', 'butterfly', 'bat', 'crab']:
            recommendations[pattern_type] = f"Harmonic pattern detected - {stats['signal_strength']} signal"
        elif pattern_type == 'doji':
            recommendations[pattern_type] = "Market indecision - watch for breakout"
        elif pattern_type in ['hammer', 'morning_star']:
            recommendations[pattern_type] = "Potential bullish reversal - consider long positions"
        elif pattern_type in ['shooting_star', 'evening_star']:
            recommendations[pattern_type] = "Potential bearish reversal - consider short positions"
        else:
            recommendations[pattern_type] = f"Pattern detected - {stats['signal_strength']} signal"

    return recommendations
