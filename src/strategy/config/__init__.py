"""
Strategy configuration and registry.
"""
from .strategy_registry import StrategyRegistry, strategy_registry
from .risk_warnings import get_strategy_risk_info, RISK_WARNINGS

# Strategy mappings will be created after all registrations in the main __init__.py
# This is to ensure all strategies are registered before creating the maps

def get_strategy_health_status() -> dict:
    """
    Monitor strategy availability and health.

    Returns:
        Dictionary with health metrics
    """
    try:
        # Get strategies from registry since STRATEGY_MAP may not be available during import
        from .strategy_registry import strategy_registry
        all_strategies = strategy_registry.get_all_strategies()

        total_strategies = len(all_strategies)
        working_strategies = 0
        failed_strategies = []

        for name, strategy_class in all_strategies.items():
            try:
                # Test basic class attributes and inheritance (without Backtrader initialization)
                if hasattr(strategy_class, 'params') and hasattr(strategy_class, 'next'):
                    # Check if it inherits from BaseStrategy
                    from src.strategy.base.base_strategy import BaseStrategy
                    if issubclass(strategy_class, BaseStrategy):
                        working_strategies += 1
                    else:
                        failed_strategies.append(f"{name}: Not a BaseStrategy subclass")
                else:
                    failed_strategies.append(f"{name}: Missing required attributes")
            except Exception as e:
                failed_strategies.append(f"{name}: {str(e)[:50]}")

        health_score = working_strategies / total_strategies if total_strategies > 0 else 0

        return {
            'total_strategies': total_strategies,
            'working_strategies': working_strategies,
            'failed_strategies': failed_strategies,
            'health_score': health_score,
            'status': 'healthy' if health_score >= 0.9 else 'degraded' if health_score >= 0.7 else 'critical'
        }
    except Exception as e:
        return {
            'total_strategies': 0,
            'working_strategies': 0,
            'failed_strategies': [f"Health check failed: {str(e)}"],
            'health_score': 0.0,
            'status': 'error'
        }

def validate_strategy_compatibility(strategy_name: str, instrument: str) -> dict:
    """
    Validate if a strategy is compatible with an instrument.

    Args:
        strategy_name: Name of the strategy
        instrument: Trading instrument

    Returns:
        Compatibility validation result
    """
    try:
        metadata = strategy_registry.get_strategy_metadata(strategy_name)
        if not metadata:
            return {'compatible': False, 'reason': 'Strategy not found'}

        suitable_instruments = metadata.get('suitable_instruments', [])
        compatible = instrument in suitable_instruments or not suitable_instruments

        return {
            'compatible': compatible,
            'reason': 'Compatible' if compatible else f'Not recommended for {instrument}',
            'suitable_instruments': suitable_instruments,
            'risk_level': metadata.get('risk_level', 'UNKNOWN')
        }
    except Exception as e:
        return {'compatible': False, 'reason': f'Validation error: {str(e)}'}

__all__ = [
    'StrategyRegistry', 'strategy_registry', 'get_strategy_risk_info', 'RISK_WARNINGS',
    'get_strategy_health_status', 'validate_strategy_compatibility'
]
