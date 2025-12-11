"""
Trading UI Module
=================
User interface components and utilities for trading operations.
"""

def render_advanced_backtesting():
    """
    Render advanced backtesting interface.
    This function provides the main entry point for the advanced backtesting UI.
    """
    # Import the actual backtesting module
    try:
        from src.dashboard.ui_components.render_advanced_backtesting import render_advanced_backtesting as internal_render
        return internal_render()
    except ImportError:
        # Fallback to basic implementation if not available
        import streamlit as st
        st.title("Advanced Backtesting Studio")
        st.info("Advanced backtesting components are being loaded...")
        return None


def AITradingUI():
    """
    AI Trading UI component placeholder.
    """
    try:
        import streamlit as st
        st.subheader("🤖 AI Trading Dashboard")
        st.info("AI Trading components are loading...")
        return None
    except ImportError:
        return None


def TradingDashboard():
    """
    Trading dashboard component placeholder.
    """
    try:
        import streamlit as st
        st.subheader("📊 Trading Dashboard")
        st.info("Trading dashboard components are loading...")
        return None
    except ImportError:
        return None

# Export the main functions
__all__ = ['render_advanced_backtesting', 'AITradingUI', 'TradingDashboard']
