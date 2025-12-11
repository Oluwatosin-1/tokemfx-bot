"""
Moving Average Strategies
=========================
Trend-following strategies using moving averages.

This module contains:
- Moving Average Crossover Strategy
- EMA + RSI Hybrid Strategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class MovingAverageCrossStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.

    This strategy generates buy signals when the fast moving average crosses above
    the slow moving average, and sell signals when it crosses below.

    Parameters:
        fast_period (int): Period for fast moving average (default: 10)
        slow_period (int): Period for slow moving average (default: 30)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        super().__init__()

        # Calculate moving averages
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)

        # Calculate crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        self.logger.info(f"Initialized MA Cross strategy: fast={self.p.fast_period}, slow={self.p.slow_period}")

    def next(self):
        """Execute trading logic on each new bar."""
        # Check for position
        if not self.position:
            # No position - look for buy signal
            if self.crossover > 0:
                # Fast MA crossed above slow MA - bullish signal
                self.buy()
                self.logger.info(f"BUY signal at {self.data.close[0]:.5f}")

        elif self.position.size > 0:
            # Long position - look for sell signal
            if self.crossover < 0:
                # Fast MA crossed below slow MA - bearish signal
                self.close()
                self.logger.info(f"SELL signal (close long) at {self.data.close[0]:.5f}")

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)


class EMARSIHybridStrategy(BaseStrategy):
    """
    EMA + RSI Hybrid Strategy with ATR Trailing Stops.

    This advanced strategy combines:
    - EMA trend filter (fast/slow crossover)
    - RSI mean reversion signals
    - ATR-based trailing stops for risk management

    Parameters:
        fast_ema (int): Period for fast EMA (default: 10)
        slow_ema (int): Period for slow EMA (default: 30)
        rsi_period (int): Period for RSI calculation (default: 14)
        rsi_overbought (float): RSI overbought level (default: 70)
        rsi_oversold (float): RSI oversold level (default: 30)
        atr_period (int): Period for ATR calculation (default: 14)
        atr_multiplier (float): ATR multiplier for stop distance (default: 1.5)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("fast_ema", 10),
        ("slow_ema", 30),
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("atr_period", 14),
        ("atr_multiplier", 1.5),
        ("size", 1000),
    )

    def __init__(self):
        super().__init__()

        # Trend indicators
        self.ema_fast = bt.indicators.EMA(self.data.close, period=self.p.fast_ema)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=self.p.slow_ema)

        # Momentum indicator
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)

        # Volatility-based stop loss
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)

        # Track entry orders for bracket orders
        self.entry_order = None

        self.logger.info(f"Initialized EMA+RSI Hybrid strategy: "
                        f"fast_ema={self.p.fast_ema}, slow_ema={self.p.slow_ema}, "
                        f"rsi_period={self.p.rsi_period}")

    def next(self):
        """Execute hybrid strategy logic."""
        # Trend filter - EMA alignment
        ema_trend_up = self.ema_fast[0] > self.ema_slow[0]
        ema_trend_down = self.ema_fast[0] < self.ema_slow[0]

        if not self.position:
            # No position - look for entry signals

            # Long signal: EMA trend up + RSI oversold
            if ema_trend_up and self.rsi[0] < self.p.rsi_oversold:
                entry_price = self.data.close[0]
                atr_stop = entry_price - (self.atr[0] * self.p.atr_multiplier)

                # Enter long with trailing stop
                self.entry_order = self.buy(size=self.p.size)

                # Place ATR-based stop-loss
                self.sell(
                    exectype=bt.Order.Stop,
                    price=atr_stop,
                    size=self.p.size,
                    parent=self.entry_order
                )

                self.logger.info(f"BUY signal: EMA trend up + RSI oversold at {entry_price:.5f}")

            # Short signal: EMA trend down + RSI overbought
            elif ema_trend_down and self.rsi[0] > self.p.rsi_overbought:
                entry_price = self.data.close[0]
                atr_stop = entry_price + (self.atr[0] * self.p.atr_multiplier)

                # Enter short with trailing stop
                self.entry_order = self.sell(size=self.p.size)

                # Place ATR-based stop-loss
                self.buy(
                    exectype=bt.Order.Stop,
                    price=atr_stop,
                    size=self.p.size,
                    parent=self.entry_order
                )

                self.logger.info(f"SELL signal: EMA trend down + RSI overbought at {entry_price:.5f}")

        elif self.position.size > 0:
            # Long position - exit signals

            # Exit long on: EMA trend reversal OR RSI overbought
            if ema_trend_down or self.rsi[0] > self.p.rsi_overbought:
                exit_reason = "EMA trend reversal" if ema_trend_down else "RSI overbought"
                self.close()
                self.logger.info(f"EXIT LONG: {exit_reason} at {self.data.close[0]:.5f}")

        elif self.position.size < 0:
            # Short position - exit signals

            # Exit short on: EMA trend reversal OR RSI oversold
            if ema_trend_up or self.rsi[0] < self.p.rsi_oversold:
                exit_reason = "EMA trend reversal" if ema_trend_up else "RSI oversold"
                self.close()
                self.logger.info(f"EXIT SHORT: {exit_reason} at {self.data.close[0]:.5f}")

    def notify_order(self, order):
        """Enhanced order handling with bracket order management."""
        super().notify_order(order)

        # Clean up entry order reference when filled/cancelled
        if order == self.entry_order and order.status in [order.Completed, order.Cancelled]:
            self.entry_order = None

    def notify_trade(self, trade):
        """Enhanced trade notification with strategy-specific metrics."""
        super().notify_trade(trade)

        # Log performance metrics
        if trade.isclosed:
            pnl = trade.pnlcomm if hasattr(trade, 'pnlcomm') else 0
            duration = getattr(trade, 'barlen', 0)
            self.logger.info(f"Trade closed: P&L={pnl:.2f}, Duration={duration} bars")
