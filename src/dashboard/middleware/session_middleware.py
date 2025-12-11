"""
Session Management Middleware
============================
User session state and persistent settings management.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from datetime import datetime

class SessionMiddleware:
    """Session state and persistent settings management."""
    
    def __init__(self):
        self.default_settings = {
            "theme": "professional",
            "auto_refresh": True,
            "refresh_interval": 30,
            "data_limit": 1000,
            "chart_style": "candlestick",
            "risk_warnings": True
        }
    
    def get_user_settings(self, username: str) -> Dict[str, Any]:
        """Get user-specific settings (in production, load from database)."""
        # For demo, return defaults (would load from persistent storage)
        return self.default_settings.copy()
    
    def save_user_settings(self, username: str, settings: Dict[str, Any]):
        """Save user settings (in production, persist to database)."""
        # For demo, just store in session (would persist to database)
        st.session_state.user_settings = settings
    
    def get_current_template(self) -> str:
        """Get current dashboard template."""
        return st.session_state.get("current_template", "admin")
    
    def set_current_template(self, template_name: str):
        """Set current dashboard template."""
        st.session_state.current_template = template_name
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get all session data."""
        return {
            "user_session": st.session_state.get("user_session"),
            "current_template": self.get_current_template(),
            "user_settings": st.session_state.get("user_settings", self.default_settings),
            "session_start": st.session_state.get("session_start", datetime.now().isoformat()),
            "last_activity": datetime.now().isoformat()
        }
    
    def is_session_active(self) -> bool:
        """Check if user session is active."""
        return "user_session" in st.session_state
    
    def clear_session(self):
        """Clear all session data."""
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("current_", "user_"))]
        for key in keys_to_clear:
            del st.session_state[key]

# Global session middleware instance
session_middleware = SessionMiddleware()

def update_user_setting(key: str, value: Any):
    """Update individual user setting."""
    settings = session_middleware.get_user_settings(st.session_state.get("user_session", {}).get("username", "anonymous"))
    settings[key] = value
    session_middleware.save_user_settings(st.session_state["user_session"]["username"], settings)
