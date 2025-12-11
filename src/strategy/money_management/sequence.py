"""
Sequence-Based Money Management Strategies
===========================================
Fibonacci sequence and structured staking patterns.

This module contains:
- OneThreeTwoSixStrategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class OneThreeTwoSixStrategy(BaseStrategy):
    """
    1-3-2-6 Money Management Strategy.

    Fixed staking sequence based on Fibonacci: 1 unit → 3 units → 2 units → 6 units.
    Systematic money management pattern that follows specific rules.

    Parameters:
        base_unit (int): Base unit size (1 unit) (default: 1000)
        sequence (list): The 1-3-2-6 staking sequence (default: [1, 3, 2, 6])
        reset_on_loss (bool): Reset sequence on any loss (default: True)
        session_reset (bool): Reset after completing sequence (default: True)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_unit", 1000),
        ("sequence", [1, 3, 2, 6]),
        ("reset_on_loss", True),
        ("session_reset", True),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize 1-3-2-6 strategy."""
        super().__init__()

        self.sequence_index = 0
        self.session_completed = False

        self.logger.info("1-3-2-6 Strategy initialized: base_unit=%d, sequence=%s",
                        self.p.base_unit, str(self.p.sequence))

    def get_next_stake(self):
        """Get stake size for current sequence position."""
        if self.session_completed or self.sequence_index >= len(self.p.sequence):
            if self.p.session_reset:
                self.sequence_index = 0
                self.session_completed = False
            else:
                return self.p.base_unit  # Default to 1 unit

        multiplier = self.p.sequence[self.sequence_index]
        return self.p.base_unit * multiplier

    def next(self):
        """Execute 1-3-2-6 staking logic."""
        if not self.position:
            stake = self.get_next_stake()

            # Simple alternating trades for demo
            if len(self) % 2 == 0:
                self.buy(size=stake)
                self.logger.debug("BUY @ stake=%d (sequence pos=%d)",
                                stake, self.sequence_index + 1)
            else:
                self.sell(size=stake)
                self.logger.debug("SELL @ stake=%d (sequence pos=%d)",
                                stake, self.sequence_index + 1)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - advance in sequence
                self.sequence_index += 1

                # Check if sequence completed
                if self.sequence_index >= len(self.p.sequence):
                    self.session_completed = True
                    self.logger.info("SEQUENCE COMPLETED: All positions won")

                self.close()

            elif pnl < 0:
                # Loss - reset sequence if enabled
                if self.p.reset_on_loss:
                    self.sequence_index = 0
                    self.session_completed = False
                    self.logger.warning("LOSS: Reset sequence to beginning")
                self.close()

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
            self.logger.info("Trade closed: P&L = %.2f, Sequence pos = %d",
                           pnl, self.sequence_index + 1)
