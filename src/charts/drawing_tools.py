"""
Drawing Tools Module
====================
Professional drawing tools for technical analysis.
Trend lines, Support/Resistance, Channels, Fibonacci Arcs.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go

def draw_trend_lines(data: pd.DataFrame) -> Dict[str, List[Tuple[float, float]]]:
    """
    Automatically draw trend lines based on price action.

    Args:
        data: OHLC DataFrame

    Returns:
        Dict with trend lines (resistance/support lines)
    """
    if not all(col in data.columns for col in ['high', 'low', 'close']):
        raise ValueError("DataFrame must contain 'high', 'low', 'close' columns")

    highs = data['high'].values
    lows = data['low'].values
    closes = data['close'].values

    trend_lines = {
        'resistance_lines': [],
        'support_lines': [],
        'channel_lines': []
    }

    # Simple trend line detection using linear regression on recent highs/lows
    lookback = min(50, len(data))

    # Identify potential resistance points (local highs)
    resistance_points = []
    support_points = []

    for i in range(2, len(highs) - 2):
        # Local high: higher than surrounding bars
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistance_points.append((i, highs[i]))

        # Local low: lower than surrounding bars
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            support_points.append((i, lows[i]))

    # Calculate trend lines from recent significant points
    recent_highs = [(i, h) for i, h in resistance_points if i >= len(highs) - lookback]
    recent_lows = [(i, l) for i, l in support_points if i >= len(lows) - lookback]

    # Draw resistance line from recent highs
    if len(recent_highs) >= 2:
        x_vals = [point[0] for point in recent_highs]
        y_vals = [point[1] for point in recent_highs]

        # Simple linear fit
        if len(x_vals) > 1:
            slope = np.polyfit(x_vals, y_vals, 1)[0]
            intercept = np.polyfit(x_vals, y_vals, 1)[1]

            trend_lines['resistance_lines'].append({
                'slope': slope,
                'intercept': intercept,
                'start_x': min(x_vals),
                'end_x': max(x_vals)
            })

    # Draw support line from recent lows
    if len(recent_lows) >= 2:
        x_vals = [point[0] for point in recent_lows]
        y_vals = [point[1] for point in recent_lows]

        if len(x_vals) > 1:
            slope = np.polyfit(x_vals, y_vals, 1)[0]
            intercept = np.polyfit(x_vals, y_vals, 1)[1]

            trend_lines['support_lines'].append({
                'slope': slope,
                'intercept': intercept,
                'start_x': min(x_vals),
                'end_x': max(x_vals)
            })

    return trend_lines

def draw_support_resistance(data: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
    """
    Identify key support and resistance levels.

    Args:
        data: OHLC DataFrame
        window: Lookback window for level identification

    Returns:
        Dict with support and resistance levels
    """
    if not all(col in data.columns for col in ['high', 'low']):
        raise ValueError("DataFrame must contain 'high', 'low' columns")

    recent_highs = data['high'].rolling(window=window).max()
    recent_lows = data['low'].rolling(window=window).min()

    # Identify significant levels
    support_levels = []
    resistance_levels = []

    # Simple approach: use recent swing points
    for i in range(window, len(data)):
        current_high = data['high'].iloc[i]
        current_low = data['low'].iloc[i]

        # Potential resistance: current high equals or exceeds recent max
        if current_high >= recent_highs.iloc[i]:
            resistance_levels.append(current_high)

        # Potential support: current low equals or falls below recent min
        if current_low <= recent_lows.iloc[i]:
            support_levels.append(current_low)

    # Remove duplicates and sort
    support_levels = sorted(list(set([round(level, 5) for level in support_levels])))
    resistance_levels = sorted(list(set([round(level, 5) for level in resistance_levels])))

    return {
        'support_levels': support_levels[-5:],  # Last 5 levels
        'resistance_levels': resistance_levels[-5:]
    }

def draw_channels(data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Draw price channels (parallel trend lines).

    Args:
        data: OHLC DataFrame

    Returns:
        Channel definitions
    """
    trend_lines = draw_trend_lines(data)

    channels = {
        'ascending_channel': {},
        'descending_channel': {}
    }

    if trend_lines['support_lines'] and trend_lines['resistance_lines']:
        support_line = trend_lines['support_lines'][0] if trend_lines['support_lines'] else None
        resistance_line = trend_lines['resistance_lines'][0] if trend_lines['resistance_lines'] else None

        if support_line and resistance_line:
            # Calculate channel width
            start_x = max(support_line['start_x'], resistance_line['start_x'])
            end_x = min(support_line['end_x'], resistance_line['end_x'])

            if start_x < end_x:
                # Upper channel line (parallel to support)
                channel_width = (resistance_line['intercept'] + resistance_line['slope'] * end_x) - \
                               (support_line['intercept'] + support_line['slope'] * end_x)

                channels['ascending_channel'] = {
                    'upper_slope': support_line['slope'],
                    'upper_intercept': support_line['intercept'] + channel_width,
                    'lower_slope': support_line['slope'],
                    'lower_intercept': support_line['intercept'],
                    'start_x': start_x,
                    'end_x': end_x
                }

                channels['descending_channel'] = {
                    'upper_slope': support_line['slope'],
                    'upper_intercept': resistance_line['intercept'],
                    'lower_slope': support_line['slope'],
                    'lower_intercept': resistance_line['intercept'] - channel_width,
                    'start_x': start_x,
                    'end_x': end_x
                }

    return channels

def draw_fibonacci_arcs(high: float, low: float, num_arcs: int = 3
                       ) -> Dict[str, Dict[str, float]]:
    """
    Draw Fibonacci arcs (curved support/resistance levels).

    Args:
        high: Swing high price
        low: Swing low price
        num_arcs: Number of arcs to draw

    Returns:
        Arc definitions
    """
    range_size = high - low
    midpoint = low + (range_size * 0.618)  # Golden ratio midpoint

    arcs = {}
    fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]

    for i, ratio in enumerate(fib_ratios[:num_arcs]):
        radius = range_size * ratio

        arcs[f'arc_{i+1}'] = {
            'center_x': len(range(ratio)),  # Placeholder - would need actual x-coordinates
            'center_y': midpoint,
            'radius': radius,
            'fibonacci_ratio': ratio
        }

    return arcs

def add_drawing_tools(fig: go.Figure, drawing_tools: Dict[str, any]) -> go.Figure:
    """
    Add all drawing tools (trend lines, channels, etc.) to chart.

    Args:
        fig: Plotly figure
        drawing_tools: Dict containing different drawing tool definitions

    Returns:
        Updated figure with drawing tools
    """
    # Add trend lines
    if 'trend_lines' in drawing_tools:
        trend_data = drawing_tools['trend_lines']

        # Support lines
        if 'support_lines' in trend_data:
            for support in trend_data['support_lines']:
                x_range = np.linspace(support['start_x'], support['end_x'], 100)
                y_line = support['slope'] * x_range + support['intercept']

                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=y_line,
                    mode='lines',
                    name='Support Line',
                    line=dict(color='green', width=2, dash='solid'),
                    showlegend=True
                ))

        # Resistance lines
        if 'resistance_lines' in trend_data:
            for resistance in trend_data['resistance_lines']:
                x_range = np.linspace(resistance['start_x'], resistance['end_x'], 100)
                y_line = resistance['slope'] * x_range + resistance['intercept']

                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=y_line,
                    mode='lines',
                    name='Resistance Line',
                    line=dict(color='red', width=2, dash='solid'),
                    showlegend=True
                ))

    # Add channels
    if 'channels' in drawing_tools:
        channels = drawing_tools['channels']

        for channel_name, channel in channels.items():
            if channel:  # Only if channel was calculated
                x_range = np.linspace(channel['start_x'], channel['end_x'], 100)

                # Upper channel line
                upper_y = channel['upper_slope'] * x_range + channel['upper_intercept']
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=upper_y,
                    mode='lines',
                    name=f'{channel_name} Upper',
                    line=dict(color='purple', width=2, dash='dash'),
                    showlegend=True
                ))

                # Lower channel line
                lower_y = channel['lower_slope'] * x_range + channel['lower_intercept']
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=lower_y,
                    mode='lines',
                    name=f'{channel_name} Lower',
                    line=dict(color='purple', width=2, dash='dash'),
                    showlegend=True
                ))

    return fig

def create_full_analysis_chart(data: pd.DataFrame, instrument: str) -> Tuple[go.Figure, Dict[str, any]]:
    """
    Create comprehensive analysis chart with all available tools.

    Args:
        data: OHLC DataFrame
        instrument: Trading instrument name

    Returns:
        Tuple of (figure, analysis_tools_dict)
    """
    from .indicators import calculate_all_indicators
    from .fibonacci import find_pivot_points, calculate_fibonacci_retracements

    # Start with basic price chart
    fig = go.Figure()

    # Calculate all indicators
    indicators = calculate_all_indicators(data)

    # Find pivot points for Fibonacci
    swing_high, swing_low = find_pivot_points(data['close'])

    # Calculate Fibonacci levels
    fib_levels = calculate_fibonacci_retracements(swing_high, swing_low)

    # Calculate drawing tools
    trend_lines = draw_trend_lines(data)
    sr_levels = draw_support_resistance(data)
    channels = draw_channels(data)

    # Compile analysis tools
    analysis_tools = {
        'indicators': indicators,
        'fibonacci_levels': fib_levels,
        'trend_lines': trend_lines,
        'support_resistance': sr_levels,
        'channels': channels
    }

    # Create multi-row chart
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxis=True,
        vertical_spacing=0.02,
        row_width=[0.5, 0.25, 0.25],
        subplot_titles=('Price & Indicators', 'MACD Oscillator', 'RSI Momentum')
    )

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index if hasattr(data, 'index') else range(len(data)),
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name=instrument
    ), row=1, col=1)

    # Add Bollinger Bands
    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['volatility']['bollinger_upper'],
        mode='lines',
        name='BB Upper',
        line=dict(color='gray', dash='dash')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['volatility']['bollinger_lower'],
        mode='lines',
        name='BB Lower',
        fill='tonexty',
        line=dict(color='gray', dash='dash')
    ), row=1, col=1)

    # Add moving averages
    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['trend']['sma_20'],
        mode='lines',
        name='SMA 20',
        line=dict(color='blue', width=1.5)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['trend']['sma_50'],
        mode='lines',
        name='SMA 50',
        line=dict(color='orange', width=1.5)
    ), row=1, col=1)

    # MACD on row 2
    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['oscillators']['macd'],
        mode='lines',
        name='MACD',
        line=dict(color='blue')
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['oscillators']['macd_signal'],
        mode='lines',
        name='Signal',
        line=dict(color='red')
    ), row=2, col=1)

    # RSI on row 3
    fig.add_trace(go.Scatter(
        x=data.index,
        y=indicators['momentum']['rsi_14'],
        mode='lines',
        name='RSI',
        line=dict(color='purple')
    ), row=3, col=1)

    # Add RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # Add Fibonacci levels as horizontal lines
    for level_name, level_price in fib_levels.items():
        if level_name != 'trend':
            fig.add_hline(y=level_price, line_dash="dot", line_color="gold",
                         annotation_text=f"Fib {level_name}", row=1, col=1)

    fig.update_layout(
        title=f'{instrument} - Complete Technical Analysis',
        height=900,
        template='plotly_white',
        hovermode='x unified'
    )

    return fig, analysis_tools

# Helper function for subplot creation (import from chart_utils but avoid circular import)
def make_subplots(*args, **kwargs):
    """Proxy for plotly.subplots.make_subplots to avoid circular imports"""
    return go.Figure()  # Placeholder - would use actual make_subplots in real implementation
