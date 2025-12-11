"""
Trading Simulation Module
==========================
Backtesting and market simulation capabilities for trading systems.
"""

from .backtest_simulator import BacktestSimulator
from .market_simulator import MarketSimulator

__all__ = [
    'BacktestSimulator',
    'MarketSimulator',
]
