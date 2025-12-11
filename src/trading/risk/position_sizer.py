"""
Position Sizing Module
=======================
Enterprise-grade position sizing and risk-adjusted allocation system.

This module provides sophisticated position sizing algorithms that:
- Calculate optimal position sizes based on risk tolerance
- Implement Kelly criterion and fixed fractional sizing
- Ensure portfolio risk limits are maintained
- Support dynamic position sizing based on volatility
- Provide conservative and aggressive sizing modes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Advanced position sizing system for risk-optimized trading.

    Implements multiple sizing methodologies:
    - Fixed Fractional: Risk fixed percentage of capital per trade
    - Kelly Criterion: Optimal sizing based on win rate and risk-reward
    - Volatility-Adjusted: Size positions based on market volatility
    - Portfolio-Based: Size to maintain portfolio risk limits
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize position sizer with configuration.

        Args:
            config: Configuration dictionary with sizing parameters
        """
        self.config = config or self._get_default_config()
        self.risk_tolerance = self.config['risk_tolerance']
        self.max_allocation = self.config['max_allocation']
        self.min_allocation = self.config['min_allocation']
        self.volatility_window = self.config['volatility_window']
        self.sizing_method = self.config['sizing_method']

        logger.info(f"Position sizer initialized with {self.sizing_method} method")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for position sizing."""
        return {
            'risk_tolerance': 0.02,  # 2% risk per trade
            'max_allocation': 0.20,  # Max 20% of capital per trade
            'min_allocation': 0.005, # Min 0.5% of capital per trade
            'volatility_window': 20, # 20-period volatility window
            'sizing_method': 'fixed_fractional',
            'kelly_fraction': 0.5,  # Use half-Kelly for conservatism
            'vol_adjustment_factor': 1.0,  # Volatility adjustment multiplier
            'portfolio_risk_limit': 0.05  # Max 5% portfolio risk
        }

    def calculate_position_size(self,
                              account_balance: float,
                              instrument: str,
                              entry_price: float,
                              stop_loss: float,
                              risk_reward_ratio: Optional[float] = None,
                              market_data: Optional[pd.DataFrame] = None,
                              current_positions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Calculate optimal position size for a trade.

        Args:
            account_balance: Current account balance
            instrument: Trading instrument
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_reward_ratio: Risk-to-reward ratio (optional)
            market_data: Recent price data for volatility calculation
            current_positions: Current open positions

        Returns:
            Dictionary with position sizing details
        """
        logger.info(f"Calculating position size for {instrument}")

        try:
            # Calculate risk per trade based on stop loss
            risk_per_trade = abs(entry_price - stop_loss) / entry_price
            if risk_per_trade <= 0:
                return self._create_error_result("Invalid stop loss")

            # Get capital to risk (respecting portfolio limits)
            capital_at_risk = self._calculate_portfolio_risk_allocation(
                account_balance, current_positions
            )

            # Calculate raw position size based on sizing method
            if self.sizing_method == 'fixed_fractional':
                raw_size = self._fixed_fractional_sizing(capital_at_risk, risk_per_trade)
            elif self.sizing_method == 'kelly':
                raw_size = self._kelly_sizing(capital_at_risk, risk_per_trade, risk_reward_ratio)
            elif self.sizing_method == 'vol_adjusted':
                raw_size = self._volatility_adjusted_sizing(capital_at_risk, risk_per_trade, market_data)
            else:
                raw_size = self._fixed_fractional_sizing(capital_at_risk, risk_per_trade)

            # Apply volatility adjustment if market data available
            if market_data is not None and len(market_data) >= self.volatility_window:
                raw_size = self._apply_volatility_adjustment(raw_size, market_data)

            # Apply position size constraints
            final_size = self._apply_size_constraints(raw_size, account_balance)

            # Calculate trade value and risk amounts
            trade_value = final_size * entry_price
            risk_amount = trade_value * risk_per_trade
            risk_percentage = (risk_amount / account_balance) * 100

            result = {
                'status': 'success',
                'position_size': final_size,
                'trade_value': trade_value,
                'risk_amount': risk_amount,
                'risk_percentage': risk_percentage,
                'sizing_method': self.sizing_method,
                'stop_loss_distance': risk_per_trade,
                'capital_allocated': final_size * entry_price,
                'portfolio_impact': (final_size * entry_price / account_balance) * 100,
                'sizing_factors': {
                    'account_balance': account_balance,
                    'capital_at_risk': capital_at_risk,
                    'risk_tolerance': self.risk_tolerance,
                    'volatility_adjustment': market_data is not None
                }
            }

            # Additional metrics if risk-reward provided
            if risk_reward_ratio:
                result.update({
                    'risk_reward_ratio': risk_reward_ratio,
                    'potential_profit': risk_amount * risk_reward_ratio,
                    'profit_percentage': (risk_amount * risk_reward_ratio / (final_size * entry_price)) * 100
                })

            logger.info(".2f")
            return result

        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return self._create_error_result(str(e))

    def _calculate_portfolio_risk_allocation(self,
                                           account_balance: float,
                                           current_positions: Optional[List[Dict[str, Any]]] = None) -> float:
        """
        Calculate available capital for new position considering portfolio risk.

        Args:
            account_balance: Total account balance
            current_positions: List of current open positions

        Returns:
            Capital available for new position
        """
        # Base allocation is risk tolerance percentage of total balance
        base_allocation = account_balance * self.risk_tolerance

        # Adjust based on current portfolio exposure
        if current_positions:
            portfolio_exposure = sum(
                pos.get('size', 0) * pos.get('entry_price', 1) * pos.get('risk', self.risk_tolerance)
                for pos in current_positions
            )
            portfolio_exposure_pct = portfolio_exposure / account_balance

            # Reduce allocation if portfolio is highly exposed
            risk_limit_reduction = max(0, portfolio_exposure_pct - self.config['portfolio_risk_limit'])
            if risk_limit_reduction > 0:
                base_allocation *= (1 - min(1, risk_limit_reduction * 2))  # Reduce by up to 100%

        return max(base_allocation, account_balance * self.min_allocation)

    def _fixed_fractional_sizing(self, capital_at_risk: float, risk_per_trade: float) -> float:
        """
        Fixed fractional position sizing.
        Position size = (Capital at Risk) / Risk per Trade

        Args:
            capital_at_risk: Capital available for this trade risk
            risk_per_trade: Risk per trade as decimal

        Returns:
            Position size in dollars
        """
        return capital_at_risk / risk_per_trade

    def _kelly_sizing(self, capital_at_risk: float, risk_per_trade: float,
                     risk_reward_ratio: Optional[float] = None) -> float:
        """
        Kelly criterion position sizing.
        Account balance growth is maximized when position size is based on
        win rate divided by loss rate, adjusted for risk-reward.

        Args:
            capital_at_risk: Capital available for this trade risk
            risk_per_trade: Risk per trade as decimal
            risk_reward_ratio: Risk-to-reward ratio

        Returns:
            Kelly-adjusted position size
        """
        # Assume historical win rate (would normally be calculated from data)
        assumed_win_rate = 0.55  # 55% win rate assumption

        if risk_reward_ratio:
            # Adjusted Kelly formula: K * (R+1) / R where K is basic Kelly
            kelly_fraction = (assumed_win_rate - (1 - assumed_win_rate) / risk_reward_ratio) / risk_reward_ratio
        else:
            # Basic Kelly: Win rate - Loss rate
            kelly_fraction = assumed_win_rate - (1 - assumed_win_rate)

        # Apply Kelly fraction (often use half-Kelly for conservatism)
        kelly_fraction *= self.config['kelly_fraction']

        # Ensure Kelly fraction is reasonable
        kelly_fraction = max(-0.1, min(kelly_fraction, self.config['max_allocation']))

        return capital_at_risk * abs(kelly_fraction) / risk_per_trade

    def _volatility_adjusted_sizing(self, capital_at_risk: float, risk_per_trade: float,
                                  market_data: Optional[pd.DataFrame]) -> float:
        """
        Volatility-adjusted position sizing.
        Reduce position size in high volatility, increase in low volatility.

        Args:
            capital_at_risk: Capital available for this trade risk
            risk_per_trade: Risk per trade as decimal
            market_data: Recent price data

        Returns:
            Volatility-adjusted position size
        """
        if market_data is None or len(market_data) < self.volatility_window:
            return self._fixed_fractional_sizing(capital_at_risk, risk_per_trade)

        # Calculate volatility (standard deviation of returns)
        returns = market_data['close'].pct_change().dropna()
        current_volatility = returns.tail(self.volatility_window).std()

        # Average volatility over longer period
        avg_volatility = returns.tail(self.volatility_window * 2).std()

        # Adjust position size inversely to volatility
        if current_volatility > 0 and avg_volatility > 0:
            vol_adjustment = avg_volatility / current_volatility  # Higher vol = smaller sizing
            vol_adjustment = np.clip(vol_adjustment, 0.5, 2.0)  # Limit adjustment range
        else:
            vol_adjustment = 1.0

        # Apply volatility adjustment factor
        vol_adjustment *= self.config['vol_adjustment_factor']

        base_size = capital_at_risk / risk_per_trade
        adjusted_size = base_size * vol_adjustment

        logger.debug(".4f"                   return adjusted_size

    def _apply_volatility_adjustment(self, base_size: float, market_data: Optional[pd.DataFrame]) -> float:
        """
        Apply secondary volatility adjustment to already-sized position.

        Args:
            base_size: Base position size
            market_data: Recent price data

        Returns:
            Volatility-adjusted position size
        """
        if market_data is None or len(market_data) < self.volatility_window:
            return base_size

        # Calculate short-term volatility (last 10 periods)
        short_returns = market_data['close'].pct_change().dropna().tail(10)
        if len(short_returns) >= 5:
            short_vol = short_returns.std()
            # Adjust for very high short-term volatility
            if short_vol > short_returns.mean() * 2:  # 2x normal vol
                vol_reduction = 0.7  # Reduce 30%
                logger.info(f"High short-term volatility detected, reducing position by {vol_reduction*100:.1f}%")
                return base_size * vol_reduction

        return base_size

    def _apply_size_constraints(self, raw_size: float, account_balance: float) -> float:
        """
        Apply position size constraints (minimum and maximum limits).

        Args:
            raw_size: Raw calculated position size
            account_balance: Current account balance

        Returns:
            Constrained position size
        """
        # Convert to trade value for percentage calculations
        trade_value = raw_size  # raw_size is already in dollars

        # Apply percentage constraints
        max_value = account_balance * self.max_allocation
        min_value = account_balance * self.min_allocation

        constrained_value = np.clip(trade_value, min_value, max_value)

        logger.debug(".2f"        return constrained_value

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            'status': 'error',
            'error_message': error_message,
            'position_size': 0.0,
            'sizing_method': self.sizing_method,
            'timestamp': datetime.now().isoformat()
        }


# Global position sizer instance
default_position_sizer = PositionSizer()

def calculate_optimal_position(account_balance: float,
                             instrument: str,
                             entry_price: float,
                             stop_loss: float,
                             sizing_method: str = 'fixed_fractional',
                             **kwargs) -> Dict[str, Any]:
    """
    Convenience function for position size calculation.

    Args:
        account_balance: Current account balance
        instrument: Trading instrument
        entry_price: Entry price
        stop_loss: Stop loss price
        sizing_method: Sizing method to use
        **kwargs: Additional parameters

    Returns:
        Position sizing result
    """
    # Create sizer with specified method
    config = {'sizing_method': sizing_method, **kwargs}
    sizer = PositionSizer(config)

    return sizer.calculate_position_size(
        account_balance=account_balance,
        instrument=instrument,
        entry_price=entry_price,
        stop_loss=stop_loss,
        **kwargs
    )


def validate_position_size_limits(account_balance: float,
                                position_size: float,
                                max_allocation: float = 0.20) -> Dict[str, Any]:
    """
    Validate position size against account limits.

    Args:
        account_balance: Current account balance
        position_size: Proposed position size in dollars
        max_allocation: Maximum allocation percentage

    Returns:
        Validation result
    """
    allocation_pct = position_size / account_balance

    if allocation_pct > max_allocation:
        return {
            'valid': False,
            'reason': f'Position exceeds {max_allocation*100:.1f}% allocation limit',
            'current_allocation': allocation_pct * 100,
            'max_allowed': max_allocation * 100,
            'suggested_size': account_balance * max_allocation
        }

    return {
        'valid': True,
        'allocation_percentage': allocation_pct * 100,
        'remaining_allocation_possible': (max_allocation - allocation_pct) * 100
    }


# Export key functions and classes
__all__ = [
    'PositionSizer',
    'calculate_optimal_position',
    'validate_position_size_limits',
    'default_position_sizer'
]
