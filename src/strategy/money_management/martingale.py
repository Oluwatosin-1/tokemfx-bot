"""
Martingale Strategies
=====================
Classic and modified Martingale position sizing.

This module contains:
- MartingaleStrategy (Classic doubling on loss)
- ReverseMartingaleStrategy (Aka Anti-Martingale)
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class MartingaleStrategy(BaseStrategy):
    """
    Classic Martingale Strategy - HIGH RISK.

    Doubles stake after each loss until profit is made.
    EXTREMELY HIGH RISK - Can lead to total account loss in losing streaks.

    Parameters:
        base_stake (int): Initial stake size (default: 1000)
        multiplier (float): Stake multiplier after loss (default: 2.0)
        max_stake (int): Maximum stake limit (default: 50000)
        max_losses (int): Maximum consecutive losses before reset (default: 5)
        reset_on_win (bool): Reset stake to base on any win (default: True)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_stake", 1000),
        ("multiplier", 2.0),
        ("max_stake", 50000),
        ("max_losses", 5),
        ("reset_on_win", True),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize Martingale strategy."""
        super().__init__()

        self.current_stake = self.p.base_stake
        self.consecutive_losses = 0
        self.max_stake_hit = False

        # Simple demo signals - replace with real signals
        self.signal_counter = 0

        self.logger.warning("⚠️ MARTINGALE WARNING: This strategy can lead to total account loss! Use only for educational purposes.")

    def next(self):
        """Execute Martingale staking logic."""
        if not self.position:
            if self.max_stake_hit:
                return  # Stop trading if max stake limit hit

            stake = min(self.current_stake, self.p.max_stake)

            # Very basic alternating signals for demo
            self.signal_counter += 1
            is_buy_signal = self.signal_counter % 2 == 1

            if is_buy_signal:
                self.buy(size=stake)
                self.logger.info("BUY @ stake=%d (losses=%d)", stake, self.consecutive_losses)
            else:
                self.sell(size=stake)
                self.logger.info("SELL @ stake=%d (losses=%d)", stake, self.consecutive_losses)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - reset stake to base and reset loss counter
                self.current_stake = self.p.base_stake
                self.consecutive_losses = 0
                self.max_stake_hit = False
                self.close()
                self.logger.info("WIN: Reset stake to %d", self.p.base_stake)

            elif pnl < 0:
                # Loss - increase stake for next trade
                self.consecutive_losses += 1

                if self.consecutive_losses >= self.p.max_losses:
                    # Too many consecutive losses, reset everything
                    self.logger.error("MARTINGALE STOP: Too many consecutive losses (%d)",
                                    self.consecutive_losses)
                    self.current_stake = self.p.base_stake
                    self.consecutive_losses = 0
                    self.max_stake_hit = True
                    self.close()
                else:
                    # Classic Martingale: double the stake
                    new_stake = min(self.current_stake * self.p.multiplier, self.p.max_stake)
                    self.current_stake = new_stake

                    if self.current_stake >= self.p.max_stake:
                        self.max_stake_hit = True

                    self.close()
                    self.logger.warning("LOSS: Next stake increased to %d", self.current_stake)

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

        if order.status == order.Completed:
            self.logger.debug("Order completed: %s %d @ %.5f",
                            "BUY" if order.size > 0 else "SELL",
                            abs(order.size), order.executed.price)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)

        if trade.isclosed:
            pnl = trade.pnlcomm if hasattr(trade, 'pnlcomm') else 0
            self.logger.info("Trade closed: P&L = %.2f", pnl)


class ReverseMartingaleStrategy(BaseStrategy):
    """
    Reverse Martingale (Anti-Martingale) Strategy.

    Doubles stake after wins, resets on losses.
    More profitable during winning streaks but riskier.

    Parameters:
        base_stake (int): Initial stake size (default: 1000)
        multiplier (float): Stake multiplier after win (default: 2.0)
        max_stake (int): Maximum stake limit (default: 8000)
        max_wins (int): Maximum consecutive wins before reset (default: 4)
        reset_on_loss (bool): Reset stake to base on any loss (default: True)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_stake", 1000),
        ("multiplier", 2.0),
        ("max_stake", 8000),
        ("max_wins", 4),
        ("reset_on_loss", True),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize Reverse Martingale strategy."""
        super().__init__()

        self.current_stake = self.p.base_stake
        self.consecutive_wins = 0
        self.max_stake_reached = False

        # Simple demo signals
        self.signal_counter = 0

        self.logger.info("Reverse Martingale initialized: base_stake=%d",
                        self.p.base_stake)

    def next(self):
        """Execute Reverse Martingale staking logic."""
        if not self.position:
            if self.max_stake_reached:
                return  # Wait for reset

            stake = min(self.current_stake, self.p.max_stake)

            # Basic alternating signals for demo
            self.signal_counter += 1
            is_buy_signal = self.signal_counter % 2 == 1

            if is_buy_signal:
                self.buy(size=stake)
                self.logger.info("BUY @ stake=%d (wins=%d)", stake, self.consecutive_wins)
            else:
                self.sell(size=stake)
                self.logger.info("SELL @ stake=%d (wins=%d)", stake, self.consecutive_wins)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - increase stake for next trade
                self.consecutive_wins += 1
                new_stake = min(self.current_stake * self.p.multiplier, self.p.max_stake)
                self.current_stake = new_stake

                if self.current_stake >= self.p.max_stake:
                    self.max_stake_reached = True

                # Reset after consecutive wins limit
                if self.consecutive_wins >= self.p.max_wins:
                    self.current_stake = self.p.base_stake
                    self.consecutive_wins = 0
                    self.max_stake_reached = False

                self.close()
                self.logger.info("WIN: Stake increased to %d (wins=%d)",
                               self.current_stake, self.consecutive_wins)

            elif pnl < 0:
                # Loss - reset stake immediately
                if self.p.reset_on_loss:
                    self.current_stake = self.p.base_stake
                    self.consecutive_wins = 0
                    self.max_stake_reached = False
                    self.logger.info("LOSS: Reset stake to %d", self.p.base_stake)
                self.close()

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)

        if trade.isclosed:
            pnl = trade.pnlcomm if hasattr(trade, 'pnlcomm') else 0
            self.logger.info("Trade closed: P&L = %.2f", pnl)
