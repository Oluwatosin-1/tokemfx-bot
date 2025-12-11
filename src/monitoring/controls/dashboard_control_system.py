#!/usr/bin/env python3
"""
🎛️ Comprehensive Dashboard Control System

Provides complete system management interface for trading operations:
- Real-time monitoring and control
- Multi-strategy management
- Risk management interface
- Performance analytics
- System administration controls
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import our emergency control system
from src.monitoring.emergency.emergency_controls import (
    EmergencyControlSystem, EmergencyLevel, CircuitBreakerState,
    emergency_stop, pause_trading, resume_trading, get_system_status,
    is_trading_allowed, trigger_circuit_breaker, reset_circuit_breaker
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyState(Enum):
    """Trading strategy states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class SystemMode(Enum):
    """System operating modes."""
    MAINTENANCE = "maintenance"
    SIMULATION = "simulation"
    LIVE = "live"
    BACKTEST = "backtest"

@dataclass
class StrategyInfo:
    """Strategy information and metrics."""
    name: str
    state: StrategyState
    description: str
    start_time: Optional[datetime]
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    config: Dict[str, Any] = None

@dataclass
class MarketDataInfo:
    """Market data monitoring information."""
    symbol: str
    last_price: float
    change_pct: float
    volume: int
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    status: str = "connected"

@dataclass
class DashboardCommand:
    """Dashboard control command."""
    command_id: str
    action: str
    parameters: Dict[str, Any]
    issued_by: str
    timestamp: datetime
    executed: bool = False
    result: Optional[str] = None
    error: Optional[str] = None

class DashboardControlSystem:
    """Comprehensive dashboard control and management system."""

    def __init__(self, emergency_system: Optional[EmergencyControlSystem] = None):
        self.emergency_system = emergency_system or EmergencyControlSystem()
        self.system_mode = SystemMode.SIMULATION

        # Strategy management
        self.strategies: Dict[str, StrategyInfo] = {}
        self.enabled_strategies: List[str] = []

        # Market data monitoring
        self.market_data: Dict[str, MarketDataInfo] = {}
        self.active_market_data_feeds: List[str] = []

        # Performance monitoring
        self.system_metrics = {
            'uptime_seconds': 0,
            'total_trades': 0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'monthly_pnl': 0.0,
            'active_strategies': 0,
            'market_feeds_active': 0,
            'last_update': datetime.now()
        }

        # Command history
        self.command_history: List[DashboardCommand] = []

        # Locks and synchronization
        self.lock = threading.Lock()

        # Callbacks
        self.status_update_callbacks: List[Callable] = []

        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        logger.info("🎛️ Dashboard Control System initialized")
        logger.info(f"   Mode: {self.system_mode.value}")
        logger.info(f"   Emergency system: Connected")

    def start_monitoring(self):
        """Start background monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🎛️ Dashboard monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🎛️ Dashboard monitoring stopped")

    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                self._update_system_metrics()
                self._notify_status_callbacks()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(30)  # Wait before retry

    def _update_system_metrics(self):
        """Update system performance metrics."""
        with self.lock:
            now = datetime.now()
            self.system_metrics.update({
                'uptime_seconds': int((now - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()),
                'active_strategies': len([s for s in self.strategies.values() if s.state == StrategyState.RUNNING]),
                'market_feeds_active': len(self.active_market_data_feeds),
                'last_update': now
            })

    def _notify_status_callbacks(self):
        """Notify status update callbacks."""
        status = self.get_full_status()
        for callback in self.status_update_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")

    # ============ STRATEGY MANAGEMENT ============

    def register_strategy(self, name: str, description: str, config: Dict[str, Any]):
        """Register a new trading strategy."""
        with self.lock:
            if name in self.strategies:
                raise ValueError(f"Strategy '{name}' already registered")

            strategy = StrategyInfo(
                name=name,
                state=StrategyState.STOPPED,
                description=description,
                start_time=None,
                config=config
            )

            self.strategies[name] = strategy
            logger.info(f"📈 Strategy registered: {name}")

    def enable_strategy(self, strategy_name: str):
        """Enable a trading strategy."""
        self._execute_command("enable_strategy", {"strategy": strategy_name}, "dashboard")

    def disable_strategy(self, strategy_name: str):
        """Disable a trading strategy."""
        self._execute_command("disable_strategy", {"strategy": strategy_name}, "dashboard")

    def start_strategy(self, strategy_name: str):
        """Start a trading strategy."""
        self._execute_command("start_strategy", {"strategy": strategy_name}, "dashboard")

    def stop_strategy(self, strategy_name: str):
        """Stop a trading strategy."""
        self._execute_command("stop_strategy", {"strategy": strategy_name}, "dashboard")

    def pause_strategy(self, strategy_name: str):
        """Pause a trading strategy."""
        self._execute_command("pause_strategy", {"strategy": strategy_name}, "dashboard")

    def update_strategy_config(self, strategy_name: str, config_updates: Dict[str, Any]):
        """Update strategy configuration."""
        self._execute_command("update_strategy_config",
                            {"strategy": strategy_name, "updates": config_updates}, "dashboard")

    def get_strategy_status(self, strategy_name: str) -> Optional[Dict]:
        """Get strategy status."""
        strategy = self.strategies.get(strategy_name)
        return asdict(strategy) if strategy else None

    # ============ MARKET DATA MANAGEMENT ============

    def register_market_feed(self, symbol: str):
        """Register a market data feed for monitoring."""
        with self.lock:
            if symbol not in self.active_market_data_feeds:
                self.active_market_data_feeds.append(symbol)

                # Initialize with dummy data
                self.market_data[symbol] = MarketDataInfo(
                    symbol=symbol,
                    last_price=0.0,
                    change_pct=0.0,
                    volume=0,
                    bid=0.0,
                    ask=0.0,
                    spread=0.0,
                    timestamp=datetime.now()
                )

                logger.info(f"📊 Market feed registered: {symbol}")

    def unregister_market_feed(self, symbol: str):
        """Unregister a market data feed."""
        with self.lock:
            if symbol in self.active_market_data_feeds:
                self.active_market_data_feeds.remove(symbol)
                if symbol in self.market_data:
                    del self.market_data[symbol]
                logger.info(f"📊 Market feed unregistered: {symbol}")

    def update_market_data(self, symbol: str, price: float, volume: int = 0,
                          bid: float = None, ask: float = None):
        """Update market data for a symbol."""
        with self.lock:
            if symbol not in self.market_data:
                self.register_market_feed(symbol)

            data = self.market_data[symbol]
            prev_price = data.last_price or price

            data.last_price = price
            data.volume = volume
            data.bid = bid or (price - 0.01)
            data.ask = ask or (price + 0.01)
            data.spread = data.ask - data.bid
            data.change_pct = ((price - prev_price) / prev_price * 100) if prev_price > 0 else 0.0
            data.timestamp = datetime.now()
            data.status = "connected"

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get market data for a symbol."""
        data = self.market_data.get(symbol)
        return asdict(data) if data else None

    # ============ SYSTEM CONTROL ============

    def set_system_mode(self, mode: SystemMode):
        """Set system operating mode."""
        with self.lock:
            old_mode = self.system_mode
            self.system_mode = mode

            # Mode-specific actions
            if mode == SystemMode.MAINTENANCE:
                emergency_stop("Entering maintenance mode")
            elif mode == SystemMode.LIVE and old_mode != SystemMode.LIVE:
                logger.warning("⚠️ Switching to LIVE trading mode!")
            elif mode == SystemMode.SIMULATION:
                logger.info("🧪 Switched to simulation mode")

            self._execute_command("set_system_mode", {"mode": mode.value}, "dashboard")
            logger.info(f"🎛️ System mode changed: {old_mode.value} -> {mode.value}")

    def emergency_system_stop(self):
        """System-wide emergency stop."""
        self._execute_command("emergency_stop", {}, "dashboard")

    def emergency_pause(self):
        """System-wide emergency pause."""
        self._execute_command("emergency_pause", {}, "dashboard")

    def resume_system(self):
        """Resume system operation."""
        self._execute_command("resume_system", {}, "dashboard")

    def trigger_system_circuit_breaker(self, reason: str):
        """Trigger system-wide circuit breaker."""
        self._execute_command("trigger_circuit_breaker", {"reason": reason}, "dashboard")

    def reset_system_circuit_breaker(self):
        """Reset system-wide circuit breaker."""
        self._execute_command("reset_circuit_breaker", {}, "dashboard")

    # ============ PERFORMANCE MONITORING ============

    def update_strategy_metrics(self, strategy_name: str, pnl: float = 0,
                               wins: int = 0, losses: int = 0):
        """Update strategy performance metrics."""
        with self.lock:
            if strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]

                strategy.total_pnl += pnl
                strategy.wins += wins
                strategy.losses += losses
                strategy.total_trades += (wins + losses)

                if strategy.total_trades > 0:
                    strategy.win_rate = strategy.wins / strategy.total_trades

    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report."""
        with self.lock:
            total_pnl = sum(s.total_pnl for s in self.strategies.values())
            total_trades = sum(s.total_trades for s in self.strategies.values())
            total_wins = sum(s.wins for s in self.strategies.values())

            return {
                'system_pnl': total_pnl,
                'total_trades': total_trades,
                'total_wins': total_wins,
                'system_win_rate': total_wins / total_trades if total_trades > 0 else 0.0,
                'active_strategies': len([s for s in self.strategies.values() if s.state == StrategyState.RUNNING]),
                'strategies': {name: asdict(strategy) for name, strategy in self.strategies.items()},
                'market_feeds': {symbol: asdict(data) for symbol, data in self.market_data.items()},
                'metrics': self.system_metrics
            }

    # ============ COMMAND SYSTEM ============

    def _execute_command(self, action: str, parameters: Dict[str, Any], issued_by: str):
        """Execute a dashboard command."""
        command = DashboardCommand(
            command_id=f"cmd_{int(time.time())}_{action}",
            action=action,
            parameters=parameters,
            issued_by=issued_by,
            timestamp=datetime.now()
        )

        try:
            result = self._handle_command_action(action, parameters)
            command.executed = True
            command.result = f"Command executed successfully: {result}"
            logger.info(f"✅ Dashboard command executed: {action}")

        except Exception as e:
            command.error = str(e)
            logger.error(f"❌ Dashboard command failed: {action} - {e}")

        with self.lock:
            self.command_history.append(command)

        return command

    def _handle_command_action(self, action: str, parameters: Dict[str, Any]) -> str:
        """Handle specific command actions."""
        if action == "enable_strategy":
            strategy = parameters["strategy"]
            if strategy not in self.enabled_strategies:
                self.enabled_strategies.append(strategy)
            return f"Strategy {strategy} enabled"

        elif action == "disable_strategy":
            strategy = parameters["strategy"]
            if strategy in self.enabled_strategies:
                self.enabled_strategies.remove(strategy)
            return f"Strategy {strategy} disabled"

        elif action == "start_strategy":
            strategy = parameters["strategy"]
            if strategy in self.strategies:
                self.strategies[strategy].state = StrategyState.RUNNING
                self.strategies[strategy].start_time = datetime.now()
            return f"Strategy {strategy} started"

        elif action == "stop_strategy":
            strategy = parameters["strategy"]
            if strategy in self.strategies:
                self.strategies[strategy].state = StrategyState.STOPPED
            return f"Strategy {strategy} stopped"

        elif action == "pause_strategy":
            strategy = parameters["strategy"]
            if strategy in self.strategies:
                self.strategies[strategy].state = StrategyState.PAUSED
            return f"Strategy {strategy} paused"

        elif action == "set_system_mode":
            self.system_mode = SystemMode(parameters["mode"])
            return f"System mode set to {self.system_mode.value}"

        elif action == "emergency_stop":
            emergency_stop("Dashboard emergency stop")
            return "Emergency stop triggered"

        elif action == "emergency_pause":
            pause_trading("Dashboard emergency pause")
            return "Emergency pause triggered"

        elif action == "resume_system":
            resume_trading()
            return "System resumed"

        elif action == "trigger_circuit_breaker":
            trigger_circuit_breaker(parameters["reason"])
            return f"Circuit breaker triggered: {parameters['reason']}"

        elif action == "reset_circuit_breaker":
            reset_circuit_breaker()
            return "Circuit breaker reset"

        elif action == "update_strategy_config":
            strategy = parameters["strategy"]
            updates = parameters["updates"]
            if strategy in self.strategies:
                self.strategies[strategy].config.update(updates)
            return f"Strategy {strategy} config updated"

        else:
            raise ValueError(f"Unknown command action: {action}")

    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history."""
        with self.lock:
            return [asdict(cmd) for cmd in self.command_history[-limit:]]

    # ============ STATUS AND MONITORING ============

    def add_status_callback(self, callback: Callable):
        """Add status update callback."""
        self.status_update_callbacks.append(callback)

    def get_full_status(self) -> Dict:
        """Get complete system status."""
        with self.lock:
            return {
                'system_mode': self.system_mode.value,
                'emergency_system': self.emergency_system.get_status(),
                'strategies': {name: asdict(strategy) for name, strategy in self.strategies.items()},
                'enabled_strategies': self.enabled_strategies,
                'market_data': {symbol: asdict(data) for symbol, data in self.market_data.items()},
                'active_feeds': self.active_market_data_feeds,
                'system_metrics': self.system_metrics,
                'performance': self.get_performance_report(),
                'last_updated': datetime.now().isoformat()
            }

    def export_configuration(self) -> Dict:
        """Export complete system configuration."""
        with self.lock:
            return {
                'system_mode': self.system_mode.value,
                'strategies': {name: asdict(strategy) for name, strategy in self.strategies.items()},
                'enabled_strategies': self.enabled_strategies,
                'active_market_feeds': self.active_market_data_feeds,
                'emergency_limits': asdict(self.emergency_system.risk_limits),
                'export_time': datetime.now().isoformat()
            }

    def import_configuration(self, config: Dict):
        """Import system configuration."""
        with self.lock:
            # Import strategies
            if 'strategies' in config:
                for name, strategy_dict in config['strategies'].items():
                    # Convert back from dict to StrategyInfo
                    strategy = StrategyInfo(**strategy_dict)
                    self.strategies[name] = strategy

            # Import enabled strategies
            if 'enabled_strategies' in config:
                self.enabled_strategies = config['enabled_strategies']

            # Import market feeds
            if 'active_market_feeds' in config:
                for symbol in config['active_market_feeds']:
                    self.register_market_feed(symbol)

            logger.info("🎛️ Configuration imported successfully")

# Global dashboard control instance
dashboard_system = DashboardControlSystem()

# Start monitoring
dashboard_system.start_monitoring()

# Convenience functions for integration
def start_strategy(name: str):
    """Start a trading strategy."""
    dashboard_system.start_strategy(name)

def stop_strategy(name: str):
    """Stop a trading strategy."""
    dashboard_system.stop_strategy(name)

def get_dashboard_status():
    """Get complete dashboard status."""
    return dashboard_system.get_full_status()

def register_market_feed(symbol: str):
    """Register market data feed."""
    dashboard_system.register_market_feed(symbol)

def update_market_price(symbol: str, price: float, volume: int = 0):
    """Update market price data."""
    dashboard_system.update_market_data(symbol, price, volume)

# Exports for compatibility with other modules
dashboard_controller = dashboard_system  # Alias for backward compatibility

def execute_trade(order_type: str, symbol: str, amount: float, **kwargs):
    """Execute trade through dashboard control system."""
    return dashboard_controller._execute_command(
        "execute_trade",
        {"order_type": order_type, "symbol": symbol, "amount": amount, **kwargs},
        "dashboard"
    )

def create_streamlit_control_interface():
    """
    Create a Streamlit-based control interface for the dashboard.

    Returns:
        A Streamlit app function for dashboard control
    """
    try:
        import streamlit as st
    except ImportError:
        def placeholder_interface():
            """Placeholder when Streamlit is not available."""
            print("❌ Streamlit not available. Install with: pip install streamlit")
            print("📊 Dashboard control interface requires Streamlit")
            return None
        return placeholder_interface

    def streamlit_dashboard():
        """
        Streamlit dashboard control interface.
        """
        st.title("🎛️ TokemFX Dashboard Control System")
        st.markdown("---")

        # System Status
        st.header("📊 System Status")
        status = dashboard_controller.get_full_status()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("System Mode", status.get('system_mode', 'Unknown'))
        with col2:
            active_strategies = len(status.get('strategies', {}))
            st.metric("Active Strategies", active_strategies)
        with col3:
            market_feeds = len(status.get('active_feeds', []))
            st.metric("Market Feeds", market_feeds)

        # Strategy Management
        st.header("🎯 Strategy Management")
        strategies = status.get('strategies', {})

        if strategies:
            for strategy_name, strategy_info in strategies.items():
                with st.expander(f"Strategy: {strategy_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**State:** {strategy_info.get('state', 'Unknown')}")
                    with col2:
                        st.write(f"**Trades:** {strategy_info.get('total_trades', 0)}")
                    with col3:
                        pnl = strategy_info.get('total_pnl', 0)
                        st.write(f"**P&L:** ${pnl:.2f}")

                    # Control buttons
                    if strategy_info.get('state') == 'STOPPED':
                        if st.button(f"Start {strategy_name}", key=f"start_{strategy_name}"):
                            dashboard_controller.start_strategy(strategy_name)
                            st.success(f"Started {strategy_name}")
                            st.rerun()
                    elif strategy_info.get('state') == 'RUNNING':
                        if st.button(f"Stop {strategy_name}", key=f"stop_{strategy_name}"):
                            dashboard_controller.stop_strategy(strategy_name)
                            st.success(f"Stopped {strategy_name}")
                            st.rerun()
        else:
            st.info("No strategies configured")

        # Market Data
        st.header("📈 Market Data")
        market_data = status.get('market_data', {})

        if market_data:
            market_df = []
            for symbol, data in market_data.items():
                market_df.append({
                    'Symbol': symbol,
                    'Price': data.get('last_price', 0),
                    'Change %': data.get('change_pct', 0),
                    'Status': data.get('status', 'Unknown')
                })

            if market_df:
                import pandas as pd
                st.dataframe(pd.DataFrame(market_df))
        else:
            st.info("No market data available")

        # System Controls
        st.header("🎛️ System Controls")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Emergency Stop", type="secondary"):
                dashboard_controller.emergency_system_stop()
                st.error("Emergency stop activated!")

        with col2:
            if st.button("Pause All", type="secondary"):
                dashboard_controller.emergency_pause()
                st.warning("All trading paused")

        with col3:
            if st.button("Resume All", type="primary"):
                dashboard_controller.resume_system()
                st.success("System resumed")

        # Performance Report
        st.header("📊 Performance Report")
        performance = status.get('performance', {})

        if performance:
            col1, col2, col3 = st.columns(3)
            with col1:
                total_pnl = performance.get('system_pnl', 0)
                st.metric("Total P&L", f"${total_pnl:.2f}")
            with col2:
                total_trades = performance.get('total_trades', 0)
                st.metric("Total Trades", total_trades)
            with col3:
                win_rate = performance.get('system_win_rate', 0)
                st.metric("Win Rate", f"{win_rate:.1%}")

        # System Logs
        st.header("📋 Recent Commands")
        commands = dashboard_controller.get_command_history(limit=5)

        if commands:
            for cmd in commands:
                timestamp = cmd.get('timestamp', 'Unknown')
                action = cmd.get('action', 'Unknown')
                status_icon = "✅" if cmd.get('executed') else "❌"
                st.write(f"{status_icon} {timestamp}: {action}")
        else:
            st.info("No recent commands")

        # Auto-refresh
        st.markdown("---")
        st.caption("Dashboard auto-refreshes every 30 seconds")
        time.sleep(30)
        st.rerun()

    return streamlit_dashboard

if __name__ == "__main__":
    # Example usage and testing
    print("🎛️ Dashboard Control System Test")

    # Register some test strategies
    dashboard_system.register_strategy(
        "momentum_strategy",
        "Momentum-based trading strategy",
        {"symbol": "R_10", "position_size": 1000}
    )

    dashboard_system.register_strategy(
        "mean_reversion",
        "Mean reversion trading strategy",
        {"symbol": "frxUSDJPY", "threshold": 0.001}
    )

    # Register market feeds
    dashboard_system.register_market_feed("R_10")
    dashboard_system.register_market_feed("frxUSDJPY")

    # Start strategies
    dashboard_system.start_strategy("momentum_strategy")

    # Get status
    status = dashboard_system.get_full_status()
    print(f"System status: {status['system_mode']}")
    print(f"Active strategies: {status['emergency_system']['position_count']}")

    # Update market data
    dashboard_system.update_market_data("R_10", 123.45, 100000, 123.44, 123.46)

    print("✅ Dashboard Control System operational!")

    # Keep running for 30 seconds to test monitoring
    time.sleep(30)

    print("🎛️ Test completed!")
