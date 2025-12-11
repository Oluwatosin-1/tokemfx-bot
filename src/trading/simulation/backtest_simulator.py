"""
Backtest Simulator Class
=========================

Provides backtesting simulation capabilities for trading strategies.
Integrates with the backtesting module for comprehensive strategy evaluation.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class BacktestSimulator:
    """
    Comprehensive backtest simulation engine for trading strategies.

    Provides integration with backtesting module for full strategy evaluation
    including performance metrics, risk analysis, and trade simulation.
    """

    def __init__(self, initial_balance: float = 10000.0,
                 commission_per_trade: float = 0.001,
                 slippage: float = 0.0005):
        """
        Initialize backtest simulator

        Args:
            initial_balance: Starting portfolio balance
            commission_per_trade: Commission as fraction per trade
            slippage: Slippage as fraction of price
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission_per_trade = commission_per_trade
        self.slippage = slippage

        # Trading history and positions
        self.positions = {}
        self.trade_history = []
        self.portfolio_history = []

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

        logger.info(f"✅ BacktestSimulator initialized with ${initial_balance:,}")

    def execute_backtest(self, strategy_function: Callable,
                        market_data: pd.DataFrame,
                        strategy_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a backtest using a strategy function

        Args:
            strategy_function: Function that generates trading signals
            market_data: OHLCV dataframe with market data
            strategy_params: Parameters to pass to strategy function

        Returns:
            Complete backtest results and performance metrics
        """
        if strategy_params is None:
            strategy_params = {}

        logger.info("🏁 Starting backtest execution")

        try:
            # Reset simulator state
            self._reset()

            # Generate signals using the strategy
            signals = self._generate_signals(strategy_function, market_data, strategy_params)

            # Execute trades based on signals
            results = self._execute_trades(signals, market_data)

            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(market_data)

            # Compile final results
            backtest_results = {
                'initial_balance': self.initial_balance,
                'final_balance': self.balance,
                'total_return': (self.balance - self.initial_balance) / self.initial_balance,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.winning_trades / max(1, self.total_trades),
                'trade_history': self.trade_history,
                'portfolio_history': self.portfolio_history,
                'signals': signals,
                'performance_metrics': metrics,
                'strategy_params': strategy_params,
                'execution_time': pd.Timestamp.now()
            }

            logger.info("✅ Backtest completed successfully")
            logger.info(f"📊 Final balance: ${self.balance:,.2f} (Return: {backtest_results['total_return']:.2%})")

            return backtest_results

        except Exception as e:
            logger.error(f"❌ Backtest execution failed: {e}")
            return {'error': str(e), 'status': 'FAILED'}

    def _generate_signals(self, strategy_function: Callable,
                         market_data: pd.DataFrame,
                         params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate trading signals using strategy function

        Args:
            strategy_function: Strategy signal generation function
            market_data: Market data DataFrame
            params: Strategy parameters

        Returns:
            List of trading signals with timestamps and actions
        """
        signals = []
        try:
            # Call strategy function to get signals
            signals = strategy_function(market_data, **params)

            # Validate signal format
            valid_signals = []
            for signal in signals:
                if self._validate_signal(signal):
                    valid_signals.append(signal)
                else:
                    logger.warning(f"Invalid signal format: {signal}")

            logger.info(f"📈 Generated {len(valid_signals)} valid trading signals")
            return valid_signals

        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return []

    def _execute_trades(self, signals: List[Dict[str, Any]],
                       market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute trades based on generated signals

        Args:
            signals: List of trading signals
            market_data: Market data for price reference

        Returns:
            Trade execution results
        """
        execution_results = {
            'executed_trades': 0,
            'failed_trades': 0,
            'total_volume': 0.0
        }

        try:
            for signal in signals:
                success = self._execute_single_trade(signal, market_data)
                if success:
                    execution_results['executed_trades'] += 1
                    execution_results['total_volume'] += signal.get('volume', 0)
                else:
                    execution_results['failed_trades'] += 1

            logger.info(f"💼 Executed {execution_results['executed_trades']} trades")

        except Exception as e:
            logger.error(f"Trade execution error: {e}")

        return execution_results

    def _execute_single_trade(self, signal: Dict[str, Any], market_data: pd.DataFrame) -> bool:
        """
        Execute a single trade based on signal

        Args:
            signal: Trade signal dictionary
            market_data: Market data for pricing

        Returns:
            True if trade executed successfully
        """
        try:
            action = signal.get('action', '').upper()
            symbol = signal.get('symbol', 'DEFAULT')
            volume = signal.get('volume', 1.0)

            if action not in ['BUY', 'SELL', 'CLOSE']:
                logger.warning(f"Unknown action: {action}")
                return False

            # Get current price (simplified - use close price)
            current_price = signal.get('price', 100.0)  # Default fallback

            # Apply slippage and commission
            execution_price = self._apply_slippage_and_commission(current_price, action)

            # Record the trade
            trade_record = {
                'timestamp': signal.get('timestamp'),
                'action': action,
                'symbol': symbol,
                'volume': volume,
                'price': current_price,
                'execution_price': execution_price,
                'commission': abs(execution_price * volume * self.commission_per_trade),
                'slippage_amount': abs(execution_price - current_price)
            }

            # Update positions and balance
            if action == 'BUY':
                self.balance -= (execution_price * volume + trade_record['commission'])
                self.positions[symbol] = self.positions.get(symbol, 0) + volume
            elif action == 'SELL':
                self.balance += (execution_price * volume - trade_record['commission'])
                self.positions[symbol] = self.positions.get(symbol, 0) - volume
            elif action == 'CLOSE':
                position_size = self.positions.get(symbol, 0)
                if position_size > 0:
                    # Close long position
                    self.balance += (execution_price * abs(position_size) - trade_record['commission'])
                else:
                    # Close short position
                    self.balance -= (execution_price * abs(position_size) + trade_record['commission'])
                self.positions[symbol] = 0

            self.trade_history.append(trade_record)
            self.portfolio_history.append({
                'timestamp': signal.get('timestamp'),
                'balance': self.balance,
                'positions': self.positions.copy()
            })

            self.total_trades += 1
            return True

        except Exception as e:
            logger.error(f"Single trade execution failed: {e}")
            return False

    def _apply_slippage_and_commission(self, price: float, action: str) -> float:
        """
        Apply slippage and commission to trade price

        Args:
            price: Base trade price
            action: 'BUY' or 'SELL'

        Returns:
            Adjusted execution price
        """
        # Apply slippage
        slippage_adjustment = price * self.slippage
        if action.upper() == 'BUY':
            execution_price = price + slippage_adjustment
        else:
            execution_price = price - slippage_adjustment

        return execution_price

    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate that a signal has required fields"""
        required_fields = ['action', 'timestamp']

        for field in required_fields:
            if field not in signal:
                return False

        return signal['action'].upper() in ['BUY', 'SELL', 'CLOSE']

    def _calculate_performance_metrics(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if not self.trade_history:
            return {'status': 'NO_TRADES'}

        try:
            # Get buy and hold return for comparison
            buy_hold_return = self._calculate_buy_hold_return(market_data)

            # Calculate returns
            total_return = (self.balance - self.initial_balance) / self.initial_balance

            # Calculate Sharpe ratio (simplified)
            if len(self.portfolio_history) > 1:
                returns = [h['balance'] for h in self.portfolio_history]
                returns_pct = pd.Series(returns).pct_change().dropna()

                if len(returns_pct) > 0:
                    sharpe_ratio = returns_pct.mean() / returns_pct.std() if returns_pct.std() > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0

            # Calculate drawdown
            peak_balance = self.initial_balance
            max_drawdown = 0
            current_drawdown = 0

            for record in self.portfolio_history:
                balance = record['balance']
                if balance > peak_balance:
                    peak_balance = balance
                    current_drawdown = 0
                else:
                    current_drawdown = (peak_balance - balance) / peak_balance
                    max_drawdown = max(max_drawdown, current_drawdown)

            metrics = {
                'total_return': total_return,
                'annualized_return': self._annualize_return(total_return, len(self.portfolio_history)),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': self.winning_trades / max(1, self.total_trades),
                'total_trades': self.total_trades,
                'buy_hold_comparison': total_return - buy_hold_return,
                'profit_factor': self._calculate_profit_factor(),
                'average_win': self._calculate_average_win(),
                'average_loss': self._calculate_average_loss()
            }

            return metrics

        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            return {'error': str(e), 'status': 'CALCULATION_ERROR'}

    def _calculate_buy_hold_return(self, market_data: pd.DataFrame) -> float:
        """Calculate buy-and-hold return for comparison"""
        try:
            if market_data.empty or 'close' not in market_data.columns:
                return 0.0

            initial_price = market_data['close'].iloc[0]
            final_price = market_data['close'].iloc[-1]
            return (final_price - initial_price) / initial_price
        except:
            return 0.0

    def _annualize_return(self, total_return: float, periods: int) -> float:
        """Annualize return based on number of periods"""
        if periods <= 0:
            return 0.0

        # Assuming daily data, 252 trading days per year
        years = periods / 252
        if years <= 0:
            return 0.0

        return (1 + total_return) ** (1 / years) - 1

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        gross_profit = sum(t['price'] * t['volume'] for t in self.trade_history if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t['price'] * t['volume'] for t in self.trade_history if t.get('pnl', 0) < 0))

        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    def _calculate_average_win(self) -> float:
        """Calculate average winning trade"""
        winning_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
        if not winning_trades:
            return 0.0

        return sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)

    def _calculate_average_loss(self) -> float:
        """Calculate average losing trade"""
        losing_trades = [t for t in self.trade_history if t.get('pnl', 0) < 0]
        if not losing_trades:
            return 0.0

        return sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)

    def _reset(self):
        """Reset simulator state for new backtest"""
        self.balance = self.initial_balance
        self.positions = {}
        self.trade_history = []
        self.portfolio_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Get current portfolio snapshot"""
        total_value = self.balance
        for symbol, quantity in self.positions.items():
            # Simplified - would need current prices for real valuation
            total_value += quantity * 100  # placeholder

        return {
            'current_balance': self.balance,
            'positions': self.positions,
            'total_portfolio_value': total_value,
            'unrealized_pnl': 0.0,  # Would need current prices
            'total_trades': self.total_trades
        }
