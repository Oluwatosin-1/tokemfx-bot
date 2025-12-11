"""
Dashboard UI Components Package
===============================
Collection of reusable dashboard UI components and widgets.

This package provides:
- Interactive chart components
- Data visualization widgets
- Streaming data displays
- Trading interface components

NOTE: These components are designed to be used within a larger Streamlit app.
They do not call st.set_page_config() as that must be done by the main app.
"""

# Import all UI components for easy access
from .render_live_trading import render_live_trading
from .render_advanced_backtesting import render_advanced_backtesting
from .render_ai_health_monitor import render_ai_monitoring

__all__ = [
    'render_live_trading',
    'render_advanced_backtesting',
    'render_ai_monitoring'
]
