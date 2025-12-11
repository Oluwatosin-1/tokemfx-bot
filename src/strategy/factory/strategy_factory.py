"""
Strategy Factory
================
Factory pattern for dynamic strategy instantiation.

This module provides:
- Dynamic strategy creation
- Parameter validation
- Strategy configuration
- Factory pattern implementation
"""

import importlib
import inspect
from typing import Dict, Any, Type, Optional, Union, Callable
from dataclasses import dataclass

from ..config.strategy_registry import strategy_registry
from ..config.risk_warnings import require_risk_acknowledgment, get_strategy_risk_info


@dataclass
class StrategyInstance:
    """Container for strategy instance and metadata."""
    strategy: Any
    parameters: Dict[str, Any]
    risk_info: Dict[str, Any]
    validation_result: Dict[str, Any]


class StrategyFactory:
    """
    Factory for creating and configuring trading strategies.
    Provides validation, risk checking, and instantiation.
    """

    def __init__(self):
        """Initialize the strategy factory."""
        self._strategy_cache = {}
        self._validation_enabled = True
        self._risk_checking_enabled = True

    def create_strategy(self,
                       strategy_name: str,
                       parameters: Optional[Dict[str, Any]] = None,
                       instrument: str = "",
                       validate: bool = True,
                       risk_check: bool = True,
                       user_experience: str = 'intermediate') -> StrategyInstance:
        """
        Create and configure a strategy instance.

        Args:
            strategy_name: Name of the strategy to create
            parameters: Strategy parameters
            instrument: Trading instrument
            validate: Whether to validate parameters
            risk_check: Whether to perform risk checking
            user_experience: User experience level

        Returns:
            StrategyInstance with strategy and metadata

        Raises:
            ValueError: If strategy creation fails or validation fails
        """
        parameters = parameters or {}

        # Add instrument to parameters if specified
        if instrument and 'instrument' not in parameters:
            parameters['instrument'] = instrument

        # Check if risk acknowledgment is required
        if risk_check and self._risk_checking_enabled:
            if require_risk_acknowledgment(strategy_name, user_experience):
                raise ValueError(
                    f"High-risk strategy '{strategy_name}' requires explicit risk acknowledgment. "
                    f"Use risk_check=False to bypass this check for demo purposes only."
                )

        # Get strategy class from registry
        strategy_class = strategy_registry.get_strategy(strategy_name)
        if not strategy_class:
            raise ValueError(f"Strategy '{strategy_name}' not found in registry")

        # Validate parameters
        validation_result = {'is_valid': True, 'issues': [], 'warnings': []}
        if validate and self._validation_enabled:
            validation_result = strategy_registry.validate_strategy_parameters(
                strategy_name, parameters
            )

            if not validation_result['is_valid']:
                issues = '; '.join(validation_result['issues'])
                raise ValueError(f"Parameter validation failed for '{strategy_name}': {issues}")

        # Create strategy instance
        try:
            strategy_instance = strategy_class(**parameters)
        except Exception as e:
            raise ValueError(f"Failed to create strategy '{strategy_name}': {e}")

        # Get risk information
        risk_info = get_strategy_risk_info(strategy_class)

        return StrategyInstance(
            strategy=strategy_instance,
            parameters=parameters.copy(),
            risk_info=risk_info,
            validation_result=validation_result
        )

    def create_multiple_strategies(self,
                                 strategy_configs: Dict[str, Dict[str, Any]],
                                 instrument: str = "",
                                 validate: bool = True,
                                 risk_check: bool = True,
                                 user_experience: str = 'intermediate') -> Dict[str, StrategyInstance]:
        """
        Create multiple strategy instances from a configuration dictionary.

        Args:
            strategy_configs: Dictionary of strategy_name -> parameters
            instrument: Default trading instrument
            validate: Whether to validate parameters
            risk_check: Whether to perform risk checking
            user_experience: User experience level

        Returns:
            Dictionary of strategy_name -> StrategyInstance

        Raises:
            ValueError: If any strategy creation fails
        """
        strategies = {}
        errors = []

        for strategy_name, params in strategy_configs.items():
            try:
                # Use instrument from params or default
                strat_instrument = params.get('instrument', instrument)

                strategy_instance = self.create_strategy(
                    strategy_name=strategy_name,
                    parameters={k: v for k, v in params.items() if k != 'instrument'},  # Remove instrument from params
                    instrument=strat_instrument,
                    validate=validate,
                    risk_check=risk_check,
                    user_experience=user_experience
                )

                strategies[strategy_name] = strategy_instance

            except Exception as e:
                errors.append(f"{strategy_name}: {e}")

        if errors:
            error_msg = "Failed to create some strategies:\n" + "\n".join(errors)
            raise ValueError(error_msg)

        return strategies

    def get_available_strategies(self,
                               category: Optional[str] = None,
                               risk_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get available strategies with optional filtering.

        Args:
            category: Filter by category ('technical', 'ml', 'money_management')
            risk_filter: Filter by maximum risk level ('LOW', 'MEDIUM', 'HIGH')

        Returns:
            Dictionary of strategy metadata
        """
        all_strategies = strategy_registry.list_strategies()
        filtered_strategies = {}

        for strategy_info in all_strategies:
            strategy_name = strategy_info['name']

            # Category filter
            if category and strategy_info.get('category') != category:
                continue

            # Risk filter
            if risk_filter and strategy_info.get('risk_level') in ['EXTREME']:
                continue
            if risk_filter == 'MEDIUM' and strategy_info.get('risk_level') in ['HIGH', 'EXTREME']:
                continue
            if risk_filter == 'LOW' and strategy_info.get('risk_level') != 'LOW':
                continue

            filtered_strategies[strategy_name] = strategy_info

        return filtered_strategies

    def validate_strategy_combination(self, strategy_instances: Dict[str, StrategyInstance]) -> Dict[str, Any]:
        """
        Validate a combination of strategies for portfolio use.

        Args:
            strategy_instances: Dictionary of strategy instances

        Returns:
            Validation results
        """
        issues = []
        warnings = []

        # Check for conflicting strategies
        strategy_names = list(strategy_instances.keys())

        # Risk concentration check
        high_risk_count = sum(1 for inst in strategy_instances.values()
                            if inst.risk_info.get('risk_level') in ['HIGH', 'EXTREME'])

        if high_risk_count > len(strategy_names) / 2:
            warnings.append("High concentration of risky strategies detected")

        # Similar strategy check (basic)
        if len(set(strategy_names)) < len(strategy_names):
            issues.append("Duplicate strategy names detected")

        # Parameter conflicts (this could be expanded)
        conflicting_params = []
        for name1, inst1 in strategy_instances.items():
            for name2, inst2 in strategy_instances.items():
                if name1 != name2:
                    # Check for overlapping parameter names that might conflict
                    common_params = set(inst1.parameters.keys()) & set(inst2.parameters.keys())
                    if common_params and inst1.parameters != inst2.parameters:
                        conflicting_params.append(f"{name1} vs {name2}: {list(common_params)}")

        if conflicting_params:
            warnings.extend(conflicting_params)

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'strategy_count': len(strategy_instances),
            'risky_strategy_count': high_risk_count
        }

    def create_strategy_with_config(self,
                                  config: Dict[str, Any],
                                  user_experience: str = 'intermediate') -> StrategyInstance:
        """
        Create a strategy from a complete configuration dictionary.

        Args:
            config: Complete strategy configuration
                {
                    'strategy_name': str,
                    'parameters': dict,
                    'instrument': str (optional),
                    'validation_enabled': bool (optional),
                    'risk_check_enabled': bool (optional)
                }
            user_experience: User experience level

        Returns:
            Configured strategy instance
        """
        strategy_name = config.get('strategy_name')
        if not strategy_name:
            raise ValueError("Configuration must include 'strategy_name'")

        parameters = config.get('parameters', {})
        instrument = config.get('instrument', '')
        validate = config.get('validation_enabled', True)
        risk_check = config.get('risk_check_enabled', True)

        return self.create_strategy(
            strategy_name=strategy_name,
            parameters=parameters,
            instrument=instrument,
            validate=validate,
            risk_check=risk_check,
            user_experience=user_experience
        )

    def enable_validation(self, enabled: bool = True):
        """Enable or disable parameter validation."""
        self._validation_enabled = enabled

    def enable_risk_checking(self, enabled: bool = True):
        """Enable or disable risk checking."""
        self._risk_checking_enabled = enabled

    def clear_cache(self):
        """Clear the strategy instantiation cache."""
        self._strategy_cache.clear()

    def get_factory_stats(self) -> Dict[str, Any]:
        """Get factory usage statistics."""
        return {
            'strategies_created': len(self._strategy_cache),
            'validation_enabled': self._validation_enabled,
            'risk_checking_enabled': self._risk_checking_enabled,
            'registry_size': strategy_registry.get_strategy_summary()
        }


# Global factory instance
strategy_factory = StrategyFactory()
