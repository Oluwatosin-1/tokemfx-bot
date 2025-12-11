"""
Timeframe Management for Multi-Timeframe Trading
===============================================
Handles different chart intervals: 1M, 5M, 15M, 1H, 4H, 1D, 1W, 1M
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Available timeframes with their periods
TIMEFRAMES = {
    "1M": {"label": "1 Minute", "seconds": 60, "ticks": "M1"},
    "5M": {"label": "5 Minutes", "seconds": 300, "ticks": "M5"},
    "15M": {"label": "15 Minutes", "seconds": 900, "ticks": "M15"},
    "1H": {"label": "1 Hour", "seconds": 3600, "ticks": "H1"},
    "4H": {"label": "4 Hours", "seconds": 14400, "ticks": "H4"},
    "1D": {"label": "1 Day", "seconds": 86400, "ticks": "D1"},
    "1W": {"label": "1 Week", "seconds": 604800, "ticks": "W1"},
    "1M": {"label": "1 Month", "seconds": 2592000, "ticks": "M1"}
}

def get_available_timeframes():
    """Get list of available timeframe options for UI"""
    return list(TIMEFRAMES.keys())

def get_timeframe_label(timeframe):
    """Get human-readable label for timeframe"""
    return TIMEFRAMES.get(timeframe, {}).get("label", timeframe)

def get_timeframe_seconds(timeframe):
    """Get timeframe duration in seconds"""
    return TIMEFRAMES.get(timeframe, {}).get("seconds", 60)

def aggregate_ohlc_data(df, target_tf):
    """
    Aggregate OHLC data to target timeframe
    df: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
    target_tf: Target timeframe (1M, 5M, 15M, 1H, etc.)
    """
    if df.empty:
        return df.copy()

    # Convert time column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])

    # Set time as index for resampling
    df = df.set_index('time')

    target_freq = get_resample_frequency(target_tf)

    try:
        # Resample to target timeframe
        aggregated = df.resample(target_freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        return aggregated.reset_index()

    except Exception as e:
        print(f"Error aggregating timeframe data: {e}")
        return df.reset_index()

def get_resample_frequency(timeframe):
    """
    Convert timeframe string to pandas resample frequency
    """
    mapping = {
        "1M": "1min",
        "5M": "5min",
        "15M": "15min",
        "1H": "1H",
        "4H": "4H",
        "1D": "1D",
        "1W": "1W",
        "1M": "1MS"  # Month start
    }

    return mapping.get(timeframe, "1min")

def fetch_timeframe_data(broker, instrument, timeframe, count=500):
    """
    Fetch data for specific instrument and timeframe
    Returns aggregated OHLC data
    """
    try:
        # Get base 1-minute data
        base_df = broker.fetch_candles(instrument, "M1", count=count)

        if base_df.empty:
            return base_df

        # If requested timeframe is 1M, return as-is
        if timeframe == "1M":
            return base_df

        # Aggregate to target timeframe
        aggregated_df = aggregate_ohlc_data(base_df, timeframe)

        return aggregated_df

    except Exception as e:
        print(f"Error fetching timeframe data: {e}")
        return pd.DataFrame()

def calculate_price_change(df, period=1):
    """
    Calculate price change over specified period
    """
    if df.empty or 'close' not in df.columns:
        return 0

    if len(df) < period + 1:
        return 0

    current_price = df['close'].iloc[-1]
    past_price = df['close'].iloc[-(period + 1)]

    if past_price == 0:
        return 0

    return ((current_price - past_price) / past_price) * 100

def get_timeframe_price_stats(df):
    """
    Get price statistics for a timeframe
    """
    if df.empty:
        return {
            'current_price': 0,
            'price_change': 0,
            'high_24h': 0,
            'low_24h': 0,
            'volume': 0
        }

    current_price = df['close'].iloc[-1] if 'close' in df.columns else 0

    # Calculate 24h change (approximate based on available data)
    price_change = calculate_price_change(df, min(len(df)-1, 1440))  # 1440 minutes = 24h

    high_24h = df['high'].tail(1440).max() if len(df) >= 1440 else df['high'].max()
    low_24h = df['low'].tail(1440).min() if len(df) >= 1440 else df['low'].min()
    volume = df['volume'].sum() if 'volume' in df.columns else 0

    return {
        'current_price': current_price,
        'price_change': price_change,
        'high_24h': high_24h,
        'low_24h': low_24h,
        'volume': volume
    }
