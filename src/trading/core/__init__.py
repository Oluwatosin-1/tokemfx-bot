"""
Trading Core Module
===================
Core trading intelligence and automated trading systems.
"""

from .auto_trading_bot import AutoTradingBot, start_ai_trading, stop_ai_trading, get_trading_status
from .trading_intelligence import TradingIntelligence, analyze_backtest_for_trading, execute_ai_trade, track_trade_performance
from .signal_generator import SignalGenerator, create_signal_generator

__all__ = [
    'AutoTradingBot',
    'TradingIntelligence',
    'SignalGenerator',
    'start_ai_trading',
    'stop_ai_trading',
    'get_trading_status',
    'analyze_backtest_for_trading',
    'execute_ai_trade',
    'track_trade_performance',
    'create_signal_generator',
]
