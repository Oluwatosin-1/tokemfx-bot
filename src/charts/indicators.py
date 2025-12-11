"""
Technical Indicators Module
===========================
Complete suite of technical indicators for professional analysis.
RSI, MACD, Bollinger Bands, Moving Averages, Stochastic, Williams %R, Volume Profile.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        data: DataFrame with 'close' column
        period: RSI period (default 14)

    Returns:
        RSI series
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if 'close' not in data.columns:
        raise ValueError("DataFrame must contain 'close' column")

    if len(data) < period + 1:
        # Return empty series for insufficient data
        return pd.Series(dtype=float, index=data.index)

    close_prices = data['close']

    # Input validation
    if close_prices.isnull().all():
        raise ValueError("Close prices contain no valid data")

    # Calculate price changes
    delta = close_prices.diff()

    # Calculate gains and losses
    gains = (delta.where(delta > 0, 0))
    losses = (-delta.where(delta < 0, 0))

    # RSI requires period+1 data points for first calculation
    # Create RSI series with NaN for insufficient data
    rsi = pd.Series(index=close_prices.index, dtype=float)

    # Calculate RSI starting from period index (first valid calculation)
    for i in range(period, len(close_prices)):
        # Get gains and losses for the period ending at i
        period_gains = gains.iloc[i-period:i]  # period values ending at i-1
        period_losses = losses.iloc[i-period:i]

        # Calculate simple averages for the period
        avg_gain = period_gains.mean() if len(period_gains) > 0 else 0
        avg_loss = period_losses.mean() if len(period_losses) > 0 else 0

        # Handle division by zero
        if avg_loss == 0:
            rs = float('inf') if avg_gain > 0 else 0
        else:
            rs = avg_gain / avg_loss

        rsi.iloc[i] = 100 - (100 / (1 + rs))

    return rsi

def calculate_macd(data: pd.DataFrame, fast_period: int = 12, slow_period: int = 26,
                  signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        data: DataFrame with 'close' column
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    if 'close' not in data.columns:
        raise ValueError("DataFrame must contain 'close' column")

    close_prices = data['close']

    # Calculate EMAs
    fast_ema = close_prices.ewm(span=fast_period, adjust=False).mean()
    slow_ema = close_prices.ewm(span=slow_period, adjust=False).mean()

    # Calculate MACD line
    macd_line = fast_ema - slow_ema

    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Calculate histogram
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20,
                            standard_deviations: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        data: DataFrame with 'close' column
        period: Moving average period
        standard_deviations: Number of standard deviations

    Returns:
        Tuple of (Upper Band, Middle Band/SMA, Lower Band)
    """
    if 'close' not in data.columns:
        raise ValueError("DataFrame must contain 'close' column")

    close_prices = data['close']

    # Calculate middle band (SMA)
    middle_band = close_prices.rolling(window=period).mean()

    # Calculate standard deviation
    std_dev = close_prices.rolling(window=period).std()

    # Calculate upper and lower bands
    upper_band = middle_band + (std_dev * standard_deviations)
    lower_band = middle_band - (std_dev * standard_deviations)

    return upper_band, middle_band, lower_band

def calculate_moving_averages(data: pd.DataFrame, periods: List[int] = [20, 50, 200]
                            ) -> Dict[str, pd.Series]:
    """
    Calculate various moving averages.

    Args:
        data: DataFrame with 'close' column
        periods: List of periods for different MAs

    Returns:
        Dict of moving average series
    """
    if 'close' not in data.columns:
        raise ValueError("DataFrame must contain 'close' column")

    close_prices = data['close']
    moving_averages = {}

    for period in periods:
        ma_key = f'SMA_{period}'
        moving_averages[ma_key] = close_prices.rolling(window=period).mean()

        # EMA version
        ema_key = f'EMA_{period}'
        moving_averages[ema_key] = close_prices.ewm(span=period, adjust=False).mean()

    return moving_averages

def calculate_stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3
                       ) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    Args:
        data: DataFrame with 'high', 'low', 'close' columns
        k_period: K line period
        d_period: D line period

    Returns:
        Tuple of (%K, %D)
    """
    if not all(col in data.columns for col in ['high', 'low', 'close']):
        raise ValueError("DataFrame must contain 'high', 'low', 'close' columns")

    high_prices = data['high']
    low_prices = data['low']
    close_prices = data['close']

    # Calculate %K
    lowest_low = low_prices.rolling(window=k_period).min()
    highest_high = high_prices.rolling(window=k_period).max()

    percent_k = 100 * ((close_prices - lowest_low) / (highest_high - lowest_low))

    # Calculate %D (SMA of %K)
    percent_d = percent_k.rolling(window=d_period).mean()

    return percent_k, percent_d

def calculate_williams_r(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Williams %R.

    Args:
        data: DataFrame with 'high', 'low', 'close' columns
        period: Williams %R period

    Returns:
        Williams %R series
    """
    if not all(col in data.columns for col in ['high', 'low', 'close']):
        raise ValueError("DataFrame must contain 'high', 'low', 'close' columns")

    high_prices = data['high']
    low_prices = data['low']
    close_prices = data['close']

    highest_high = high_prices.rolling(window=period).max()
    lowest_low = low_prices.rolling(window=period).min()

    williams_r = -100 * ((highest_high - close_prices) / (highest_high - lowest_low))

    return williams_r

def calculate_volume_profile(data: pd.DataFrame, bins: int = 50) -> pd.DataFrame:
    """
    Calculate Volume Profile.

    Args:
        data: DataFrame with 'close', 'volume' columns
        bins: Number of price bins

    Returns:
        Volume profile DataFrame with price levels and volume
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if not all(col in data.columns for col in ['close', 'volume']):
        raise ValueError("DataFrame must contain 'close', 'volume' columns")

    if len(data) == 0:
        return pd.DataFrame(columns=['price_level', 'volume'])

    # Handle potential null values
    close_prices = data['close'].ffill().fillna(1.0)
    volume_data = data['volume'].fillna(0)

    price_min = close_prices.min()
    price_max = close_prices.max()

    # Validate price range
    if price_min >= price_max:
        return pd.DataFrame({'price_level': [price_min], 'volume': [volume_data.sum()]})

    # Ensure bins is reasonable
    bins = max(2, min(bins, len(data)))

    # Create price bins
    try:
        price_bins = np.linspace(price_min, price_max, bins)
    except (ValueError, TypeError):
        # Fallback for edge cases
        price_bins = np.array([price_min, price_max])

    volume_profile = []

    for i in range(len(price_bins) - 1):
        bin_start = price_bins[i]
        bin_end = price_bins[i + 1]

        # Find bars within this price range
        in_bin = (close_prices >= bin_start) & (close_prices < bin_end)

        # Safely sum volume (handle different types)
        try:
            total_volume = float(volume_data[in_bin].sum())
        except (TypeError, ValueError, AttributeError):
            total_volume = 0.0

        volume_profile.append({
            'price_level': (bin_start + bin_end) / 2,
            'volume': total_volume
        })

    if not volume_profile:
        return pd.DataFrame({'price_level': [price_min], 'volume': [0.0]})

    return pd.DataFrame(volume_profile)

def add_indicator_to_chart(fig: go.Figure, indicator_data: pd.Series,
                         indicator_name: str, color: str = 'blue',
                         row: Optional[int] = None) -> go.Figure:
    """
    Add technical indicator to existing chart.

    Args:
        fig: Plotly figure
        indicator_data: Indicator series
        indicator_name: Display name for the indicator
        color: Line color
        row: Subplot row (if multi-row chart)

    Returns:
        Updated figure
    """
    if not isinstance(fig, go.Figure):
        raise ValueError("fig must be a plotly.graph_objects.Figure")

    if not isinstance(indicator_data, pd.Series):
        raise ValueError("indicator_data must be a pandas Series")

    indicator_trace = go.Scatter(
        x=indicator_data.index,
        y=indicator_data.values,
        mode='lines',
        name=indicator_name,
        line=dict(color=color, width=1.5),
        showlegend=True
    )

    # Determine where to add the trace
    if row is not None and row > 1:
        # For indicators on separate rows (RSI, MACD, etc.)
        # Check if figure has enough rows
        try:
            fig.add_trace(indicator_trace, row=row, col=1)
        except (ValueError, IndexError):
            # If subplot doesn't exist, add to main chart
            fig.add_trace(indicator_trace)
    else:
        # Add to main price chart
        fig.add_trace(indicator_trace)

    return fig

# Convenience functions for common indicators
def calculate_all_indicators(data: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Calculate all major technical indicators for comprehensive analysis.

    Returns:
        Dict with flat structure compatible with dashboard expectations
    """
    # Calculate individual periods and create proper structure
    sma20_series = data['close'].rolling(window=20).mean()
    sma50_series = data['close'].rolling(window=50).mean()
    ema12_series = data['close'].ewm(span=12, adjust=False).mean()
    ema26_series = data['close'].ewm(span=26, adjust=False).mean()

    indicators = {
        # RSI
        'rsi': calculate_rsi(data, 14),
        # Stochastic Oscillator
        'stochastic_k': calculate_stochastic(data)[0],
        'stochastic_d': calculate_stochastic(data)[1],
        # Williams %R
        'williams_r': calculate_williams_r(data),
        # Bollinger Bands
        'bb_upper': calculate_bollinger_bands(data)[0],
        'bb_middle': calculate_bollinger_bands(data)[1],
        'bb_lower': calculate_bollinger_bands(data)[2],
        # Moving averages
        'sma_20': sma20_series,
        'ema_20': data['close'].ewm(span=20, adjust=False).mean(),
        'sma_50': sma50_series,
        'ema_50': data['close'].ewm(span=50, adjust=False).mean(),
        # MACD components
        'macd': calculate_macd(data)[0],
        'macd_signal': calculate_macd(data)[1],
    }

    return indicators
