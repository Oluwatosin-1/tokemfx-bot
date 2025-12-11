"""
Strategy Registry
=================
Centralized strategy discovery and management system.

This module provides:
- Strategy discovery and loading
- Category-based organization
- Parameter validation
- Strategy metadata management
"""

from typing import Dict, Type, Any, List, Optional


class StrategyRegistry:
    """
    Centralized registry for all trading strategies.
    Provides discovery, validation, and metadata management.
    """

    def __init__(self):
        """Initialize the strategy registry."""
        self._strategies = {}
        self._categories = {}
        self._metadata = {}

        # Initialize empty categories
        self._categories = {
            'technical': {},
            'ml': {},
            'money_management': {},
            'hybrid': {}
        }

    def register_strategy(self, strategy_class: Type, category: str,
                         metadata: Optional[Dict[str, Any]] = None):
        """
        Register a strategy class in the registry.

        Args:
            strategy_class: Strategy class to register
            category: Category to place the strategy in
            metadata: Additional metadata for the strategy
        """
        strategy_name = strategy_class.__name__

        # Store in main registry
        self._strategies[strategy_name] = strategy_class

        # Store in category
        if category not in self._categories:
            self._categories[category] = {}
        self._categories[category][strategy_name] = strategy_class

        # Store metadata
        default_metadata = {
            'name': strategy_name,
            'category': category,
            'description': getattr(strategy_class, '__doc__', '').strip() or 'No description',
            'parameters': getattr(strategy_class, 'params', ()),
            'risk_level': self._assess_risk_level(strategy_class),
            'suitable_instruments': self._get_suitable_instruments(strategy_class)
        }

        if metadata:
            default_metadata.update(metadata)

        self._metadata[strategy_name] = default_metadata

    def get_strategy(self, name: str) -> Optional[Type]:
        """
        Get a strategy class by name.

        Args:
            name: Strategy name

        Returns:
            Strategy class or None if not found
        """
        return self._strategies.get(name)

    def get_strategies_by_category(self, category: str) -> Dict[str, Type]:
        """
        Get all strategies in a specific category.

        Args:
            category: Category name

        Returns:
            Dictionary of strategy_name -> strategy_class
        """
        return self._categories.get(category, {}).copy()

    def get_strategy_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a strategy.

        Args:
            name: Strategy name

        Returns:
            Strategy metadata or None if not found
        """
        return self._metadata.get(name)

    def get_all_strategies(self) -> Dict[str, Type]:
        """
        Get all registered strategies with clean class names.

        Returns:
            Dictionary of strategy_name -> strategy_class for programmatic use
        """
        strategies = {}

        # Add all strategies with their class names
        for name, cls in self._strategies.items():
            strategies[name] = cls

        return strategies

    def get_strategies_for_ui(self) -> Dict[str, Type]:
        """
        Get all registered strategies with display names for UI dropdowns.

        Returns:
            Dictionary suitable for UI dropdowns with emoji prefixes
        """
        strategies = {}

        # Technical strategies
        for name, cls in self.get_strategies_by_category('technical').items():
            strategies[f"📈 {name}"] = cls

        # ML strategies
        for name, cls in self.get_strategies_by_category('ml').items():
            strategies[f"🤖 {name}"] = cls

        # Money management strategies
        for name, cls in self.get_strategies_by_category('money_management').items():
            strategies[f"💰 {name}"] = cls

        # Hybrid strategies
        for name, cls in self.get_strategies_by_category('hybrid').items():
            strategies[f"🔄 {name}"] = cls

        return strategies

    def get_money_management_strategies(self) -> Dict[str, Type]:
        """
        Get money management strategies with risk warnings.

        Returns:
            Dictionary of display_name -> strategy_class
        """
        money_strategies = {}
        for name, cls in self.get_strategies_by_category('money_management').items():
            if 'Martingale' in name:
                money_strategies[f"💰 {name} (HIGH RISK)"] = cls
            else:
                money_strategies[f"🎲 {name}"] = cls

        return money_strategies

    def validate_strategy_parameters(self, strategy_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters for a strategy.

        Args:
            strategy_name: Name of strategy to validate
            parameters: Parameter dictionary to validate

        Returns:
            Validation result with 'is_valid' and 'issues'
        """
        strategy_class = self.get_strategy(strategy_name)
        if not strategy_class:
            return {'is_valid': False, 'issues': [f'Strategy {strategy_name} not found']}

        # Get strategy parameters
        strategy_params = getattr(strategy_class, 'params', ())
        param_names = [param[0] for param in strategy_params]

        issues = []
        warnings = []

        # Check required parameters
        for param_name, _, _ in strategy_params:
            if param_name not in parameters and param_name != 'instrument':
                warnings.append(f'Missing parameter: {param_name}')

        # Check parameter ranges
        for param_name, _, min_val, max_val in strategy_params:
            if param_name in parameters:
                value = parameters[param_name]
                if hasattr(min_val, '__call__'):  # Skip callable defaults
                    continue

                if min_val is not None and value < min_val:
                    issues.append(f'{param_name} below minimum: {value} < {min_val}')
                if max_val is not None and value > max_val:
                    issues.append(f'{param_name} above maximum: {value} > {max_val}')

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    def _assess_risk_level(self, strategy_class: Type) -> str:
        """Assess risk level based on strategy characteristics."""
        name = strategy_class.__name__

        # High risk strategies
        if any(term in name.lower() for term in ['martingale', 'gambling']):
            return 'EXTREME'

        # Medium risk strategies
        if any(term in name.lower() for term in ['reverse', 'progressive']):
            return 'HIGH'

        # Default to medium
        return 'MEDIUM'

    def _get_suitable_instruments(self, strategy_class: Type) -> List[str]:
        """Determine suitable instruments for the strategy."""
        # This could be enhanced based on strategy characteristics
        return ['R_10', 'R_25', 'R_50', 'R_75', 'R_100',
                'frxEURUSD', 'frxUSDJPY', 'frxGBPUSD', 'frxAUDUSD']

    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        Get a detailed list of all strategies with metadata.

        Returns:
            List of strategy information dictionaries
        """
        strategies = []
        for name, metadata in self._metadata.items():
            strategies.append({
                'name': name,
                'display_name': self._get_display_name(name, metadata),
                **metadata
            })

        return sorted(strategies, key=lambda x: x['name'])

    def _get_display_name(self, name: str, metadata: Dict[str, Any]) -> str:
        """Generate a display name for the strategy."""
        category = metadata.get('category', '')
        icons = {
            'technical': '📊',
            'ml': '🤖',
            'money_management': '💰',
            'hybrid': '🔄'
        }
        icon = icons.get(category, '📈')
        return f"{icon} {name}"

    def get_strategy_summary(self) -> Dict[str, int]:
        """Get a summary of registered strategies."""
        return {
            'total': len(self._strategies),
            'technical': len(self._categories.get('technical', {})),
            'ml': len(self._categories.get('ml', {})),
            'money_management': len(self._categories.get('money_management', {})),
            'hybrid': len(self._categories.get('hybrid', {}))
        }


# Global registry instance
strategy_registry = StrategyRegistry()
