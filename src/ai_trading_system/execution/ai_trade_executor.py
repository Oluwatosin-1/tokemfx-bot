"""
AI Trade Executor
=================
Intelligent execution of trade signals based on AI analysis and market conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import time

from src.ai_trading_system.analytics.performance_analyzer import performance_analyzer
from src.ai_trading_system.decision_engine.strategy_selector import ai_strategy_selector
from src.strategy import strategy_factory, strategy_registry

# Configure logging
logger = logging.getLogger('ai_executor')

class AITradeExecutor:
    """
    AI-powered trade execution system.
    Analyzes market conditions, selects optimal strategy, and executes trades.
    """

    def __init__(self,
                 account_balance: float = 10000.0,
                 risk_per_trade: float = 0.02,
                 enable_live_trading: bool = False):

        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.enable_live_trading = enable_live_trading

        # Execution state
        self.active_trades = {}
        self.execution_history = []
        self.daily_pnl = 0.0
        self.daily_trade_count = 0

        # Risk limits
        self.max_daily_trades = 10
        self.max_daily_loss_pct = 0.05  # 5% max daily loss
        self.min_confidence_threshold = 0.6

        # Market condition tracking
        self.last_market_analysis = None
        self.market_analysis_timestamp = None
        self.market_cache_duration = timedelta(minutes=15)

        logger.info("🎯 AI Trade Executor initialized")
        logger.info(f"💰 Account Balance: ${account_balance:,.0f}")
        logger.info(f"🎲 Risk per Trade: {risk_per_trade*100:.1f}%")

    def analyze_and_execute_trade(self,
                                 current_data: pd.DataFrame,
                                 instrument: str = "R_10",
                                 risk_preference: str = 'balanced') -> Dict[str, Any]:
        """
        Complete AI trade decision pipeline: analyze → select → execute.

        Args:
            current_data: Live market data
            instrument: Trading instrument
            risk_preference: Risk preference level

        Returns:
            Trade execution result
        """
        print(f"🤖 AI Trade Execution for {instrument}...")

        execution_result = {
            'timestamp': datetime.now(),
            'instrument': instrument,
            'decision': 'NO_TRADE',
            'reason': '',
            'confidence': 0.0,
            'risk_assessment': {},
            'trade_signal': None,
            'execution_status': 'PENDING'
        }

        # Step 1: Risk limit checks
        if not self._check_risk_limits():
            execution_result['reason'] = 'Risk limits exceeded'
            execution_result['execution_status'] = 'CANCELLED'
            print("❌ Trade cancelled: Risk limits exceeded")
            return execution_result

        # Step 2: AI Strategy Selection
        try:
            strategy_selection = ai_strategy_selector.select_optimal_strategy(
                current_data,
                risk_preference=risk_preference
            )

            if not strategy_selection.get('selected_strategy'):
                execution_result['reason'] = 'No suitable strategy found'
                execution_result['execution_status'] = 'CANCELLED'
                print("❌ Trade cancelled: No suitable strategy")
                return execution_result

            selected_strategy = strategy_selection['selected_strategy']
            confidence = strategy_selection['confidence']

            execution_result['confidence'] = confidence
            execution_result['strategy_selection'] = strategy_selection

            # Step 3: Confidence threshold check
            if confidence < self.min_confidence_threshold:
                execution_result['reason'] = f'Low confidence: {confidence:.2f} < {self.min_confidence_threshold:.2f}'
                execution_result['execution_status'] = 'CANCELLED'
                print(f"❌ Trade cancelled: Low confidence {confidence:.2f}")
                return execution_result

            # Step 4: Calculate position sizing
            position_size_pct = ai_strategy_selector.calculate_position_size(
                strategy_selection,
                self.account_balance
            )

            position_value = self.account_balance * position_size_pct

            # Step 5: Generate trade signal using selected strategy
            trade_signal = self._generate_strategy_signal(
                selected_strategy,
                current_data,
                confidence,
                position_value
            )

            if not trade_signal:
                execution_result['reason'] = 'Strategy generated no signal'
                execution_result['execution_status'] = 'CANCELLED'
                print("❌ Trade cancelled: Strategy generated no signal")
                return execution_result

            execution_result['trade_signal'] = trade_signal
            execution_result['decision'] = 'TRADE_SIGNAL_GENERATED'

            # Step 6: Execute trade (if live trading enabled)
            if self.enable_live_trading:
                execution_status = self._execute_live_trade(trade_signal, instrument)
                execution_result['execution_status'] = execution_status

                if execution_status == 'EXECUTED':
                    execution_result['decision'] = 'TRADE_EXECUTED'
                    self._update_portfolio_state(trade_signal)
                else:
                    execution_result['reason'] = f'Execution failed: {execution_status}'
            else:
                execution_result['execution_status'] = 'SIMULATED'
                execution_result['decision'] = 'SIMULATION_MODE'

            # Step 7: Update AI monitoring
            self._update_ai_monitoring(strategy_selection, trade_signal)

            # Step 8: Log execution
            self._log_trade_execution(execution_result)

            print("✅ SUCCESS: AI trade decision completed")
            print(f"🎯 Strategy: {selected_strategy}")
            print(f"🎯 Confidence: {confidence:.1f}")
            if execution_result['execution_status'] == 'EXECUTED':
                print("💰 LIVE TRADE EXECUTED")
            else:
                print(f"📊 {execution_result['execution_status']}")

        except Exception as e:
            execution_result['execution_status'] = 'ERROR'
            execution_result['reason'] = f'AI execution error: {str(e)}'
            logger.error(f"AI execution error: {e}")
            print(f"❌ AI execution error: {e}")

        return execution_result

    def _check_risk_limits(self) -> bool:
        """
        Check if current trading activity is within risk limits.

        Returns:
            True if trading is allowed, False otherwise
        """
        # Daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return False

        # Daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / self.account_balance if self.account_balance > 0 else 1.0
        if daily_loss_pct >= self.max_daily_loss_pct:
            return False

        # Active trade concentration (max 3 concurrent trades)
        if len(self.active_trades) >= 3:
            return False

        return True

    def _generate_strategy_signal(self,
                                strategy_name: str,
                                market_data: pd.DataFrame,
                                confidence: float,
                                position_value: float) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal using selected strategy.

        Args:
            strategy_name: Name of selected strategy
            market_data: Current market data
            confidence: AI confidence in the trade
            position_value: Dollar value for position

        Returns:
            Trade signal dictionary or None
        """
        try:
            if len(market_data) < 50:
                return None

            current_price = market_data['close'].iloc[-1] if 'close' in market_data.columns else 0

            # Get strategy class and create instance
            strategy_class = strategy_registry.get_strategy(strategy_name)
            if not strategy_class:
                return None

            # Create strategy instance with confidence as instrument param
            strategy_instance = strategy_class(instrument=strategy_name[-8:])  # Use last 8 chars as instrument

            # Generate signal (simplified - would need Backtrader integration for full signals)
            signal_generated = self._simulate_strategy_signal(strategy_instance, market_data, strategy_name)

            if signal_generated:
                # Calculate stop loss and take profit based on strategy type
                stop_loss, take_profit = self._calculate_bracket_levels(
                    strategy_name, current_price, confidence
                )

                trade_signal = {
                    'strategy_name': strategy_name,
                    'direction': signal_generated.get('direction', 'BUY'),
                    'entry_price': current_price,
                    'position_size': position_value,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'instrument': strategy_name[-8:],  # Simplified
                    'signal_strength': signal_generated.get('strength', 0.5),
                    'market_conditions': {
                        'price': current_price,
                        'timestamp': datetime.now(),
                        'confidence': confidence
                    }
                }

                return trade_signal

        except Exception as e:
            logger.error(f"Error generating strategy signal for {strategy_name}: {e}")

        return None

    def _simulate_strategy_signal(self, strategy_instance, market_data: pd.DataFrame, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        Simulate strategy signal generation (simplified version).

        In production, this would use Backtrader to run the strategy.
        """
        try:
            # Get recent data
            recent_data = market_data.tail(20).copy() if len(market_data) > 20 else market_data

            # Strategy-specific signal generation
            signal_strength = 0.0

            if 'MovingAverage' in strategy_name:
                # MA crossover signal
                if len(recent_data) >= 50:
                    fast_ma = recent_data['close'].rolling(10).mean().iloc[-1]
                    slow_ma = recent_data['close'].rolling(30).mean().iloc[-1]
                    current_price = recent_data['close'].iloc[-1]

                    if current_price > fast_ma > slow_ma:
                        return {'direction': 'BUY', 'strength': 0.7, 'reason': 'MA crossover up'}
                    elif current_price < fast_ma < slow_ma:
                        return {'direction': 'SELL', 'strength': 0.7, 'reason': 'MA crossover down'}

            elif 'RSI' in strategy_name:
                # RSI signal
                if len(recent_data) >= 14:
                    # Simplified RSI calculation
                    rsi = self._calculate_simple_rsi(recent_data['close'])
                    if rsi < 30:
                        return {'direction': 'BUY', 'strength': 0.6, 'reason': 'RSI oversold'}
                    elif rsi > 70:
                        return {'direction': 'SELL', 'strength': 0.6, 'reason': 'RSI overbought'}

            elif 'Bollinger' in strategy_name:
                # Bollinger breakout signal
                if len(recent_data) >= 20:
                    upper, lower = self._calculate_bollinger_bands(recent_data['close'])
                    current_price = recent_data['close'].iloc[-1]

                    if current_price > upper:
                        return {'direction': 'BUY', 'strength': 0.8, 'reason': 'Upper BB breakout'}
                    elif current_price < lower:
                        return {'direction': 'SELL', 'strength': 0.8, 'reason': 'Lower BB breakout'}

            # Default random signal for demo (weak)
            if signal_strength < 0.3:
                return None

        except Exception as e:
            logger.error(f"Error simulating signal for {strategy_name}: {e}")

        return None

    def _calculate_simple_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate simple RSI."""
        if len(prices) < period:
            return 50.0

        gains = []
        losses = []

        for i in range(1, min(period + 1, len(prices))):
            change = prices.iloc[-i] - prices.iloc[-i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if not losses or sum(losses) == 0:
            return 100.0 if gains else 50.0

        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses)
        rs = avg_gain / avg_loss if avg_loss > 0 else 0
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, dev: float = 2.0) -> Tuple[float, float]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return prices.iloc[-1], prices.iloc[-1]

        sma = prices.rolling(period).mean().iloc[-1]
        std = prices.rolling(period).std().iloc[-1]

        upper = sma + (std * dev)
        lower = sma - (std * dev)

        return upper, lower

    def _calculate_bracket_levels(self, strategy_name: str, entry_price: float, confidence: float) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels based on strategy type.

        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        # Base levels as percentage of entry price
        base_stop_pct = 0.02  # 2% base stop loss
        base_target_pct = 0.04  # 4% base take profit

        # Adjust based on strategy type
        if 'Breakout' in strategy_name:
            # Tighter stops for breakouts (they need room to run)
            stop_pct = base_stop_pct * 1.5  # 3% stop
            target_pct = base_target_pct * 2.0  # 8% target
        elif 'Martingale' in strategy_name:
            # Very tight stops for Martingale
            stop_pct = base_stop_pct * 0.5  # 1% stop
            target_pct = base_target_pct * 0.5  # 2% target
        elif 'ATR' in strategy_name:
            # ATR-based stops (volatility-adjusted)
            stop_pct = base_stop_pct * 1.2  # 2.4% stop
            target_pct = base_target_pct * 1.5  # 6% target
        else:
            # Standard for other strategies
            stop_pct = base_stop_pct
            target_pct = base_target_pct

        # Adjust based on confidence (higher confidence = wider targets)
        confidence_multiplier = 0.5 + (confidence * 2.0)  # 0.5 to 2.5 range
        target_pct *= confidence_multiplier

        # Calculate actual prices
        stop_loss = entry_price * (1 - stop_pct)  # Simplify to % from entry
        take_profit = entry_price * (1 + target_pct)

        return stop_loss, take_profit

    def _execute_live_trade(self, trade_signal: Dict[str, Any], instrument: str) -> str:
        """
        Execute trade on live platform (simplified version).

        Args:
            trade_signal: Trade signal details
            instrument: Trading instrument

        Returns:
            Execution status
        """
        try:
            # In production, this would connect to Deriv API or broker
            execution_id = f"ai_trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Simulate execution (replace with actual API calls)
            time.sleep(0.1)  # Simulate API call delay

            # Record trade
            trade_record = {
                'execution_id': execution_id,
                'timestamp': datetime.now(),
                'instrument': instrument,
                'strategy': trade_signal['strategy_name'],
                'direction': trade_signal['direction'],
                'entry_price': trade_signal['entry_price'],
                'position_size': trade_signal['position_size'],
                'stop_loss': trade_signal['stop_loss'],
                'take_profit': trade_signal['take_profit'],
                'confidence': trade_signal['confidence'],
                'status': 'ACTIVE'
            }

            self.active_trades[execution_id] = trade_record
            self.daily_trade_count += 1

            logger.info(f"🎯 LIVE TRADE EXECUTED: {trade_signal['direction']} {instrument}")
            return 'EXECUTED'

        except Exception as e:
            logger.error(f"Live trade execution failed: {e}")
            return 'FAILED'

    def _update_portfolio_state(self, trade_signal: Dict[str, Any]):
        """
        Update portfolio state after trade execution.
        """
        # Update account balance (assume position entered at market)
        position_value = trade_signal['position_size']

        # Reserve margin (simplified)
        margin_required = position_value * 0.1  # Assume 10% margin

        if margin_required <= self.account_balance:
            self.account_balance -= margin_required
            logger.info(f"💰 Account updated. Balance: ${self.account_balance:,.0f}")

    def _update_ai_monitoring(self, strategy_selection: Dict[str, Any], trade_signal: Dict[str, Any]):
        """
        Update AI monitoring system with trade details.
        """
        # AI monitoring placeholder - removed ai_monitor import to fix import errors
        logger.info("🤖 AI monitoring update skipped (monitoring system not available)")
        pass  # Replace with real monitoring when ai_monitor module is implemented

    def _log_trade_execution(self, execution_result: Dict[str, Any]):
        """
        Log trade execution for analysis and reporting.
        """
        self.execution_history.append(execution_result)

        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def update_trade_status(self, trade_id: str, status_update: Dict[str, Any]):
        """
        Update status of an active trade.

        Args:
            trade_id: Trade execution ID
            status_update: Status update details
        """
        if trade_id in self.active_trades:
            trade = self.active_trades[trade_id]
            trade.update(status_update)

            if status_update.get('status') in ['CLOSED', 'STOPPED', 'TARGET_HIT']:
                # Calculate P&L
                if 'final_price' in status_update:
                    direction = trade['direction']
                    entry_price = trade['entry_price']
                    exit_price = status_update['final_price']

                    if direction == 'BUY':
                        pnl = (exit_price - entry_price) * (trade['position_size'] / entry_price)
                    else:
                        pnl = (entry_price - exit_price) * (trade['position_size'] / entry_price)

                    self.daily_pnl += pnl
                    trade['final_pnl'] = pnl

                    # Update AI monitoring with outcome
                    self._update_trade_outcome(trade, pnl > 0)

                    logger.info(f"📊 Trade {trade_id} closed. P&L: ${pnl:.2f}")

                # Remove from active trades
                del self.active_trades[trade_id]

    def _update_trade_outcome(self, trade: Dict[str, Any], profitable: bool):
        """
        Update AI monitoring with trade outcome.
        """
        # AI monitoring placeholder - removed ai_monitor import to fix import errors
        logger.info("🤖 Trade outcome logged (monitoring system not available)")
        pass  # Replace with real monitoring when ai_monitor module is implemented

    def get_executor_status(self) -> Dict[str, Any]:
        """
        Get current executor status and statistics.

        Returns:
            Comprehensive status report
        """
        return {
            'account_balance': self.account_balance,
            'daily_pnl': self.daily_pnl,
            'daily_trade_count': self.daily_trade_count,
            'active_trades': len(self.active_trades),
            'active_trade_details': self.active_trades,
            'execution_history_count': len(self.execution_history),
            'risk_limits': {
                'max_daily_trades': self.max_daily_trades,
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'min_confidence_threshold': self.min_confidence_threshold
            },
            'live_trading_enabled': self.enable_live_trading,
            'last_update': datetime.now()
        }

    def reset_daily_counters(self):
        """
        Reset daily trading counters (call at start of new trading day).
        """
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        self.active_trades = {}
        logger.info("🔄 Daily trading counters reset")

# Global executor instance
ai_trade_executor = AITradeExecutor()

def analyze_and_execute_trade(market_data: pd.DataFrame,
                            instrument: str = "R_10",
                            risk_preference: str = 'balanced') -> Dict[str, Any]:
    """
    High-level AI trade analysis and execution function.

    Args:
        market_data: Current market data
        instrument: Trading instrument
        risk_preference: Risk preference level

    Returns:
        Trade execution result
    """
    return ai_trade_executor.analyze_and_execute_trade(market_data, instrument, risk_preference)

def get_executor_status() -> Dict[str, Any]:
    """
    Get AI executor current status.

    Returns:
        Status information
    """
    return ai_trade_executor.get_executor_status()

__all__ = [
    'AITradeExecutor',
    'ai_trade_executor',
    'analyze_and_execute_trade',
    'get_executor_status'
]
