"""
TokemFX Configuration Module
============================
Centralized configuration management system for the entire application.

This module provides:
- Environment variable management
- Configuration file handling
- Settings validation
- Secrets management
- Dynamic configuration updates
"""

from .settings import AppSettings, DatabaseSettings, APISettings, TradingSettings
from .validator import ConfigValidator, validate_configuration
from .environment import EnvironmentManager, get_env_var, set_env_var

__all__ = [
    'AppSettings',
    'DatabaseSettings',
    'APISettings',
    'TradingSettings',
    'ConfigValidator',
    'validate_configuration',
    'EnvironmentManager',
    'get_env_var',
    'set_env_var',
]

__version__ = "1.0.0"
