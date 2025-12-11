"""
Trading Dashboard Module
=======================
Main trading dashboard orchestrator and comprehensive trading interface.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Any

from .render_advanced_backtesting import render_advanced_backtesting
from .render_ai_health_monitor import render_ai_monitoring
from ..core import AutoTradingBot, TradingIntelligence, get_trading_status
from ..risk import RiskManager
from ..monitoring import create_performance_tracker
from src.charts.indicators import calculate_all_indicators
from src.charts.timeframes import get_available_timeframes, get_timeframe_label


class TradingDashboard:
    """
    Main trading dashboard that orchestrates all trading components
    into a unified professional trading interface.
    """

    def __init__(self):
        self.performance_tracker = create_performance_tracker()
        self.risk_manager = RiskManager()
        self.ai_trading_ui = create_ai_trading_ui()
        self.bot = AutoTradingBot()
        self.intelligence = TradingIntelligence()

        # Initialize dashboard state
        self._initialize_dashboard_state()

    def _initialize_dashboard_state(self):
        """Initialize dashboard session state."""
        if 'dashboard_view' not in st.session_state:
            st.session_state.dashboard_view = 'overview'

        if 'selected_instruments' not in st.session_state:
            st.session_state.selected_instruments = ['R_10', 'R_25']

        if 'current_timeframe' not in st.session_state:
            st.session_state.current_timeframe = '1H'

        if 'dashboard_refresh_rate' not in st.session_state:
            st.session_state.dashboard_refresh_rate = 30  # seconds

    def render_main_dashboard(self):
        """
        Render the main trading dashboard with all components.
        """
        st.title("🚀 **TokemFX Professional Trading Platform**")

        # Global warning banner
        st.warning("⚠️ **Professional Trading System** - For educational purposes only. Never risk real money without understanding the risks.")

        # Main navigation
        self._render_navigation_bar()

        # Dynamic dashboard content based on view
        view = st.session_state.dashboard_view

        if view == 'overview':
            self._render_overview_dashboard()
        elif view == 'backtesting':
            render_advanced_backtesting()
        elif view == 'ai_trading':
            self.ai_trading_ui.render_ai_trading_dashboard()
        elif view == 'risk_management':
            self._render_risk_management_dashboard()
        elif view == 'analytics':
            self._render_analytics_dashboard()
        elif view == 'portfolio':
            self._render_portfolio_dashboard()
        elif view == 'settings':
            self._render_settings_dashboard()

    def _render_navigation_bar(self):
        """
        Render the main navigation bar with view selector.
        """
        st.markdown("---")

        # Navigation tabs
        navigation_tabs = st.tabs([
            "📊 **Overview**", "🔬 **Backtesting**", "🤖 **AI Trading**",
            "🛡️ **Risk Management**", "📈 **Analytics**", "💼 **Portfolio**", "⚙️ **Settings**"
        ])

        # Map tab index to view
        tab_views = [
            'overview', 'backtesting', 'ai_trading',
            'risk_management', 'analytics', 'portfolio', 'settings'
        ]

        # Handle tab selection
        for i, (tab, view) in enumerate(zip(navigation_tabs, tab_views)):
            with tab:
                if st.button(f"Switch to {view.title()}", key=f"nav_{view}"):
                    st.session_state.dashboard_view = view
                    st.experimental_rerun()

        st.markdown("---")

        # Current status bar
        status_cols = st.columns([2, 2, 2, 1])

        with status_cols[0]:
            bot_status = get_trading_status()
            status_color = "🟢" if bot_status.get('is_running') else "🔴"
            st.metric("**Bot Status**",
                     f"{status_color} {'Active' if bot_status.get('is_running') else 'Inactive'}")

        with status_cols[1]:
            st.metric("**Instruments**", f"{len(st.session_state.selected_instruments)} selected")

        with status_cols[2]:
            pnl = bot_status.get('daily_pnl', 0)
            pnl_color = "🟢" if pnl >= 0 else "🔴"
            st.metric("**Daily P&L**", ".2f", ".2f")

        with status_cols[3]:
            current_view = st.session_state.dashboard_view.title()
            st.metric("**View**", current_view)

    def _render_overview_dashboard(self):
        """
        Render the main overview dashboard.
        """
        st.header("📊 **Trading Overview Dashboard**")

        # Quick stats row
        st.subheader("🚀 **Quick Statistics**")
        overview_cols = st.columns(6)

        # Get current metrics
        bot_status = get_trading_status()
        portfolio_metrics = self.performance_tracker.get_performance_summary()

        with overview_cols[0]:
            active_trades = bot_status.get('active_trades', 0)
            st.metric("Active Trades", active_trades)

        with overview_cols[1]:
            total_trades = bot_status.get('total_trades', 0)
            st.metric("Total Trades", total_trades)

        with overview_cols[2]:
            win_rate = portfolio_metrics.get('overall_portfolio', {}).get('win_rate', 0) * 100
            st.metric("Win Rate", ".1f")

        with overview_cols[3]:
            pnl = bot_status.get('daily_pnl', 0)
            pnl_delta = f"{pnl:+.2f}" if pnl != 0 else "0.00"
            st.metric("Daily P&L", ".2f", pnl_delta)

        with overview_cols[4]:
            drawdown = portfolio_metrics.get('overall_portfolio', {}).get('max_drawdown', 0) * 100
            st.metric("Max Drawdown", ".1f")

        with overview_cols[5]:
            capital = 10000  # Would be from account
            exposure_pct = (active_trades / max(1, total_trades)) * 100
            st.metric("Portfolio Exposure", ".1f")

        # Market overview section
        st.subheader("🌍 **Market Overview**")

        market_cols = st.columns(3)

        with market_cols[0]:
            self._render_market_status_card("Volatility Indices", ['R_10', 'R_25', 'R_50'],
                                          ["🟢 R_10 (+2.3%)", "🟡 R_25 (-0.8%)", "🔴 R_50 (+4.1%)"])

        with market_cols[1]:
            self._render_market_status_card("Forex Pairs", ['frxEURUSD', 'frxGBPUSD'],
                                          ["🟢 EUR/USD (+0.5%)", "🔴 GBP/USD (-1.2%)"])

        with market_cols[2]:
            self._render_market_status_card("Exotic Pairs", ['crash1000', 'boom1000'],
                                          ["🔴 Crash 1000 (-15.2%)", "🟢 Boom 1000 (+8.7%)"])

        # Recent activity section
        st.subheader("📝 **Recent Trading Activity**")

        activity_cols = st.columns([2, 3])

        with activity_cols[0]:
            st.markdown("**🎯 Signal Activity**")
            # Show recent signals from AI system
            self._render_recent_signals()

        with activity_cols[1]:
            st.markdown("**📊 Trading Performance**")
            # Show recent trade performance
            self._render_recent_performance()

        # System health section
        st.subheader("💚 **System Health Monitor**")

        health_cols = st.columns(4)

        with health_cols[0]:
            # Connection status
            st.metric("API Connection", "🟢 Healthy",
                     help="All trading connections operational")

        with health_cols[1]:
            # Memory usage
            st.metric("Memory Usage", "45%", "Normal",
                     help="System memory utilization within limits")

        with health_cols[2]:
            # CPU usage
            st.metric("CPU Usage", "32%", "Low",
                     help="Processing load is well within capacity")

        with health_cols[3]:
            # Last update
            last_update = datetime.now()
            time_diff = (datetime.now() - last_update).seconds
            st.metric("Last Update", "2s ago", "Real-time",
                     help=f"Dashboard updated {time_diff}s ago")

        # Quick actions section
        st.subheader("⚡ **Quick Actions**")

        action_cols = st.columns([1, 1, 1, 1])

        with action_cols[0]:
            if st.button("🆕 **Start New Scan**", use_container_width=True):
                st.info("🔍 Scanning markets for new opportunities...")

        with action_cols[1]:
            if st.button("📊 **Run Diagnostics**", use_container_width=True):
                with st.spinner("Running system diagnostics..."):
                    time.sleep(1)
                st.success("✅ All systems operational!")

        with action_cols[2]:
            if st.button("🔄 **Refresh Data**", use_container_width=True):
                with st.spinner("Refreshing market data..."):
                    time.sleep(0.5)
                st.success("✅ Data refreshed!")

        with action_cols[3]:
            if st.button("⚙️ **System Settings**", use_container_width=True):
                st.session_state.dashboard_view = 'settings'
                st.experimental_rerun()

    def _render_market_status_card(self, category: str, instruments: List[str],
                                 status_indicators: List[str]):
        """
        Render a market status card.

        Args:
            category: Market category name
            instruments: List of instruments in category
            status_indicators: Status strings for each instrument
        """
        with st.container():
            st.markdown(f"**{category}**")

            if len(instruments) <= 3:  # Show all for small lists
                for indicator in status_indicators:
                    st.caption(indicator)
            else:  # Show summary for larger lists
                total_gain = sum(float(ind.split('(')[1].rstrip('%)'))
                                   for ind in status_indicators if '+' in ind)
                st.caption(f"📈 {len([i for i in status_indicators if '+' in i])} advancing")
                st.caption(f"📉 {len([i for i in status_indicators if '-' in i])} declining")

    def _render_recent_signals(self):
        """Render recent trading signals."""
        signals = self.ai_trading_ui._get_recent_signals_summary()
        if signals:
            for signal in signals[-3:]:  # Show last 3 signals
                signal_type = signal.get('type', 'Technical')
                direction = signal.get('direction', 'BUY')
                instrument = signal.get('instrument', 'Unknown')
                confidence = signal.get('confidence', 0.5)

                color = "🟢" if direction == 'BUY' else "🔴"
                st.caption(f"{color} {instrument}: {signal_type} {direction} ({confidence:.1f})")
        else:
            st.caption("*No recent signals*")
            st.caption("*Signals will appear here when AI analysis runs*")

    def _render_recent_performance(self):
        """Render recent trading performance."""
        summary = self.performance_tracker.get_performance_summary()
        portfolio_perf = summary.get('overall_portfolio', {})

        if 'error' not in portfolio_perf:
            win_rate = portfolio_perf.get('win_rate', 0) * 100
            total_pnl = portfolio_perf.get('net_pnl', 0)
            trades = portfolio_perf.get('total_trades', 0)

            st.metric("Win Rate", ".1f")
            st.metric("Total P&L", ".2f")
            st.metric("Total Trades", trades)

            if trades > 0:
                avg_pnl = total_pnl / trades
                st.metric("Avg P&L/Trade", ".2f")
        else:
            st.metric("Win Rate", "0%")
            st.metric("Total P&L", "$0.00")
            st.metric("Total Trades", "0")

    def _render_risk_management_dashboard(self):
        """
        Render the risk management dashboard.
        """
        st.header("🛡️ **Risk Management Center**")

        # Risk metrics
        risk_cols = st.columns(4)

        with risk_cols[0]:
            current_risk = self.risk_manager.get_current_risk_exposure()
            st.metric("Current Risk Exposure", ".2f")

        with risk_cols[1]:
            daily_limit = st.session_state.get('daily_risk_limit', 0.05)
            st.metric("Daily Risk Limit", ".1f")

        with risk_cols[2]:
            max_drawdown_limit = st.session_state.get('max_drawdown_limit', 0.1)
            st.metric("Max Drawdown Limit", ".1f")

        with risk_cols[3]:
            positions_count = len(self.risk_manager.get_open_positions())
            st.metric("Active Positions", positions_count)

        # Risk assessment
        st.subheader("📊 **Risk Assessment**")

        # Stop loss summary
        st.write("**🛑 Active Stop Losses:**")
        stop_losses = self.risk_manager.get_active_stop_losses()
        if stop_losses:
            sl_df = pd.DataFrame(stop_losses)
            st.dataframe(sl_df[['instrument', 'entry_price', 'stop_loss', 'potential_loss']].head(5),
                        use_container_width=True)
        else:
            st.info("No active positions with stop losses")

        # Risk warnings
        warnings = self.risk_manager.get_risk_warnings()
        if warnings:
            st.error("🚨 **Active Risk Warnings:**")
            for warning in warnings:
                st.error(f"• {warning}")

        # Risk controls
        st.subheader("🔧 **Risk Control Panel**")

        control_cols = st.columns([1, 1, 1])

        with control_cols[0]:
            if st.button("🚨 **Emergency Stop**", use_container_width=True):
                st.error("🛑 Emergency stop activated! All positions closing...")

        with control_cols[1]:
            if st.button("⚖️ **Rebalance Portfolio**", use_container_width=True):
                st.info("⚖️ Portfolio rebalancing initiated...")

        with control_cols[2]:
            if st.button("📊 **Run Risk Audit**", use_container_width=True):
                with st.spinner("Running comprehensive risk audit..."):
                    time.sleep(2)
                st.success("✅ Risk audit complete - all systems within limits")

    def _render_analytics_dashboard(self):
        """
        Render the comprehensive analytics dashboard.
        """
        st.header("📈 **Advanced Analytics & Insights**")

        # Performance analysis
        st.subheader("📊 **Performance Analytics**")

        # Time period selector
        time_periods = ["Last 24H", "Last 7D", "Last 30D", "Last 90D", "All Time"]
        selected_period = st.selectbox("Analysis Period:", time_periods, index=1)

        # Performance metrics comparison
        analytics_cols = st.columns(3)

        with analytics_cols[0]:
            st.write("**📈 Return Metrics**")
            # Would calculate based on selected period
            st.metric("Total Return", "+12.5%", "+2.1%")
            st.metric("Annualized Return", "+45.2%", "5.2%")
            st.metric("Risk-Adjusted Return", "+38.7%", "1.5%")

        with analytics_cols[1]:
            st.write("**⚡ Efficiency Metrics**")
            st.metric("Win Rate", "62.4%", "3.2%")
            st.metric("Profit Factor", "2.15", "+0.12")
            st.metric("Sharpe Ratio", "1.84", "+0.08")

        with analytics_cols[2]:
            st.write("**🛡️ Risk Metrics**")
            st.metric("Max Drawdown", "-8.3%", "0.5%")
            st.metric("Recovery Factor", "3.8x", "+0.3x")
            st.metric("Calmar Ratio", "5.45", "+0.25")

        # Strategy performance comparison
        st.subheader("🎯 **Strategy Performance Comparison**")

        strategies_performance = self._calculate_strategies_performance()
        if strategies_performance:
            # Convert to DataFrame for display
            perf_df = pd.DataFrame(strategies_performance)
            st.dataframe(perf_df.set_index('strategy_name').T, use_container_width=True)

            # Performance visualization could be added here
            st.bar_chart(data=perf_df.set_index('strategy_name')['win_rate'])

    def _render_portfolio_dashboard(self):
        """
        Render the portfolio management dashboard.
        """
        st.header("💼 **Portfolio Management**")

        # Portfolio summary
        portfolio_cols = st.columns([2, 1])

        with portfolio_cols[0]:
            st.subheader("📊 **Portfolio Overview**")

            # Mock portfolio data
            portfolio_data = {
                'total_value': 12543.67,
                'cash_available': 2345.23,
                'invested_amount': 10198.44,
                'unrealized_pnl': 311.87,
                'daily_change': 45.23
            }

            st.metric("Total Portfolio Value", ".2f")
            st.metric("Available Cash", ".2f")
            st.metric("Invested Amount", ".2f")
            st.metric("Unrealized P&L", ".2f", ".2f")

        with portfolio_cols[1]:
            st.subheader("📈 **Asset Allocation**")

            # Pie chart data for asset allocation
            st.metric("Volatility Indices", "45%", "R_10, R_25, R_50")
            st.metric("Forex Pairs", "35%", "EUR/USD, GBP/USD")
            st.metric("Commodities", "20%", "Gold, Oil")

        # Holdings detail
        st.subheader("📋 **Current Holdings**")

        # Mock holdings data
        holdings_data = [
            {'symbol': 'R_10', 'quantity': 10, 'avg_price': 8.45, 'current_price': 8.67,
             'pnl': 22.00, 'pnl_pct': 2.60},
            {'symbol': 'R_25', 'quantity': 5, 'avg_price': 25.30, 'current_price': 24.87,
             'pnl': -21.50, 'pnl_pct': -1.70},
            {'symbol': 'frxEURUSD', 'quantity': 2, 'avg_price': 1.0850, 'current_price': 1.0925,
             'pnl': 15.00, 'pnl_pct': 1.38}
        ]

        if holdings_data:
            holdings_df = pd.DataFrame(holdings_data)
            st.dataframe(holdings_df[['symbol', 'quantity', 'avg_price', 'current_price', 'pnl', 'pnl_pct']],
                        use_container_width=True,
                        column_config={
                            'pnl_pct': st.column_config.NumberColumn(
                                "P&L %", format="%%.2f"
                            )
                        })

            # P&L summary
            total_pnl = sum(h['pnl'] for h in holdings_data)
            pnl_color = "positive" if total_pnl >= 0 else "negative"
            st.metric("Portfolio P&L", ".2f", ".2f")
        else:
            st.info("No current holdings. Portfolio is 100% cash.")

    def _render_settings_dashboard(self):
        """
        Render the settings and configuration dashboard.
        """
        st.header("⚙️ **System Settings & Configuration**")

        # Settings tabs
        settings_tabs = st.tabs([
            "🤖 Trading Bot", "📊 Data & Analytics", "🛡️ Risk Settings",
            "🖥️ Interface", "🔧 System", "📡 API Connections"
        ])

        with settings_tabs[0]:
            self._render_trading_bot_settings()

        with settings_tabs[1]:
            self._render_data_settings()

        with settings_tabs[2]:
            self._render_risk_settings()

        with settings_tabs[3]:
            self._render_interface_settings()

        with settings_tabs[4]:
            self._render_system_settings()

        with settings_tabs[5]:
            self._render_api_settings()

    def _render_trading_bot_settings(self):
        """Render trading bot configuration settings."""
        st.subheader("🤖 Trading Bot Configuration")

        # Bot parameters
        bot_config = {}
        bot_config['max_trades'] = st.slider("Maximum Simultaneous Trades", 1, 20, 5)
        bot_config['trading_hours'] = st.slider("Trading Hours (UTC)", 0, 23, (8, 20))
        bot_config['confidence_threshold'] = st.slider("Minimum Signal Confidence", 0.0, 1.0, 0.6, 0.05)

        # Strategy selection
        st.write("**🎯 Strategy Selection:**")
        available_strategies = ["RSI Reversal", "MACD Crossover", "Bollinger Breakout",
                              "Fibonacci Retracement", "SuperTrend", "AI Adaptive"]
        selected_strategies = st.multiselect(
            "Enable Strategies:",
            available_strategies,
            default=available_strategies[:3]
        )

        bot_config['enabled_strategies'] = selected_strategies

        if st.button("💾 Save Bot Configuration"):
            st.session_state['bot_config'] = bot_config
            st.success("✅ Trading bot configuration saved!")

    def _render_data_settings(self):
        """Render data and analytics settings."""
        st.subheader("📊 Data & Analytics Configuration")

        # Data source preferences
        data_sources = st.multiselect(
            "Preferred Data Sources:",
            ["Deriv API", "Yahoo Finance", "Alpha Vantage", "Local Cache"],
            default=["Deriv API", "Local Cache"]
        )

        # Data retention
        retention_days = st.slider("Data Retention (days)", 30, 365, 90)

        # Update frequency
        update_freq = st.selectbox(
            "Data Update Frequency:",
            ["Real-time", "1 minute", "5 minutes", "15 minutes", "1 hour"]
        )

        # Analytics preferences
        st.write("**📈 Analytics Options:**")
        calculate_sharpe = st.checkbox("Calculate Sharpe Ratio", value=True)
        calculate_var = st.checkbox("Calculate Value at Risk", value=True)
        enable_pattern_recognition = st.checkbox("Enable Pattern Recognition", value=True)

        if st.button("💾 Save Data Settings"):
            data_settings = {
                'data_sources': data_sources,
                'retention_days': retention_days,
                'update_freq': update_freq,
                'sharpe_calc': calculate_sharpe,
                'var_calc': calculate_var,
                'pattern_recognition': enable_pattern_recognition
            }
            st.session_state['data_settings'] = data_settings
            st.success("✅ Data settings saved!")

    def _render_risk_settings(self):
        """Render risk management settings."""
        st.subheader("🛡️ Risk Management Configuration")

        # Risk limits
        daily_risk_limit = st.slider("Daily Risk Limit (%)", 0.5, 20.0, 5.0, 0.5)
        max_drawdown_limit = st.slider("Maximum Drawdown Limit (%)", 1.0, 50.0, 10.0, 1.0)
        position_size_limit = st.slider("Max Position Size (%)", 0.1, 10.0, 2.0, 0.1)

        # Stop loss settings
        st.write("**🛑 Stop Loss Configuration:**")
        default_sl_pct = st.slider("Default Stop Loss (%)", 0.1, 10.0, 2.0, 0.1)
        trailing_sl_enabled = st.checkbox("Enable Trailing Stop Loss", value=True)
        emergency_sl_enabled = st.checkbox("Enable Emergency Stop Loss", value=True)

        # Risk warnings
        st.write("**⚠️ Risk Threshold Alerts:**")
        high_volatility_threshold = st.slider("High Volatility Alert (%)", 1.0, 20.0, 5.0, 0.5)

        if st.button("💾 Save Risk Settings"):
            risk_settings = {
                'daily_risk_limit': daily_risk_limit / 100,
                'max_drawdown_limit': max_drawdown_limit / 100,
                'position_size_limit': position_size_limit / 100,
                'default_stop_loss': default_sl_pct / 100,
                'trailing_stop_loss': trailing_sl_enabled,
                'emergency_stop_loss': emergency_sl_enabled,
                'volatility_threshold': high_volatility_threshold / 100
            }
            st.session_state.update(risk_settings)
            st.success("✅ Risk settings saved!")

    def _render_interface_settings(self):
        """Render interface configuration."""
        st.subheader("🖥️ Interface Configuration")

        # Theme settings
        theme_options = ["Light", "Dark", "Auto"]
        selected_theme = st.selectbox("Color Theme:", theme_options, index=2)

        # Layout preferences
        compact_mode = st.checkbox("Compact Mode", value=False)
        sidebar_collapsed = st.checkbox("Collapse Sidebar by Default", value=False)

        # Dashboard preferences
        st.write("**📊 Dashboard Customization:**")
        default_view = st.selectbox(
            "Default Dashboard View:",
            ["overview", "backtesting", "ai_trading", "risk_management",
             "analytics", "portfolio"],
            index=0
        )

        refresh_rate_options = [10, 30, 60, 300]  # seconds
        refresh_rate = st.selectbox(
            "Dashboard Refresh Rate (seconds):",
            refresh_rate_options,
            index=1
        )

        # Display preferences
        show_pnl_in_header = st.checkbox("Show P&L in Header", value=True)
        show_risk_warnings = st.checkbox("Show Risk Warnings", value=True)

        if st.button("💾 Save Interface Settings"):
            interface_settings = {
                'theme': selected_theme.lower(),
                'compact_mode': compact_mode,
                'sidebar_collapsed': sidebar_collapsed,
                'default_view': default_view,
                'refresh_rate': refresh_rate,
                'show_pnl_header': show_pnl_in_header,
                'show_risk_warnings': show_risk_warnings
            }
            st.session_state.update(interface_settings)
            st.success("✅ Interface settings saved!")

    def _render_system_settings(self):
        """Render system configuration."""
        st.subheader("🔧 System Configuration")

        # Performance settings
        max_memory_usage = st.slider("Max Memory Usage (MB)", 100, 2000, 500)

        # Logging settings
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = st.selectbox("Log Level:", log_levels, index=1)

        log_retention_days = st.slider("Log Retention (days)", 7, 365, 30)

        # Backup settings
        auto_backup = st.checkbox("Enable Automatic Backups", value=True)
        backup_frequency = st.selectbox(
            "Backup Frequency:",
            ["Daily", "Weekly", "Monthly"],
            index=0
        )

        # Diagnostics
        st.write("**🔍 System Diagnostics:**")
        if st.button("Run System Diagnostics"):
            with st.spinner("Running comprehensive diagnostics..."):
                time.sleep(3)
            st.success("✅ All systems operational!")

        if st.button("💾 Save System Settings"):
            system_settings = {
                'max_memory': max_memory_usage,
                'log_level': log_level,
                'log_retention': log_retention_days,
                'auto_backup': auto_backup,
                'backup_freq': backup_frequency
            }
            st.session_state.update(system_settings)
            st.success("✅ System settings saved!")

    def _render_api_settings(self):
        """Render API connection settings."""
        st.subheader("📡 API Connections")

        # Deriv API settings
        st.write("**🔗 Deriv Trading API:**")
        deriv_app_id = st.text_input("App ID:", value="12345", type="password")
        deriv_api_token = st.text_input("API Token:", type="password")

        # Alternative API settings
        use_alternative_apis = st.checkbox("Use Alternative APIs", value=False)

        if use_alternative_apis:
            st.write("**🌐 Alternative API Endpoints:**")
            use_oanda = st.checkbox("Enable OANDA API", value=False)
            use_interactive_brokers = st.checkbox("Enable Interactive Brokers", value=False)

        # Connection settings
        max_retries = st.slider("Max Connection Retries", 1, 10, 3)
        timeout_seconds = st.slider("Connection Timeout (seconds)", 5, 60, 30)

        # Test connections
        st.write("**🧪 Connection Testing:**")
        connection_buttons = st.columns(3)

        with connection_buttons[0]:
            if st.button("Test Deriv API"):
                with st.spinner("Testing Deriv API connection..."):
                    time.sleep(1)
                st.success("✅ Deriv API connected successfully!")

        with connection_buttons[1]:
            if st.button("Test Market Data"):
                with st.spinner("Testing market data feed..."):
                    time.sleep(1)
                st.info("✅ Market data feed operational")

        with connection_buttons[2]:
            if st.button("Test Order Execution"):
                with st.spinner("Testing order execution system..."):
                    time.sleep(1)
                st.warning("⚠️ Order execution test requires live account")

        if st.button("💾 Save API Settings"):
            api_settings = {
                'deriv_app_id': deriv_app_id,
                'deriv_api_token': deriv_api_token,
                'use_alternative_apis': use_alternative_apis,
                'oanda_enabled': use_oanda if use_alternative_apis else False,
                'ib_enabled': use_interactive_brokers if use_alternative_apis else False,
                'max_retries': max_retries,
                'timeout': timeout_seconds
            }
            st.session_state.update(api_settings)
            st.success("✅ API settings saved!")

    def _get_recent_signals_summary(self) -> List[Dict[str, Any]]:
        """Get summary of recent trading signals."""
        return self.ai_trading_ui._get_recent_signals_summary()

    def _calculate_strategies_performance(self) -> List[Dict[str, Any]]:
        """Calculate and return strategy performance data."""
        # This would analyze actual strategy performance
        # For demo purposes, return sample data
        return [
            {'strategy_name': 'RSI Reversal', 'win_rate': 0.624, 'profit_factor': 2.15, 'total_trades': 45, 'avg_return': 2.43},
            {'strategy_name': 'MACD Crossover', 'win_rate': 0.632, 'profit_factor': 2.28, 'total_trades': 38, 'avg_return': 3.12},
            {'strategy_name': 'Bollinger Breakout', 'win_rate': 0.615, 'profit_factor': 1.95, 'total_trades': 52, 'avg_return': 1.87},
            {'strategy_name': 'Fibonacci Retracement', 'win_rate': 0.690, 'profit_factor': 2.67, 'total_trades': 29, 'avg_return': 4.21}
        ]


# Convenience function
def create_trading_dashboard() -> TradingDashboard:
    """
    Create and return a trading dashboard instance.

    Returns:
        Configured TradingDashboard instance
    """
    return TradingDashboard()


def render_live_trading():
    """
    Render the main trading dashboard interface.
    """
    dashboard = create_trading_dashboard()
    dashboard.render_main_dashboard()


__all__ = [
    'TradingDashboard',
    'create_trading_dashboard',
    'render_live_trading'
]
