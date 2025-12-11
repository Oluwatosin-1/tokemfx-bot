"""
Trading Broker for TokemFX Trading Module
===========================================
Handles real-time trading execution and market data connectivity.

This module provides interfaces for:
- Live trading execution through Deriv API
- Account management and balance tracking
- Real-time market data streaming
- Order placement and trade management
"""

import os
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import websocket
import threading
import time
import requests
import logging

logger = logging.getLogger(__name__)

# ─── Network Resilience Integration ────────────────────────────────────────────

# Import network resilience manager
from src.network_resilience import network_resilience, OperationalMode

# ─── Abstract Broker Interface ─────────────────────────────────────────────

class TradingBroker(ABC):
    """Abstract base class for trading brokers."""

    @abstractmethod
    def connect_and_authenticate(self) -> bool:
        """Establish connection and authenticate with broker."""
        pass

    @abstractmethod
    def fetch_candles(self,
                     instrument: str,
                     granularity: str,
                     start: datetime = None,
                     end: datetime = None,
                     count: int = None) -> pd.DataFrame:
        """Return OHLCV DataFrame indexed by timestamp."""
        pass

    @abstractmethod
    def place_order(self, instrument: str, units: int, **kwargs) -> Dict[str, Any]:
        """Execute a market order."""
        pass

    @abstractmethod
    def get_account_balance(self) -> Dict[str, Any]:
        """Get current account balance."""
        pass

    @abstractmethod
    def get_account_status(self) -> Dict[str, Any]:
        """Get detailed account information."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if broker is connected and authenticated."""
        pass

    def cleanup(self):
        """Clean up resources."""
        pass


# ─── Deriv Implementation ─────────────────────────────────────────────────

class DerivBroker(TradingBroker):
    """
    Deriv CFD trading broker implementation.

    Supports both API token and OAuth authentication for demo and real accounts.
    Handles live trading execution and market data retrieval.
    """

    def __init__(self, config=None):
        """
        Initialize Deriv broker with configuration.

        Args:
            config: Broker configuration dictionary or APISettings object
        """
        # Import unified config
        if config is None:
            from src.config.settings import APISettings
            self.config = APISettings()
        elif hasattr(config, 'deriv_api_token'):  # APISettings object
            self.config = config
        else:  # Dictionary
            self.config = type('Config', (), config)()

        # Connection state
        self.ws = None
        self.is_authenticated = False
        self.auth_token_used = None
        self.account_type = self._detect_account_type()
        self.last_connection_attempt = None
        self.connection_lock = threading.Lock()

        logger.info(f"Deriv Broker initialized - Auth mode: {self.config.auth_mode}, Account type: {self.account_type}")

    def _detect_account_type(self) -> str:
        """Detect account type based on configuration and available tokens."""
        # If user explicitly set account type in env, use that
        account_type_env = os.getenv("DERIV_ACCOUNT_TYPE", "").upper()

        if account_type_env == "DEMO":
            return "DEMO"
        elif account_type_env == "REAL":
            if self.config.deriv_oauth_token:
                return "REAL_OAUTH"
            else:
                return "REAL_API"

        # Auto-detection based on available tokens
        if self.config.deriv_oauth_token and self.config.deriv_account_id:
            return "REAL_OAUTH"
        elif self.config.deriv_api_token and self.config.deriv_account_id:
            return "DETECTING_FROM_API"
        elif self.config.deriv_api_token:
            return "DEMO"
        else:
            return "UNKNOWN"

    def _update_account_type_from_api(self, account_info: Dict[str, Any]):
        """Update account type based on actual API response."""
        is_virtual = account_info.get("is_virtual", False)
        login_id = account_info.get("loginid", "unknown")

        if is_virtual:
            self.account_type = "DEMO"
        else:
            if self.auth_token_used == "oauth":
                self.account_type = "REAL_OAUTH"
            else:
                self.account_type = "REAL_API"

        logger.info(f"Updated account type: {self.account_type} (from API response, virtual: {is_virtual})")

    def connect_and_authenticate(self) -> bool:
        """
        Establish WebSocket connection and authenticate using appropriate method.

        Returns:
            bool: True if successful connection and authentication
        """
        with self.connection_lock:
            try:
                self.last_connection_attempt = datetime.now(timezone.utc)

                logger.info(f"Connecting to Deriv WebSocket: {self.config.get_websocket_url()}")
                self.ws = websocket.create_connection(
                    self.config.get_websocket_url(),
                    timeout=self.config.connection_timeout
                )

                # Choose authentication method
                if self.config.auth_mode == "oauth" and self.config.deriv_oauth_token:
                    logger.info("Authenticating with Deriv using OAuth token...")
                    return self._authenticate_oauth()
                elif self.config.auth_mode == "api" or (self.config.auth_mode == "auto" and self.config.deriv_api_token):
                    logger.info("Authenticating with Deriv using API token...")
                    return self._authenticate_api()
                else:
                    logger.warning("No suitable authentication token found")
                    return False

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                return False

    def _authenticate_api(self) -> bool:
        """Authenticate using API token."""
        if not self.config.deriv_api_token:
            logger.error("No API token available")
            return False

        try:
            auth_msg = {"authorize": self.config.deriv_api_token}
            self.ws.send(json.dumps(auth_msg))
            response = self.ws.recv()
            auth_data = json.loads(response)

            if auth_data.get("error"):
                logger.error(f"API token authentication failed: {auth_data['error']['message']}")
                return False
            else:
                self.is_authenticated = True
                self.auth_token_used = "api"

                # Get account information
                account_info = auth_data.get("authorize", {})
                self._update_account_type_from_api(account_info)

                balance = account_info.get("balance", 0)
                currency = account_info.get("currency", "USD")
                login_id = account_info.get("loginid", "unknown")

                logger.info("Deriv authentication successful")
                logger.info(f"Account: {'Demo' if self.account_type == 'DEMO' else 'Real'} ({login_id})")
                logger.info(f"Balance: {balance} {currency} (Auth method: API Token)")

                return True

        except Exception as e:
            logger.error(f"API token authentication error: {e}")
            return False

    def _authenticate_oauth(self) -> bool:
        """Authenticate using OAuth token."""
        if not self.config.deriv_oauth_token:
            logger.error("No OAuth token available")
            return False

        try:
            auth_msg = {"authorize": self.config.deriv_oauth_token}
            self.ws.send(json.dumps(auth_msg))
            response = self.ws.recv()
            auth_data = json.loads(response)

            if auth_data.get("error"):
                logger.error(f"OAuth authentication failed: {auth_data['error']['message']}")
                return False
            else:
                self.is_authenticated = True
                self.auth_token_used = "oauth"

                # Get account information
                account_info = auth_data.get("authorize", {})
                self._update_account_type_from_api(account_info)

                balance = account_info.get("balance", 0)
                currency = account_info.get("currency", "USD")
                login_id = account_info.get("loginid", "unknown")

                logger.info("Deriv OAuth authentication successful")
                logger.info(f"Account: {'Demo' if self.account_type == 'DEMO' else 'Real'} ({login_id})")
                logger.info(f"Balance: {balance} {currency} (Auth method: OAuth Token)")

                return True

        except Exception as e:
            logger.error(f"OAuth authentication error: {e}")
            return False

    def _send_request(self, request_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send synchronous WebSocket request and return response with resilience patterns.

        Args:
            request_msg: Request message dictionary

        Returns:
            Response dictionary or None if failed
        """
        def make_request() -> Dict[str, Any]:
            """Inner function for the actual network request."""
            if not self.is_connected():
                logger.warning("Not connected, attempting to reconnect...")
                if not self.connect_and_authenticate():
                    raise Exception("Failed to establish connection")

            try:
                # Add unique request ID
                req_id = abs(hash(str(uuid.uuid4()))) % 1000000
                request_msg["req_id"] = req_id

                logger.debug(f"Sending request: {request_msg.get('ticks_history', 'N/A')}")
                self.ws.send(json.dumps(request_msg))

                # Receive response with timeout (using safe config access)
                timeout = getattr(self.config, 'connection_timeout', 30) if hasattr(self.config, 'connection_timeout') else 30
                self.ws.settimeout(timeout)
                response = self.ws.recv()
                response_data = json.loads(response)

                logger.debug(f"Received response for req_id: {response_data.get('req_id')}")

                if response_data.get("error"):
                    error_code = response_data['error'].get('code', '')
                    error_message = response_data['error'].get('message', '')

                    # Handle permission/OAuth errors differently - these are not network issues
                    if 'permission denied' in error_message.lower() or 'oauth' in error_message.lower():
                        logger.warning(f"OAuth Permission Error: {error_message}")
                        # Return the error response but don't raise exception for circuit breaker
                        return response_data
                    else:
                        # For other API errors, treat as network issues for resilience
                        logger.warning(f"API Error: {response_data['error']}")
                        raise Exception(f"API Error: {response_data['error']}")

                return response_data

            except websocket.WebSocketTimeoutException:
                logger.error("Request timed out")
                raise Exception("Request timeout")
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise e

        # Execute with resilience patterns
        return network_resilience.execute_with_resilience(make_request)

    def fetch_candles(self, instrument: str, granularity: str,
                     start: datetime = None, end: datetime = None, count: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV candles from Deriv.

        Args:
            instrument: Trading instrument symbol
            granularity: Time granularity ('M1', 'H1', 'D', etc.)
            start: Start datetime (optional)
            end: End datetime (optional)
            count: Number of candles to fetch

        Returns:
            DataFrame with OHLCV columns indexed by timestamp
        """
        try:
            if granularity.upper() == "M1":
                # Use ticks_history for 1-minute data
                req = {
                    "ticks_history": instrument,
                    "count": count,
                    "end": "latest",
                    "style": "ticks"
                }

                resp = self._send_request(req)
                if resp and not resp.get("error"):
                    ticks = resp.get("history", {}).get("prices", [])
                    times = resp.get("history", {}).get("times", [])

                    if ticks and times:
                        data = []
                        for t, v in zip(times, ticks):
                            dt = datetime.fromtimestamp(t, tz=timezone.utc)
                            data.append({
                                "time": dt,
                                "open": v,
                                "high": v,
                                "low": v,
                                "close": v,
                                "volume": 1
                            })
                        df = pd.DataFrame(data).set_index("time")
                        logger.debug(f"Fetched {len(df)} ticks for {instrument}")
                        return df

            elif granularity.upper() in ["H1", "D", "W"]:
                # Use OHLC endpoint for higher timeframes
                req = {
                    "ohlc": {
                        "symbol": instrument,
                        "granularity": self._granularity_to_seconds(granularity),
                        "count": count
                    }
                }

                resp = self._send_request(req)
                if resp and not resp.get("error"):
                    candles = resp.get("ohlc", {}).get("candles", [])
                    if candles:
                        data = []
                        for candle in candles:
                            dt = datetime.fromtimestamp(candle[0], tz=timezone.utc)
                            data.append({
                                "time": dt,
                                "open": candle[1],
                                "high": candle[2],
                                "low": candle[3],
                                "close": candle[4],
                                "volume": candle[5] if len(candle) > 5 else 0
                            })

                        df = pd.DataFrame(data).set_index("time")
                        logger.debug(f"Fetched {len(df)} OHLC candles for {instrument}")
                        return df

            logger.warning(f"No data available for {instrument} {granularity}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching candles for {instrument}: {e}")
            return pd.DataFrame()

    def _granularity_to_seconds(self, granularity: str) -> int:
        """Convert granularity string to seconds for OHLC requests."""
        mapping = {
            "M1": 60,
            "M5": 300,
            "M15": 900,
            "M30": 1800,
            "H1": 3600,
            "H4": 14400,
            "D": 86400,
            "W": 604800
        }
        return mapping.get(granularity.upper(), 3600)

    def place_order(self, instrument: str, units: int, **kwargs) -> Dict[str, Any]:
        """
        Place CFD order via Deriv WebSocket.

        Args:
            instrument: Trading instrument
            units: Positive for buy, negative for sell
            **kwargs: Additional order parameters

        Returns:
            Order response dictionary
        """
        if not self.is_connected():
            return {"error": {"message": "Not connected or authenticated"}}

        try:
            contract_type = "CALL" if units > 0 else "PUT"
            stake = abs(units)

            req = {
                "buy": 1,
                "symbol": instrument,
                "contract_type": contract_type,
                "stake": stake,
                "currency": "USD",
                "basis": "stake",
                "duration": kwargs.get("duration", 5),  # 5 ticks default
                "duration_unit": kwargs.get("duration_unit", "m")  # minutes
            }

            # Add optional parameters
            if "stop_loss" in kwargs:
                req["stop_loss"] = kwargs["stop_loss"]
            if "take_profit" in kwargs:
                req["take_profit"] = kwargs["take_profit"]

            response = self._send_request(req)

            if response and not response.get("error"):
                logger.info(f"Order placed successfully for {instrument}: {stake} units")
            else:
                logger.warning(f"Order failed for {instrument}: {response.get('error', {}).get('message', 'Unknown error')}")

            return response or {"error": {"message": "No response from broker"}}

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": {"message": f"Order placement failed: {str(e)}"}}

    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get current account balance with automatic OAuth fallback.

        Returns:
            Balance response dictionary
        """
        logger.info("Checking account balance...")

        req = {"balance": 1, "account": "all"}
        response = self._send_request(req)

        if response and response.get("error"):
            error_msg = response["error"]["message"]
            logger.warning(f"Balance access failed: {error_msg}")

            # Check if this is an OAuth permission error
            if "permission denied" in error_msg.lower() and "oauth" in error_msg.lower():
                logger.info("Account requires OAuth token - attempting OAuth authentication...")

                # Close current connection and try OAuth
                self._close_connection()

                if self.config.deriv_oauth_token:
                    logger.info("Switching to OAuth mode...")
                    # Temporarily change auth mode for this attempt
                    old_auth_mode = self.config.auth_mode
                    self.config.auth_mode = "oauth"

                    if self.connect_and_authenticate():
                        logger.info("OAuth authentication successful, retrying balance request...")
                        response = self._send_request(req)

                        if response and not response.get("error"):
                            logger.info("Account balance retrieved successfully with OAuth")
                            self.account_type = "REAL_OAUTH"
                        else:
                            # Restore original auth mode and try account status
                            self.config.auth_mode = old_auth_mode
                            logger.error("Even OAuth balance access failed")
                            logger.info("Falling back to account status...")
                            return self.get_account_status()
                    else:
                        # Restore original auth mode
                        self.config.auth_mode = old_auth_mode
                        logger.error("OAuth authentication failed")
                        logger.info("Falling back to account status...")
                        return self.get_account_status()
                else:
                    logger.warning("No OAuth token available for balance access")
                    logger.info("Falling back to account status...")
                    return self.get_account_status()

            if "oauth" in error_msg.lower() or "permission" in error_msg.lower():
                logger.info("This account requires OAuth token for balance access")
                logger.info("Set DERIV_OAUTH_TOKEN in your .env file or use DERIV_AUTH_MODE=oauth")

        # Fallback to account status if balance still fails
        if not response or response.get("error"):
            logger.info("Falling back to account status...")
            return self.get_account_status()

        logger.info("Account balance retrieved successfully")
        return response

    def get_account_status(self) -> Dict[str, Any]:
        """Get detailed account information."""
        req = {"get_account_status": 1}
        response = self._send_request(req)

        if not response:
            logger.error("Failed to get account status")

        return response or {"error": {"message": "Could not retrieve account status"}}

    def get_statement(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get trading statement/transactions history.

        Args:
            limit: Maximum number of transactions to retrieve

        Returns:
            Statement response dictionary
        """
        req = {
            "statement": 1,
            "description": 1,
            "limit": limit,
            "offset": 0
        }
        response = self._send_request(req)

        if not response or response.get("error"):
            logger.warning("Failed to get trading statement")
            return response or {"error": {"message": "Could not retrieve statement"}}

        logger.debug(f"Retrieved {len(response.get('transactions', []))} transactions")
        return response

    def get_positions(self) -> Dict[str, Any]:
        """
        Get all open positions/contracts.

        Returns:
            Positions response dictionary
        """
        # If we have simulated positions stored, return those first (for demo trading)
        if hasattr(self, '_positions') and self._positions:
            simulated_contracts = self._positions.get('portfolio', {}).get('contracts', [])
            if simulated_contracts:
                logger.debug(f"Returning {len(simulated_contracts)} simulated positions")
                return self._positions

        # Otherwise, try to get real positions from API
        req = {"portfolio": 1}
        response = self._send_request(req)

        if not response or response.get("error"):
            # If API call fails and we have simulated positions, return those
            if hasattr(self, '_positions') and self._positions:
                logger.debug(f"API failed, returning {len(self._positions.get('portfolio', {}).get('contracts', []))} simulated positions")
                return self._positions

            logger.warning("Failed to get positions")
            return response or {"error": {"message": "Could not retrieve positions"}}

        logger.debug(f"Retrieved positions data from API")
        return response

    def close_position(self, contract_id: str) -> Dict[str, Any]:
        """
        Close a specific open position/contract.

        Args:
            contract_id: The contract ID to close

        Returns:
            Close position response dictionary
        """
        req = {
            "sell": 1,
            "contract_id": contract_id
        }
        response = self._send_request(req)

        if response and not response.get("error"):
            logger.info(f"Position {contract_id} closed successfully")
        else:
            logger.warning(f"Failed to close position {contract_id}")

        return response or {"error": {"message": "Could not close position"}}

    def close_all_positions(self) -> Dict[str, Any]:
        """
        Close all open positions/contracts.

        Returns:
            Response dictionary with results for each closed position
        """
        # First get all open positions
        positions_response = self.get_positions()

        if not positions_response or positions_response.get("error"):
            return {"error": {"message": "Could not retrieve positions to close"}}

        contracts = positions_response.get("portfolio", {}).get("contracts", [])
        results = []

        for contract in contracts:
            contract_id = contract.get("contract_id")
            if contract_id:
                close_result = self.close_position(contract_id)
                results.append({
                    "contract_id": contract_id,
                    "instrument": contract.get("display_name", "Unknown"),
                    "close_result": close_result
                })

        logger.info(f"Attempted to close {len(results)} positions")
        return {
            "total_positions": len(contracts),
            "close_attempts": len(results),
            "results": results
        }

    def get_available_instruments(self) -> Dict[str, Any]:
        """Get list of available trading instruments from Deriv."""
        req = {"contracts_for": "symbol"}
        response = self._send_request(req)

        if not response or response.get("error"):
            logger.warning("Failed to get available instruments")

        return response or {"error": {"message": "Could not retrieve instruments"}}

    def subscribe_market_data(self, symbol: str, subscribe: bool = True) -> Dict[str, Any]:
        """Subscribe to real-time market data."""
        req = {
            "ticks": symbol,
            "subscribe": 1 if subscribe else 0
        }
        response = self._send_request(req)

        if response and not response.get("error"):
            logger.info(f"{'Subscribed to' if subscribe else 'Unsubscribed from'} {symbol} market data")
        else:
            logger.warning(f"Failed to {'subscribe to' if subscribe else 'unsubscribe from'} {symbol}")

        return response or {"error": {"message": "Subscription failed"}}

    def is_connected(self) -> bool:
        """Check if broker is connected and authenticated."""
        return (self.ws is not None and
                self.is_authenticated and
                self.ws.connected)

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status and capabilities."""
        auth_config = self.config.get_deriv_auth_config()

        return {
            'is_connected': self.is_connected(),
            'is_authenticated': self.is_authenticated,
            'auth_method_used': self.auth_token_used,
            'account_type': self.account_type,
            'available_tokens': {
                'api_token': bool(auth_config['api_token']),
                'oauth_token': bool(auth_config['oauth_token'])
            },
            'auth_mode': self.config.auth_mode,
            'account_id': auth_config['account_id'],
            'last_connection_attempt': self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
        }

    def _close_connection(self):
        """Close WebSocket connection safely."""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            finally:
                self.ws = None
                self.is_authenticated = False
                self.auth_token_used = None

    def cleanup(self):
        """Clean up resources and close connections."""
        self._close_connection()
        logger.info("Deriv broker cleanup completed")
