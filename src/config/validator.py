"""
TokemFX Configuration Validator
===============================
Validation and sanity checking for configuration settings.

This module provides:
- Configuration validation
- Schema enforcement
- Range checking
- Cross-setting validation
- Security validation
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Configuration validator with comprehensive validation rules"""

    def __init__(self):
        self.validation_rules = {
            'app_settings': self._validate_app_settings,
            'database_settings': self._validate_database_settings,
            'api_settings': self._validate_api_settings,
            'trading_settings': self._validate_trading_settings,
        }

    def validate_config(self, config_type: str, config_obj: Any) -> Dict[str, Any]:
        """
        Validate a configuration object.

        Args:
            config_type: Type of configuration ('app_settings', 'database_settings', etc.)
            config_obj: Configuration object to validate

        Returns:
            Validation results dictionary
        """
        if config_type not in self.validation_rules:
            return {
                'is_valid': False,
                'errors': [f"Unknown configuration type: {config_type}"],
                'warnings': [],
                'severity': 'error'
            }

        try:
            validator_func = self.validation_rules[config_type]
            return validator_func(config_obj)
        except Exception as e:
            logger.error(f"Validation failed for {config_type}: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'severity': 'error'
            }

    def _validate_app_settings(self, settings) -> Dict[str, Any]:
        """Validate AppSettings"""
        errors = []
        warnings = []

        # Environment validation
        valid_environments = ['development', 'staging', 'production', 'testing']
        if settings.environment not in valid_environments:
            errors.append(f"Invalid environment '{settings.environment}'. Must be one of: {valid_environments}")

        # Path validation
        if not Path(settings.root_directory).exists():
            warnings.append(f"Root directory does not exist: {settings.root_directory}")

        # Performance validation
        if settings.max_workers < 1 or settings.max_workers > 32:
            errors.append(f"max_workers must be between 1-32, got {settings.max_workers}")

        if settings.memory_limit_mb < 128:
            warnings.append(f"Low memory limit: {settings.memory_limit_mb}MB may cause issues")

        # Log level validation
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if settings.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level '{settings.log_level}'. Must be one of: {valid_log_levels}")

        return self._create_validation_result(errors, warnings)

    def _validate_database_settings(self, settings) -> Dict[str, Any]:
        """Validate DatabaseSettings"""
        errors = []
        warnings = []

        # Redis validation
        if settings.redis_enabled:
            if not (1 <= settings.redis_port <= 65535):
                errors.append(f"Invalid Redis port: {settings.redis_port}")

            if settings.redis_host == "":
                errors.append("Redis host cannot be empty")

            if settings.redis_ttl_historical <= 0:
                errors.append(f"Redis TTL for historical data must be positive, got {settings.redis_ttl_historical}")

        # PostgreSQL validation
        if settings.postgresql_enabled:
            if not (1 <= settings.postgresql_port <= 65535):
                errors.append(f"Invalid PostgreSQL port: {settings.postgresql_port}")

            if settings.postgresql_user == "" or settings.postgresql_database == "":
                errors.append("PostgreSQL user and database cannot be empty")

        # Connection pooling validation
        if settings.max_connections < 1:
            errors.append(f"max_connections must be at least 1, got {settings.max_connections}")

        if settings.connection_timeout < 1:
            errors.append(f"connection_timeout must be at least 1 second, got {settings.connection_timeout}")

        return self._create_validation_result(errors, warnings)

    def _validate_api_settings(self, settings) -> Dict[str, Any]:
        """Validate APISettings"""
        errors = []
        warnings = []

        # Deriv API validation
        if settings.deriv_enabled:
            # URL validation
            if not settings.deriv_api_url.startswith(('ws://', 'wss://')):
                errors.append(f"Deriv API URL must use WebSocket protocol, got {settings.deriv_api_url}")

            # App ID validation
            if settings.deriv_app_id <= 0:
                errors.append(f"Invalid Deriv App ID: {settings.deriv_app_id}")

            # Account type validation
            if settings.deriv_account_type not in ['demo', 'real']:
                errors.append(f"Invalid account type '{settings.deriv_account_type}'. Must be 'demo' or 'real'")

        # Authentication validation
        valid_auth_modes = ['api', 'oauth']
        if settings.auth_mode not in valid_auth_modes:
            errors.append(f"Invalid auth mode '{settings.auth_mode}'. Must be one of: {valid_auth_modes}")

        if settings.auth_mode == 'oauth' and not settings.deriv_oauth_token:
            warnings.append("OAuth mode selected but no OAuth token provided")

        # Connection validation
        if settings.connection_timeout < 5:
            errors.append(f"Connection timeout too low: {settings.connection_timeout}s (minimum 5s)")

        if settings.max_retry_attempts < 0:
            errors.append(f"max_retry_attempts cannot be negative, got {settings.max_retry_attempts}")

        # Rate limiting validation
        if settings.rate_limit_requests <= 0:
            errors.append(f"rate_limit_requests must be positive, got {settings.rate_limit_requests}")

        if settings.rate_limit_window <= 0:
            errors.append(f"rate_limit_window must be positive, got {settings.rate_limit_window}")

        return self._create_validation_result(errors, warnings)

    def _validate_trading_settings(self, settings) -> Dict[str, Any]:
        """Validate TradingSettings"""
        errors = []
        warnings = []

        # Account settings validation
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD']
        if settings.default_currency not in valid_currencies:
            errors.append(f"Invalid currency '{settings.default_currency}'. Must be one of: {valid_currencies}")

        if settings.default_leverage < 1 or settings.default_leverage > 1000:
            errors.append(f"Invalid leverage {settings.default_leverage}. Must be between 1-1000")

        # Risk management validation
        if not 0 < settings.max_account_risk_pct <= 10:
            errors.append(f"max_account_risk_pct must be between 0-10%, got {settings.max_account_risk_pct}%")

        if not 0 < settings.max_position_size_pct <= 20:
            errors.append(f"max_position_size_pct must be between 0-20%, got {settings.max_position_size_pct}%")

        if settings.max_position_size_pct > settings.max_account_risk_pct:
            warnings.append("Position size limit exceeds account risk limit - this may cause issues")

        if not 0 < settings.max_drawdown_limit <= 50:
            errors.append(f"max_drawdown_limit must be between 0-50%, got {settings.max_drawdown_limit}%")

        # Position management validation
        if settings.max_open_positions < 1 or settings.max_open_positions > 50:
            errors.append(f"max_open_positions must be between 1-50, got {settings.max_open_positions}")

        valid_sizing_methods = ['fixed', 'kelly', 'percent_risk']
        if settings.position_sizing_method not in valid_sizing_methods:
            errors.append(f"Invalid sizing method '{settings.position_sizing_method}'. Must be one of: {valid_sizing_methods}")

        # Strategy parameter validation
        if settings.default_fast_period >= settings.default_slow_period:
            errors.append(f"Fast period ({settings.default_fast_period}) must be less than slow period ({settings.default_slow_period})")

        if not 10 <= settings.default_rsi_period <= 50:
            errors.append(f"RSI period must be between 10-50, got {settings.default_rsi_period}")

        if settings.default_rsi_oversold >= settings.default_rsi_overbought:
            errors.append("RSI oversold level must be below overbought level")

        # Execution validation
        if settings.slippage_tolerance < 0 or settings.slippage_tolerance > 0.01:
            errors.append(f"slippage_tolerance must be between 0-1%, got {settings.slippage_tolerance}")

        if settings.execution_timeout < 10 or settings.execution_timeout > 300:
            warnings.append(f"Unusual execution timeout: {settings.execution_timeout}s")

        # Trading hours validation
        if settings.trading_hours_enabled:
            try:
                # Validate time format
                import datetime
                datetime.datetime.strptime(settings.market_open_time, '%H:%M')
                datetime.datetime.strptime(settings.market_close_time, '%H:%M')
            except ValueError:
                errors.append("Invalid time format for trading hours (must be HH:MM)")

        # Call built-in validation method
        risk_issues = settings.validate_risk_parameters()
        for issue_key, issue_msg in risk_issues.items():
            errors.append(f"Risk validation - {issue_key}: {issue_msg}")

        return self._create_validation_result(errors, warnings)

    def _create_validation_result(self, errors: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Create standardized validation result"""
        is_valid = len(errors) == 0

        severity = 'error' if errors else ('warning' if warnings else 'success')

        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'severity': severity,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }


def validate_configuration(config_dict: Dict[str, Any],
                          schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate configuration dictionary against schema.

    Args:
        config_dict: Configuration dictionary to validate
        schema: Optional validation schema

    Returns:
        Validation results
    """
    validator = ConfigValidator()
    results = {}

    # Validate each configuration section
    config_sections = ['app_settings', 'database_settings', 'api_settings', 'trading_settings']

    all_valid = True
    total_errors = 0
    total_warnings = 0

    for section in config_sections:
        if section in config_dict or f"{section}_obj" in config_dict:
            # Get config object (either directly or from config_dict)
            config_obj = config_dict.get(section) or config_dict.get(f"{section}_obj")

            if config_obj:
                section_result = validator.validate_config(section, config_obj)
                results[section] = section_result

                if not section_result['is_valid']:
                    all_valid = False

                total_errors += section_result['error_count']
                total_warnings += section_result['warning_count']
            else:
                results[section] = {
                    'is_valid': False,
                    'errors': [f"Configuration object not found for {section}"],
                    'warnings': [],
                    'severity': 'error',
                    'error_count': 1,
                    'warning_count': 0
                }
                all_valid = False
                total_errors += 1

    # Schema validation if provided
    if schema:
        schema_result = validate_against_schema(config_dict, schema)
        results['schema_validation'] = schema_result

        if not schema_result['is_valid']:
            all_valid = False
            total_errors += schema_result['error_count']

    results['overall'] = {
        'is_valid': all_valid,
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'severity': 'error' if total_errors > 0 else ('warning' if total_warnings > 0 else 'success')
    }

    return results


def validate_against_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration against a JSON schema"""
    errors = []
    warnings = []

    try:
        # Basic schema validation
        for key, rules in schema.items():
            if key not in config:
                if rules.get('required', False):
                    errors.append(f"Required field missing: {key}")
                continue

            value = config[key]
            expected_type = rules.get('type')

            # Type validation
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{key}' must be string, got {type(value).__name__}")
                elif expected_type == 'number':
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field '{key}' must be number, got {type(value).__name__}")
                    else:
                        # Range validation
                        min_val = rules.get('minimum')
                        max_val = rules.get('maximum')
                        if min_val is not None and value < min_val:
                            errors.append(f"Field '{key}' must be >= {min_val}, got {value}")
                        if max_val is not None and value > max_val:
                            errors.append(f"Field '{key}' must be <= {max_val}, got {value}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{key}' must be boolean, got {type(value).__name__}")

            # Enum validation
            allowed_values = rules.get('enum')
            if allowed_values and value not in allowed_values:
                errors.append(f"Field '{key}' must be one of {allowed_values}, got {value}")

            # Pattern validation
            pattern = rules.get('pattern')
            if pattern and isinstance(value, str):
                if not re.match(pattern, value):
                    errors.append(f"Field '{key}' does not match pattern {pattern}")

    except Exception as e:
        errors.append(f"Schema validation failed: {str(e)}")

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'severity': 'error' if errors else 'success',
        'error_count': len(errors),
        'warning_count': len(warnings)
    }


def validate_environment_variables(required_vars: List[str],
                                 optional_vars: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate that required environment variables are set.

    Args:
        required_vars: List of required environment variable names
        optional_vars: List of optional environment variable names

    Returns:
        Validation results
    """
    import os

    errors = []
    warnings = []

    # Check required variables
    for var in required_vars:
        if var not in os.environ or os.environ[var].strip() == "":
            errors.append(f"Required environment variable not set: {var}")
        elif len(os.environ[var]) < 8 and 'token' in var.lower():
            warnings.append(f"Potentially short token length for {var}")

    # Check optional variables
    if optional_vars:
        for var in optional_vars:
            if var in os.environ and os.environ[var].strip() == "":
                warnings.append(f"Optional environment variable is empty: {var}")

    # Security checks
    sensitive_vars = ['token', 'password', 'secret', 'key']
    for var in required_vars + (optional_vars or []):
        if var in os.environ:
            value = os.environ[var]

            # Check for potentially sensitive data in logs
            for sensitive in sensitive_vars:
                if sensitive.lower() in var.lower() and len(value) > 10:
                    warnings.append(f"Sensitive environment variable detected: {var} (ensure not logged)")

            # Check for common weak patterns (for tokens/keys)
            if any(s in var.lower() for s in ['token', 'key', 'secret']):
                if value in ['12345', 'password', 'admin', 'test']:
                    warnings.append(f"Potentially weak value for sensitive variable: {var}")

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'severity': 'error' if errors else ('warning' if warnings else 'success'),
        'error_count': len(errors),
        'warning_count': len(warnings)
    }


def validate_file_permissions(file_path: str, required_permissions: str = 'rw') -> Dict[str, Any]:
    """
    Validate file permissions for configuration files.

    Args:
        file_path: Path to file to check
        required_permissions: Required permissions ('r', 'w', 'rw')

    Returns:
        Permission validation results
    """
    errors = []
    warnings = []

    path = Path(file_path)

    if not path.exists():
        return {
            'is_valid': False,
            'errors': [f"File does not exist: {file_path}"],
            'warnings': warnings,
            'severity': 'error'
        }

    try:
        # Check read permission
        if 'r' in required_permissions and not path.stat().st_mode & 0o400:
            errors.append(f"Read permission denied for {file_path}")

        # Check write permission
        if 'w' in required_permissions and not path.stat().st_mode & 0o200:
            errors.append(f"Write permission denied for {file_path}")

        # Security warnings
        if oct(path.stat().st_mode)[-2:] == '77':
            warnings.append(f"File permissions too permissive (777): {file_path}")

    except Exception as e:
        errors.append(f"Permission check failed: {str(e)}")

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'severity': 'error' if errors else ('warning' if warnings else 'success'),
        'error_count': len(errors),
        'warning_count': len(warnings)
    }


def validate_network_connectivity(hosts: List[str], timeout: int = 5) -> Dict[str, Any]:
    """
    Validate network connectivity to required hosts.

    Args:
        hosts: List of hostnames/IPs to test
        timeout: Connection timeout in seconds

    Returns:
        Connectivity validation results
    """
    errors = []
    warnings = []

    try:
        import socket

        for host in hosts:
            try:
                # Try to resolve hostname
                socket.gethostbyname(host)
                # Try a basic connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                # For basic connectivity test, try port 80
                result = sock.connect_ex((host, 80))
                sock.close()

                if result != 0:
                    warnings.append(f"Cannot connect to {host} (may be firewalled)")

            except socket.gaierror:
                errors.append(f"Cannot resolve hostname: {host}")
            except socket.timeout:
                warnings.append(f"Connection timeout to {host}")
            except Exception as e:
                warnings.append(f"Connectivity check failed for {host}: {str(e)}")

    except ImportError:
        warnings.append("Socket module not available for connectivity testing")

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'severity': 'error' if errors else ('warning' if warnings else 'success'),
        'error_count': len(errors),
        'warning_count': len(warnings)
    }
