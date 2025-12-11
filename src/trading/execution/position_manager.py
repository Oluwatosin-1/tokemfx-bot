"""
Position Management System
==========================
Advanced position tracking and risk management for trading positions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class Position:
    """
    Represents a single trading position with all relevant information.
    """

    def __init__(self,
                 position_id: str,
                 instrument: str,
                 direction: str,
                 size: float,
                 entry_price: float,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None,
                 timestamp: Optional[datetime] = None):

        self.position_id = position_id
        self.instrument = instrument
        self.direction = direction  # 'BUY' or 'SELL'
        self.size = size
        self.entry_price = entry_price
        self.current_price = entry_price  # Will be updated as position is monitored
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = timestamp or datetime.now()

        # Performance tracking
        self.pnl_percentage = 0.0
        self.pnl_absolute = 0.0
        self.unrealized_pnl = 0.0
        self.max_profit = 0.0
        self.max_loss = 0.0

        # Status and flags
        self.status = 'OPEN'  # OPEN, PARTIAL_CLOSE, CLOSED
        self.closing_trades = []  # List of closing trades and their P&L

        logger.info(f"📊 Position created: {position_id} - {direction} {size} {instrument} @ {entry_price}")

    def update_price(self, current_price: float) -> Dict[str, Any]:
        """
        Update position with latest price and calculate P&L.

        Args:
            current_price: Latest market price

        Returns:
            Dictionary with P&L update information
        """
        self.current_price = current_price

        # Calculate unrealized P&L
        if self.direction == 'BUY':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
            self.pnl_percentage = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SELL
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
            self.pnl_percentage = ((self.entry_price - current_price) / self.entry_price) * 100

        # Track max profit/loss
        self.max_profit = max(self.max_profit, self.pnl_percentage)
        self.max_loss = min(self.max_loss, self.pnl_percentage)

        # Check stop loss and take profit levels
        exit_signals = self._check_exit_conditions(current_price)

        return {
            'position_id': self.position_id,
            'current_price': current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'pnl_percentage': self.pnl_percentage,
            'exit_signals': exit_signals,
            'max_profit': self.max_profit,
            'max_loss': self.max_loss
        }

    def _check_exit_conditions(self, current_price: float) -> Dict[str, bool]:
        """
        Check if position should be closed based on stop loss/take profit.

        Args:
            current_price: Current market price

        Returns:
            Dictionary with exit signals
        """
        signals = {
            'stop_loss_hit': False,
            'take_profit_hit': False,
            'trailing_stop_hit': False
        }

        if self.direction == 'BUY':
            if self.stop_loss and current_price <= self.stop_loss:
                signals['stop_loss_hit'] = True
            if self.take_profit and current_price >= self.take_profit:
                signals['take_profit_hit'] = True
        else:  # SELL
            if self.stop_loss and current_price >= self.stop_loss:
                signals['stop_loss_hit'] = True
            if self.take_profit and current_price <= self.take_profit:
                signals['take_profit_hit'] = True

        return signals

    def close_position(self, close_price: float, partial_size: Optional[float] = None) -> Dict[str, Any]:
        """
        Close the position (fully or partially).

        Args:
            close_price: Price at which position is closed
            partial_size: Optional partial close size

        Returns:
            Closing trade information
        """
        close_size = partial_size if partial_size else self.size

        # Calculate P&L for this closing trade
        if self.direction == 'BUY':
            trade_pnl = (close_price - self.entry_price) * close_size
        else:
            trade_pnl = (self.entry_price - close_price) * close_size

        trade_info = {
            'position_id': self.position_id,
            'instrument': self.instrument,
            'direction': self.direction,
            'close_size': close_size,
            'entry_price': self.entry_price,
            'close_price': close_price,
            'pnl': trade_pnl,
            'close_time': datetime.now()
        }

        self.closing_trades.append(trade_info)

        # Update position status
        if partial_size:
            if partial_size >= self.size:
                self.status = 'CLOSED'
                self.size = 0
            else:
                self.status = 'PARTIAL_CLOSE'
                self.size -= partial_size
        else:
            self.status = 'CLOSED'
            self.size = 0

        # Calculate final P&L if fully closed
        if self.status == 'CLOSED':
            self.pnl_absolute = sum(trade['pnl'] for trade in self.closing_trades)
            self.pnl_percentage = (self.pnl_absolute / (self.entry_price * close_size)) * 100

        logger.info(f"📤 Position {self.position_id} closed: P&L ${trade_pnl:.2f}")

        return trade_info

    def get_position_info(self) -> Dict[str, Any]:
        """
        Get complete position information.

        Returns:
            Dictionary with all position details
        """
        return {
            'position_id': self.position_id,
            'instrument': self.instrument,
            'direction': self.direction,
            'size': self.size,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'status': self.status,
            'pnl_percentage': self.pnl_percentage,
            'pnl_absolute': self.pnl_absolute,
            'unrealized_pnl': self.unrealized_pnl,
            'max_profit': self.max_profit,
            'max_loss': self.max_loss,
            'timestamp': self.timestamp,
            'closing_trades': self.closing_trades
        }


class PositionManager:
    """
    Advanced position management system for tracking and controlling trading positions.
    """

    def __init__(self, max_positions: int = 10, max_total_risk: float = 0.05):
        self.positions = {}  # position_id -> Position
        self.max_positions = max_positions
        self.max_total_risk = max_total_risk

        # Risk tracking
        self.total_exposure = 0.0
        self.total_risk = 0.0
        self.total_unrealized_pnl = 0.0

        logger.info(f"PositionManager initialized - Max positions: {max_positions}, Max risk: {max_total_risk*100}%")

    def open_position(self,
                     instrument: str,
                     direction: str,
                     size: float,
                     entry_price: float,
                     stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Open a new trading position.

        Args:
            instrument: Trading instrument
            direction: 'BUY' or 'SELL'
            size: Position size
            entry_price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            Dictionary with position creation result
        """
        # Check position limits
        if len(self.positions) >= self.max_positions:
            return {
                'success': False,
                'error': f'Maximum positions limit reached ({self.max_positions})',
                'position_id': None
            }

        # Check risk limits
        risk_amount = abs(entry_price * size * (abs(stop_loss - entry_price) / entry_price)) if stop_loss else entry_price * size * 0.01
        if self.total_risk + risk_amount > self.max_total_risk:
            return {
                'success': False,
                'error': f'Risk limit exceeded. Current risk: {self.total_risk*100:.1f}%, Max: {self.max_total_risk*100:.1f}%',
                'position_id': None
            }

        # Create position
        position_id = str(uuid.uuid4())[:8]
        position = Position(position_id, instrument, direction, size, entry_price, stop_loss, take_profit)

        self.positions[position_id] = position
        self.total_exposure += entry_price * size
        self.total_risk += risk_amount if stop_loss else risk_amount

        logger.info(f"✅ Position opened: {position_id} - {direction} {size} {instrument}")

        return {
            'success': True,
            'position_id': position_id,
            'position': position.get_position_info()
        }

    def close_position(self, position_id: str, close_price: float, partial_size: Optional[float] = None) -> Dict[str, Any]:
        """
        Close an existing position.

        Args:
            position_id: Position identifier
            close_price: Closing price
            partial_size: Optional partial close size

        Returns:
            Dictionary with position closure result
        """
        if position_id not in self.positions:
            return {
                'success': False,
                'error': f'Position {position_id} not found',
                'pnl': 0.0
            }

        position = self.positions[position_id]
        closing_trade = position.close_position(close_price, partial_size)

        # Update totals if fully closed
        if position.status == 'CLOSED':
            del self.positions[position_id]
            self.total_exposure -= position.entry_price * position.size
            # Risk adjustment would be more complex in real implementation

        self.total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        logger.info(f"✅ Position closed: {position_id} - P&L ${closing_trade['pnl']:.2f}")

        return {
            'success': True,
            'position_id': position_id,
            'closing_trade': closing_trade,
            'remaining_size': position.size,
            'status': position.status
        }

    def update_positions(self, price_updates: Dict[str, float]) -> Dict[str, Any]:
        """
        Update all positions with latest prices.

        Args:
            price_updates: Dictionary of instrument -> price mappings

        Returns:
            Dictionary with position updates and exit signals
        """
        updates = {}
        exit_signals = []

        for position_id, position in self.positions.items():
            if position.instrument in price_updates:
                current_price = price_updates[position.instrument]
                update_info = position.update_price(current_price)
                updates[position_id] = update_info

                # Check for automatic exit signals
                if any(update_info['exit_signals'].values()):
                    exit_signals.append({
                        'position_id': position_id,
                        'exit_signals': update_info['exit_signals'],
                        'current_price': current_price,
                        'position_info': position.get_position_info()
                    })

        # Recalculate total P&L
        self.total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        return {
            'position_updates': updates,
            'exit_signals': exit_signals,
            'total_unrealized_pnl': self.total_unrealized_pnl,
            'active_positions': len(self.positions)
        }

    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get complete portfolio status information.

        Returns:
            Dictionary with portfolio overview
        """
        open_positions = [pos.get_position_info() for pos in self.positions.values()]
        closed_positions = []

        # Calculate portfolio metrics
        total_value = sum(pos['entry_price'] * pos['size'] for pos in open_positions)
        total_risk = sum(abs(pos['stop_loss'] - pos['entry_price']) / pos['entry_price'] * pos['entry_price'] * pos['size'] if pos['stop_loss'] else 0 for pos in open_positions)

        return {
            'total_positions': len(self.positions),
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'total_exposure': self.total_exposure,
            'total_risk': self.total_risk,
            'unrealized_pnl': self.total_unrealized_pnl,
            'max_positions': self.max_positions,
            'max_risk_limit': self.max_total_risk
        }

    def check_position_limits(self, new_position_size: float, new_risk: float) -> Dict[str, bool]:
        """
        Check if a new position would exceed limits.

        Args:
            new_position_size: Size of potential new position
            new_risk: Risk amount of potential new position

        Returns:
            Dictionary with limit check results
        """
        position_limit_ok = len(self.positions) < self.max_positions
        exposure_limit_ok = self.total_exposure + new_position_size <= self.max_total_risk * 10000  # Assuming $10k base
        risk_limit_ok = self.total_risk + new_risk <= self.max_total_risk

        return {
            'can_open_position': position_limit_ok and exposure_limit_ok and risk_limit_ok,
            'position_limit_ok': position_limit_ok,
            'exposure_limit_ok': exposure_limit_ok,
            'risk_limit_ok': risk_limit_ok,
            'current_positions': len(self.positions),
            'current_exposure': self.total_exposure,
            'current_risk': self.total_risk
        }

    def emergency_stop_all(self, close_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Emergency stop all positions at current market prices.

        Args:
            close_prices: Dictionary of instrument -> closing price mappings

        Returns:
            List of closure results
        """
        closure_results = []

        for position_id, position in list(self.positions.items()):
            if position.instrument in close_prices:
                close_price = close_prices[position.instrument]
                result = self.close_position(position_id, close_price)
                closure_results.append(result)
            else:
                logger.warning(f"No price available for emergency close of position {position_id}")

        logger.warning(f"🚨 EMERGENCY STOP: Closed {len(closure_results)} positions")

        return closure_results


# Convenience functions
def create_position_manager(max_positions: int = 10, max_risk: float = 0.05) -> PositionManager:
    """
    Create and return a position manager instance.

    Args:
        max_positions: Maximum number of concurrent positions
        max_risk: Maximum total portfolio risk (as fraction)

    Returns:
        Configured PositionManager instance
    """
    return PositionManager(max_positions, max_risk)


__all__ = [
    'Position',
    'PositionManager',
    'create_position_manager'
]
