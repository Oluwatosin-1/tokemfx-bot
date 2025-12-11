"""
Technical analysis strategies.
"""
from .moving_average import MovingAverageCrossStrategy, EMARSIHybridStrategy
from .oscillators import RSIReversionStrategy, MACDStrategy
from .breakout import BollingerBreakoutStrategy, ATRBreakoutStrategy
from .trend import SuperTrendStrategy

__all__ = [
    'MovingAverageCrossStrategy', 'EMARSIHybridStrategy',
    'RSIReversionStrategy', 'MACDStrategy',
    'BollingerBreakoutStrategy', 'ATRBreakoutStrategy',
    'SuperTrendStrategy'
]
