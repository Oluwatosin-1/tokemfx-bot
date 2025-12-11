"""
TokemFX Environment Manager
===========================
Environment variable management and configuration loading.

This module provides:
- Environment variable access with validation
- Secret management and security
- Dynamic environment detection
- Configuration environment loading
"""

import os
import logging
from typing import Dict, Any, Optional, Union, List, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Centralized environment variable management with security and validation.
    """

    def __init__(self, prefix: str = "TOKEMFX_", auto_load: bool = True):
        """
        Initialize environment manager.

        Args:
            prefix: Environment variable prefix for this application
            auto_load: Automatically load relevant env vars on init
        """
        self.prefix = prefix
        self._cache = {}
        self._validators = {}

        if auto_load:
            self.load_application_environment()

    def load_application_environment(self) -> Dict[str, Any]:
        """
        Load all TokemFX-related environment variables.

        Returns:
            Dictionary of loaded environment variables
        """
        env_vars = {}

        # Define expected environment variables
        expected_vars = {
            # API Keys and tokens
            'DERIV_API_TOKEN': None,
            'DERIV_ACCOUNT_ID': None,
            'DERIV_OAUTH_TOKEN': None,
            'DERIV_APP_ID': '96454',

            # Database
            'REDIS_URL': None,
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379',
            'REDIS_PASSWORD': None,
            'POSTGRES_URL': None,

            # Application settings
            'ENVIRONMENT': 'development',
            'LOG_LEVEL': 'INFO',
            'MAX_WORKERS': '4',
            'MEMORY_LIMIT_MB': '1024',

            # Feature flags
            'ENABLE_MONITORING': 'true',
            'ENABLE_ALERTS': 'true',
            'ENABLE_CACHING': 'true',

            # Paths
            'LOG_DIR': 'logs',
            'CACHE_DIR': 'cache',
            'DATA_DIR': 'data',
            'CONFIG_DIR': 'config',

            # Secrets (marked as sensitive)
            'ENCRYPTION_KEY': None,
            'JWT_SECRET': None,

            # Database credentials
            'DB_USER': None,
            'DB_PASSWORD': None,
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'tokemfx',
        }

        for var_name, default_value in expected_vars.items():
            full_name = f"{self.prefix}{var_name}" if self.prefix != "TOKEMFX_" else var_name

            try:
                value = self.get_env_var(var_name, default_value)
                if value is not None:
                    env_vars[var_name] = value

                # Security: Don't cache sensitive values
                if not self._is_sensitive_variable(var_name):
                    self._cache[var_name] = value

            except Exception as e:
                logger.warning(f"Failed to load environment variable {var_name}: {e}")

        logger.info(f"Loaded {len(env_vars)} environment variables")
        return env_vars

    def get_env_var(self, name: str,
                   default: Any = None,
                   required: bool = False,
                   validator: Optional[Callable[[Any], bool]] = None) -> Any:
        """
        Get environment variable with validation and type conversion.

        Args:
            name: Environment variable name (without prefix)
            default: Default value if not set
            required: Whether variable is required
            validator: Optional validation function

        Returns:
            Environment variable value or default
        """
        full_name = f"{self.prefix}{name}" if self.prefix != "TOKEMFX_" else name

        # Check cache first (for non-sensitive vars)
        if name in self._cache and not self._is_sensitive_variable(name):
            return self._cache[name]

        value = os.environ.get(full_name)

        if value is None or value.strip() == "":
            if required:
                raise ValueError(f"Required environment variable '{full_name}' is not set")
            return default

        # Type conversion
        converted_value = self._convert_value(value)

        # Validation
        if validator and not validator(converted_value):
            raise ValueError(f"Environment variable '{full_name}' failed validation")

        # Security check for sensitive variables
        if self._is_sensitive_variable(name) and len(str(converted_value)) > 0:
            logger.info(f"Sensitive environment variable '{full_name}' loaded (length: {len(str(converted_value))})")

        return converted_value

    def set_env_var(self, name: str, value: Any, persistent: bool = False) -> bool:
        """
        Set environment variable.

        Args:
            name: Variable name (without prefix)
            value: Variable value
            persistent: Whether to make persistent (modify actual env)

        Returns:
            Success status
        """
        try:
            full_name = f"{self.prefix}{name}" if self.prefix != "TOKEMFX_" else name

            # Convert value to string for environment
            str_value = str(value) if value is not None else ""

            # Set in current process
            os.environ[full_name] = str_value

            # Update cache (for non-sensitive vars)
            if not self._is_sensitive_variable(name):
                self._cache[name] = value

            logger.debug(f"Set environment variable: {full_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to set environment variable {name}: {e}")
            return False

    def get_all_env_vars(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Get all environment variables (optionally including sensitive ones).

        Args:
            include_sensitive: Whether to include sensitive variables

        Returns:
            Dictionary of environment variables
        """
        all_vars = {}

        # Get from cache
        for name, value in self._cache.items():
            if include_sensitive or not self._is_sensitive_variable(name):
                all_vars[name] = value

        # Get any additional env vars that match our prefix
        prefix_len = len(self.prefix) if self.prefix != "TOKEMFX_" else 0
        for env_name, env_value in os.environ.items():
            if env_name.startswith(self.prefix):
                var_name = env_name[prefix_len:] if prefix_len > 0 else env_name

                if var_name not in all_vars:  # Don't overwrite cache
                    if include_sensitive or not self._is_sensitive_variable(var_name):
                        all_vars[var_name] = self._convert_value(env_value)

        return all_vars

    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate current environment configuration.

        Returns:
            Validation results
        """
        results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }

        # Check required variables for basic functionality
        required_vars = []
        for var in ['DERIV_API_TOKEN', 'DERIV_APP_ID']:
            try:
                self.get_env_var(var, required=True)
            except ValueError:
                required_vars.append(var)

        if required_vars:
            results['is_valid'] = False
            results['issues'].append(f"Missing required variables: {', '.join(required_vars)}")
            results['recommendations'].append("Set required environment variables or configure API credentials")

        # Check database configuration
        if self.get_env_var('DB_USER') and not self.get_env_var('DB_PASSWORD'):
            results['warnings'].append("Database user specified but no password set")

        # Security checks
        sensitive_vars = ['ENCRYPTION_KEY', 'JWT_SECRET', 'DERIV_OAUTH_TOKEN']
        weak_keys = []

        for var in sensitive_vars:
            try:
                value = self.get_env_var(var)
                if value and str(value) in ['12345', 'password', 'admin', 'test', 'key']:
                    weak_keys.append(var)
            except:
                pass

        if weak_keys:
            results['issues'].append(f"Weak or default values detected for: {', '.join(weak_keys)}")
            results['recommendations'].append("Generate strong random keys for sensitive variables")

        # Path validation
        paths_to_check = ['LOG_DIR', 'CACHE_DIR', 'DATA_DIR']
        missing_dirs = []

        for path_var in paths_to_check:
            try:
                path_str = self.get_env_var(path_var)
                if path_str:
                    path = Path(path_str)
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                    elif not path.is_dir():
                        missing_dirs.append(path_var)
            except Exception as e:
                results['warnings'].append(f"Path validation failed for {path_var}: {e}")

        if missing_dirs:
            results['warnings'].append(f"Some path variables point to files instead of directories: {', '.join(missing_dirs)}")

        return results

    def create_env_file_template(self, output_path: str = ".env.template") -> bool:
        """
        Create a .env template file with all supported variables.

        Args:
            output_path: Path to save template file

        Returns:
            Success status
        """
        template = """# TokemFX Environment Configuration Template
# Copy this file to .env and fill in your actual values

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

# Deriv API Credentials (Required)
DERIV_API_TOKEN=your_api_token_here
DERIV_ACCOUNT_ID=your_account_id_here
DERIV_APP_ID=96454

# OAuth Token (Alternative authentication - more secure)
DERIV_OAUTH_TOKEN=your_oauth_token_here

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379/0

# PostgreSQL Configuration (Optional - for advanced features)
POSTGRES_URL=postgresql://user:password@localhost:5432/tokemfx
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tokemfx

# ==============================================================================
# APPLICATION SETTINGS
# ==============================================================================

# Environment
ENVIRONMENT=development

# Performance
MAX_WORKERS=4
MEMORY_LIMIT_MB=1024

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Feature Flags
ENABLE_MONITORING=true
ENABLE_ALERTS=true
ENABLE_CACHING=true

# ==============================================================================
# PATHS
# ==============================================================================

# Data directories
CACHE_DIR=cache
DATA_DIR=data
CONFIG_DIR=config

# ==============================================================================
# SECURITY
# ==============================================================================

# Generate strong random keys (64+ characters recommended)
ENCRYPTION_KEY=your_random_encryption_key_here
JWT_SECRET=your_random_jwt_secret_here

# ==============================================================================
# EXPERT SETTINGS (Optional)
# ==============================================================================

# Backtesting configuration
BACKTEST_CACHE_ENABLED=true
BACKTEST_VALIDATION_ENABLED=true
BACKTEST_MAX_WORKERS=4

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
"""

        try:
            with open(output_path, 'w') as f:
                f.write(template)

            logger.info(f"Created environment template file: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create environment template: {e}")
            return False

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Convert string environment variable to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Converted value
        """
        value = value.strip()

        # Boolean conversion
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False

        # Integer conversion
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def _is_sensitive_variable(self, name: str) -> bool:
        """
        Check if a variable name contains sensitive information.

        Args:
            name: Variable name to check

        Returns:
            True if variable contains sensitive data
        """
        sensitive_keywords = [
            'token', 'key', 'secret', 'password', 'credential',
            'auth', 'oauth', 'bearer', 'jwt', 'encryption'
        ]

        name_lower = name.lower()
        return any(keyword in name_lower for keyword in sensitive_keywords)

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get comprehensive environment information.

        Returns:
            Dictionary with environment details
        """
        import platform

        return {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'working_directory': str(Path.cwd()),
            'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown')),
            'env_var_count': len(dict(os.environ)),
            'sensitive_vars_loaded': len([
                name for name in self.get_all_env_vars(include_sensitive=True).keys()
                if self._is_sensitive_variable(name)
            ]),
            'config_vars_loaded': len(self._cache),
            'environment_validation': self.validate_environment()
        }


def get_env_var(name: str, default: Any = None, required: bool = False) -> Any:
    """
    Convenience function to get environment variable.

    Args:
        name: Variable name
        default: Default value
        required: Whether required

    Returns:
        Variable value
    """
    manager = EnvironmentManager()
    return manager.get_env_var(name, default, required)


def set_env_var(name: str, value: Any) -> bool:
    """
    Convenience function to set environment variable.

    Args:
        name: Variable name
        value: Variable value

    Returns:
        Success status
    """
    manager = EnvironmentManager()
    return manager.set_env_var(name, value)


def load_environment_from_file(file_path: str) -> bool:
    """
    Load environment variables from .env style file.

    Args:
        file_path: Path to environment file

    Returns:
        Success status
    """
    try:
        if not Path(file_path).exists():
            logger.warning(f"Environment file not found: {file_path}")
            return False

        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

        logger.info(f"Loaded environment variables from {file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to load environment file {file_path}: {e}")
        return False


def create_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Args:
        length: Token length in characters

    Returns:
        Random token string
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))
