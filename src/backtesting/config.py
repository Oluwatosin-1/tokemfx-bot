"""
TokemFX Backtesting Configuration
=================================
Configuration management for backtesting operations.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfiguration:
    """Centralized configuration for backtesting operations"""

    # Data settings
    data_cache_enabled: bool = True
    data_cache_ttl_hours: int = 24
    data_validation_enabled: bool = True
    parallel_data_loading: bool = True

    # Engine settings
    max_workers: int = 4
    chunk_size: int = 1000
    memory_limit_mb: int = 512
    enable_progress_tracking: bool = True

    # Performance settings
    enable_slippage_model: bool = False
    enable_commission_model: bool = True
    enable_data_quality_checks: bool = True

    # Statistical settings
    significance_level: float = 0.05
    bootstrap_samples: int = 1000
    monte_carlo_simulations: int = 100

    # Optimization settings
    optimization_timeout_seconds: int = 3600
    max_evaluations_per_worker: int = 50
    enable_hyperopt: bool = True
    enable_walk_forward: bool = True

    # Risk management settings
    max_drawdown_limit: float = 0.5  # 50%
    risk_free_rate: float = 0.03     # 3%
    value_at_risk_confidence: float = 0.95

    # Output settings
    export_results: bool = True
    export_format: str = "json"  # json, csv, both
    create_reports: bool = True
    save_charts: bool = True

    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    log_directory: str = "logs"

    # Paths
    cache_directory: str = "cache"
    results_directory: str = "results"
    reports_directory: str = "reports"

    # Strategy defaults
    default_commission: float = 0.0002  # 0.02%
    default_slippage: float = 0.0001    # 0.01%
    default_initial_cash: float = 10000.0

    # Advanced features
    enable_ai_monitoring: bool = True
    enable_system_audit: bool = True
    enable_production_monitoring: bool = False

    # Custom settings (for extensibility)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class StrategyConfigs:
    """Strategy-specific configuration templates"""

    @staticmethod
    def get_moving_average_config() -> Dict[str, Any]:
        """Configuration for Moving Average strategies"""
        return {
            'fast_period_range': list(range(5, 21, 2)),      # 5, 7, 9, ..., 19
            'slow_period_range': list(range(20, 51, 5)),     # 20, 25, 30, ..., 50
            'signal_strength_threshold': 0.001,              # Minimum crossover strength
            'confirmation_periods': 2,                       # Periods to confirm crossover
        }

    @staticmethod
    def get_rsi_config() -> Dict[str, Any]:
        """Configuration for RSI strategies"""
        return {
            'rsi_period_range': list(range(7, 22, 2)),       # 7, 9, 11, ..., 21
            'oversold_range': list(range(25, 36, 2)),        # 25, 27, 29, ..., 35
            'overbought_range': list(range(65, 76, 2)),      # 65, 67, 69, ..., 75
            'confirmation_periods': 1,                       # RSI periods to stay in zone
        }

    @staticmethod
    def get_bollinger_config() -> Dict[str, Any]:
        """Configuration for Bollinger Band strategies"""
        return {
            'period_range': list(range(15, 26, 2)),          # 15, 17, 19, ..., 25
            'deviation_range': [1.5, 2.0, 2.5, 3.0],        # Standard deviation multiples
            'touch_threshold_percentage': 0.1,               # How close to band to trigger
            'squeeze_threshold': 1.5,                        # Band squeeze signal threshold
        }

    @staticmethod
    def get_atr_config() -> Dict[str, Any]:
        """Configuration for ATR-based strategies"""
        return {
            'atr_period_range': list(range(7, 22, 3)),       # 7, 10, 13, 16, 19
            'multiplier_range': [1.0, 1.5, 2.0, 2.5, 3.0],  # ATR multiplier for stops
            'min_stop_distance': 0.001,                      # Minimum stop distance (1 pip)
            'adaptive_multiplier': True,                     # Adjust multiplier based on volatility
        }

    @staticmethod
    def get_config_for_strategy(strategy_name: str) -> Dict[str, Any]:
        """Get appropriate configuration for a strategy"""
        config_methods = {
            'ma': StrategyConfigs.get_moving_average_config,
            'rsi': StrategyConfigs.get_rsi_config,
            'bollinger': StrategyConfigs.get_bollinger_config,
            'atr': StrategyConfigs.get_atr_config,
            'moving_average': StrategyConfigs.get_moving_average_config,
            'bollinger_breakout': StrategyConfigs.get_bollinger_config,
            'atr_breakout': StrategyConfigs.get_atr_config,
        }

        # Find matching config
        strategy_lower = strategy_name.lower()
        for key, method in config_methods.items():
            if key in strategy_lower:
                return method()

        # Default configuration
        return StrategyConfigs.get_moving_average_config()


def load_config_from_file(config_path: str) -> BacktestConfiguration:
    """
    Load configuration from JSON/YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Loaded configuration object
    """
    import json

    path = Path(config_path)

    if not path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        return BacktestConfiguration()

    try:
        if path.suffix.lower() == '.json':
            with open(path, 'r') as f:
                config_data = json.load(f)
        else:
            logger.warning(f"Unsupported config format: {path.suffix}")
            return BacktestConfiguration()

        # Convert dict to BacktestConfiguration
        config = BacktestConfiguration()
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        logger.info(f"Loaded configuration from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return BacktestConfiguration()


def save_config_to_file(config: BacktestConfiguration, config_path: str) -> bool:
    """
    Save configuration to JSON file.

    Args:
        config: Configuration object to save
        config_path: Path to save configuration

    Returns:
        Success status
    """
    import json

    try:
        # Convert dataclass to dict
        config_dict = {}
        for key, value in config.__dict__.items():
            if key != 'custom_settings' or value:
                config_dict[key] = value

        # Create directory if needed
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Saved configuration to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False


def get_default_configuration() -> BacktestConfiguration:
    """Get default backtesting configuration"""
    return BacktestConfiguration()


def validate_configuration(config: BacktestConfiguration) -> Dict[str, Any]:
    """
    Validate configuration parameters.

    Args:
        config: Configuration to validate

    Returns:
        Validation results
    """
    issues = []

    # Validate numeric ranges
    if not 1 <= config.max_workers <= 16:
        issues.append(f"max_workers must be between 1-16, got {config.max_workers}")

    if not 0.01 <= config.significance_level <= 0.2:
        issues.append(f"significance_level must be between 0.01-0.2, got {config.significance_level}")

    if not 50 <= config.bootstrap_samples <= 10000:
        issues.append(f"bootstrap_samples must be between 50-10000, got {config.bootstrap_samples}")

    if not 500 <= config.chunk_size <= 10000:
        issues.append(f"chunk_size must be between 500-10000, got {config.chunk_size}")

    # Validate paths
    if config.log_directory and not os.path.isabs(config.log_directory):
        Path(config.cache_directory).mkdir(parents=True, exist_ok=True)

    if config.cache_directory and not os.path.isabs(config.cache_directory):
        Path(config.cache_directory).mkdir(parents=True, exist_ok=True)

    # Validate risk parameters
    if not 0 <= config.max_drawdown_limit <= 1:
        issues.append(f"max_drawdown_limit must be between 0-1 (0-100%), got {config.max_drawdown_limit}")

    if not 0 <= config.risk_free_rate <= 0.1:
        issues.append(f"risk_free_rate must be between 0-0.1 (0-10%), got {config.risk_free_rate}")

    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': []
    }


def merge_configurations(base_config: BacktestConfiguration,
                        override_config: BacktestConfiguration) -> BacktestConfiguration:
    """
    Merge two configurations, with override_config taking precedence.

    Args:
        base_config: Base configuration
        override_config: Configuration to override base values

    Returns:
        Merged configuration
    """
    merged = BacktestConfiguration()

    # Apply base config
    for key, value in base_config.__dict__.items():
        if key != 'custom_settings' or value:
            setattr(merged, key, value)

    # Apply overrides
    for key, value in override_config.__dict__.items():
        if hasattr(merged, key):
            setattr(merged, key, value)

    # Merge custom settings
    merged.custom_settings.update(base_config.custom_settings)
    merged.custom_settings.update(override_config.custom_settings)

    return merged


def get_environment_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables.

    Returns:
        Configuration dictionary from environment
    """
    env_config = {}

    # Data settings
    env_config['data_cache_enabled'] = os.getenv('BACKTEST_CACHE_ENABLED', 'true').lower() == 'true'
    env_config['data_validation_enabled'] = os.getenv('BACKTEST_VALIDATION_ENABLED', 'true').lower() == 'true'
    env_config['parallel_data_loading'] = os.getenv('BACKTEST_PARALLEL_LOADING', 'true').lower() == 'true'

    # Engine settings
    env_config['max_workers'] = int(os.getenv('BACKTEST_MAX_WORKERS', '4'))
    env_config['chunk_size'] = int(os.getenv('BACKTEST_CHUNK_SIZE', '1000'))
    env_config['memory_limit_mb'] = int(os.getenv('BACKTEST_MEMORY_LIMIT', '512'))

    # Performance settings
    env_config['enable_slippage_model'] = os.getenv('BACKTEST_SLIPPAGE_ENABLED', 'false').lower() == 'true'
    env_config['enable_commission_model'] = os.getenv('BACKTEST_COMMISSION_ENABLED', 'true').lower() == 'true'

    # Optimization settings
    env_config['optimization_timeout_seconds'] = int(os.getenv('BACKTEST_OPT_TIMEOUT', '3600'))
    env_config['max_evaluations_per_worker'] = int(os.getenv('BACKTEST_MAX_EVALS', '50'))

    # Risk settings
    env_config['max_drawdown_limit'] = float(os.getenv('BACKTEST_MAX_DD', '0.5'))
    env_config['risk_free_rate'] = float(os.getenv('BACKTEST_RF_RATE', '0.03'))

    # Output settings
    env_config['export_results'] = os.getenv('BACKTEST_EXPORT_RESULTS', 'true').lower() == 'true'
    env_config['export_format'] = os.getenv('BACKTEST_EXPORT_FORMAT', 'json')
    env_config['create_reports'] = os.getenv('BACKTEST_CREATE_REPORTS', 'true').lower() == 'true'

    # Paths
    env_config['log_directory'] = os.getenv('BACKTEST_LOG_DIR', 'logs')
    env_config['cache_directory'] = os.getenv('BACKTEST_CACHE_DIR', 'cache')
    env_config['results_directory'] = os.getenv('BACKTEST_RESULTS_DIR', 'results')

    return env_config


def apply_environment_config(base_config: BacktestConfiguration) -> BacktestConfiguration:
    """
    Apply environment variable configuration to base config.

    Args:
        base_config: Base configuration to modify

    Returns:
        Configuration with environment overrides applied
    """
    env_config = get_environment_config()

    for key, value in env_config.items():
        if hasattr(base_config, key):
            setattr(base_config, key, value)

    return base_config


def create_config_from_dict(config_dict: Dict[str, Any]) -> BacktestConfiguration:
    """
    Create BacktestConfiguration from dictionary.

    Args:
        config_dict: Dictionary containing configuration values

    Returns:
        BacktestConfiguration object
    """
    config = BacktestConfiguration()

    for key, value in config_dict.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config
