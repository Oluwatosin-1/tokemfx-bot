"""
Base Strategy Class
===================
Event-driven trading strategy base class with risk management integration.

This provides the foundation for all trading strategies with:
- Event-driven execution
- Risk management integration
- Logging and monitoring
- Parameter validation
"""

import backtrader as bt
from datetime import datetime, timezone
# Import from new modular event system
try:
    from src.event import EventBus, EventType, TradingEvent, event_bus
except ImportError:
    # Fallback for backward compatibility
    try:
        from tokemfx.event import publish_order_signal
        event_bus = None
        EventType = None
        TradingEvent = None
    except ImportError:
        print("⚠️ WARNING: Event system not available - strategies will work but without event publishing")
        publish_order_signal = None
        event_bus = None
        EventType = None
        TradingEvent = None


class BaseStrategy(bt.Strategy):
    """
    Base event-driven trading strategy.
    Publishes signals via event bus instead of direct execution.
    Allows risk management interception and loose coupling.

    Parameters:
        instrument (str): Symbol name for event publishing
    """

    params = (
        ("instrument", ""),  # Symbol name for event publishing
    )

    def __init__(self):
        """Initialize base strategy with event system."""
        super().__init__()
        self.logger = self._setup_logging()

        # Validate instrument parameter
        if not self.p.instrument:
            self.logger.warning("No instrument specified for strategy")

    def _setup_logging(self):
        """Setup strategy-specific logging."""
        import logging
        return logging.getLogger(f"{self.__class__.__name__}[{self.p.instrument}]")

    def notify_order(self, order):
        """
        Called when an order status changes.
        Publishes events to the event bus for risk management.
        """
        try:
            if event_bus and EventType and TradingEvent:
                from datetime import datetime

                if order.status == order.Completed:
                    event = TradingEvent(
                        event_type=EventType.ORDER_EXECUTED,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "order_id": getattr(order, 'ref', ''),
                            "symbol": self.p.instrument,
                            "size": order.size,
                            "price": order.executed.price if hasattr(order, 'executed') else 0,
                            "type": "BUY" if order.size > 0 else "SELL",
                            "strategy": self.__class__.__name__
                        },
                        source=f"strategy_{self.__class__.__name__}"
                    )
                    event_bus.publish(event)
                    self.logger.info(f"Order executed: {order.size} @ {order.executed.price:.5f}")

                elif order.status == order.Cancelled:
                    event = TradingEvent(
                        event_type=EventType.ORDER_CANCELLED,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "symbol": self.p.instrument,
                            "reason": "cancelled",
                            "strategy": self.__class__.__name__
                        },
                        source=f"strategy_{self.__class__.__name__}"
                    )
                    event_bus.publish(event)
                    self.logger.warning("Order cancelled")

                elif order.status == order.Rejected:
                    self.logger.error(f"Order rejected: {order.getstatusname()}")

        except Exception as e:
            self.logger.error(f"Error in notify_order: {e}")

    def notify_trade(self, trade):
        """
        Called when a trade is closed.
        Publishes P&L events for monitoring.
        """
        try:
            if event_bus and EventType and TradingEvent:
                from datetime import datetime

                if trade.isclosed:
                    pnl = trade.pnlcomm if hasattr(trade, 'pnlcomm') else 0
                    event = TradingEvent(
                        event_type=EventType.TRADE_CLOSED,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "symbol": self.p.instrument,
                            "pnl": pnl,
                            "duration": getattr(trade, 'barlen', 0),
                            "strategy": self.__class__.__name__,
                            "return_pct": (pnl / abs(trade.price)) * 100 if trade.price != 0 else 0
                        },
                        source=f"strategy_{self.__class__.__name__}"
                    )
                    event_bus.publish(event)

                    # Log the trade result
                    if pnl > 0:
                        self.logger.info(f"Trade closed - Profit: ${pnl:.6f}")
                    else:
                        self.logger.warning(f"Trade closed - Loss: ${pnl:.6f}")

        except Exception as e:
            self.logger.error(f"Error in notify_trade: {e}")

    def next(self):
        """Override this method in subclasses for strategy logic."""
        raise NotImplementedError("Subclasses must implement next()")

    def log(self, txt, dt=None):
        """Logging method that works with backtrader datetime."""
        dt = dt or self.datas[0].datetime.datetime() if len(self.datas) > 0 else None
        dt_str = dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ""
        self.logger.info(f"{dt_str} {txt}")

    def get_position_value(self):
        """Get current position value."""
        return self.position.size * self.data.close[0] if self.position else 0

    def get_portfolio_value(self):
        """Get current portfolio value."""
        try:
            return self.broker.getvalue()
        except:
            return self.cash

    @property
    def cash(self):
        """Get available cash."""
        try:
            return self.broker.getcash()
        except:
            return 0

    @property
    def position_size(self):
        """Get current position size."""
        return self.position.size if self.position else 0

    @property
    def unrealized_pnl(self):
        """Get unrealized profit/loss."""
        return self.position.pnl if self.position else 0

    def can_buy(self, size):
        """Check if we can execute a buy order."""
        return self.cash >= (size * self.data.close[0])

    def can_sell(self, size):
        """Check if we can execute a sell order."""
        return abs(self.position_size) >= size if self.position_size < 0 else True
