"""
AI Trading System Module
========================
Complete AI/ML trading capabilities with continuous learning.
Dedicated module for machine learning-enhanced trading algorithms.
"""

from .main import AITradingCoordinator

try:
    from .analytics.performance_analyzer import PerformanceAnalyzer
except ImportError:
    PerformanceAnalyzer = None

try:
    from .decision_engine.strategy_selector import AIStrategySelector
except ImportError:
    AIStrategySelector = None

try:
    from .execution.ai_trade_executor import AITradeExecutor
except ImportError:
    AITradeExecutor = None

try:
    from .monitoring.model_health import AIModelHealthMonitor
except ImportError:
    AIModelHealthMonitor = None

__all__ = [
    'AITradingCoordinator',
    'PerformanceAnalyzer',
    'AIStrategySelector',
    'AITradeExecutor',
    'AIModelHealthMonitor'
]

__version__ = "1.0.0"
__description__ = "AI/ML Enhanced Trading System for TokemFX"
