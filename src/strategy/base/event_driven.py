"""
Event-Driven Mixin
==================
Enhancements to BaseStrategy for advanced event handling.

This mixin provides additional event-driven capabilities:
- Strategy state management
- Advanced order management
- Performance tracking
- Emergency controls integration
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional


class EventDrivenMixin:
    """
    Mixin class that enhances strategies with advanced event handling.
    """

    def __init__(self):
        """Initialize event-driven features."""
        self._strategy_state = {
            'active': True,
            'emergency_stop': False,
            'last_signal': None,
            'signal_count': 0,
            'trade_count': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'last_trade_time': None,
            'last_trade_result': None
        }

        self._performance_metrics = {
            'total_pnl': 0,
            'win_rate': 0,
            'avg_trade_pnl': 0,
            'max_drawdown': 0,
            'current_drawdown': 0,
            'peak_value': self.get_portfolio_value()
        }

    def check_emergency_conditions(self) -> bool:
        """
        Check for emergency stop conditions.

        Returns:
            True if emergency stop should be activated
        """
        try:
            # Check drawdown limits
            if hasattr(self, 'p') and hasattr(self.p, 'max_drawdown'):
                portfolio_value = self.get_portfolio_value()
                peak_value = self._performance_metrics['peak_value']
                current_drawdown = (peak_value - portfolio_value) / peak_value

                if current_drawdown > self.p.max_drawdown:
                    self.logger.critical(f"Emergency stop: Drawdown limit exceeded ({current_drawdown:.1%} > {self.p.max_drawdown:.1%})")
                    return True

            # Check consecutive losses
            if self._strategy_state['consecutive_losses'] >= 5:
                self.logger.critical(f"Emergency stop: Too many consecutive losses ({self._strategy_state['consecutive_losses']})")
                return True

            # Check time-based stops
            if hasattr(self, 'p') and hasattr(self.p, 'max_trade_frequency'):
                # Implementation would check trade frequency limits
                pass

        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")

        return False

    def update_performance_metrics(self, pnl: float):
        """
        Update strategy performance metrics.

        Args:
            pnl: Profit/loss from last trade
        """
        self._strategy_state['trade_count'] += 1

        # Update win/loss streak
        if pnl > 0:
            self._strategy_state['consecutive_wins'] += 1
            self._strategy_state['consecutive_losses'] = 0
            self._strategy_state['last_trade_result'] = 'win'
        else:
            self._strategy_state['consecutive_losses'] += 1
            self._strategy_state['consecutive_wins'] = 0
            self._strategy_state['last_trade_result'] = 'loss'

        # Update performance metrics
        self._performance_metrics['total_pnl'] += pnl

        # Update drawdown calculations
        current_value = self.get_portfolio_value()
        if current_value > self._performance_metrics['peak_value']:
            self._performance_metrics['peak_value'] = current_value
            self._performance_metrics['current_drawdown'] = 0
        else:
            self._performance_metrics['current_drawdown'] = (self._performance_metrics['peak_value'] - current_value) / self._performance_metrics['peak_value']
            self._performance_metrics['max_drawdown'] = max(
                self._performance_metrics['max_drawdown'],
                self._performance_metrics['current_drawdown']
            )

        # Calculate win rate
        total_trades = self._strategy_state['trade_count']
        winning_trades = sum(1 for trade in self._strategy_state.get('trade_history', []) if trade.get('pnl', 0) > 0)
        self._performance_metrics['win_rate'] = winning_trades / total_trades if total_trades > 0 else 0

    def log_strategy_status(self):
        """Log current strategy status."""
        status = f"""
Strategy Status Report:
├── Active: {self._strategy_state['active']}
├── Emergency Stop: {self._strategy_state['emergency_stop']}
├── Position Size: {self.position_size}
├── Unrealized P&L: {self.unrealized_pnl:.2f}
├── Total Trades: {self._strategy_state['trade_count']}
├── Win Rate: {self._performance_metrics['win_rate']:.1%}
├── Current Drawdown: {self._performance_metrics['current_drawdown']:.1%}
├── Max Drawdown: {self._performance_metrics['max_drawdown']:.1%}
├── Consecutive Wins: {self._strategy_state['consecutive_wins']}
└── Consecutive Losses: {self._strategy_state['consecutive_losses']}
        """
        self.logger.info(status.strip())

    def pre_next_checks(self) -> bool:
        """
        Perform pre-next() checks to ensure safe execution.

        Returns:
            True if strategy can continue, False if it should be paused
        """
        # Check emergency conditions
        if self.check_emergency_conditions():
            self._strategy_state['emergency_stop'] = True
            self._strategy_state['active'] = False
            return False

        # Check if strategy is active
        if not self._strategy_state['active']:
            return False

        return True

    def post_signal_actions(self, signal_type: str, data: Optional[Dict[str, Any]] = None):
        """
        Perform actions after signal generation.

        Args:
            signal_type: Type of signal (BUY, SELL, HOLD)
            data: Additional signal data
        """
        self._strategy_state['last_signal'] = {
            'type': signal_type,
            'timestamp': datetime.now(),
            'data': data or {}
        }
        self._strategy_state['signal_count'] += 1

        self.logger.debug(f"Signal generated: {signal_type} ({self._strategy_state['signal_count']} total)")

    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy statistics.

        Returns:
            Dictionary with strategy statistics
        """
        return {
            'state': self._strategy_state.copy(),
            'performance': self._performance_metrics.copy(),
            'position': {
                'size': self.position_size,
                'value': self.get_position_value(),
                'pnl': self.unrealized_pnl
            },
            'account': {
                'cash': self.cash,
                'portfolio_value': self.get_portfolio_value()
            }
        }

    def reset_strategy_state(self):
        """Reset strategy state (for testing or recovery)."""
        self._strategy_state = {
            'active': True,
            'emergency_stop': False,
            'last_signal': None,
            'signal_count': 0,
            'trade_count': 0,
            'consecutive_losses': 0,
            'consecutive_wins': 0,
            'last_trade_time': None,
            'last_trade_result': None,
            'trade_history': []
        }

        self._performance_metrics = {
            'total_pnl': 0,
            'win_rate': 0,
            'avg_trade_pnl': 0,
            'max_drawdown': 0,
            'current_drawdown': 0,
            'peak_value': self.get_portfolio_value()
        }

        self.logger.info("Strategy state reset")
