"""
Oscillator Strategies
=====================
Momentum and oscillator-based strategies.

This module contains:
- RSI Reversion Strategy
- MACD Strategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class RSIReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy.

    This strategy trades when RSI reaches extreme levels:
    - Buy when RSI is oversold (below rsi_oversold threshold)
    - Sell when RSI is overbought (above rsi_overbought threshold)
    - Holds position for a specified number of periods

    Parameters:
        rsi_period (int): Period for RSI calculation (default: 14)
        rsi_overbought (float): RSI overbought level (default: 70)
        rsi_oversold (float): RSI oversold level (default: 30)
        period_hold (int): Number of periods to hold position (default: 5)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("period_hold", 5),
    )

    def __init__(self):
        """Initialize RSI strategy indicators."""
        super().__init__()
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.hold_counter = 0

        self.logger.info("RSI Strategy initialized: period=%d, overbought=%.1f, oversold=%.1f",
                        self.p.rsi_period, self.p.rsi_overbought, self.p.rsi_oversold)

    def next(self):
        """Execute RSI reversion logic."""
        if not self.position:
            # No position - look for entry signals
            if self.rsi[0] < self.p.rsi_oversold:
                # RSI oversold - bullish signal
                self.buy()
                self.hold_counter = 0
                self.logger.info("BUY signal: RSI oversold at %.2f", self.rsi[0])

            elif self.rsi[0] > self.p.rsi_overbought:
                # RSI overbought - bearish signal
                self.sell()
                self.hold_counter = 0
                self.logger.info("SELL signal: RSI overbought at %.2f", self.rsi[0])

        elif self.position.size != 0:
            # In position - check hold period
            self.hold_counter += 1

            if self.hold_counter >= self.p.period_hold:
                # Hold period complete - exit position
                exit_reason = "hold period complete"
                self.close()
                self.logger.info("EXIT: %s after %d periods", exit_reason, self.hold_counter)

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy.

    This strategy uses MACD crossovers for trend signals:
    - Buy when MACD line crosses above signal line
    - Sell when MACD line crosses below signal line

    Parameters:
        fast (int): Fast EMA period (default: 12)
        slow (int): Slow EMA period (default: 26)
        signal (int): Signal line period (default: 9)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("fast", 12),
        ("slow", 26),
        ("signal", 9),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize MACD strategy indicators."""
        super().__init__()

        # MACD indicator with specified periods
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast,
            period_me2=self.p.slow,
            period_signal=self.p.signal
        )

        # Crossover detector for MACD vs signal line
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        self.logger.info("MACD Strategy initialized: fast=%d, slow=%d, signal=%d",
                        self.p.fast, self.p.slow, self.p.signal)

    def next(self):
        """Execute MACD crossover logic."""
        if not self.position:
            # No position - look for MACD signals
            if self.crossover > 0:
                # MACD crosses above signal line - bullish
                self.buy(size=self.p.size)
                self.logger.info("BUY signal: MACD crossover at price %.5f", self.data.close[0])

            elif self.crossover < 0:
                # MACD crosses below signal line - bearish
                self.sell(size=self.p.size)
                self.logger.info("SELL signal: MACD crossover at price %.5f", self.data.close[0])

        elif self.position.size > 0:
            # Long position - exit on bearish crossover
            if self.crossover < 0:
                self.close()
                self.logger.info("EXIT LONG: MACD crossover at price %.5f", self.data.close[0])

        elif self.position.size < 0:
            # Short position - exit on bullish crossover
            if self.crossover > 0:
                self.close()
                self.logger.info("EXIT SHORT: MACD crossover at price %.5f", self.data.close[0])

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)
