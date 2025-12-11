"""
Progressive Money Management Strategies
=======================================
D'Alembert, Reverse D'Alembert, and Oscar's Grind.

This module contains:
- DAlembertStrategy
- ReverseDAlembertStrategy
- OscarsGrindStrategy
"""

import backtrader as bt
from ..base.base_strategy import BaseStrategy


class DAlembertStrategy(BaseStrategy):
    """
    D'Alembert Money Management Strategy.

    Increases stake by 1 unit after loss, decreases by 1 unit after win.
    More conservative than Martingale.

    Parameters:
        base_stake (int): Initial stake size (default: 1000)
        step_size (int): Unit size to increase/decrease (default: 100)
        max_stake (int): Maximum stake limit (default: 5000)
        min_stake (int): Minimum stake limit (default: 500)
        session_target (int): Target profit to reset session (default: 2000)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_stake", 1000),
        ("step_size", 100),
        ("max_stake", 5000),
        ("min_stake", 500),
        ("session_target", 2000),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize D'Alembert strategy."""
        super().__init__()

        self.current_stake = self.p.base_stake
        self.session_profit = 0
        self.trade_count = 0

        self.logger.info("D'Alembert initialized: base_stake=%d, step=%d",
                        self.p.base_stake, self.p.step_size)

    def next(self):
        """Execute D'Alembert staking logic."""
        if not self.position:
            stake = max(min(self.current_stake, self.p.max_stake), self.p.min_stake)

            # Basic alternating signals for demo
            if self.trade_count % 2 == 0:
                self.buy(size=stake)
                self.logger.debug("BUY @ stake=%d", stake)
            else:
                self.sell(size=stake)
                self.logger.debug("SELL @ stake=%d", stake)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - decrease stake
                self.current_stake = max(self.current_stake - self.p.step_size, self.p.min_stake)
                self.session_profit += pnl
                self.close()

                # Reset if session target reached
                if self.p.session_target > 0 and self.session_profit >= self.p.session_target:
                    self.current_stake = self.p.base_stake
                    self.session_profit = 0
                    self.logger.info("SESSION TARGET reached - reset to base stake")

            elif pnl < 0:
                # Loss - increase stake
                self.current_stake = min(self.current_stake + self.p.step_size, self.p.max_stake)
                self.close()
                self.logger.warning("LOSS: Stake increased to %d", self.current_stake)

            self.trade_count += 1

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)


class OscarsGrindStrategy(BaseStrategy):
    """
    Oscar's Grind Strategy.

    Aims to make exactly 1 unit of profit per session through progressive staking.
    Increases stake only on wins to reach target faster.

    Parameters:
        base_stake (int): Initial stake size (default: 1000)
        target_profit (int): Session profit target (default: 1000)
        max_stake (int): Maximum stake per trade (default: 5000)
        reset_on_target (bool): Reset progression on target reached (default: True)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_stake", 1000),
        ("target_profit", 1000),
        ("max_stake", 5000),
        ("reset_on_target", True),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize Oscar's Grind strategy."""
        super().__init__()

        self.current_stake = self.p.base_stake
        self.session_profit = 0
        self.stage = 1  # Current progression stage

        self.logger.info("Oscar's Grind initialized: base_stake=%d, target=%d",
                        self.p.base_stake, self.p.target_profit)

    def next(self):
        """Execute Oscar's Grind logic."""
        if not self.position:
            if self.session_profit >= self.p.target_profit:
                return  # Session target reached

            stake = min(self.current_stake, self.p.max_stake)

            # Alternating trades for demo
            if len(self) % 2 == 0:
                self.buy(size=stake)
                self.logger.debug("BUY @ stake=%d (stage=%d)", stake, self.stage)
            else:
                self.sell(size=stake)
                self.logger.debug("SELL @ stake=%d (stage=%d)", stake, self.stage)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - increase stake and advance stage
                self.current_stake = min(self.current_stake + self.p.base_stake, self.p.max_stake)
                self.session_profit += pnl
                self.stage += 1
                self.close()

                # Check if target reached
                if self.session_profit >= self.p.target_profit:
                    self.logger.info("TARGET REACHED: Session P&L = %.2f", self.session_profit)
                    if self.p.reset_on_target:
                        self.current_stake = self.p.base_stake
                        self.session_profit = 0
                        self.stage = 1
                        self.logger.info("Reset for new session")

            elif pnl < 0:
                # Loss - keep same stake
                self.close()
                self.logger.warning("LOSS: Keep stake at %d", self.current_stake)

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)


class ReverseDAlembertStrategy(BaseStrategy):
    """
    Reverse D'Alembert Strategy.

    Opposite of D'Alembert - increases stake after wins, decreases after losses.
    More aggressive approach.

    Parameters:
        base_stake (int): Initial stake size (default: 1000)
        step_size (int): Unit change size (default: 100)
        max_stake (int): Maximum stake limit (default: 5000)
        min_stake (int): Minimum stake limit (default: 200)
        win_limit (int): Reset after consecutive wins (default: 5)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("base_stake", 1000),
        ("step_size", 100),
        ("max_stake", 5000),
        ("min_stake", 200),
        ("win_limit", 5),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize Reverse D'Alembert strategy."""
        super().__init__()

        self.current_stake = self.p.base_stake
        self.consecutive_wins = 0

        self.logger.info("Reverse D'Alembert initialized: base_stake=%d",
                        self.p.base_stake)

    def next(self):
        """Execute Reverse D'Alembert staking logic."""
        if not self.position:
            stake = max(min(self.current_stake, self.p.max_stake), self.p.min_stake)

            # Alternating trades for demo
            if len(self) % 2 == 0:
                self.buy(size=stake)
                self.logger.debug("BUY @ stake=%d (wins=%d)", stake, self.consecutive_wins)
            else:
                self.sell(size=stake)
                self.logger.debug("SELL @ stake=%d (wins=%d)", stake, self.consecutive_wins)

        elif self.position:
            pnl = self.position.pnlcomm if hasattr(self.position, 'pnlcomm') else 0

            if pnl > 0:
                # Win - increase stake
                self.current_stake = min(self.current_stake + self.p.step_size, self.p.max_stake)
                self.consecutive_wins += 1

                # Reset after consecutive wins limit
                if self.consecutive_wins >= self.p.win_limit:
                    self.current_stake = self.p.base_stake
                    self.consecutive_wins = 0

                self.close()
                self.logger.info("WIN: Stake to %d (wins=%d)", self.current_stake, self.consecutive_wins)

            elif pnl < 0:
                # Loss - decrease stake
                self.current_stake = max(self.current_stake - self.p.step_size, self.p.min_stake)
                self.consecutive_wins = 0
                self.close()
                self.logger.warning("LOSS: Stake decreased to %d", self.current_stake)

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)
