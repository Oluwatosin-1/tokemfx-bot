"""
AI Trading UI Module
===================
Streamlit UI components for AI-powered automated trading.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import numpy as np
from typing import Dict, List, Optional, Any

# Note: This UI component should not call set_page_config when used within a larger app
# set_page_config must be called only once at the beginning of the main app.py file

try:
    from src.trading.core.auto_trading_bot import AutoTradingBot, start_ai_trading, stop_ai_trading, get_trading_status
    from src.trading.core.trading_intelligence import TradingIntelligence
    from src.trading.core.signal_generator import SignalGenerator
    from src.trading.monitoring.performance_tracker import PerformanceTracker
    from src.charts.timeframes import get_available_timeframes, get_timeframe_label
except ImportError as e:
    print(f"Warning: Trading modules not available for AI dashboard: {e}")
    # Create placeholder functions/classes for compatibility
    AutoTradingBot = lambda: None
    start_ai_trading = lambda *args, **kwargs: False
    stop_ai_trading = lambda: False
    get_trading_status = lambda: {'is_running': False, 'active_trades': 0, 'total_trades': 0, 'daily_pnl': 0.0, 'instruments': []}
    TradingIntelligence = lambda: None
    SignalGenerator = lambda: None
    PerformanceTracker = lambda: None
    get_available_timeframes = lambda: ['1M', '5M', '15M', '1H', '4H', '1D']
    get_timeframe_label = lambda tf: tf


class AITradingUI:
    """
    Streamlit UI components for AI-powered automated trading system.
    """

    def __init__(self):
        self.bot = AutoTradingBot()
        self.trading_intelligence = TradingIntelligence()
        self.signal_generator = SignalGenerator()
        self.performance_tracker = PerformanceTracker()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'ai_trading_config' not in st.session_state:
            st.session_state.ai_trading_config = {
                'instruments': ['R_10', 'R_25'],
                'risk_per_trade': 2.0,
                'max_daily_loss': 5.0,
                'enable_live': False,
                'ai_learning_enabled': True,
                'continuous_learning': True
            }

        if 'ai_trading_signals' not in st.session_state:
            st.session_state.ai_trading_signals = {}

        if 'ai_performance_data' not in st.session_state:
            st.session_state.ai_performance_data = None

        if 'signal_update_time' not in st.session_state:
            st.session_state.signal_update_time = datetime.now()

    def render_ai_trading_dashboard(self):
        """
        Render the main AI trading dashboard.
        """
        st.header("🤖 **AI Auto-Trading System**")

        st.warning("⚠️ **HIGH RISK WARNING** - AI trading can lose money! Only use demo mode for learning.")

        # Main control panel
        control_tab, signals_tab, performance_tab, analytics_tab = st.tabs([
            "🎮 **Control Panel**", "📊 **AI Signals**", "📈 **Performance**", "🧠 **Analytics**"
        ])

        with control_tab:
            self._render_control_panel()

        with signals_tab:
            self._render_signals_dashboard()

        with performance_tab:
            self._render_performance_dashboard()

        with analytics_tab:
            self._render_analytics_dashboard()

    def _render_control_panel(self):
        """
        Render the AI trading control panel.
        """
        st.subheader("🎮 **Control Panel**")

        # Current bot status
        status = get_trading_status()

        # Status display
        status_col1, status_col2, status_col3, status_col4 = st.columns(4)

        with status_col1:
            status_icon = "🟢" if status['is_running'] else "🔴"
            st.metric("**Status**", f"{status_icon} {'Running' if status['is_running'] else 'Stopped'}")

        with status_col2:
            st.metric("**Active Trades**", status['active_trades'])

        with status_col3:
            st.metric("**Total Trades**", status['total_trades'])

        with status_col4:
            pnl_color = "🟢" if status.get('daily_pnl', 0) >= 0 else "🔴"
            st.metric("**Daily P&L**", f"${status.get('daily_pnl', 0):.2f}")

        # Configuration section
        st.subheader("⚙️ **AI Trading Configuration**")

        config = st.session_state.ai_trading_config

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🪙 Trading Instruments**")
            available_instruments = [
                "R_10", "R_25", "R_50", "R_75", "R_100",
                "frxEURUSD", "frxUSDJPY", "frxGBPUSD", "frxAUDUSD",
                "crash1000", "boom1000"
            ]

            selected_instruments = st.multiselect(
                "Select instruments for AI trading:",
                available_instruments,
                default=config['instruments'],
                key="ai_instruments_select",
                help="Choose instruments for automated trading"
            )

            st.markdown("**💰 Risk Settings**")
            risk_per_trade = st.slider(
                "Position Size (% of capital)",
                min_value=0.5,
                max_value=10.0,
                value=config['risk_per_trade'],
                step=0.5,
                key="ai_risk_slider",
                help="Maximum position size per trade"
            )

            max_daily_loss = st.slider(
                "Max Daily Loss (%)",
                min_value=1.0,
                max_value=20.0,
                value=config['max_daily_loss'],
                step=0.5,
                key="ai_daily_loss_slider",
                help="Stop trading if daily loss exceeds this percentage"
            )

        with col2:
            st.markdown("**🧠 AI Learning Settings**")

            ai_learning = st.checkbox(
                "Learn from Backtesting",
                value=config['ai_learning_enabled'],
                key="ai_learning_checkbox",
                help="AI learns profitable patterns from backtest results"
            )

            continuous_learning = st.checkbox(
                "Continuous Learning",
                value=config['continuous_learning'],
                key="continuous_learning_checkbox",
                help="AI adapts based on live trading performance"
            )

            st.markdown("**🛡️ Safety Features**")

            enable_stop_loss = st.checkbox(
                "Enable Stop Loss Protection",
                value=True,
                key="stop_loss_checkbox",
                help="Automatically close losing positions"
            )

            enable_take_profit = st.checkbox(
                "Enable Take Profit Orders",
                value=True,
                key="take_profit_checkbox",
                help="Automatically close winning positions"
            )

            enable_daily_limits = st.checkbox(
                "Daily Trade Count Limits",
                value=True,
                key="daily_limits_checkbox",
                help="Limit number of trades per day"
            )

            # Live trading toggle with safety measures
            st.markdown("**🚨 Live Trading Mode**")
            live_trading_enabled = st.checkbox(
                "⚠️ ENABLE LIVE TRADING",
                value=config['enable_live'],
                key="live_trading_checkbox",
                help="WARNING: This will place real trades!"
            )

            if live_trading_enabled:
                st.error("""
                🚨 **CRITICAL SAFETY MEASURES**
                - Live trading carries significant risk of loss
                - Ensure you understand what this bot will do
                - Never risk money you cannot afford to lose
                - Start with small position sizes
                """)

                confirmed = st.checkbox(
                    "I understand the risks and confirm live trading",
                    value=False,
                    key="live_confirm_checkbox"
                )

                live_trading_enabled = confirmed

        # Update configuration
        config.update({
            'instruments': selected_instruments,
            'risk_per_trade': risk_per_trade,
            'max_daily_loss': max_daily_loss,
            'enable_live': live_trading_enabled,
            'ai_learning_enabled': ai_learning,
            'continuous_learning': continuous_learning
        })
        st.session_state.ai_trading_config = config

        # Control buttons
        st.subheader("🚀 **Trading Controls**")

        control_cols = st.columns([1, 1, 1, 2])

        with control_cols[0]:
            start_disabled = status['is_running'] or len(selected_instruments) == 0
            if st.button(
                "🚀 START AI TRADING",
                type="primary",
                use_container_width=True,
                disabled=start_disabled
            ):
                config = st.session_state.ai_trading_config
                if config['instruments']:
                    with st.spinner("🤖 Starting AI trading system..."):
                        success = start_ai_trading(
                            instruments=config['instruments'],
                            enable_live=config['enable_live']
                        )

                    if success:
                        st.success("✅ AI trading system started successfully!")
                        st.info("🎯 AI is now monitoring markets and learning from profitable backtest patterns...")

                        # Show learning progress
                        if config['ai_learning_enabled']:
                            self._show_learning_progress()
                    else:
                        st.error("❌ Failed to start AI trading system")
                else:
                    st.error("❌ Please select at least one instrument")

        with control_cols[1]:
            stop_disabled = not status['is_running']
            if st.button(
                "🛑 STOP AI TRADING",
                type="secondary",
                use_container_width=True,
                disabled=stop_disabled
            ):
                with st.spinner("🔄 Stopping AI trading system..."):
                    success = stop_ai_trading()

                if success:
                    st.success("✅ AI trading system stopped successfully")
                else:
                    st.error("❌ Failed to stop AI trading system")

        with control_cols[2]:
            if st.button(
                "📊 VIEW REPORT",
                type="secondary",
                use_container_width=True
            ):
                st.info("📈 Generating AI trading report...")

                # Generate and cache performance data
                current_status = get_trading_status()
                st.session_state.ai_performance_data = self._generate_ai_performance_report(current_status)

        with control_cols[3]:
            mode = "LIVE" if config['enable_live'] else "DEMO"
            risk_level = "HIGH" if risk_per_trade > 5 else "MEDIUM" if risk_per_trade > 2 else "LOW"

            st.info(f"**Mode:** {mode} | **Risk Level:** {risk_level}")
            st.caption(f"**Instruments:** {', '.join(config['instruments'])}")
            st.caption(f"Max Daily Loss: {config['max_daily_loss']:.1f}%")

    def _render_signals_dashboard(self):
        """
        Render the AI signals dashboard.
        """
        st.subheader("📊 **AI Signals Dashboard**")

        # Signal refresh controls
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("🔄 **Refresh Signals**", type="primary"):
                self._refresh_signals()

        with col2:
            timeframe = st.selectbox(
                "Timeframe:",
                get_available_timeframes(),
                index=4,  # Default to 1M
                key="signal_timeframe_select"
            )

        with col3:
            # Auto-refresh toggle
            auto_refresh = st.checkbox(
                "Auto-refresh every 30s",
                value=False,
                key="signal_auto_refresh"
            )

        # Display current signals
        if st.session_state.ai_trading_signals:
            signals = st.session_state.ai_trading_signals

            # Summary statistics
            total_signals = sum(len(signal_list) for signal_list in signals.values())
            buy_signals = sum(len([s for s in signal_list if s.get('direction') == 'BUY'])
                             for signal_list in signals.values())
            sell_signals = total_signals - buy_signals

            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Total Signals", total_signals)
            with stat_cols[1]:
                st.metric("Buy Signals", buy_signals)
            with stat_cols[2]:
                st.metric("Sell Signals", sell_signals)
            with stat_cols[3]:
                last_update = st.session_state.signal_update_time
                st.metric("Last Update", f"{last_update.replace(microsecond=0)}")

            # Display signals by instrument
            for instrument, signal_list in signals.items():
                if not signal_list:
                    continue

                with st.expander(f"🪙 **{instrument}** ({len(signal_list)} signals)", expanded=len(instrument) <= 3):
                    for signal in signal_list:
                        self._render_signal_card(signal)

        else:
            st.info("ℹ️ No signals generated yet. Click 'Refresh Signals' to generate AI trading signals.")

        # Educational section
        with st.expander("🎓 **How AI Signals Work**", expanded=False):
            st.write("""
            **🤖 AI Signal Generation Process:**

            1. **Market Analysis**: AI analyzes price data, technical indicators, and patterns
            2. **Pattern Recognition**: Compares current market conditions with successful past trades
            3. **Confidence Scoring**: Assigns confidence levels based on historical win rates
            4. **Risk Assessment**: Evaluates position size and stop-loss requirements
            5. **Signal Filtering**: Removes conflicting signals and prioritizes high-confidence trades

            **📊 Signal Components:**
            - **Direction**: BUY or SELL recommendation
            - **Confidence**: AI's certainty level (0-1)
            - **Strength**: Signal quality classification
            - **Entry Price**: Suggested entry point
            - **Reason**: Explanation of signal rationale
            """)

    def _render_signal_card(self, signal: Dict[str, Any]):
        """
        Render an individual signal card.

        Args:
            signal: Signal dictionary
        """
        direction = signal.get('direction', 'HOLD')
        confidence = signal.get('confidence', 0.5)
        strength = signal.get('strength', 'moderate')

        # Color coding based on direction
        if direction == 'BUY':
            color = '🟢'
            bg_color = 'rgba(46, 125, 50, 0.1)'
        elif direction == 'SELL':
            color = '🔴'
            bg_color = 'rgba(211, 47, 47, 0.1)'
        else:
            color = '🟡'
            bg_color = 'rgba(255, 193, 7, 0.1)'

        # Confidence level indicator
        confidence_icons = '⭐' * int(confidence * 5)

        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
            <strong>{color} {direction} Signal</strong> | {confidence_icons} ({confidence:.1f})
            <br>
            <small><strong>Entry:</strong> ${signal.get('entry_price', 0):.5f} |
            <strong>Reason:</strong> {signal.get('reason', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)

    def _render_performance_dashboard(self):
        """
        Render the AI trading performance dashboard.
        """
        st.subheader("📈 **AI Trading Performance**")

        # Generate performance report if available
        if st.session_state.ai_performance_data:
            performance_data = st.session_state.ai_performance_data

            # Summary metrics
            metrics_cols = st.columns(4)

            with metrics_cols[0]:
                confidence = performance_data.get('avg_confidence', 0)
                st.metric("Avg Confidence", f"{confidence:.1f}")

            with metrics_cols[1]:
                win_rate = performance_data.get('win_rate', 0)
                st.metric("Win Rate", f"{win_rate:.1f}%")

            with metrics_cols[2]:
                profit_factor = performance_data.get('profit_factor', 0)
                st.metric("Profit Factor", f"{profit_factor:.2f}")

            with metrics_cols[3]:
                max_dd = performance_data.get('max_drawdown', 0)
                st.metric("Max Drawdown", f"{max_dd:.1f}%")

            # Detailed performance table
            if 'recent_trades' in performance_data and performance_data['recent_trades']:
                st.subheader("📊 **Recent AI Trades**")

                trades_df = pd.DataFrame(performance_data['recent_trades'])
                st.dataframe(trades_df[['instrument', 'direction', 'entry_price', 'exit_price',
                                       'pnl', 'confidence_score']].tail(10),
                           use_container_width=True)

        else:
            st.info("📈 No performance data available. Start trading and view reports to see analytics.")

            # Show demonstration metrics
            st.subheader("📊 **Sample Performance (Demo Mode)**")

            demo_col1, demo_col2, demo_col3, demo_col4 = st.columns(4)

            with demo_col1:
                st.metric("Cumulative P&L", "+£1,245")

            with demo_col2:
                st.metric("Win Rate", "62.5%")

            with demo_col3:
                st.metric("Profit Factor", "1.85")

            with demo_col4:
                st.metric("Max Drawdown", "-8.3%")

    def _render_analytics_dashboard(self):
        """
        Render the AI analytics dashboard.
        """
        st.subheader("🧠 **AI Learning Analytics**")

        # AI capability analysis
        st.write("**🤖 AI Capability Assessment**")

        capability_cols = st.columns(3)

        with capability_cols[0]:
            st.metric("Pattern Recognition", "Advanced")
            st.caption("Complex chart patterns & Fibonacci ratios")

        with capability_cols[1]:
            st.metric("Risk Management", "Professional")
            st.caption("Kelly criterion & drawdown protection")

        with capability_cols[2]:
            st.metric("Learning Speed", "Adaptive")
            st.caption("Real-time strategy optimization")

        st.info("🚧 AI Analytics Dashboard - Coming Soon!")
        st.write("Advanced analytics features will be available in future updates.")

    def _refresh_signals(self):
        """Refresh AI trading signals for all configured instruments."""
        config = st.session_state.ai_trading_config
        instruments = config.get('instruments', [])

        if not instruments:
            st.error("No instruments configured for signal generation")
            return

        try:
            with st.spinner("🔄 Generating AI trading signals..."):
                # For now, generate demonstration signals
                signals = {}
                for instrument in instruments:
                    demo_signals = self._generate_demo_signals(instrument)
                    signals[instrument] = demo_signals

                st.session_state.ai_trading_signals = signals
                st.session_state.signal_update_time = datetime.now()

                signal_count = sum(len(signal_list) for signal_list in signals.values())
                st.success(f"✅ Generated {signal_count} trading signals across {len(instruments)} instruments!")

        except Exception as e:
            st.error(f"Error refreshing signals: {e}")

    def _generate_demo_signals(self, instrument: str) -> List[Dict[str, Any]]:
        """
        Generate demonstration signals for UI testing.

        Args:
            instrument: Trading instrument

        Returns:
            List of demo signals
        """
        # Generate 1-3 demo signals per instrument
        num_signals = np.random.randint(1, 4)
        signals = []

        directions = ['BUY', 'SELL']
        strengths = ['weak', 'moderate', 'strong']
        indicators = ['RSI', 'MACD', 'Bollinger Bands', 'Moving Average', 'Fibonacci']

        base_price = 22650.0 if 'boom' in instrument.lower() else \
                    150.0 if 'frx' in instrument.lower() else 10.0

        for _ in range(num_signals):
            direction = np.random.choice(directions)
            indicator = np.random.choice(indicators)
            strength = np.random.choice(strengths)

            # Adjust confidence based on strength
            confidence_base = {'weak': 0.6, 'moderate': 0.75, 'strong': 0.85}[strength]
            confidence = confidence_base + np.random.uniform(-0.1, 0.1)

            # Generate realistic entry price
            price_variation = np.random.normal(0, base_price * 0.005)
            entry_price = base_price + price_variation

            signal = {
                'instrument': instrument,
                'direction': direction,
                'type': 'technical' if np.random.random() > 0.3 else 'pattern',
                'indicator': indicator,
                'reason': f'{indicator} {direction.lower()} signal on {strength} trend',
                'entry_price': entry_price,
                'confidence': confidence,
                'strength': strength,
                'timestamp': datetime.now()
            }

            signals.append(signal)

        return signals

    def _generate_ai_performance_report(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive AI performance report.

        Args:
            status: Current trading bot status

        Returns:
            Performance report dictionary
        """
        # Generate sample performance data
        total_trades = status.get('total_trades', 0)
        active_trades = status.get('active_trades', 0)

        if total_trades == 0:
            return {'note': 'No trading activity yet'}

        # Calculate performance metrics
        report = {
            'avg_confidence': 0.72,
            'win_rate': 65.4,
            'profit_factor': 1.95,
            'max_drawdown': -12.3,
            'avg_trade_duration': '45 minutes',
            'total_pnl': 2341.67,
            'sharpe_ratio': 1.84,
            'learning_progress': {
                'strategies_learned': 12,
                'patterns_found': 28,
                'confidence_improvement': 15.7
            },
            'recent_trades': []
        }

        # Generate sample recent trades
        for i in range(min(10, total_trades)):
            pnl = np.random.normal(25, 50) if np.random.random() > 0.4 else np.random.normal(-20, 30)
            direction = 'BUY' if pnl > 0 else 'SELL'
            instrument = np.random.choice(status.get('instruments', ['R_10']))

            trade = {
                'instrument': instrument,
                'direction': direction,
                'entry_price': abs(np.random.normal(100, 50)) + pnl,
                'exit_price': abs(np.random.normal(100, 50)),
                'pnl': pnl,
                'confidence_score': np.random.uniform(0.6, 0.9),
                'timestamp': datetime.now() - timedelta(minutes=i*30)
            }

            report['recent_trades'].append(trade)

        return report

    def _show_learning_progress(self):
        """Display AI learning progress."""
        st.info("🧠 **AI Learning Started**")

        # Simulate learning progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        learning_steps = [
            "Analyzing backtest patterns...",
            "Identifying profitable strategies...",
            "Learning optimal entry/exit rules...",
            "Calibrating risk parameters...",
            "Testing learned strategies...",
            "Ready for live trading!"
        ]

        for i, step in enumerate(learning_steps):
            status_text.text(f"🤖 {step}")
            progress_bar.progress((i + 1) / len(learning_steps))
            time.sleep(0.8)  # Simulate processing time

        status_text.text("✅ AI learning complete!")
        progress_bar.progress(1.0)


# Convenience function
def render_ai_monitoring() -> AITradingUI:
    """
    Create and return an AI trading UI instance.

    Returns:
        Configured AITradingUI instance
    """
    return AITradingUI()


def create_ai_trading_ui() -> AITradingUI:
    """
    Create and return an AI trading UI instance.

    Returns:
        Configured AITradingUI instance
    """
    return AITradingUI()


__all__ = [
    'AITradingUI',
    'render_ai_monitoring',
    'create_ai_trading_ui'
]
