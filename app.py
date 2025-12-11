"""
TokemFX Enterprise Trading Dashboard
Professional trading platform with full functionality.
"""

# Setup proper Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import json
from typing import List, Dict, Any

# ============================================================================
# ENTERPRISE DASHBOARD - FULL FUNCTIONALITY
# ============================================================================

# Prevent multiple set_page_config calls across the entire application
if not hasattr(st, '_page_config_set'):
    st.set_page_config(
        page_title="TokemFX Professional Trading",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"  # Changed from expanded to collapsed
    )
    st._page_config_set = True

# ============================================================================
# DASHBOARD CONFIGURATION
# ============================================================================

def load_dashboard_template_lazy(template_name: str = "admin") -> list:
    """
    Load dashboard template configuration.
    """
    try:
        from src.dashboard.dashboard_loader import load_dashboard_template
        return load_dashboard_template(template_name)
    except Exception as e:
        print(f"Warning: Could not load dashboard template: {e}")
        # Return fallback configuration
        return [
            {"name": "dashboard", "title": "📊 Dashboard", "component": "render_advanced_dashboard", "icon": "📊"},
            {"name": "backtesting", "title": "🔍 Backtest Studio", "component": "render_advanced_backtesting", "icon": "🔍"},
            {"name": "live_trading", "title": "🎯 Live Trading", "component": "render_live_trading", "icon": "🎯"},
            {"name": "ai_health", "title": "🤖 AI Health", "component": "render_ai_health_monitor", "icon": "🤖"}
        ]

def load_dashboard_component(component_name: str):
    """
    Load and render a specific dashboard component.
    """
    if component_name == 'dashboard':
        from src.dashboard.dashboard_module import render_advanced_dashboard
        render_advanced_dashboard()

    elif component_name == 'backtesting':
        try:
            from src.dashboard.components.backtesting_studio import render_backtesting_studio
            render_backtesting_studio()
        except ImportError:
            from src.dashboard.ui_components.render_advanced_backtesting import render_advanced_backtesting
            render_advanced_backtesting()

    elif component_name == 'live_trading':
        try:
            from src.dashboard.components.live_trading import render_live_trading
            render_live_trading()
        except ImportError:
            from src.dashboard.ui_components.render_live_trading import render_live_trading
            render_live_trading()

    elif component_name == 'ai_health':
        try:
            from src.dashboard.components.ai_monitoring import render_ai_monitoring
            render_ai_monitoring()
        except ImportError:
            from src.dashboard.ui_components.render_ai_health_monitor import render_ai_monitoring
            render_ai_monitoring()

    elif component_name == 'ai_trading':
        try:
            from src.dashboard.components.ai_trading import render_ai_trading
            render_ai_trading()
        except ImportError:
            st.header("🤖 **AI Trading Dashboard**")
            st.info("AI trading dashboard component coming soon.")

    elif component_name == 'optimize':
        try:
            from src.dashboard.components.strategy_optimizer import render_strategy_optimizer
            render_strategy_optimizer()
        except Exception as e:
            st.header("🎯 **Strategy Optimizer**")
            st.error(f"❌ Failed to load strategy optimizer: {str(e)[:100]}")
            st.info("Strategy optimizer feature temporarily unavailable.")
            with st.expander("Debug Info", expanded=False):
                st.code(f"Error: {e}\nComponent: {component_name}")

    elif component_name == 'performance':
        try:
            from src.dashboard.components.performance_monitor import render_performance_monitor
            render_performance_monitor()
        except ImportError:
            st.header("📈 **Performance Monitor**")
            st.info("Performance monitoring feature coming soon.")

    elif component_name == 'system_audit':
        try:
            from src.dashboard.components.system_audit import render_system_audit
            render_system_audit()
        except ImportError:
            st.header("🔬 **System Audit**")
            st.info("System audit feature coming soon.")

    elif component_name == 'production_monitor':
        try:
            from src.dashboard.components.production_monitor import render_production_monitor
            render_production_monitor()
        except ImportError:
            st.header("📊 **Production Monitor**")
            st.info("Production monitoring feature coming soon.")

    elif component_name == 'alert_dashboard':
        try:
            from src.dashboard.components.alert_dashboard import render_alert_dashboard
            render_alert_dashboard()
        except ImportError:
            st.header("🚨 **Alert Dashboard**")
            st.info("Alert monitoring feature coming soon.")

    elif component_name == 'infrastructure':
        try:
            from src.dashboard.components.infrastructure import render_infrastructure
            render_infrastructure()
        except ImportError:
            st.header("🔧 **Infrastructure**")
            st.info("Infrastructure monitoring feature coming soon.")

def render_fallback_component(tab_config):
    """Render fallback component for missing features."""
    with st.container():
        st.warning(f"⚠️ {tab_config['title']} is currently being developed")
        with st.expander("Component Information", expanded=False):
            st.code(f"""
Component: {tab_config['name']}
Title: {tab_config['title']}
Category: {(tab_config.get('category', 'Unknown')).title()}
Status: Development in Progress
URL: http://0.0.0.0:8501
            """)

# ============================================================================
# MAIN DASHBOARD FUNCTION
# ============================================================================

def main():
    """Main dashboard application - clean interface without sidebar clutter."""

    # Template selection (put in main area instead of sidebar)
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = 'admin'

    try:
        from src.dashboard.dashboard_loader import get_available_templates
        templates = get_available_templates()
    except:
        templates = {'admin': 'Administrator Dashboard'}

    # Dynamic tab loading based on template
    try:
        tab_configurations = load_dashboard_template_lazy(st.session_state.selected_template)
    except Exception as e:
        st.error(f"Configuration loading error: {e}")
        tab_configurations = [
            {"name": "dashboard", "title": "📊 Dashboard", "component": "render_advanced_dashboard", "icon": "📊"},
            {"name": "backtesting", "title": "🔍 Backtest Studio", "component": "render_advanced_backtesting", "icon": "🔍"},
            {"name": "live_trading", "title": "🎯 Live Trading", "component": "render_live_trading", "icon": "🎯"},
            {"name": "ai_health", "title": "🤖 AI Health", "component": "render_ai_health_monitor", "icon": "🤖"}
        ]

    # Create tabs dynamically
    tab_count = len(tab_configurations)
    tabs = st.tabs([config['title'] for config in tab_configurations])

    # Render each component in its tab
    for i, (tab, tab_config) in enumerate(zip(tabs, tab_configurations)):
        with tab:
            try:
                # Load the component
                load_dashboard_component(tab_config['name'])

            except Exception as e:
                st.error(f"❌ Error loading {tab_config['name']}: {str(e)[:100]}")
                render_fallback_component(tab_config)

if __name__ == "__main__":
    main()
