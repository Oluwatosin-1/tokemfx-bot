"""
TokemFX Trading Module
=======================
Enterprise-grade trading engine with AI automation, risk management, and professional execution.

Core Components:
- Core Trading Engine: Auto trading bots and AI intelligence
- Execution Layer: Real broker integration and order management
- Risk Management: Position limits and drawdown controls
- Simulation: Backtesting and market simulation
- Monitoring: Performance tracking and analytics
- UI: Professional trading dashboard interfaces
"""

# Main exports from trading module
from .core import AutoTradingBot, TradingIntelligence
from .execution import TradingBroker, PositionManager
from .risk import RiskManager, RiskCalculator
from .simulation import BacktestSimulator, MarketSimulator
from .monitoring import PerformanceTracker
from .ui import render_advanced_backtesting, AITradingUI, TradingDashboard
from .core import SignalGenerator

# Legacy compatibility
from .core.auto_trading_bot import start_ai_trading, stop_ai_trading, get_trading_status
from .core.trading_intelligence import analyze_backtest_for_trading, execute_ai_trade

# Version info
__version__ = "2.0.0"
__description__ = "Professional trading engine with AI automation"

__all__ = [
    # Core components
    'AutoTradingBot', 'TradingIntelligence',
    'TradingBroker', 'PositionManager',
    'RiskManager', 'RiskCalculator',
    'BacktestSimulator', 'PerformanceTracker',
    'TradingDashboardUI',

    # Legacy functions
    'start_ai_trading', 'stop_ai_trading', 'get_trading_status',
    'analyze_backtest_for_trading', 'execute_ai_trade',
]
