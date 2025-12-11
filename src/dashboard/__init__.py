"""
Dashboard Module for TokemFX
============================
Handles all dashboard rendering functions and UI components.
"""

from .portfolio import render_portfolio_performance, get_portfolio_metrics
from src.dashboard.components.portfolio_dashboard import render_portfolio_overview

__all__ = [
    'render_portfolio_performance',
    'render_portfolio_overview',
    'get_portfolio_metrics'
]
