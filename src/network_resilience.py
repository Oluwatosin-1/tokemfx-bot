"""
Network Resilience Layer for TokemFX
====================================

Enterprise-grade network handling with resilience patterns:
- Circuit breaker pattern
- Exponential backoff retry
- Multi-endpoint failover
- Connection pooling
- Health monitoring
- Graceful degradation
- Operational mode switching
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
import socket
import ssl
import logging
from dataclasses import dataclass
from collections import deque
import json

logger = logging.getLogger(__name__)

class OperationalMode(Enum):
    """System operational modes based on network connectivity."""
    CONNECTED = "connected"      # Full API functionality
    DEGRADED = "degraded"        # Limited functionality with fallbacks
    OFFLINE = "offline"          # Demo data only with warnings

class CircuitBreakerState(Enum):
    """Circuit breaker states for failover protection."""
    CLOSED = "closed"            # Normal operation
    OPEN = "open"               # Failing, reject calls
    HALF_OPEN = "half_open"     # Testing recovery

@dataclass
class ConnectionStats:
    """Real-time connection health statistics."""
    total_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    average_response_time: float = 0.0
    last_successful_connect: Optional[float] = None
    last_failure: Optional[float] = None
    consecutive_failures: int = 0
    circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    dns_resolution_failures: int = 0
    ssl_handshake_failures: int = 0
    timeout_failures: int = 0

@dataclass
class Endpoint:
    """WebSocket endpoint configuration."""
    url: str
    priority: int
    region: str
    healthy: bool = True
    last_health_check: Optional[float] = None
    consecutive_failures: int = 0
    average_response_time: float = 0.0

class NetworkResilienceManager:
    """
    Enterprise network resilience manager with multiple failover strategies.

    Features:
    - Circuit breaker pattern for cascading failure prevention
    - Multi-endpoint failover with health monitoring
    - Exponential backoff with jitter
    - Connection pooling and reuse
    - Operational mode switching (connected/degraded/offline)
    - Real-time health monitoring and alerting
    """

    def __init__(self):
        # Core endpoints configuration
        self.endpoints = self._initialize_endpoints()
        self.connection_pool: Dict[str, List[Any]] = {}
        self.max_connections_per_endpoint = 5
        self.connection_timeout = 10
        self.enable_connection_reuse = True

        # Circuit breaker configuration
        self.failure_threshold = 5
        self.recovery_timeout = 60
        self.expected_exception = Exception

        # Retry configuration
        self.max_retries = 5
        self.base_retry_delay = 1.0
        self.max_retry_delay = 30.0
        self.retry_jitter = 0.1

        # Health monitoring
        self.health_check_interval = 30
        self.slow_response_threshold = 2.0
        self.error_rate_threshold = 0.05  # 5%

        # Operational mode management
        self.current_mode = OperationalMode.CONNECTED
        self.mode_switch_callbacks: List[Callable] = []
        self.degraded_mode_timeout = 300  # 5 minutes

        # Connection statistics
        self.stats = ConnectionStats()
        self.endpoint_stats: Dict[str, ConnectionStats] = {}

        # Monitoring and alerting
        self.alert_thresholds = {
            'error_rate': 0.05,
            'slow_responses': 0.20,
            'consecutive_failures': 3
        }

        # Initialize monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        self.start_health_monitoring()

        logger.info("🛡️ Network Resilience Manager initialized")

    def _initialize_endpoints(self) -> List[Endpoint]:
        """Initialize WebSocket endpoints with failover hierarchy."""
        return [
            # Primary endpoints
            Endpoint(
                url="wss://ws.derivws.com/websockets/v3?app_id=96454",
                priority=1,
                region="global"
            ),
            # Regional backup endpoints
            Endpoint(
                url="wss://ws.derivws.com/websockets/v3?app_id=1089",  # Backup app ID
                priority=2,
                region="global"
            ),
            # Future: Add more regional endpoints as needed
            # Endpoint(url="wss://ws-eu.derivws.com/websockets/v3?app_id=96454", priority=2, region="eu"),
            # Endpoint(url="wss://ws-asia.derivws.com/websockets/v3?app_id=96454", priority=2, region="asia"),
        ]

    def get_healthy_endpoint(self) -> Optional[Endpoint]:
        """
        Get the healthiest available endpoint using failover logic.

        Returns the highest priority healthy endpoint, or None if all are unhealthy.
        """
        healthy_endpoints = [ep for ep in self.endpoints if self._is_endpoint_healthy(ep)]

        if not healthy_endpoints:
            logger.error("❌ All endpoints are unhealthy - falling back to offline mode")
            self._switch_operational_mode(OperationalMode.OFFLINE)
            return None

        # Return highest priority healthy endpoint
        return min(healthy_endpoints, key=lambda ep: ep.priority)

    def _is_endpoint_healthy(self, endpoint: Endpoint) -> bool:
        """Check if an endpoint is considered healthy."""
        if not endpoint.healthy:
            return False

        # Check last health check
        if endpoint.last_health_check:
            time_since_check = time.time() - endpoint.last_health_check
            if time_since_check > self.health_check_interval * 2:
                # Stale health check - mark as potentially unhealthy
                return False

        # Check consecutive failures
        if endpoint.consecutive_failures >= self.failure_threshold:
            return False

        # Check circuit breaker for this endpoint
        endpoint_stats = self.endpoint_stats.get(endpoint.url, ConnectionStats())
        if endpoint_stats.circuit_breaker_state == CircuitBreakerState.OPEN:
            return False

        return True

    def execute_with_resilience(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation with full resilience patterns.

        Args:
            operation: The function to execute
            *args, **kwargs: Arguments for the operation

        Returns:
            Result of the operation or fallback data
        """
        start_time = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                # Check circuit breaker
                if self._circuit_breaker_open():
                    logger.warning("🔌 Circuit breaker OPEN - failing fast")
                    return self._get_fallback_data(operation.__name__)

                # Execute operation
                result = operation(*args, **kwargs)

                # Success - update stats and close circuit breaker
                self._record_success(time.time() - start_time)
                return result

            except self.expected_exception as e:
                execution_time = time.time() - start_time
                error_type = self._classify_error(e)

                logger.warning(f"⚠️ Operation attempt {attempt + 1} failed: {error_type} - {str(e)[:100]}")

                # Record failure
                self._record_failure(error_type, execution_time)

                # Check if we should continue retrying
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"⏳ Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Operation failed after {self.max_retries + 1} attempts")
                    return self._get_fallback_data(operation.__name__)

            except Exception as e:
                # Unexpected error - record but don't retry
                logger.error(f"💥 Unexpected error in resilient execution: {e}")
                self._record_failure("unexpected", time.time() - start_time)
                return self._get_fallback_data(operation.__name__)

    def _circuit_breaker_open(self) -> bool:
        """Check if circuit breaker should block requests."""
        consecutive_failures = self.stats.consecutive_failures

        if consecutive_failures >= self.failure_threshold:
            if self.stats.circuit_breaker_state != CircuitBreakerState.OPEN:
                self.stats.circuit_breaker_state = CircuitBreakerState.OPEN
                logger.warning("🔌 CIRCUIT BREAKER: OPEN (too many failures)")

                # Schedule circuit breaker reset
                def reset_circuit_breaker():
                    time.sleep(self.recovery_timeout)
                    self.stats.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                    logger.info("🔌 CIRCUIT BREAKER: HALF_OPEN (testing recovery)")

                reset_thread = threading.Thread(target=reset_circuit_breaker, daemon=True)
                reset_thread.start()

            return self.stats.circuit_breaker_state == CircuitBreakerState.OPEN

        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(self.base_retry_delay * (2 ** attempt), self.max_retry_delay)

        # Add jitter to prevent thundering herd
        jitter = delay * self.retry_jitter * (0.5 - time.time() % 1)  # Random jitter
        delay += jitter

        return max(0.1, delay)  # Minimum 100ms

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for better handling."""
        error_str = str(error).lower()

        if "nodename nor servname" in error_str or "name resolution" in error_str:
            self.stats.dns_resolution_failures += 1
            return "dns_failure"

        elif "ssl" in error_str or "tls" in error_str or "certificate" in error_str:
            self.stats.ssl_handshake_failures += 1
            return "ssl_failure"

        elif "timeout" in error_str or "timed out" in error_str:
            self.stats.timeout_failures += 1
            return "timeout"

        elif "connection" in error_str and "lost" in error_str:
            return "connection_lost"

        else:
            return "general_failure"

    def _record_success(self, response_time: float):
        """Record successful operation."""
        self.stats.total_attempts += 1
        self.stats.successful_connections += 1
        self.stats.consecutive_failures = 0
        self.stats.last_successful_connect = time.time()

        # Update moving average response time
        if self.stats.average_response_time == 0:
            self.stats.average_response_time = response_time
        else:
            self.stats.average_response_time = (
                self.stats.average_response_time * 0.9 + response_time * 0.1
            )

        # Update circuit breaker
        if self.stats.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
            self.stats.circuit_breaker_state = CircuitBreakerState.CLOSED
            logger.info("🔌 CIRCUIT BREAKER: CLOSED (connection restored)")

        # Check if we should switch back to connected mode
        if self.current_mode != OperationalMode.CONNECTED:
            current_error_rate = 1 - (self.stats.successful_connections / self.stats.total_attempts)
            if current_error_rate < self.error_rate_threshold:
                self._switch_operational_mode(OperationalMode.CONNECTED)

    def _record_failure(self, error_type: str, response_time: float):
        """Record failed operation."""
        self.stats.total_attempts += 1
        self.stats.failed_connections += 1

        # OAuth permission errors should NOT count towards circuit breaker failures
        # They are API permission issues, not network connectivity issues
        if error_type != 'oauth_permission_denied':
            self.stats.consecutive_failures += 1

        self.stats.last_failure = time.time()

    def _get_fallback_data(self, operation_name: str) -> Any:
        """
        Get fallback data when operations fail.

        Returns appropriate fallback data based on the operation type.
        """
        # Switch to degraded mode if not already
        if self.current_mode == OperationalMode.CONNECTED:
            self._switch_operational_mode(OperationalMode.DEGRADED)

        # Return fallback data based on operation
        if "balance" in operation_name.lower():
            return {"balance": 10000.0, "currency": "USD", "status": "demo", "timestamp": time.time()}

        elif "candles" in operation_name.lower() or "ohlc" in operation_name.lower():
            return {"candles": self._generate_demo_candles(), "status": "demo_data", "warning": "Using fallback data due to connectivity issues"}

        elif "account" in operation_name.lower():
            return {"account_id": "DEMO123", "type": "demo", "status": "connected_demo"}

        else:
            return {"status": "demo_data", "warning": "Using fallback data due to connectivity issues"}

    def _generate_demo_candles(self) -> List[Dict]:
        """Generate demo candle data for backtesting fallback."""
        candles = []
        base_price = 100.0
        current_time = datetime.now()

        for i in range(100):  # Generate 100 demo candles
            timestamp = current_time - timedelta(minutes=i*5)
            volatility = 0.02  # 2% volatility

            open_price = base_price + (i % 20 - 10) * volatility * base_price
            close_price = open_price * (1 + (0.5 - (time.time() % 1)) * volatility)
            high_price = max(open_price, close_price) * (1 + abs(time.time() % 0.01))
            low_price = min(open_price, close_price) * (1 - abs(time.time() % 0.01))

            candles.append({
                "timestamp": timestamp.timestamp(),
                "open": round(open_price, 4),
                "high": round(high_price, 4),
                "low": round(low_price, 4),
                "close": round(close_price, 4),
                "volume": 1000 + (i * 10),
                "status": "demo_data"
            })

            base_price = close_price

        return candles

    def _switch_operational_mode(self, new_mode: OperationalMode):
        """Switch system operational mode."""
        if new_mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = new_mode

            logger.info(f"🔄 OPERATIONAL MODE SWITCH: {old_mode.value} → {new_mode.value}")

            # Notify callbacks
            for callback in self.mode_switch_callbacks:
                try:
                    callback(old_mode, new_mode)
                except Exception as e:
                    logger.error(f"Error in mode switch callback: {e}")

    def add_mode_switch_callback(self, callback: Callable):
        """Add callback for operational mode switches."""
        self.mode_switch_callbacks.append(callback)

    def start_health_monitoring(self):
        """Start background health monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("🔍 Health monitoring started")

    def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while self.monitoring_active:
            try:
                self._perform_health_checks()

                # Check for alerts
                self._check_alert_conditions()

                time.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.health_check_interval)

    def _perform_health_checks(self):
        """Perform comprehensive health checks on all endpoints."""
        for endpoint in self.endpoints:
            try:
                # Simple connectivity test (in production, this would be more sophisticated)
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                # Parse URL for connection test
                url_parts = endpoint.url.replace('wss://', '').replace('ws://', '').split('/')[0]
                host = url_parts.split(':')[0]
                port = 443  # Assume WSS

                result = sock.connect_ex((host, port))
                sock.close()

                response_time = time.time() - start_time

                if result == 0:
                    # Success
                    endpoint.healthy = True
                    endpoint.consecutive_failures = 0
                    endpoint.last_health_check = time.time()
                    endpoint.average_response_time = (
                        endpoint.average_response_time * 0.9 + response_time * 0.1
                    )
                else:
                    # Failure
                    endpoint.consecutive_failures += 1
                    if endpoint.consecutive_failures >= 3:
                        endpoint.healthy = False
                        logger.warning(f"⚠️ Endpoint {endpoint.url} marked unhealthy")

            except Exception as e:
                endpoint.consecutive_failures += 1
                logger.debug(f"Health check failed for {endpoint.url}: {e}")

    def _check_alert_conditions(self):
        """Check if any alert conditions are met."""
        # Error rate alert
        if self.stats.total_attempts > 10:
            error_rate = self.stats.failed_connections / self.stats.total_attempts
            if error_rate > self.alert_thresholds['error_rate']:
                logger.warning(f"⚠️ High error rate detected: {error_rate:.1%} (threshold: {self.alert_thresholds['error_rate']:.1%})")
                self._switch_operational_mode(OperationalMode.DEGRADED)

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for monitoring."""
        return {
            "operational_mode": self.current_mode.value,
            "circuit_breaker": self.stats.circuit_breaker_state.value,
            "connection_stats": {
                "total_attempts": self.stats.total_attempts,
                "success_rate": (self.stats.successful_connections / max(self.stats.total_attempts, 1)) * 100,
                "average_response_time": self.stats.average_response_time,
                "consecutive_failures": self.stats.consecutive_failures
            },
            "endpoint_status": [
                {
                    "url": ep.url,
                    "healthy": ep.healthy,
                    "priority": ep.priority,
                    "response_time": ep.average_response_time,
                    "failures": ep.consecutive_failures
                }
                for ep in self.endpoints
            ],
            "error_breakdown": {
                "dns_failures": self.stats.dns_resolution_failures,
                "ssl_failures": self.stats.ssl_handshake_failures,
                "timeouts": self.stats.timeout_failures
            },
            "timestamp": time.time()
        }

    def reset_stats(self):
        """Reset connection statistics (useful for testing)."""
        self.stats = ConnectionStats()
        self.endpoint_stats = {}
        logger.info("📊 Network statistics reset")

# Global network resilience instance
network_resilience = NetworkResilienceManager()
