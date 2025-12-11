"""
Interactive Chart Utilities for TokemFX
========================================
TradingView-style charts with technical indicators and interactive features.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
import datetime

def create_price_chart(df: pd.DataFrame,
                      instrument: str,
                      timeframe: str,
                      show_volume: bool = True,
                      add_fibonacci: bool = False,
                      fib_levels: Optional[Dict[str, float]] = None,
                      height: int = 600,
                      data_source: str = "live") -> go.Figure:
    """
    Create interactive price chart with OHLC candles and volume.

    Args:
        df: OHLC data with columns ['time', 'open', 'high', 'low', 'close', 'volume']
        instrument: Trading instrument name
        timeframe: Chart timeframe (1M, 5M, 1H, etc.)
        show_volume: Include volume subplot
        add_fibonacci: Add Fibonacci level annotations
        fib_levels: Fibonacci levels to display
        height: Chart height in pixels
        data_source: Source of data ('live', 'cached', 'demo')

    Returns:
        Plotly figure object
    """
    # ── Get REAL data if empty DataFrame provided ───────────────────────────
    if df.empty:
        try:
            # Import the new trading modules to get real data
            from src.trading.execution.broker import DerivBroker
            from src.trading.execution.data_handler import DataHandler

            broker = DerivBroker()
            if broker.connect_and_authenticate():
                data_handler = DataHandler(broker=broker)
                # Convert timeframe to granularity
                granularity = timeframe.upper()
                if timeframe == "1M":
                    granularity = "M1"
                elif timeframe == "5M":
                    granularity = "M5"
                elif timeframe == "1H":
                    granularity = "H1"

                # Get real data for the instrument
                df = data_handler.get_latest(instrument, granularity, count=500)
                data_source = "live"
            else:
                # Fallback to demo data if no connection
                df = get_demo_chart_data(instrument, timeframe)
                data_source = "demo"
        except ImportError:
            # Fallback to demo data if modules not available
            df = get_demo_chart_data(instrument, timeframe)
            data_source = "demo"

    if df.empty:
        # Return empty chart with connection message
        fig = go.Figure()
        fig.add_annotation(
            text=f"No price data available for {instrument}\nSource: {data_source}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title=f"{instrument} - {timeframe} ({data_source.upper()})",
            height=height,
            template='plotly_white'
        )
        return fig

    # ── Validate data format ────────────────────────────────────────────────
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        # Check if data is indexed by time
        if isinstance(df.index, pd.DatetimeIndex):
            # Data might be in index format
            if not df.index.name and 'time' not in df.columns:
                df = df.reset_index()
                df.rename(columns={'index': 'time'}, inplace=True)

        # Still invalid? Return error chart
        if not all(col in df.columns for col in required_cols):
            fig = go.Figure()
            fig.add_annotation(
                text="Invalid data format - missing OHLC columns",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            return fig

    # ── Normalize time column ──────────────────────────────────────────────
    if 'time' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        # Use index as time if no time column
        df = df.reset_index()
        df.rename(columns={'index': 'time'}, inplace=True)

    if 'time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['time']):
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])

    # ── Create chart layout ────────────────────────────────────────────────
    if show_volume and 'volume' in df.columns and not df['volume'].empty:
        fig = make_subplots(
            rows=2, cols=1,
            vertical_spacing=0.02,
            row_width=[0.7, 0.3],
            subplot_titles=(f'{instrument} - {timeframe} ({data_source.upper()})', 'Volume')
        )
        fig.update_xaxes(matches='x')
        has_volume = True
    else:
        fig = go.Figure()
        fig.update_layout(title=f'{instrument} - {timeframe} ({data_source.upper()})')
        has_volume = False

    # Add candlestick chart
    candlestick = go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=f'{instrument}',
        increasing_line_color='#00C853',  # Green for bullish
        decreasing_line_color='#D32F2F',  # Red for bearish
        increasing_fillcolor='#00C853',
        decreasing_fillcolor='#D32F2F',
        line=dict(width=1),
    )

    if has_volume:
        fig.add_trace(candlestick, row=1, col=1)
    else:
        fig.add_trace(candlestick)

    # Add Fibonacci retracement levels
    if add_fibonacci and fib_levels:
        _add_fibonacci_lines(fig, fib_levels, has_volume)

    # Add volume bars
    if has_volume and 'volume' in df.columns:
        volume_colors = ['#00C853' if c >= o else '#D32F2F'
                        for c, o in zip(df['close'], df['open'])]

        volume_bar = go.Bar(
            x=df['time'],
            y=df['volume'],
            name='Volume',
            marker_color=volume_colors,
            opacity=0.7
        )
        fig.add_trace(volume_bar, row=2, col=1)

    # Update layout
    fig.update_layout(
        title=f'{instrument} - {timeframe} Price Chart',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,  # Hide rangeslider for cleaner look
        height=height,
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
    )

    # Update axes
    fig.update_xaxes(
        type='date',
        showgrid=True,
        gridcolor='lightgray',
        tickformat='%H:%M\n%b %d',
        tickangle=0,
    )

    if has_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1, showgrid=True, gridcolor='lightgray')

    return fig

def add_fibonacci_levels(fig: go.Figure,
                        fib_levels: Dict[str, float],
                        x_range: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
                        has_volume: bool = False) -> go.Figure:
    """
    Add Fibonacci level lines to existing chart.

    Args:
        fig: Plotly figure to modify
        fib_levels: Dictionary of Fibonacci levels
        x_range: Date range for Fibonacci lines
        has_volume: Whether chart has volume subplot

    Returns:
        Modified figure with Fibonacci lines
    """
    if not fib_levels:
        return fig

    # Default x-range if not provided
    if x_range is None:
        if hasattr(fig, 'data') and fig.data:
            fig.data.sort(key=lambda trace: len(trace.x) if hasattr(trace, 'x') else 0, reverse=True)
            x_range = (fig.data[0].x.min(), fig.data[0].x.max())
        else:
            x_range = (datetime.datetime.now() - datetime.timedelta(days=1),
                      datetime.datetime.now())

    # Define colors for different Fibonacci levels
    fib_colors = {
        '0.236': '#FF9800',  # Orange
        '0.382': '#2196F3',  # Blue
        '0.500': '#9C27B0',  # Purple
        '0.618': '#4CAF50',  # Green
        '0.786': '#FF5722',  # Deep Orange
        '1.000': '#795548',  # Brown
        '1.272': '#607D8B',  # Blue Gray
        '1.618': '#E91E63',  # Pink
    }

    row = 1 if has_volume else None

    for level_name, level_price in fib_levels.items():
        if level_name == 'trend':
            continue

        # Get color or use default
        color = fib_colors.get(level_name, '#9E9E9E')

        # Add horizontal line
        fig.add_hline(
            y=level_price,
            line_dash="dot",
            line_color=color,
            line_width=1,
            row=row,
            annotation_text=f"Fib {level_name}",
            annotation_position="top left",
            annotation_font_color=color,
            annotation_font_size=10
        )

        # Add scatter point for level visibility
        fig.add_trace(
            go.Scatter(
                x=[x_range[0]],  # Just show at start
                y=[level_price],
                mode='markers',
                marker=dict(size=1, color=color),
                showlegend=False,
                hoverinfo='text',
                hovertext=f"Fibonacci {level_name}: {level_price:.5f}",
            ),
            row=row,
            col=1
        )

    return fig

def _add_fibonacci_lines(fig: go.Figure, fib_levels: Dict[str, float], has_volume: bool):
    """Helper function to add Fibonacci lines directly to chart traces"""
    # This is called from create_price_chart
    add_fibonacci_levels(fig, fib_levels, has_volume=has_volume)

def create_multi_timeframe_chart(df_1m: pd.DataFrame,
                                df_5m: pd.DataFrame = None,
                                df_1h: pd.DataFrame = None,
                                instrument: str = "INSTRUMENT",
                                height: int = 800) -> go.Figure:
    """
    Create multi-timeframe chart showing different intervals.

    Args:
        df_1m: 1-minute OHLC data
        df_5m: 5-minute OHLC data (optional)
        df_1h: 1-hour OHLC data (optional)
        instrument: Trading instrument name
        height: Chart height in pixels

    Returns:
        Multi-timeframe interactive chart
    """
    fig = go.Figure()

    # Add 1-minute candlesticks
    if not df_1m.empty:
        candlestick_1m = go.Candlestick(
            x=df_1m['time'] if pd.api.types.is_datetime64_any_dtype(df_1m['time']) else pd.to_datetime(df_1m['time']),
            open=df_1m['open'],
            high=df_1m['high'],
            low=df_1m['low'],
            close=df_1m['close'],
            name='1M',
            increasing_line_color='#C8E6C9',
            decreasing_line_color='#FFCDD2',
            opacity=0.7,
        )
        fig.add_trace(candlestick_1m)

    # Add 5-minute as overlay (if available)
    if df_5m is not None and not df_5m.empty:
        candlestick_5m = go.Candlestick(
            x=df_5m['time'] if pd.api.types.is_datetime64_any_dtype(df_5m['time']) else pd.to_datetime(df_5m['time']),
            open=df_5m['open'],
            high=df_5m['high'],
            low=df_5m['low'],
            close=df_5m['close'],
            name='5M Overlay',
            increasing_line_color='#00C853',
            decreasing_line_color='#D32F2F',
            line_width=2,
        )
        fig.add_trace(candlestick_5m)

    # Update layout
    fig.update_layout(
        title=f'{instrument} - Multi-Timeframe Analysis',
        yaxis_title='Price',
        height=height,
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
    )

    fig.update_xaxes(
        type='date',
        rangeslider_visible=True,
        gridcolor='lightgray',
        tickformat='%H:%M\n%b %d',
    )

    return fig

def get_chart_theme_colors(theme: str = 'light') -> Dict[str, str]:
    """
    Get color scheme for different chart themes.

    Args:
        theme: 'light', 'dark', 'tradingview'

    Returns:
        Dictionary of color values
    """
    themes = {
        'light': {
            'background': 'white',
            'grid': 'lightgray',
            'bullish': '#00C853',
            'bearish': '#D32F2F',
            'text': '#333333',
        },
        'dark': {
            'background': '#1a1a1a',
            'grid': '#333333',
            'bullish': '#4CAF50',
            'bearish': '#F44336',
            'text': '#FFFFFF',
        },
        'tradingview': {
            'background': '#181a20',
            'grid': '#2a2e39',
            'bullish': '#03C988',
            'bearish': '#FF4A93',
            'text': '#D1D4DC',
        }
    }

    return themes.get(theme, themes['light'])

def export_chart_to_html(fig: go.Figure, filename: str, include_plotlyjs: bool = True):
    """
    Export chart to standalone HTML file.

    Args:
        fig: Plotly figure to export
        filename: Output filename (without .html extension)
        include_plotlyjs: Include Plotly.js library (makes file larger)
    """
    html_file = f"{filename}.html"
    fig.write_html(html_file, include_plotlyjs=include_plotlyjs, full_html=True)
    return html_file

def detect_pivot_points(df: pd.DataFrame,
                       left_bars: int = 5,
                       right_bars: int = 5,
                       pivot_type: str = "both") -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Detect pivot points (HH, HL, LH, LL) in price data.

    Args:
        df: DataFrame with OHLC data
        left_bars: Bars to look left of pivot
        right_bars: Bars to look right of pivot
        pivot_type: "both", "high", or "low"

    Returns:
        Tuple of (high_pivot_points, low_pivot_points) as [(index, price), ...]
    """
    if not all(col in df.columns for col in ['high', 'low']):
        raise ValueError("DataFrame must contain 'high' and 'low' columns")

    high_pivots = []
    low_pivots = []

    for i in range(left_bars, len(df) - right_bars):
        # Check for high pivot (Higher High)
        if pivot_type in ["both", "high"]:
            is_high_pivot = True
            for j in range(i - left_bars, i + right_bars + 1):
                if j != i and df.iloc[j]['high'] >= df.iloc[i]['high']:
                    is_high_pivot = False
                    break
            if is_high_pivot:
                high_pivots.append((i, df.iloc[i]['high']))

        # Check for low pivot (Lower Low)
        if pivot_type in ["both", "low"]:
            is_low_pivot = True
            for j in range(i - left_bars, i + right_bars + 1):
                if j != i and df.iloc[j]['low'] <= df.iloc[i]['low']:
                    is_low_pivot = False
                    break
            if is_low_pivot:
                low_pivots.append((i, df.iloc[i]['low']))

    return high_pivots, low_pivots

def detect_hhll_patterns(high_pivots: List[Tuple[int, float]],
                         low_pivots: List[Tuple[int, float]]) -> Dict[str, List]:
    """
    Detect HH/HL/LH/LL patterns from pivot points.

    Args:
        high_pivots: List of (index, high_price) tuples
        low_pivots: List of (index, low_price) tuples

    Returns:
        Dict with pattern lists
    """
    patterns = {
        'hh': [],  # Higher Highs
        'hl': [],  # Higher Lows
        'lh': [],  # Lower Highs
        'll': []   # Lower Lows
    }

    # Sort pivots by index
    high_pivots.sort(key=lambda x: x[0])
    low_pivots.sort(key=lambda x: x[0])

    # Detect Higher Highs (HH)
    for i in range(1, len(high_pivots)):
        prev_high = high_pivots[i-1][1]
        curr_high = high_pivots[i][1]
        if curr_high > prev_high:
            patterns['hh'].append({
                'start': high_pivots[i-1],
                'end': high_pivots[i],
                'trend': 'bullish'
            })

    # Detect Lower Highs (LH)
    for i in range(1, len(high_pivots)):
        prev_high = high_pivots[i-1][1]
        curr_high = high_pivots[i][1]
        if curr_high < prev_high:
            patterns['lh'].append({
                'start': high_pivots[i-1],
                'end': high_pivots[i],
                'trend': 'bearish'
            })

    # Detect Higher Lows (HL)
    for i in range(1, len(low_pivots)):
        prev_low = low_pivots[i-1][1]
        curr_low = low_pivots[i][1]
        if curr_low > prev_low:
            patterns['hl'].append({
                'start': low_pivots[i-1],
                'end': low_pivots[i],
                'trend': 'bullish'
            })

    # Detect Lower Lows (LL)
    for i in range(1, len(low_pivots)):
        prev_low = low_pivots[i-1][1]
        curr_low = low_pivots[i][1]
        if curr_low < prev_low:
            patterns['ll'].append({
                'start': low_pivots[i-1],
                'end': low_pivots[i],
                'trend': 'bearish'
            })

    return patterns

def create_hhll_annotated_chart(df: pd.DataFrame,
                               instrument: str,
                               timeframe: str,
                               show_patterns: bool = True,
                               left_bars: int = 5,
                               right_bars: int = 5,
                               height: int = 600) -> go.Figure:
    """
    Create price chart with HHLL pattern annotations.

    Args:
        df: OHLC data
        instrument: Trading instrument name
        timeframe: Chart timeframe
        show_patterns: Whether to show HHLL patterns
        left_bars: Bars for pivot detection
        right_bars: Bars for pivot detection
        height: Chart height

    Returns:
        Annotated Plotly figure
    """
    # Create base price chart
    fig = create_price_chart(df, instrument, timeframe, height=height)

    if not show_patterns:
        return fig

    # Detect pivot points
    high_pivots, low_pivots = detect_pivot_points(df, left_bars, right_bars)

    # Detect HHLL patterns
    patterns = detect_hhll_patterns(high_pivots, low_pivots)

    # Convert indices to timestamps for plotting
    time_index = df.index if hasattr(df.index, 'values') else range(len(df))

    # Add high pivots (triangles pointing up)
    if high_pivots:
        high_indices = [p[0] for p in high_pivots]
        high_prices = [p[1] for p in high_pivots]
        if len(time_index) > max(high_indices):
            high_times = [time_index[i] for i in high_indices]

            fig.add_trace(go.Scatter(
                x=high_times,
                y=high_prices,
                mode='markers',
                marker=dict(symbol='triangle-up', size=10, color='red'),
                name='High Pivot',
                showlegend=True,
                hovertemplate='High Pivot: %{y:.5f}<extra></extra>'
            ))

    # Add low pivots (triangles pointing down)
    if low_pivots:
        low_indices = [p[0] for p in low_pivots]
        low_prices = [p[1] for p in low_pivots]
        if len(time_index) > max(low_indices):
            low_times = [time_index[i] for i in low_indices]

            fig.add_trace(go.Scatter(
                x=low_times,
                y=low_prices,
                mode='markers',
                marker=dict(symbol='triangle-down', size=10, color='green'),
                name='Low Pivot',
                showlegend=True,
                hovertemplate='Low Pivot: %{y:.5f}<extra></extra>'
            ))

    # Add pattern lines
    pattern_colors = {
        'hh': 'green',      # Higher Highs - bullish
        'hl': 'lightgreen', # Higher Lows - bullish
        'lh': 'red',        # Lower Highs - bearish
        'll': 'pink'        # Lower Lows - bearish
    }

    pattern_names = {
        'hh': 'Higher High (HH)',
        'hl': 'Higher Low (HL)',
        'lh': 'Lower High (LH)',
        'll': 'Lower Low (LL)'
    }

    for pattern_type, pattern_list in patterns.items():
        if not pattern_list:
            continue

        for i, pattern in enumerate(pattern_list):
            start_idx, start_price = pattern['start']
            end_idx, end_price = pattern['end']

            if start_idx < len(time_index) and end_idx < len(time_index):
                fig.add_trace(go.Scatter(
                    x=[time_index[start_idx], time_index[end_idx]],
                    y=[start_price, end_price],
                    mode='lines',
                    line=dict(color=pattern_colors[pattern_type], width=2, dash='dot'),
                    name=f'{pattern_names[pattern_type]} #{i+1}',
                    showlegend=i == 0,  # Only show legend for first instance
                    hovertemplate=f'{pattern_names[pattern_type]}: %{y:.5f}<extra></extra>'
                ))

    # Add pattern summary to layout
    total_patterns = sum(len(patterns) for patterns in patterns.values())
    pattern_summary = f"Found {len(high_pivots)} high pivots, {len(low_pivots)} low pivots, {total_patterns} HHLL patterns"

    fig.update_layout(
        title=f'{instrument} - {timeframe} HHLL Analysis<br><sup>{pattern_summary}</sup>',
        annotations=[
            dict(
                text="🟢 Higher Highs (HH), 🔴 Lower Highs (LH)",
                xref="paper", yref="paper",
                x=0, y=1.05,
                showarrow=False,
                font=dict(size=10)
            ),
            dict(
                text="🟢 Higher Lows (HL), 🔴 Lower Lows (LL)",
                xref="paper", yref="paper",
                x=0, y=1.02,
                showarrow=False,
                font=dict(size=10)
            )
        ]
    )

    return fig

def add_technical_indicators_to_chart(fig: go.Figure,
                                    df: pd.DataFrame,
                                    indicators: List[str] = None) -> go.Figure:
    """
    Add technical indicators to an existing chart.

    Args:
        fig: Plotly figure
        df: DataFrame with OHLC data
        indicators: List of indicators to add

    Returns:
        Updated figure with indicators
    """
    if indicators is None:
        indicators = ['sma_20', 'sma_50', 'rsi_14']

    try:
        from .indicators import calculate_all_indicators
        indicator_data = calculate_all_indicators(df)

        # Add moving averages
        if 'sma_20' in indicators and 'trend' in indicator_data:
            sma_20 = indicator_data['trend']['sma_20']
            fig.add_trace(go.Scatter(
                x=df.index,
                y=sma_20.values,
                mode='lines',
                name='SMA 20',
                line=dict(color='blue', width=1.5)
            ))

        if 'sma_50' in indicators and 'trend' in indicator_data:
            sma_50 = indicator_data['trend']['sma_50']
            fig.add_trace(go.Scatter(
                x=df.index,
                y=sma_50.values,
                mode='lines',
                name='SMA 50',
                line=dict(color='orange', width=1.5)
            ))

        # Add RSI subplot
        if 'rsi_14' in indicators and 'momentum' in indicator_data:
            rsi_data = indicator_data['momentum']['rsi_14']

            # Create subplot for RSI
            from plotly.subplots import make_subplots

            # Recreate figure with RSI subplot
            fig_new = make_subplots(
                rows=2, cols=1,
                vertical_spacing=0.02,
                subplot_titles=('Price', 'RSI (14)'),
                row_width=[0.7, 0.3]
            )
            # Manually link x-axes for compatibility
            fig_new.update_xaxes(matches='x')

            # Copy existing traces to new figure
            for trace in fig.data:
                fig_new.add_trace(trace, row=1, col=1)

            # Add RSI
            fig_new.add_trace(go.Scatter(
                x=df.index,
                y=rsi_data.values,
                mode='lines',
                name='RSI (14)',
                line=dict(color='purple', width=1.5)
            ), row=2, col=1)

            # Add RSI reference lines
            fig_new.add_hline(y=70, line_dash='dash', line_color='red', row=2, col=1,
                            annotation_text='Overbought (70)', annotation_position='right')
            fig_new.add_hline(y=30, line_dash='dash', line_color='green', row=2, col=1,
                            annotation_text='Oversold (30)', annotation_position='right')

            fig = fig_new

    except ImportError:
        fig.add_annotation(
            text="⚠️ Indicator calculation not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="orange")
        )

    return fig

def get_demo_chart_data(instrument: str, timeframe: str, count: int = 500) -> pd.DataFrame:
    """
    Generate demo OHLCV data for testing when real data is unavailable.

    Args:
        instrument: Trading instrument name
        timeframe: Chart timeframe
        count: Number of bars to generate

    Returns:
        DataFrame with demo OHLCV data
    """
    # Generate time series
    now = datetime.datetime.now()
    if timeframe.endswith('M'):
        # Minutes
        minutes = int(timeframe[:-1])
        periods = [now - datetime.timedelta(minutes=i) for i in range(count * minutes, 0, -minutes)]
    elif timeframe.endswith('H'):
        # Hours
        hours = int(timeframe[:-1])
        periods = [now - datetime.timedelta(hours=i) for i in range(count * hours, 0, -hours)]
    else:
        # Days
        periods = [now - datetime.timedelta(days=i) for i in range(count, 0, -1)]

    # Base price based on instrument type
    if "R_" in instrument:
        base_price = 100.0  # Volatility indices
    elif "frx" in instrument:
        base_price = 1.05 + np.random.random() * 0.3  # Forex pairs
    elif "cry" in instrument:
        base_price = 1000 + np.random.random() * 90000  # Crypto
    else:
        base_price = 100.0 + np.random.random() * 500

    # Generate realistic price movements
    prices = []
    current_price = base_price

    for i in range(count):
        if i == 0:
            price_change = np.random.normal(0, base_price * 0.0005)  # Small random change
        else:
            # Trend with some volatility
            trend = 0.0001 if np.random.random() > 0.45 else -0.0001  # Slight upward bias
            volatility = base_price * 0.002  # 0.2% volatility
            price_change = trend + np.random.normal(0, volatility)

        current_price += price_change

        # Create OHLC from close price with some spread
        spread = abs(price_change) * np.random.uniform(0.1, 0.5)
        open_price = current_price - price_change
        high_price = max(open_price, current_price) + spread
        low_price = min(open_price, current_price) - spread
        close_price = current_price
        volume = int(np.random.uniform(100, 10000)) if instrument.startswith(('cry', 'R_')) else 0

        prices.append({
            'time': periods[i],
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': volume
        })

    df = pd.DataFrame(prices)
    df.set_index('time', inplace=True)
    return df

# Convenience functions for backward compatibility
def create_interactive_chart(*args, **kwargs):
    """Alias for create_price_chart"""
    return create_price_chart(*args, **kwargs)

def add_fib_levels_to_chart(*args, **kwargs):
    """Alias for add_fibonacci_levels"""
    return add_fibonacci_levels(*args, **kwargs)
