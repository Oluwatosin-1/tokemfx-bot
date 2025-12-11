"""
Breakout Strategies
===================
Volatility breakout and channel trading strategies.

This module contains:
- Bollinger Breakout Strategy
- ATR Breakout Strategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class BollingerBreakoutStrategy(BaseStrategy):
    """
    Bollinger Bands Breakout Strategy.

    This strategy trades breakouts from Bollinger Band squeezes:
    - Buy when price breaks above upper Bollinger Band
    - Sell when price breaks below lower Bollinger Band
    - Exit when price returns inside the bands

    Parameters:
        bb_period (int): Period for Bollinger Band calculation (default: 20)
        bb_dev (float): Standard deviation multiplier for bands (default: 2.0)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("bb_period", 20),
        ("bb_dev", 2.0),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize Bollinger breakout strategy indicators."""
        super().__init__()

        # Bollinger Bands with specified parameters
        bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.bb_period,
            devfactor=self.p.bb_dev
        )

        # Extract individual bands
        self.bb_high = bb.top
        self.bb_low = bb.bot
        self.bb_mid = bb.mid

        # Band width for volatility measurement
        self.band_width = (self.bb_high - self.bb_low) / self.bb_mid

        self.logger.info("Bollinger Breakout Strategy initialized: period=%d, dev=%.1f",
                        self.p.bb_period, self.p.bb_dev)

    def next(self):
        """Execute Bollinger breakout logic."""
        if not self.position:
            # No position - look for breakouts
            if self.data.close[0] > self.bb_high[0]:
                # Price breaks above upper band - bullish breakout
                self.buy(size=self.p.size)
                self.logger.info("BUY signal: Bollinger breakout above (price=%.5f, band=%.5f)",
                               self.data.close[0], self.bb_high[0])

            elif self.data.close[0] < self.bb_low[0]:
                # Price breaks below lower band - bearish breakout
                self.sell(size=self.p.size)
                self.logger.info("SELL signal: Bollinger breakout below (price=%.5f, band=%.5f)",
                               self.data.close[0], self.bb_low[0])

        elif self.position.size > 0:
            # Long position - exit if price returns inside bands
            if self.data.close[0] < self.bb_high[0]:
                self.close()
                self.logger.info("EXIT LONG: Price returned inside bands (price=%.5f)",
                               self.data.close[0])

        elif self.position.size < 0:
            # Short position - exit if price returns inside bands
            if self.data.close[0] > self.bb_low[0]:
                self.close()
                self.logger.info("EXIT SHORT: Price returned inside bands (price=%.5f)",
                               self.data.close[0])

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)


class ATRBreakoutStrategy(BaseStrategy):
    """
    ATR (Average True Range) Breakout Strategy with Bracket Orders.

    This strategy uses volatility-based breakouts with ATR for:
    - Entry based on Donchian channel breaks
    - Stop-loss and take-profit based on ATR multiples
    - Risk management using volatility-adjusted stops

    Parameters:
        donchian_period (int): Period for Donchian channel (default: 20)
        atr_period (int): Period for ATR calculation (default: 14)
        atr_multiplier (float): ATR multiplier for stop distance (default: 1.0)
        risk_reward (float): Risk-reward ratio for take-profit (default: 2.0)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("donchian_period", 20),
        ("atr_period", 14),
        ("atr_multiplier", 1.0),
        ("risk_reward", 2.0),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize ATR breakout strategy indicators."""
        super().__init__()

        # Donchian channel for breakout detection
        self.don_high = bt.indicators.Highest(self.data.high, period=self.p.donchian_period)
        self.don_low = bt.indicators.Lowest(self.data.low, period=self.p.donchian_period)

        # ATR for volatility-based stops
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)

        # Track orders for bracket management
        self.entry_order = None

        self.logger.info("ATR Breakout Strategy initialized: donchian=%d, atr=%d, multiplier=%.1f",
                        self.p.donchian_period, self.p.atr_period, self.p.atr_multiplier)

    def next(self):
        """Execute ATR breakout logic."""
        if not self.position:
            # No position - look for Donchian breakouts
            if self.data.close[0] > self.don_high[-1]:
                # Break above prior Donchian high - bullish breakout
                entry_price = self.data.close[0]
                atr_value = self.atr[0]
                stop_distance = atr_value * self.p.atr_multiplier
                stop_price = entry_price - stop_distance
                limit_price = entry_price + (stop_distance * self.p.risk_reward)

                # Enter long with bracket orders
                self.entry_order = self.buy_bracket(
                    size=self.p.size,
                    price=entry_price,
                    stopprice=stop_price,
                    limitprice=limit_price
                )

                self.logger.info("BUY signal: ATR breakout (entry=%.5f, stop=%.5f, limit=%.5f)",
                               entry_price, stop_price, limit_price)

        # Note: No explicit exit logic here - managed by bracket orders automatically
        # The bracket orders handle stop-loss and take-profit automatically

    def notify_order(self, order):
        """Enhanced order handling for bracket orders."""
        super().notify_order(order)

        # Clean up entry order reference when filled/cancelled
        if order == self.entry_order and order.status in [order.Completed, order.Cancelled]:
            self.entry_order = None

    def notify_trade(self, trade):
        """Handle bracket order trade completion."""
        super().notify_trade(trade)

        if trade.isclosed:
            pnl = trade.pnlcomm if hasattr(trade, 'pnlcomm') else 0
            self.logger.info("Bracket order trade closed: P&L=%.2f", pnl)
