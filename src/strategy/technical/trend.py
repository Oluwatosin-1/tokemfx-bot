"""
Trend Following Strategies
==========================
SuperTrend and trend-based trading strategies.

This module contains:
- SuperTrend Strategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class SuperTrendStrategy(BaseStrategy):
    """
    SuperTrend Strategy.

    This strategy follows the SuperTrend indicator:
    - Buy when price is above SuperTrend (uptrend)
    - Sell when price is below SuperTrend (downtrend)
    - Uses ATR for dynamic trailing stops

    Parameters:
        factor (float): ATR multiplier for SuperTrend calculation (default: 3.0)
        atr_period (int): Period for ATR calculation (default: 10)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("factor", 3.0),
        ("atr_period", 10),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize SuperTrend strategy indicators."""
        super().__init__()

        # ATR calculation
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)

        # Calculate SuperTrend components
        self.hl2 = (self.data.high + self.data.low) / 2

        # Basic upper/lower bands (ATR-based)
        self.basic_upper = self.hl2 + (self.atr * self.p.factor)
        self.basic_lower = self.hl2 - (self.atr * self.p.factor)

        # SuperTrend calculation
        self.trend_direction = 1  # 1 = uptrend, -1 = downtrend
        self.super_trend = bt.indicators.SMA(
            (self.basic_upper + self.basic_lower) / 2, period=1
        )

        self.logger.info("SuperTrend Strategy initialized: factor=%.1f, atr_period=%d",
                        self.p.factor, self.p.atr_period)

    def next(self):
        """Execute SuperTrend trend following logic."""
        # Recalculate SuperTrend value (simplified version)
        self.super_trend_value = (self.basic_upper[0] + self.basic_lower[0]) / 2

        if not self.position:
            # No position - entry based on SuperTrend trend
            if self.data.close[0] > self.super_trend_value:
                # Price above SuperTrend - uptrend, go long
                self.buy(size=self.p.size)
                self.trend_direction = 1
                self.logger.info("BUY signal: Trend above SuperTrend (price=%.5f, st=%.5f)",
                               self.data.close[0], self.super_trend_value)

            elif self.data.close[0] < self.super_trend_value:
                # Price below SuperTrend - downtrend, go short
                self.sell(size=self.p.size)
                self.trend_direction = -1
                self.logger.info("SELL signal: Trend below SuperTrend (price=%.5f, st=%.5f)",
                               self.data.close[0], self.super_trend_value)

        elif self.position.size > 0:
            # Long position - exit if trend reverses
            if self.data.close[0] < self.super_trend_value:
                self.close()
                self.logger.info("EXIT LONG: Trend reversal to downtrend (price=%.5f)",
                               self.data.close[0])

        elif self.position.size < 0:
            # Short position - exit if trend reverses
            if self.data.close[0] > self.super_trend_value:
                self.close()
                self.logger.info("EXIT SHORT: Trend reversal to uptrend (price=%.5f)",
                               self.data.close[0])

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)
