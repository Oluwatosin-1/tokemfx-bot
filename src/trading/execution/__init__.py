"""
Trading Execution Module
========================
Real broker integration and order execution management.
"""

from .broker import TradingBroker
from .position_manager import PositionManager

__all__ = [
    'TradingBroker',
    'PositionManager',
]
