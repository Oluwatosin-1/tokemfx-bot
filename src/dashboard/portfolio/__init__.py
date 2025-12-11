"""
Portfolio Dashboard Module
==========================
Portfolio management and visualization components.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

def render_portfolio_performance():
    """Render portfolio performance overview."""
    st.header("📊 Portfolio Performance")

    # Sample portfolio data
    portfolio_data = {
        'Asset': ['R_10', 'frxEURUSD', 'frxGBPUSD', 'Cash', 'Total'],
        'Value': [2500.00, 1800.00, 3200.00, 10002.89, 18702.89],
        'Allocation': [13.4, 9.6, 17.1, 53.5, 100.0],
        'P&L': [234.56, -89.23, 456.78, 0.0, 602.11],
        'Change %': [10.3, -3.2, 16.6, 0.0, 3.3]
    }

    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    return df

def get_portfolio_metrics():
    """Get portfolio metrics."""
    return {
        'total_value': 18702.89,
        'total_pnl': 602.11,
        'total_change_pct': 3.3,
        'sharpe_ratio': 1.45,
        'max_drawdown': -4.2,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

__all__ = ['render_portfolio_performance', 'get_portfolio_metrics']
