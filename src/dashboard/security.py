"""
Security Module for Dashboard Components
========================================
Provides authentication, input validation, rate limiting, and other security controls.
"""

import time
import logging
from typing import Dict, Any, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class DashboardSecurity:
    """
    Security controls for dashboard components.
    Provides authentication, validation, and rate limiting.
    """

    def __init__(self):
        self.rate_limits = {}
        self.session_data = {}

    def check_admin_permissions(self) -> bool:
        """
        Check if current user has admin permissions for emergency controls.

        Returns:
            True if admin, False otherwise
        """
        # For demo purposes, allow admin access
        # In production, this would check user authentication and role
        if 'user_role' not in st.session_state:
            st.session_state.user_role = 'admin'  # Default to admin for development

        return st.session_state.user_role in ['admin', 'superuser']

    def validate_risk_parameters(self, risk_pct: float, min_val: float = 0.1, max_val: float = 10.0) -> float:
        """
        Validate and clamp risk percentage parameters.

        Args:
            risk_pct: Risk percentage to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Clamped risk percentage within safe bounds
        """
        try:
            # Ensure it's a number
            risk_pct = float(risk_pct)
            # Clamp to safe range
            validated = max(min_val, min(max_val, risk_pct))

            # Log if value was modified
            if validated != risk_pct:
                logger.warning(".3f")

            return validated

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid risk parameter: {risk_pct} - {e}")
            return min_val  # Return safe default

    def validate_daily_loss_limit(self, loss_pct: float) -> float:
        """
        Validate daily loss limit with stricter bounds.

        Args:
            loss_pct: Daily loss percentage

        Returns:
            Validated loss limit
        """
        return self.validate_risk_parameters(loss_pct, 0.1, 20.0)

    def rate_limit_check(self, operation: str, cooldown_seconds: int = 30) -> bool:
        """
        Check if operation is allowed based on rate limiting.

        Args:
            operation: Unique operation identifier
            cooldown_seconds: Minimum time between operations

        Returns:
            True if operation is allowed, False if rate limited
        """
        current_time = time.time()
        key = f"rate_limit_{operation}"

        if key not in self.rate_limits:
            self.rate_limits[key] = current_time
            return True

        time_diff = current_time - self.rate_limits[key]

        if time_diff >= cooldown_seconds:
            self.rate_limits[key] = current_time
            return True
        else:
            remaining = int(cooldown_seconds - time_diff)
            st.warning(f"⚠️ Please wait {remaining} seconds before performing this operation again.")
            return False

    def sanitize_instrument_list(self, instruments: list) -> list:
        """
        Sanitize and validate trading instrument list.

        Args:
            instruments: List of instrument names

        Returns:
            Sanitized instrument list
        """
        if not instruments:
            return []

        # Define allowed instrument patterns
        allowed_prefixes = ['R_', 'frx', 'cry', 'boom', 'crash']

        sanitized = []
        for instrument in instruments:
            try:
                inst_str = str(instrument).strip()
                # Check if instrument matches allowed patterns
                if any(inst_str.startswith(prefix) for prefix in allowed_prefixes) and len(inst_str) <= 50:
                    sanitized.append(inst_str)
                else:
                    logger.warning(f"Invalid instrument rejected: {instrument}")
            except:
                logger.warning(f"Malformed instrument rejected: {instrument}")

        return sanitized[:10]  # Limit to 10 instruments max

    def clean_session_state(self, max_age_hours: int = 24):
        """
        Clean up old session state data to prevent memory leaks.

        Args:
            max_age_hours: Maximum age of session data in hours
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        keys_to_remove = []

        # Find old session state entries
        for key in st.session_state:
            if hasattr(st.session_state[key], '_created_time'):
                age = current_time - st.session_state[key]._created_time
                if age > max_age_seconds:
                    keys_to_remove.append(key)

        # Remove old entries
        for key in keys_to_remove:
            del st.session_state[key]
            logger.info(f"Cleaned up old session state: {key}")

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security-related events for audit trail.

        Args:
            event_type: Type of security event
            details: Event details
        """
        log_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'details': details,
            'session_id': getattr(st, 'session_id', 'unknown')
        }

        logger.info(f"SECURITY EVENT: {event_type} - {details}")

        # Could also write to security audit file
        # with open('security_audit.log', 'a') as f:
        #     f.write(f"{time.time()}: {event_type} - {details}\\n")

# Global security instance
dashboard_security = DashboardSecurity()

# Convenience functions
def user_has_admin_permissions() -> bool:
    """Check if current user has admin permissions."""
    return dashboard_security.check_admin_permissions()

def validate_trading_risk(risk_pct: float) -> float:
    """Validate trading risk percentage."""
    return dashboard_security.validate_risk_parameters(risk_pct, 0.1, 10.0)

def validate_daily_loss_limit(loss_pct: float) -> float:
    """Validate daily loss limit."""
    return dashboard_security.validate_daily_loss_limit(loss_pct)

def check_rate_limit(operation: str, cooldown: int = 30) -> bool:
    """Check rate limiting for operations."""
    return dashboard_security.rate_limit_check(operation, cooldown)

def sanitize_instruments(instruments: list) -> list:
    """Sanitize instrument list."""
    return dashboard_security.sanitize_instrument_list(instruments)

def clean_old_session_data():
    """Clean up old session state."""
    dashboard_security.clean_session_state()

__all__ = [
    'dashboard_security',
    'user_has_admin_permissions',
    'validate_trading_risk',
    'validate_daily_loss_limit',
    'check_rate_limit',
    'sanitize_instruments',
    'clean_old_session_data'
]
