"""
TokemFX Strategy Module
=======================
Comprehensive strategy framework for algorithmic trading.

This module provides:
- Technical analysis strategies
- Machine learning strategies
- Money management strategies
- Strategy configuration and validation
- Event-driven execution framework
"""

from .base import BaseStrategy
from .factory import StrategyFactory
from .config import (
    get_strategy_risk_info,
    StrategyRegistry,
    get_strategy_health_status,
    validate_strategy_compatibility
)

# Initialize strategy registry
from .config.strategy_registry import strategy_registry

# Register base strategy
strategy_registry.register_strategy(BaseStrategy, 'base')

# Technical strategies
try:
    from .technical.moving_average import MovingAverageCrossStrategy, EMARSIHybridStrategy
    from .technical.oscillators import RSIReversionStrategy, MACDStrategy
    from .technical.breakout import BollingerBreakoutStrategy, ATRBreakoutStrategy
    from .technical.trend import SuperTrendStrategy

    # Register technical strategies
    strategy_registry.register_strategy(MovingAverageCrossStrategy, 'technical')
    strategy_registry.register_strategy(EMARSIHybridStrategy, 'technical')
    strategy_registry.register_strategy(RSIReversionStrategy, 'technical')
    strategy_registry.register_strategy(MACDStrategy, 'technical')
    strategy_registry.register_strategy(BollingerBreakoutStrategy, 'technical')
    strategy_registry.register_strategy(ATRBreakoutStrategy, 'technical')
    strategy_registry.register_strategy(SuperTrendStrategy, 'technical')

except ImportError as e:
    print(f"Warning: Technical strategy imports failed: {e}")

# Money management strategies
try:
    from .money_management.martingale import MartingaleStrategy, ReverseMartingaleStrategy
    from .money_management.progressive import DAlembertStrategy, OscarsGrindStrategy, ReverseDAlembertStrategy
    from .money_management.sequence import OneThreeTwoSixStrategy

    # Register money management strategies with appropriate risk warnings
    strategy_registry.register_strategy(MartingaleStrategy, 'money_management',
        {'suitable_instruments': ['R_10', 'R_25', 'R_50', 'frxEURUSD']})
    strategy_registry.register_strategy(ReverseMartingaleStrategy, 'money_management')
    strategy_registry.register_strategy(DAlembertStrategy, 'money_management')
    strategy_registry.register_strategy(OscarsGrindStrategy, 'money_management')
    strategy_registry.register_strategy(ReverseDAlembertStrategy, 'money_management')
    strategy_registry.register_strategy(OneThreeTwoSixStrategy, 'money_management')

except ImportError as e:
    print(f"Warning: Money management strategy imports failed: {e}")

# ML strategies
try:
    from .ml.ensemble import MLForestStrategy
    strategy_registry.register_strategy(MLForestStrategy, 'ml')

except ImportError as e:
    print(f"Warning: ML strategy imports failed: {e}")

# Create strategy mappings after all registrations
STRATEGY_MAP = strategy_registry.get_all_strategies()  # For programmatic use
STRATEGY_MAP_UI = strategy_registry.get_strategies_for_ui()  # For UI dropdowns
MONEY_MANAGEMENT_STRATEGIES = strategy_registry.get_money_management_strategies()

# Create convenient aliases for backward compatibility
strategy_factory = StrategyFactory()

# Export commonly used classes and mappings
__version__ = "1.0.0"
__all__ = [
    # Core classes
    'BaseStrategy',
    'StrategyFactory',
    'StrategyRegistry',
    'get_strategy_risk_info',
    # Strategy mappings
    'STRATEGY_MAP',
    'MONEY_MANAGEMENT_STRATEGIES',
    # Backward compatibility aliases
    'strategy_factory',
    'strategy_registry'
]
