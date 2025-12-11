"""
TokemFX Application Settings
============================
Configuration settings for all application components.

This module defines structured configuration classes for:
- Application settings (logging, paths, etc.)
- Database settings (Redis, PostgreSQL, etc.)
- API settings (Deriv, external APIs)
- Trading settings (risk management, limits)
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """General application settings"""

    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False

    # Paths
    root_directory: str = str(Path(__file__).parent.parent.parent)
    logs_directory: str = "logs"
    cache_directory: str = "cache"
    data_directory: str = "data"
    config_directory: str = "config"

    # Performance
    max_workers: int = 4
    memory_limit_mb: int = 1024
    enable_profiling: bool = False

    # Features
    enable_monitoring: bool = True
    enable_alerts: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def get_log_directory(self) -> Path:
        """Get absolute path to logs directory"""
        return Path(self.root_directory) / self.logs_directory

    def get_cache_directory(self) -> Path:
        """Get absolute path to cache directory"""
        return Path(self.root_directory) / self.cache_directory

    def get_data_directory(self) -> Path:
        """Get absolute path to data directory"""
        return Path(self.root_directory) / self.data_directory


@dataclass
class DatabaseSettings:
    """Database connection settings for various data stores"""

    # Redis settings
    redis_enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_ttl_historical: int = 3600  # 1 hour
    redis_ttl_latest: int = 300       # 5 minutes

    # PostgreSQL settings (for future use)
    postgresql_enabled: bool = False
    postgresql_host: str = "localhost"
    postgresql_port: int = 5432
    postgresql_database: str = "tokemfx"
    postgresql_user: str = "postgres"
    postgresql_password: Optional[str] = None
    postgresql_ssl_mode: str = "require"

    # SQLite settings (for local storage)
    sqlite_enabled: bool = True
    sqlite_path: str = "cache/tokemfx.db"
    sqlite_backup_enabled: bool = True

    # Connection pooling
    max_connections: int = 10
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

    def get_redis_url(self) -> str:
        """Generate Redis connection URL"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_postgresql_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (f"postgresql://{self.postgresql_user}:{self.postgresql_password}@"
                f"{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"
                f"?sslmode={self.postgresql_ssl_mode}")


@dataclass
class APISettings:
    """External API configuration settings"""

    # Deriv API settings (consolidated from tokemfx config)
    deriv_enabled: bool = True
    deriv_api_url: str = "wss://ws.derivws.com/websockets/v3"
    deriv_app_id: int = int(os.getenv("DERIV_APP_ID", "96454"))
    deriv_account_type: str = os.getenv("DERIV_ACCOUNT_TYPE", "demo")  # auto, demo, real

    # API credentials (loaded from environment)
    deriv_api_token: Optional[str] = os.getenv("DERIV_API_TOKEN")
    deriv_account_id: Optional[str] = os.getenv("DERIV_ACCOUNT_ID")
    deriv_oauth_token: Optional[str] = os.getenv("DERIV_OAUTH_TOKEN")

    # Authentication settings
    auth_mode: str = os.getenv("DERIV_AUTH_MODE", "api")  # api, oauth
    oauth_client_id: Optional[str] = os.getenv("DERIV_CLIENT_ID", "deriv_app")
    token_refresh_enabled: bool = True
    token_refresh_interval: int = 1800  # 30 minutes

    # Connection settings
    connection_timeout: int = 30
    max_retry_attempts: int = 3
    retry_backoff: float = 1.5
    rate_limit_requests: int = 100  # per minute
    rate_limit_window: int = 60     # seconds

    # Data settings
    max_historical_bars: int = 5000
    data_compression: bool = True
    realtime_enabled: bool = True

    # Monitoring
    api_health_check: bool = True
    latency_monitoring: bool = True
    error_reporting: bool = True

    def is_oauth_enabled(self) -> bool:
        """Check if OAuth authentication is configured"""
        return self.auth_mode == "oauth" and self.deriv_oauth_token is not None

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TokemFX/1.0"
        }

        if self.deriv_oauth_token:
            headers["Authorization"] = f"Bearer {self.deriv_oauth_token}"

        return headers

    def get_websocket_url(self) -> str:
        """Generate complete Deriv WebSocket URL"""
        return f"{self.deriv_api_url}?app_id={self.deriv_app_id}"

    def get_deriv_auth_config(self) -> Dict[str, Any]:
        """Get comprehensive Deriv authentication configuration"""
        return {
            'app_id': self.deriv_app_id,
            'api_token': self.deriv_api_token,
            'oauth_token': self.deriv_oauth_token,
            'account_id': self.deriv_account_id,
            'account_type': self.deriv_account_type,
            'auth_mode': self.auth_mode,
            'client_id': self.oauth_client_id,
            'websocket_url': self.get_websocket_url(),
            'validation': {
                'has_api_token': bool(self.deriv_api_token),
                'has_oauth_token': bool(self.deriv_oauth_token),
                'has_account_id': bool(self.deriv_account_id)
            }
        }

    def validate_deriv_config(self) -> tuple[bool, list, list]:
        """Validate Deriv configuration"""
        issues = []
        recommendations = []

        # Check basic requirements
        if not self.deriv_app_id:
            issues.append("DERIV_APP_ID is missing")

        # Check authentication tokens
        if not self.deriv_api_token and not self.deriv_oauth_token:
            issues.append("No authentication token found (neither API nor OAuth)")

        if self.auth_mode == 'api' and not self.deriv_api_token:
            issues.append("Auth mode set to 'api' but DERIV_API_TOKEN is missing")

        if self.auth_mode == 'oauth' and not self.deriv_oauth_token:
            issues.append("Auth mode set to 'oauth' but DERIV_OAUTH_TOKEN is missing")

        # Check account IDs
        if not self.deriv_account_id:
            issues.append("DERIV_ACCOUNT_ID is missing")

        # Generate recommendations
        if issues:
            recommendations.append("Set your environment variables in .env file")

        if not self.deriv_oauth_token and self.deriv_account_id:
            recommendations.append("Consider using OAuth token for real account balance access")

        if self.deriv_api_token and not self.deriv_oauth_token:
            recommendations.append("API tokens work for demo accounts and basic trading")

        return len(issues) == 0, issues, recommendations


@dataclass
class TradingSettings:
    """Trading-specific configuration settings"""

    # Account settings
    default_currency: str = "USD"
    default_leverage: int = 100
    max_account_risk_pct: float = 2.0  # Max risk per trade as % of account

    # Position management
    max_open_positions: int = 5
    max_position_size_pct: float = 5.0  # Max size as % of account
    position_sizing_method: str = "fixed"  # fixed, kelly, percent_risk

    # Risk management
    stop_loss_required: bool = True
    take_profit_required: bool = True
    max_drawdown_limit: float = 10.0  # Max drawdown before stopping
    daily_loss_limit: float = 5.0     # Max daily loss
    trailing_stop_enabled: bool = False

    # Strategy defaults
    default_fast_period: int = 10
    default_slow_period: int = 30
    default_rsi_period: int = 14
    default_rsi_oversold: float = 30.0
    default_rsi_overbought: float = 70.0

    # Execution settings
    slippage_tolerance: float = 0.001  # 0.1% slippage tolerance
    max_slippage_pct: float = 0.005    # 0.5% max slippage
    execution_timeout: int = 30        # seconds
    partial_fill_allowed: bool = True

    # Monitoring and alerts
    trade_alerts_enabled: bool = True
    risk_alerts_enabled: bool = True
    performance_tracking: bool = True
    trade_journal_enabled: bool = True

    # Hours of operation
    trading_hours_enabled: bool = False
    trading_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    market_open_time: str = "00:00"    # UTC
    market_close_time: str = "23:59"   # UTC

    def validate_risk_parameters(self) -> Dict[str, str]:
        """Validate risk management parameters"""
        issues = {}

        if not 0 < self.max_account_risk_pct <= 10:
            issues['max_account_risk_pct'] = f"Must be between 0-10%, got {self.max_account_risk_pct}%"

        if not 0 < self.max_position_size_pct <= 20:
            issues['max_position_size_pct'] = f"Must be between 0-20%, got {self.max_position_size_pct}%"

        if not 0 < self.max_drawdown_limit <= 50:
            issues['max_drawdown_limit'] = f"Must be between 0-50%, got {self.max_drawdown_limit}%"

        if self.max_account_risk_pct > self.max_drawdown_limit:
            issues['risk_consistency'] = "Account risk should not exceed drawdown limit"

        return issues

    def get_kelly_fraction(self, win_rate: float, win_loss_ratio: float) -> float:
        """Calculate Kelly Criterion bet size"""
        if win_rate <= 0 or win_rate >= 1 or win_loss_ratio <= 0:
            return 0.0

        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)

        # Conservative Kelly (half size for safety)
        return max(0.0, kelly * 0.5)


@dataclass
class NotificationSettings:
    """Alert and notification configuration settings"""

    # Telegram settings
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

    # Email settings
    email_enabled: bool = False
    smtp_host: Optional[str] = os.getenv("SMTP_HOST", "smtp.titan.mail")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASS")
    smtp_use_tls: bool = True
    alert_email: Optional[str] = os.getenv("ALERT_EMAIL")

    # Risk alerting
    drawdown_alert_threshold: float = float(os.getenv("DRAW_ALERT_THRESHOLD", "0.05"))  # 5%
    risk_alerts_enabled: bool = True
    trade_alerts_enabled: bool = True
    system_alerts_enabled: bool = True

    # Notification frequency
    max_alerts_per_hour: int = 10
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"  # UTC
    quiet_hours_end: str = "06:00"    # UTC

    # Strategy-specific alerts
    strategy_alerts_enabled: bool = True
    signal_alerts_enabled: bool = True
    entry_exit_alerts_enabled: bool = True
    profit_loss_alerts_enabled: bool = True

    def is_telegram_configured(self) -> bool:
        """Check if Telegram notifications are properly configured"""
        return (self.telegram_enabled and
                bool(self.telegram_bot_token) and
                bool(self.telegram_chat_id))

    def is_email_configured(self) -> bool:
        """Check if Email notifications are properly configured"""
        return (self.email_enabled and
                bool(self.smtp_username) and
                bool(self.smtp_password) and
                bool(self.alert_email))

    def can_send_notifications(self) -> bool:
        """Check if any notification channel is configured"""
        return self.is_telegram_configured() or self.is_email_configured()

    def get_alert_channels(self) -> list[str]:
        """Get list of configured alert channels"""
        channels = []
        if self.is_telegram_configured():
            channels.append("telegram")
        if self.is_email_configured():
            channels.append("email")
        return channels


def load_settings_from_file(settings_path: str) -> AppSettings:
    """
    Load application settings from JSON file.

    Args:
        settings_path: Path to settings file

    Returns:
        Loaded AppSettings object
    """
    import json

    path = Path(settings_path)

    if not path.exists():
        logger.warning(f"Settings file not found: {settings_path}")
        return AppSettings()

    try:
        with open(path, 'r') as f:
            data = json.load(f)

        # Convert nested objects
        app_settings = AppSettings(**data.get('app', {}))
        app_settings.custom_settings = data.get('custom', {})

        return app_settings

    except Exception as e:
        logger.error(f"Failed to load settings from {settings_path}: {e}")
        return AppSettings()


def save_settings_to_file(settings: AppSettings, settings_path: str) -> bool:
    """
    Save application settings to JSON file.

    Args:
        settings: Settings object to save
        settings_path: Path to save settings

    Returns:
        Success status
    """
    import json

    try:
        # Convert to dictionary
        settings_dict = {
            'app': {
                k: v for k, v in settings.__dict__.items() if k != 'custom_settings'
            },
            'custom': settings.custom_settings
        }

        # Ensure directory exists
        Path(settings_path).parent.mkdir(parents=True, exist_ok=True)

        with open(settings_path, 'w') as f:
            json.dump(settings_dict, f, indent=2, default=str)

        logger.info(f"Settings saved to {settings_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save settings to {settings_path}: {e}")
        return False


def create_default_settings() -> AppSettings:
    """Create default application settings"""
    return AppSettings()


def merge_settings(base_settings: AppSettings, override_settings: AppSettings) -> AppSettings:
    """
    Merge two AppSettings objects, with override taking precedence.

    Args:
        base_settings: Base settings
        override_settings: Override settings

    Returns:
        Merged settings
    """
    merged = AppSettings()

    # Apply base settings
    for key, value in base_settings.__dict__.items():
        setattr(merged, key, value)

    # Apply overrides
    for key, value in override_settings.__dict__.items():
        setattr(merged, key, value)

    # Merge custom settings
    merged.custom_settings.update(base_settings.custom_settings)

    return merged

# Create global instances for easy access
app_settings = AppSettings()
api_settings = APISettings()
trading_settings = TradingSettings()
notification_settings = NotificationSettings()
database_settings = DatabaseSettings()

# Convenience aliases for backward compatibility
API_SETTINGS = api_settings
TRADING_SETTINGS = trading_settings
NOTIFICATION_SETTINGS = notification_settings

__all__ = [
    'AppSettings',
    'DatabaseSettings',
    'APISettings',
    'TradingSettings',
    'NotificationSettings',
    # Global instances
    'app_settings',
    'api_settings',
    'trading_settings',
    'notification_settings',
    'database_settings',
    # Aliases for backward compatibility
    'API_SETTINGS',
    'TRADING_SETTINGS',
    'NOTIFICATION_SETTINGS'
]
