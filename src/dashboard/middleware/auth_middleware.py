"""
Authentication Middleware
========================
User authentication and session management for dashboard access.
"""

import streamlit as st
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class AuthMiddleware:
    """Authentication and session management middleware."""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour
        self.users = self._load_user_database()
        
    def _load_user_database(self) -> Dict[str, Dict[str, Any]]:
        """Load user database (in production, this would connect to a real database)."""
        return {
            "admin": {
                "password_hash": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",  # demo hash
                "role": "admin",
                "permissions": ["full_access", "system_controls", "user_management"],
                "template": "admin",
                "last_login": None
            },
            "trader": {
                "password_hash": "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
                "role": "trader", 
                "permissions": ["execute_trades", "view_positions"],
                "template": "prop_trader",
                "last_login": None
            }
        }
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user credentials."""
        user = self.users.get(username)
        if not user:
            return False
            
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return user["password_hash"] == password_hash
    
    def get_user_session(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user session data."""
        user = self.users.get(username)
        if user:
            return {
                "username": username,
                "role": user["role"],
                "permissions": user["permissions"], 
                "template": user["template"],
                "login_time": datetime.now()
            }
        return None
    
    def check_permission(self, user_session: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in user_session.get("permissions", [])
    
    def is_session_valid(self, user_session: Dict[str, Any]) -> bool:
        """Check if user session is still valid."""
        login_time = user_session.get("login_time")
        if login_time:
            return (datetime.now() - login_time).seconds < self.session_timeout
        return False

def login_form():
    """Render login form."""
    st.sidebar.title("🔐 Login")
    
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        auth = AuthMiddleware()
        if auth.authenticate(username, password):
            user_session = auth.get_user_session(username)
            if user_session:
                st.session_state.user_session = user_session
                st.sidebar.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.sidebar.error("Session error")
        else:
            st.sidebar.error("Invalid credentials")

def logout():
    """Clear user session."""
    if "user_session" in st.session_state:
        del st.session_state.user_session

def require_login():
    """Require user to be logged in."""
    if "user_session" not in st.session_state:
        login_form()
        st.stop()

def require_permission(permission: str):
    """Require specific permission for component access."""
    if "user_session" not in st.session_state:
        st.error("Authentication required")
        st.stop()
        
    user_session = st.session_state.user_session
    auth = AuthMiddleware()
    
    if not auth.check_permission(user_session, permission):
        st.error("Insufficient permissions")
        st.stop()
        
    if not auth.is_session_valid(user_session):
        st.error("Session expired")
        logout()
        st.rerun()
