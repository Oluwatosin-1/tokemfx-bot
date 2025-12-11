"""
Event Bus System
================
Modular event-driven architecture for TokemFX trading system.

Provides:
- EventType enumeration for different event categories
- TradingEvent dataclass for structured event data
- EventBus for publishing and subscribing to events
- Global event_bus instance for system-wide communication
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import threading
import queue


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all possible event types in the trading system."""

    # Order Events
    ORDER_CREATED = "order_created"
    ORDER_EXECUTED = "order_executed"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"

    # Trade Events
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    TRADE_MODIFIED = "trade_modified"

    # Market Events
    MARKET_DATA_UPDATE = "market_data_update"
    PRICE_ALERT = "price_alert"

    # Risk Management Events
    RISK_LIMIT_BREACHED = "risk_limit_breached"
    POSITION_SIZE_WARNING = "position_size_warning"
    DRAWDOWN_WARNING = "drawdown_warning"

    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"

    # Strategy Events
    STRATEGY_SIGNAL = "strategy_signal"
    STRATEGY_EXECUTION = "strategy_execution"


@dataclass
class TradingEvent:
    """
    Structured event data for the trading system.

    Attributes:
        event_type: Type of event from EventType enum
        timestamp: When the event occurred (UTC)
        data: Dictionary containing event-specific data
        source: String identifier of the event source
        priority: Event priority (higher = more important)
    """
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    priority: int = 1

    def __post_init__(self):
        """Ensure timestamp is timezone-aware."""
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


class EventBus:
    """
    Central event bus for publishing and subscribing to events.

    Features:
    - Thread-safe event publishing and subscription
    - Priority-based event handling
    - Asynchronous event processing
    - Event filtering and routing
    """

    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue = queue.Queue(maxsize=max_queue_size)
        self._lock = threading.RLock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the event processing thread."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
        logger.info("EventBus started")

    def stop(self):
        """Stop the event processing thread."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        logger.info("EventBus stopped")

    def subscribe(self, event_type: EventType, callback: Callable[[TradingEvent], None]):
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable[[TradingEvent], None]):
        """
        Unsubscribe from events of a specific type.

        Args:
            event_type: Type of event to stop listening for
            callback: Function to remove from subscribers
        """
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    logger.debug(f"Unsubscribed from {event_type.value}")
                except ValueError:
                    logger.warning(f"Callback not found for {event_type.value}")

    def publish(self, event: TradingEvent):
        """
        Publish an event to all subscribers.

        Args:
            event: TradingEvent to publish
        """
        try:
            self._event_queue.put(event, timeout=1.0)
            logger.debug(f"Published event: {event.event_type.value} from {event.source}")
        except queue.Full:
            logger.warning("Event queue full, dropping event")

    def _process_events(self):
        """Process events from the queue (runs in background thread)."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._dispatch_event(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def _dispatch_event(self, event: TradingEvent):
        """Dispatch event to all subscribers."""
        with self._lock:
            subscribers = self._subscribers.get(event.event_type, [])

            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get number of subscribers for an event type."""
        with self._lock:
            return len(self._subscribers.get(event_type, []))

    def get_queue_size(self) -> int:
        """Get current size of event queue."""
        return self._event_queue.qsize()


# Global event bus instance - lazy initialization
_event_bus_instance = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance with lazy initialization."""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
        # Don't auto-start to prevent import blocking
        # event_bus.start() will be called when needed
    return _event_bus_instance

# For backward compatibility, create a property-like access
class _LazyEventBus:
    def __getattr__(self, name):
        return getattr(get_event_bus(), name)

    def __setattr__(self, name, value):
        setattr(get_event_bus(), name, value)

# Global event bus instance with lazy loading
event_bus = _LazyEventBus()


# Backward compatibility functions for old monolithic code
def publish_order_signal(order_data: Dict[str, Any]):
    """
    Backward compatibility function for old monolithic code.

    Args:
        order_data: Order signal data
    """
    event = TradingEvent(
        event_type=EventType.STRATEGY_SIGNAL,
        timestamp=datetime.now(timezone.utc),
        data=order_data,
        source="legacy_strategy"
    )
    event_bus.publish(event)


# Cleanup on module unload
import atexit
atexit.register(lambda: event_bus.stop())
