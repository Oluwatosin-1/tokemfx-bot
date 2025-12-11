"""
Risk Management System
======================
Advanced risk controls and portfolio protection systems.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """
    Data class for risk management limits and thresholds.
    """
    max_position_size: float = 0.02  # Max 2% per position
    max_total_exposure: float = 0.10  # Max 10% total exposure
    max_daily_loss: float = 0.05  # Max 5% daily loss
    max_drawdown: float = 0.10  # Max 10% drawdown
    max_consecutive_losses: int = 3
    max_trades_per_day: int = 10
    min_win_rate: float = 0.4  # Minimum 40% win rate
    max_volatility_adjustment: float = 0.5  # Adjust position size by max 50%

    # Stop loss settings
    default_stop_loss_pct: float = 0.02  # 2% default stop loss
    trailing_stop_activation: float = 0.005  # 0.5% profit before trailing
    trailing_stop_distance: float = 0.01  # 1% trailing stop distance

    # Correlation limits
    max_correlation_exposure: float = 0.7  # Max 70% correlation between positions


class RiskManager:
    """
    Comprehensive risk management system for trading bot protection.
    """

    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        self.risk_limits = risk_limits or RiskLimits()

        # Risk tracking state
        self.daily_pnl = 0.0
        self.current_drawdown = 0.0
        self.peak_portfolio_value = 10000.0  # Starting value
        self.portfolio_value = 10000.0
        self.daily_trade_count = 0
        self.consecutive_losses = 0
        self.last_trade_time = None

        # Position tracking
        self.open_positions = {}
        self.correlation_matrix = {}

        # Risk metrics history
        self.pnl_history = []
        self.drawdown_history = []

        self.reset_daily_stats()

        logger.info("🛡️ Risk Manager initialized with limits:")
        logger.info(f"   Max position size: {self.risk_limits.max_position_size*100:.1f}%")
        logger.info(f"   Max daily loss: {self.risk_limits.max_daily_loss*100:.1f}%")
        logger.info(f"   Max drawdown: {self.risk_limits.max_drawdown*100:.1f}%")

    def reset_daily_stats(self):
        """
        Reset daily risk statistics at start of trading day.
        """
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.consecutive_losses = 0
        self.last_trade_time = None

        logger.info("📊 Daily risk statistics reset")

    def can_open_position(self,
                         instrument: str,
                         position_size: float,
                         direction: str,
                         entry_price: float,
                         stop_loss_price: Optional[float] = None,
                         volatility_adjustment: Optional[float] = None) -> Tuple[bool, str]:
        """
        Comprehensive risk check before opening a new position.

        Args:
            instrument: Trading instrument
            position_size: Size of position (as fraction of portfolio)
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            stop_loss_price: Optional stop loss price
            volatility_adjustment: Optional volatility-based size adjustment

        Returns:
            Tuple of (approved: bool, reason: str)
        """
        # Check position size limit
        if position_size > self.risk_limits.max_position_size:
            return False, f"Position size {position_size*100:.1f}% exceeds limit {self.risk_limits.max_position_size*100:.1f}%"

        # Check total exposure limit
        total_current_exposure = sum(pos['size'] for pos in self.open_positions.values())
        if total_current_exposure + position_size > self.risk_limits.max_total_exposure:
            return False, f"Total exposure limit exceeded: {(total_current_exposure + position_size)*100:.1f}% > {self.risk_limits.max_total_exposure*100:.1f}%"
        # Check daily loss limit
        if self.daily_pnl < -self.risk_limits.max_daily_loss:
            return False, f"Daily loss limit breached: {abs(self.daily_pnl)*100:.1f}% > {self.risk_limits.max_daily_loss*100:.1f}%"
        # Check drawdown limit
        if self.current_drawdown > self.risk_limits.max_drawdown:
            return False, f"Drawdown limit breached: {self.current_drawdown*100:.1f}% > {self.risk_limits.max_drawdown*100:.1f}%"
        # Check consecutive losses
        if self.consecutive_losses >= self.risk_limits.max_consecutive_losses:
            return False, f"Consecutive losses limit reached ({self.consecutive_losses})"

        # Check daily trade count
        if self.daily_trade_count >= self.risk_limits.max_trades_per_day:
            return False, f"Daily trade limit reached ({self.daily_trade_count}/{self.risk_limits.max_trades_per_day})"

        # Check stop loss requirement
        if stop_loss_price is None:
            stop_loss_price = entry_price * (1 - self.risk_limits.default_stop_loss_pct if direction == 'BUY' else 1 + self.risk_limits.default_stop_loss_pct)

        # Calculate risk amount
        risk_amount = abs(entry_price - stop_loss_price) * position_size
        risk_pct = risk_amount / self.portfolio_value

        if risk_pct > self.risk_limits.max_position_size:
            return False, f"Risk percentage too high: {risk_pct*100:.1f}% > {self.risk_limits.max_position_size*100:.1f}%"
        # Apply volatility adjustment if provided
        if volatility_adjustment:
            adjusted_size = position_size * (1 - volatility_adjustment)
            adjusted_size = max(position_size * (1 - self.risk_limits.max_volatility_adjustment), adjusted_size)
            position_size = adjusted_size

            logger.info(f"Volatility adjustment applied: {position_size*100:.1f}%")

        return True, "Risk check passed"

    def update_portfolio_value(self, new_value: float):
        """
        Update portfolio value and calculate drawdown.

        Args:
            new_value: New portfolio value
        """
        self.portfolio_value = new_value

        # Update peak value
        self.peak_portfolio_value = max(self.peak_portfolio_value, new_value)

        # Calculate drawdown
        self.current_drawdown = (self.peak_portfolio_value - new_value) / self.peak_portfolio_value

        # Store history
        self.drawdown_history.append({
            'timestamp': datetime.now(),
            'portfolio_value': new_value,
            'drawdown': self.current_drawdown
        })

        logger.debug(f"Portfolio update: ${new_value:.3f}, Drawdown: {self.current_drawdown:.3f}")

    def record_trade(self,
                    pnl: float,
                    winning_trade: bool,
                    trade_size: float,
                    timestamp: Optional[datetime] = None):
        """
        Record a completed trade for risk tracking.

        Args:
            pnl: Profit/loss for the trade
            winning_trade: Whether the trade was profitable
            trade_size: Size of the trade
            timestamp: Optional trade timestamp
        """
        trade_time = timestamp or datetime.now()

        # Update daily statistics
        self.daily_pnl += pnl
        self.daily_trade_count += 1

        # Track consecutive losses
        if not winning_trade:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        self.last_trade_time = trade_time

        # Store trade in history
        self.pnl_history.append({
            'timestamp': trade_time,
            'pnl': pnl,
            'trade_size': trade_size,
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses
        })

        logger.info(f"📝 Trade recorded - P&L: ${pnl:.2f}, Daily P&L: ${self.daily_pnl:.2f}, Consec losses: {self.consecutive_losses}")

    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive risk metrics and limits.

        Returns:
            Dictionary with current risk status
        """
        return {
            'portfolio_value': self.portfolio_value,
            'peak_portfolio_value': self.peak_portfolio_value,
            'current_drawdown': self.current_drawdown,
            'daily_pnl': self.daily_pnl,
            'daily_trade_count': self.daily_trade_count,
            'consecutive_losses': self.consecutive_losses,

            # Risk limits
            'max_drawdown_limit': self.risk_limits.max_drawdown,
            'max_daily_loss_limit': self.risk_limits.max_daily_loss,
            'max_position_size_limit': self.risk_limits.max_position_size,
            'max_total_exposure_limit': self.risk_limits.max_total_exposure,

            # Status flags
            'breach_flags': {
                'drawdown_breach': self.current_drawdown > self.risk_limits.max_drawdown,
                'daily_loss_breach': self.daily_pnl < -self.risk_limits.max_daily_loss,
                'consecutive_loss_breach': self.consecutive_losses >= self.risk_limits.max_consecutive_losses
            },

            # Recent history
            'recent_trades': self.pnl_history[-5:] if self.pnl_history else []
        }

    def calculate_optimal_position_size(self,
                                      account_balance: float,
                                      risk_percentage: float,
                                      stop_loss_price: float,
                                      entry_price: float) -> float:
        """
        Calculate optimal position size using Kelly criterion and risk limits.

        Args:
            account_balance: Current account balance
            risk_percentage: Risk per trade as percentage
            stop_loss_price: Stop loss price
            entry_price: Entry price

        Returns:
            Optimal position size in dollars
        """
        # Calculate risk amount (distance to stop loss in price terms)
        risk_amount = abs(entry_price - stop_loss_price)

        # Position size based on fixed risk percentage
        position_value = account_balance * risk_percentage

        # Convert to number of units
        position_size = position_value / risk_amount

        # Apply risk limits
        max_position_by_value = account_balance * self.risk_limits.max_position_size
        max_position_size = max_position_by_value / risk_amount

        position_size = min(position_size, max_position_size)

        return position_size

    def should_pause_trading(self) -> Tuple[bool, str]:
        """
        Determine if trading should be paused due to risk conditions.

        Returns:
            Tuple of (pause_trading: bool, reason: str)
        """
        metrics = self.get_risk_metrics()

        # Check critical risk breaches
        if metrics['breach_flags']['drawdown_breach']:
            return True, f"Drawdown limit breached: {metrics['current_drawdown']*100:.1f}% > {metrics['max_drawdown_limit']*100:.1f}%"

        if metrics['breach_flags']['daily_loss_breach']:
            return True, f"Daily loss limit breached: {abs(metrics['daily_pnl'])*100:.1f}% > {metrics['max_daily_loss_limit']*100:.1f}%"

        if metrics['breach_flags']['consecutive_loss_breach']:
            return True, f"Too many consecutive losses ({metrics['consecutive_losses']})"

        if metrics['daily_trade_count'] >= self.risk_limits.max_trades_per_day:
            return True, f"Daily trade limit reached ({metrics['daily_trade_count']})"

        return False, "Risk conditions normal"

    def get_emergency_actions(self) -> Dict[str, Any]:
        """
        Get recommended emergency actions based on current risk state.

        Returns:
            Dictionary with emergency action recommendations
        """
        metrics = self.get_risk_metrics()

        actions = {
            'close_all_positions': False,
            'reduce_position_sizes': False,
            'increase_stop_losses': False,
            'pause_trading': False,
            'recommendations': []
        }

        # Severe drawdown - emergency stop
        if self.current_drawdown > self.risk_limits.max_drawdown * 1.2:
            actions['close_all_positions'] = True
            actions['pause_trading'] = True
            actions['recommendations'].append("🚨 CRITICAL: Execute emergency stop - close all positions")

        # High drawdown - reduce exposure
        elif self.current_drawdown > self.risk_limits.max_drawdown:
            actions['reduce_position_sizes'] = True
            actions['increase_stop_losses'] = True
            actions['pause_trading'] = True
            actions['recommendations'].append(f"Reduce exposure - current drawdown: {self.current_drawdown*100:.1f}%")

        # High consecutive losses
        elif self.consecutive_losses >= self.risk_limits.max_consecutive_losses:
            actions['pause_trading'] = True
            actions['recommendations'].append("Multiple consecutive losses - pause trading for review")

        return actions

    def update_correlation_matrix(self, price_data: Dict[str, List[float]]):
        """
        Update correlation matrix between instruments in portfolio.

        Args:
            price_data: Dictionary of instrument -> price series
        """
        if len(price_data) < 2:
            return

        # Calculate correlation matrix
        instruments = list(price_data.keys())
        correlation_matrix = {}

        for i, inst1 in enumerate(instruments):
            for inst2 in instruments[i+1:]:
                prices1 = np.array(price_data[inst1][-100:])  # Last 100 prices
                prices2 = np.array(price_data[inst2][-100:])

                if len(prices1) == len(prices2) and len(prices1) > 10:
                    correlation = np.corrcoef(prices1, prices2)[0, 1]
                    correlation_matrix[f"{inst1}_{inst2}"] = correlation

        self.correlation_matrix = correlation_matrix

        # Check for high correlation warnings
        high_corr_pairs = [(pair, corr) for pair, corr in correlation_matrix.items()
                          if abs(corr) > self.risk_limits.max_correlation_exposure]

        if high_corr_pairs:
            logger.warning("⚠️ High correlation detected between instruments:")
            for pair, corr in high_corr_pairs:
                logger.warning(f"High correlation: {pair}, correlation: {corr:.1f}")


# Convenience function
def create_risk_manager(risk_limits: Optional[RiskLimits] = None) -> RiskManager:
    """
    Create and return a risk manager instance.

    Args:
        risk_limits: Optional custom risk limits

    Returns:
        Configured RiskManager instance
    """
    return RiskManager(risk_limits)


__all__ = [
    'RiskLimits',
    'RiskManager',
    'create_risk_manager'
]
