#!/usr/bin/env python3
"""
🚨 Emergency Controls & Circuit Breaker System

Implements comprehensive emergency stop mechanisms and circuit breaker patterns
for trading system risk management.

Features:
- Emergency stop buttons
- Circuit breaker on losses/timeouts
- Risk limit enforcement
- Automatic position liquidation
- System health monitoring
- Manual override capabilities
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmergencyLevel(Enum):
    """Emergency stop levels in increasing severity."""
    WARNING = 1
    PAUSE = 2
    STOP = 3
    EMERGENCY_STOP = 4
    SYSTEM_SHUTDOWN = 5

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit broken, no trading
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class RiskLimits:
    """Risk management limits."""
    max_daily_loss: float = 1000.0  # Max loss per day ($)
    max_position_size: float = 10000.0  # Max position size ($)
    max_positions: int = 5  # Max concurrent positions
    max_drawdown_pct: float = 10.0  # Max drawdown percentage
    circuit_breaker_timeout: int = 300  # Seconds to wait after circuit break

@dataclass
class EmergencyEvent:
    """Emergency event record."""
    timestamp: datetime
    level: EmergencyLevel
    reason: str
    triggered_by: str
    details: Dict
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class EmergencyControlSystem:
    """Main emergency control and circuit breaker system."""

    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        self.risk_limits = risk_limits or RiskLimits()

        # System state
        self.emergency_level = EmergencyLevel.WARNING
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.is_trading_enabled = True
        self.system_healthy = True

        # Tracking
        self.emergency_events: List[EmergencyEvent] = []
        self.daily_pnl = 0.0
        self.daily_start_time = datetime.now()
        self.positions: Dict[str, Dict] = {}
        self.consecutive_failures = 0

        # Locks for thread safety
        self.lock = threading.Lock()

        # Callbacks
        self.emergency_callbacks: List[Callable] = []
        self.circuit_breaker_callbacks: List[Callable] = []
        self.health_check_callbacks: List[Callable] = []

        # Circuit breaker timing
        self.circuit_open_time: Optional[datetime] = None
        self.next_retry_time: Optional[datetime] = None

        logger.info("🚨 Emergency Control System initialized")
        logger.info(f"   Risk limits: {asdict(self.risk_limits)}")

    def add_emergency_callback(self, callback: Callable):
        """Add callback for emergency events."""
        self.emergency_callbacks.append(callback)

    def add_circuit_breaker_callback(self, callback: Callable):
        """Add callback for circuit breaker events."""
        self.circuit_breaker_callbacks.append(callback)

    def add_health_check_callback(self, callback: Callable):
        """Add callback for health check events."""
        self.health_check_callbacks.append(callback)

    def trigger_emergency(self, level: EmergencyLevel, reason: str, triggered_by: str = "system",
                         details: Optional[Dict] = None):
        """
        Trigger emergency event.

        Args:
            level: Emergency level to set
            reason: Reason for emergency
            triggered_by: Who/what triggered it
            details: Additional details
        """
        with self.lock:
            old_level = self.emergency_level
            self.emergency_level = level
            details = details or {}

            # Update system state based on emergency level
            if level.value >= EmergencyLevel.STOP.value:
                self.is_trading_enabled = False
            if level == EmergencyLevel.EMERGENCY_STOP:
                self._emergency_liquidate_all_positions()
            if level == EmergencyLevel.SYSTEM_SHUTDOWN:
                self._initiate_system_shutdown()

            # Record event
            event = EmergencyEvent(
                timestamp=datetime.now(),
                level=level,
                reason=reason,
                triggered_by=triggered_by,
                details=details
            )
            self.emergency_events.append(event)

            logger.warning(f"🚨 EMERGENCY: {level.name.upper()} - {reason}")

            # Notify callbacks
            for callback in self.emergency_callbacks:
                try:
                    callback(event, old_level)
                except Exception as e:
                    logger.error(f"Emergency callback error: {e}")

    def resolve_emergency(self, resolved_by: str = "system"):
        """Resolve current emergency state."""
        with self.lock:
            if self.emergency_level.value > EmergencyLevel.WARNING.value:
                old_level = self.emergency_level
                self.emergency_level = EmergencyLevel.WARNING
                self.is_trading_enabled = True

                # Update last event
                if self.emergency_events:
                    self.emergency_events[-1].resolved = True
                    self.emergency_events[-1].resolution_time = datetime.now()

                logger.info(f"✅ Emergency resolved: {old_level.value} -> {self.emergency_level.value}")

                # Notify callbacks
                for callback in self.emergency_callbacks:
                    try:
                        callback(None, old_level, resolved=True)  # Signal resolution
                    except Exception as e:
                        logger.error(f"Emergency resolution callback error: {e}")

    def trigger_circuit_breaker(self, reason: str, timeout_seconds: Optional[int] = None):
        """
        Trigger circuit breaker to prevent trading.

        Args:
            reason: Reason for circuit break
            timeout_seconds: Auto-retry timeout (uses default if None)
        """
        with self.lock:
            timeout = timeout_seconds or self.risk_limits.circuit_breaker_timeout

            self.circuit_breaker_state = CircuitBreakerState.OPEN
            self.is_trading_enabled = False
            self.circuit_open_time = datetime.now()
            self.next_retry_time = datetime.now() + timedelta(seconds=timeout)

            logger.warning(f"🔌 CIRCUIT BREAKER: OPENED - {reason}")
            logger.info(f"   Next retry: {self.next_retry_time}")

            # Notify callbacks
            for callback in self.circuit_breaker_callbacks:
                try:
                    callback("open", reason)
                except Exception as e:
                    logger.error(f"Circuit breaker callback error: {e}")

    def test_circuit_breaker(self):
        """Test if circuit breaker should transition to half-open."""
        with self.lock:
            if self.circuit_breaker_state == CircuitBreakerState.OPEN:
                if self.next_retry_time and datetime.now() >= self.next_retry_time:
                    self.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                    self.is_trading_enabled = True  # Allow limited trading

                    logger.info("🔌 CIRCUIT BREAKER: HALF-OPEN - Testing recovery")

                    # Notify callbacks
                    for callback in self.circuit_breaker_callbacks:
                        try:
                            callback("half_open", "testing_recovery")
                        except Exception as e:
                            logger.error(f"Circuit breaker test callback error: {e}")

    def close_circuit_breaker(self):
        """Close circuit breaker and resume normal operation."""
        with self.lock:
            self.circuit_breaker_state = CircuitBreakerState.CLOSED
            self.is_trading_enabled = True
            self.circuit_open_time = None
            self.next_retry_time = None

            logger.info("🔌 CIRCUIT BREAKER: CLOSED - Normal operation restored")

            # Notify callbacks
            for callback in self.circuit_breaker_callbacks:
                try:
                    callback("closed", "normal_operation")
                except Exception as e:
                    logger.error(f"Circuit breaker close callback error: {e}")

    def update_daily_pnl(self, pnl_change: float):
        """Update daily PnL and check risk limits."""
        with self.lock:
            self.daily_pnl += pnl_change

            # Check daily loss limit
            if -self.daily_pnl >= self.risk_limits.max_daily_loss:
                self.trigger_emergency(
                    EmergencyLevel.EMERGENCY_STOP,
                    f"Daily loss limit exceeded: ${-self.daily_pnl:.2f}/{self.risk_limits.max_daily_loss:.2f}",
                    "risk_manager",
                    {"daily_loss": -self.daily_pnl, "limit": self.risk_limits.max_daily_loss}
                )

    def add_position(self, position_id: str, position_data: Dict):
        """Add or update position."""
        with self.lock:
            self.positions[position_id] = position_data

            # Check position limits
            if len(self.positions) > self.risk_limits.max_positions:
                self.trigger_emergency(
                    EmergencyLevel.STOP,
                    f"Too many positions: {len(self.positions)}/{self.risk_limits.max_positions}",
                    "position_manager"
                )

            # Check individual position size
            position_value = position_data.get('value', 0)
            if position_value > self.risk_limits.max_position_size:
                logger.warning(f"⚠️ Position size warning: ${position_value:.2f}")

    def record_trade_failure(self):
        """Record a trade failure."""
        with self.lock:
            self.consecutive_failures += 1

            if self.consecutive_failures >= 5:  # Circuit breaker after 5 failures
                self.trigger_circuit_breaker("5 consecutive trade failures")

    def record_trade_success(self):
        """Record a trade success."""
        with self.lock:
            self.consecutive_failures = 0

    def health_check(self) -> bool:
        """Perform system health check."""
        with self.lock:
            issues = []

            # Check emergency level
            if self.emergency_level.value >= EmergencyLevel.STOP.value:
                issues.append(f"Emergency level: {self.emergency_level.value}")

            # Check circuit breaker
            if self.circuit_breaker_state == CircuitBreakerState.OPEN:
                issues.append("Circuit breaker open")

            # Check trading enabled
            if not self.is_trading_enabled:
                issues.append("Trading disabled")

            # Check daily loss
            if -self.daily_pnl >= (self.risk_limits.max_daily_loss * 0.8):
                issues.append("Approaching daily loss limit")

            # Check position count
            if len(self.positions) >= (self.risk_limits.max_positions * 0.9):
                issues.append("Approaching position limit")

            is_healthy = len(issues) == 0

            if is_healthy != self.system_healthy:
                self.system_healthy = is_healthy

                # Notify health check callbacks
                for callback in self.health_check_callbacks:
                    try:
                        callback(is_healthy, issues)
                    except Exception as e:
                        logger.error(f"Health check callback error: {e}")

                level = "HEALTHY" if is_healthy else "ISSUES DETECTED"
                logger.info(f"🏥 System Health: {level}")

            if issues:
                logger.warning(f"🏥 Health Issues: {', '.join(issues)}")

            return is_healthy

    def get_status(self) -> Dict:
        """Get current system status."""
        with self.lock:
            return {
                'emergency_level': self.emergency_level.value,
                'circuit_breaker': self.circuit_breaker_state.value,
                'trading_enabled': self.is_trading_enabled,
                'system_healthy': self.system_healthy,
                'daily_pnl': self.daily_pnl,
                'position_count': len(self.positions),
                'consecutive_failures': self.consecutive_failures,
                'active_positions': list(self.positions.keys()),
                'recent_events': [asdict(event) for event in self.emergency_events[-3:]],  # Last 3 events
                'circuit_next_retry': self.next_retry_time.isoformat() if self.next_retry_time else None
            }

    def reset_daily_metrics(self):
        """Reset daily metrics at start of new trading day."""
        with self.lock:
            self.daily_pnl = 0.0
            self.daily_start_time = datetime.now()
            logger.info("📅 Daily metrics reset")

    def manual_emergency_stop(self, reason: str):
        """Manual emergency stop trigger."""
        self.trigger_emergency(
            EmergencyLevel.EMERGENCY_STOP,
            f"Manual emergency stop: {reason}",
            "manual_trigger"
        )

    def manual_pause(self, reason: str):
        """Manual pause trading."""
        self.trigger_emergency(
            EmergencyLevel.PAUSE,
            f"Manual pause: {reason}",
            "manual_trigger"
        )

    def _emergency_liquidate_all_positions(self):
        """Emergency liquidation of all positions."""
        logger.warning("🚨 EMERGENCY LIQUIDATION: Liquidating all positions!")

        # Implement position liquidation logic here
        # This would integrate with your broker to close all positions

        for position_id in list(self.positions.keys()):
            logger.warning(f"   Liquidating position: {position_id}")
            # broker.close_position(position_id)
            del self.positions[position_id]

    def _initiate_system_shutdown(self):
        """System shutdown sequence."""
        logger.critical("🚨 SYSTEM SHUTDOWN: Initiating complete shutdown!")

        # Implement shutdown sequence:
        # - Stop all trading
        # - Close connections
        # - Save state
        # - Exit gracefully

        logger.critical("   All systems shutting down...")
        # os._exit(1)  # Force shutdown

# Global emergency control instance
emergency_system = EmergencyControlSystem()

# Convenience functions for dashboard integration
def emergency_stop(reason: str = "Manual emergency stop"):
    """Emergency stop all trading."""
    emergency_system.manual_emergency_stop(reason)

def pause_trading(reason: str = "Manual pause"):
    """Pause all trading."""
    emergency_system.manual_pause(reason)

def resume_trading():
    """Resume trading if safe."""
    emergency_system.resolve_emergency("manual_resume")

def get_system_status():
    """Get current system status."""
    return emergency_system.get_status()

def is_trading_allowed():
    """Check if trading is currently allowed."""
    return emergency_system.is_trading_enabled

def trigger_circuit_breaker(reason: str):
    """Trigger circuit breaker."""
    emergency_system.trigger_circuit_breaker(reason)

def reset_circuit_breaker():
    """Reset circuit breaker."""
    emergency_system.close_circuit_breaker()

# Health monitoring thread
def health_monitor_thread():
    """Background health monitoring."""
    while True:
        try:
            emergency_system.health_check()
            emergency_system.test_circuit_breaker()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            time.sleep(60)  # Retry after 1 minute

# Start health monitoring
health_thread = threading.Thread(target=health_monitor_thread, daemon=True)
health_thread.start()

if __name__ == "__main__":
    # Example usage and testing
    print("🚨 Emergency Control System Test")

    # Test emergency triggers
    emergency_stop("Test emergency stop")
    status = get_system_status()
    print(f"Status after emergency: {status['emergency_level']}")

    # Test pause
    pause_trading("Test pause")
    print(f"Trading allowed: {is_trading_allowed()}")

    # Test circuit breaker
    trigger_circuit_breaker("Test circuit breaker")
    print(f"Circuit breaker: {get_system_status()['circuit_breaker']}")

    # Test health check
    print(f"System healthy: {emergency_system.health_check()}")

    print("✅ Emergency Control System operational!")
