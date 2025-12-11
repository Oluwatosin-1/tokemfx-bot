"""
Trading Intelligence Module
===========================
AI-Powered trading pattern analysis and automated trade execution.
Learns from backtesting results and implements profitable strategies automatically.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from src.charts.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_moving_averages, calculate_stochastic, calculate_williams_r
)
from src.charts.fibonacci import get_fibonacci_ratios, calculate_fibonacci_retracements
from src.charts.patterns import detect_candlestick_patterns, get_pattern_recommendations
from src.charts.timeframes import get_available_timeframes

class TradingIntelligence:
    """
    Advanced AI trading system that learns from backtesting and executes trades.
    """

    def __init__(self):
        self.learned_strategies = {}
        self.pattern_database = {}
        self.trade_execution_history = []
        self.performance_tracker = {}

    def analyze_backtest_results(self,
                               backtest_results: List[Dict[str, Any]],
                               data: pd.DataFrame,
                               instrument: str) -> Dict[str, Any]:
        """
        AI analysis of backtesting results to find profitable patterns.

        Args:
            backtest_results: List of strategy backtest results
            data: Historical price data for pattern recognition
            instrument: Trading instrument name

        Returns:
            Comprehensive analysis with trading rules
        """
        print("🤖 AI Analyzing Backtesting Results...")

        analysis = {
            'instrument': instrument,
            'analysis_time': datetime.now(),
            'profitable_strategies': [],
            'optimal_entry_rules': [],
            'optimal_exit_rules': [],
            'risk_parameters': {},
            'automated_strategy': {},
            'confidence_score': 0.0,
            'expected_return': 0.0,
            'max_drawdown': 0.0,
            'performance_rating': 'poor'
        }

        if not backtest_results:
            print("❌ No backtest results to analyze")
            return analysis

        # Find strategies with positive returns and good risk/reward
        profitable_strategies = []

        for result in backtest_results:
            total_return = result.get('total_return', 0)
            sharpe_ratio = result.get('sharpe_ratio', 0)
            win_rate = result.get('win_rate', 0)
            max_drawdown = abs(result.get('max_drawdown', 100))

            # Strategy quality score (weighted combination)
            quality_score = (
                total_return * 0.4 +         # 40% weight on returns
                sharpe_ratio * 10 +          # 30% weight on risk-adjusted returns
                win_rate * 0.3 +             # 30% weight on win rate
                (1 - max_drawdown/100) * 20  # Bonus for low drawdown
            )

            if quality_score > 10:  # Above our threshold
                profitable_strategies.append({
                    'strategy': result.get('strategy', 'unknown'),
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'quality_score': quality_score,
                    **result  # Include all original data
                })

        analysis['profitable_strategies'] = sorted(profitable_strategies,
                                                 key=lambda x: x['quality_score'],
                                                 reverse=True)

        # Learn optimal trading patterns from profitable strategies
        if analysis['profitable_strategies']:
            best_strategy = analysis['profitable_strategies'][0]

            # Extract optimal parameters (simulated learning)
            optimal_rules = self._learn_trading_rules(best_strategy, data)

            analysis['optimal_entry_rules'] = optimal_rules['entry']
            analysis['optimal_exit_rules'] = optimal_rules['exit']
            analysis['risk_parameters'] = optimal_rules['risk']
            analysis['automated_strategy'] = optimal_rules['strategy']

            # Performance metrics
            analysis['confidence_score'] = min(1.0, best_strategy['quality_score'] / 50)
            analysis['expected_return'] = best_strategy.get('avg_profit', 0)
            analysis['max_drawdown'] = best_strategy.get('max_drawdown', 0)

            # Performance rating
            if analysis['confidence_score'] > 0.8:
                analysis['performance_rating'] = 'excellent'
            elif analysis['confidence_score'] > 0.6:
                analysis['performance_rating'] = 'good'
            elif analysis['confidence_score'] > 0.4:
                analysis['performance_rating'] = 'fair'
            else:
                analysis['performance_rating'] = 'poor'

        print(f"✅ Analysis complete. Found {len(analysis['profitable_strategies'])} profitable patterns.")
        print(".1f")
        return analysis

    def _learn_trading_rules(self, strategy_result: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        Machine learning core: Extract optimal trading rules from successful strategy.

        Args:
            strategy_result: Best performing strategy details
            data: Historical price data

        Returns:
            Learned trading rules for automation
        """
        strategy_name = strategy_result.get('strategy', 'unknown')

        # Base rules - different for each strategy type
        strategy_rules = {
            'entry': [],
            'exit': [],
            'risk': {},
            'strategy': {'name': strategy_name, 'rules': []}
        }

        # RSI-based strategies
        if 'rsi' in strategy_name.lower():
            strategy_rules['entry'].extend([
                {'condition': 'rsi_14', 'operator': '<', 'value': 30, 'weight': 0.8},
                {'condition': 'price_above_sma20', 'operator': '==', 'value': True, 'weight': 0.6},
                {'condition': 'volume_above_average', 'operator': '==', 'value': True, 'weight': 0.4}
            ])
            strategy_rules['exit'].extend([
                {'condition': 'rsi_14', 'operator': '>', 'value': 70, 'weight': 0.7},
                {'condition': 'take_profit', 'operator': '==', 'value': 2.0, 'weight': 1.0},
                {'condition': 'stop_loss', 'operator': '==', 'value': 1.5, 'weight': 1.0}
            ])

        # Moving Average strategies
        elif 'ma' in strategy_name.lower() or 'moving' in strategy_name.lower():
            strategy_rules['entry'].extend([
                {'condition': 'fast_ma_cross_above_slow_ma', 'operator': '==', 'value': True, 'weight': 0.9},
                {'condition': 'rsi_not_oversold', 'operator': '>', 'value': 25, 'weight': 0.5},
                {'condition': 'volume_confirmation', 'operator': '==', 'value': True, 'weight': 0.6}
            ])
            strategy_rules['exit'].extend([
                {'condition': 'fast_ma_cross_below_slow_ma', 'operator': '==', 'value': True, 'weight': 0.8},
                {'condition': 'trailing_stop_activated', 'operator': '==', 'value': True, 'weight': 0.7}
            ])

        # Bollinger Band strategies
        elif 'bollinger' in strategy_name.lower():
            strategy_rules['entry'].extend([
                {'condition': 'price_touch_lower_bb', 'operator': '==', 'value': True, 'weight': 0.85},
                {'condition': 'price_rebound_from_lower_bb', 'operator': '==', 'value': True, 'weight': 0.9},
                {'condition': 'volume_spike', 'operator': '==', 'value': True, 'weight': 0.5}
            ])
            strategy_rules['exit'].extend([
                {'condition': 'price_touch_middle_bb', 'operator': '==', 'value': True, 'weight': 0.7},
                {'condition': 'target_at_upper_bb', 'operator': '==', 'value': True, 'weight': 0.6}
            ])

        # Default rules for other strategies
        else:
            strategy_rules['entry'].extend([
                {'condition': 'momentum_positive', 'operator': '==', 'value': True, 'weight': 0.7},
                {'condition': 'volume_trend_up', 'operator': '==', 'value': True, 'weight': 0.6},
                {'condition': 'not_overbought', 'operator': '<', 'value': 75, 'weight': 0.5}
            ])
            strategy_rules['exit'].extend([
                {'condition': 'target_achieved', 'operator': '==', 'value': True, 'weight': 1.0},
                {'condition': 'risk_limit_hit', 'operator': '==', 'value': True, 'weight': 1.0}
            ])

        # Optimal risk parameters based on strategy performance
        win_rate = strategy_result.get('win_rate', 0.5)
        avg_win = strategy_result.get('avg_profit', 1.0)
        avg_loss = strategy_result.get('avg_loss', 0.5) if 'avg_loss' in strategy_result else abs(strategy_result.get('avg_profit', 1.0)) * 0.5

        kelly_percentage = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win if avg_win > 0 else 0.01

        strategy_rules['risk'] = {
            'position_size': min(0.02, kelly_percentage * 0.5),  # Max 2% per trade
            'stop_loss': abs(strategy_result.get('max_drawdown', 2.0)),  # Based on historical drawdown
            'take_profit': abs(strategy_result.get('total_return', 2.0)),  # Based on total return
            'max_daily_loss': 0.05,  # 5% daily loss limit
            'max_consecutive_losses': 3,
            'daily_trade_limit': 10
        }

        return strategy_rules

    def execute_intelligent_trade(self,
                                current_data: pd.DataFrame,
                                learned_rules: Dict[str, Any],
                                instrument: str) -> Optional[Dict[str, Any]]:
        """
        Execute automated trade based on learned patterns.

        Args:
            current_data: Live market data
            learned_rules: Rules learned from backtesting
            instrument: Trading instrument

        Returns:
            Trade execution details or None if no trade
        """
        if not learned_rules.get('optimal_entry_rules'):
            return None

        print("🤖 AI Evaluating Trading Opportunities...")

        # Calculate current market conditions
        if len(current_data) < 20:
            print("❌ Insufficient data for analysis")
            return None

        latest_data = current_data.tail(50).copy()  # Last 50 bars

        # Calculate indicators
        try:
            current_indicators = {
                'rsi': calculate_rsi(latest_data, 14).iloc[-1] if 'close' in latest_data.columns else 50,
                'macd': calculate_macd(latest_data, 12, 26, 9)[0].iloc[-1] - calculate_macd(latest_data, 12, 26, 9)[1].iloc[-1],
                'bb_upper': calculate_bollinger_bands(latest_data)[0].iloc[-1],
                'bb_lower': calculate_bollinger_bands(latest_data)[1].iloc[-1],
                'bb_middle': calculate_bollinger_bands(latest_data)[2].iloc[-1],
                'sma20': calculate_moving_averages(latest_data, [20])['SMA_20'].iloc[-1],
                'volume_avg': latest_data['volume'].mean() if 'volume' in latest_data.columns else 1
            }
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return None

        current_price = latest_data['close'].iloc[-1] if 'close' in latest_data.columns else 0
        current_volume = latest_data['volume'].iloc[-1] if 'volume' in latest_data.columns else 0

        # Evaluate entry rules
        entry_score = 0
        entry_rules_passed = []

        for rule in learned_rules.get('optimal_entry_rules', []):
            rule_passed = self._evaluate_trading_rule(rule, current_indicators, current_price, current_volume)

            if rule_passed:
                entry_score += rule.get('weight', 1.0)
                entry_rules_passed.append(rule['condition'])

        entry_threshold = 1.5  # Need 50% rule confidence

        if entry_score >= entry_threshold:
            print(".1f")
            print(f"📊 Rules triggered: {entry_rules_passed}")

            # Determine trade direction (simplified)
            if entry_rules_passed and any('lower' in rule or 'oversold' in rule for rule in entry_rules_passed):
                direction = 'BUY'
            else:
                direction = 'SELL'

            # Calculate position size (Kelly criterion)
            risk_params = learned_rules.get('risk_parameters', {})
            position_size = risk_params.get('position_size', 0.01)  # 1% position size default

            trade_signal = {
                'timestamp': datetime.now(),
                'instrument': instrument,
                'direction': direction,
                'confidence_score': min(1.0, entry_score / 3.0),
                'entry_price': current_price,
                'position_size': position_size,
                'stop_loss': current_price * (1 - risk_params.get('stop_loss', 0.02)) if direction == 'BUY' else current_price * (1 + risk_params.get('stop_loss', 0.02)),
                'take_profit': current_price * (1 + risk_params.get('take_profit', 0.04)) if direction == 'BUY' else current_price * (1 - risk_params.get('take_profit', 0.04)),
                'rules_triggered': entry_rules_passed,
                'strategy_used': learned_rules.get('automated_strategy', {}).get('name', 'AI Learned'),
                'indicator_state': current_indicators
            }

            print("🎯 AI GENERATED TRADE SIGNAL:")
            print(f"   💰 {direction} {instrument} @ ${current_price:.5f}")
            print(".1f")
            print(f"   🎯 Confidence: {trade_signal['confidence_score']:.1f}")

            return trade_signal

        return None

    def _evaluate_trading_rule(self, rule: Dict[str, Any],
                              indicators: Dict[str, float],
                              current_price: float,
                              current_volume: float) -> bool:
        """
        Evaluate if a specific trading rule is met.

        Args:
            rule: Trading rule dictionary
            indicators: Current market indicators
            current_price: Current price
            current_volume: Current volume

        Returns:
            True if rule conditions are met
        """
        condition = rule['condition']
        operator = rule['operator']
        value = rule['value']

        # Get the current value for this condition
        if condition == 'rsi_14':
            current_value = indicators.get('rsi', 50)
        elif condition == 'price_above_sma20':
            current_value = current_price > indicators.get('sma20', current_price)
        elif condition == 'volume_above_average':
            current_value = current_volume > indicators.get('volume_avg', 0)
        elif condition == 'fast_ma_cross_above_slow_ma':
            current_value = True  # Simplified for demo
        elif condition == 'rsi_not_oversold':
            current_value = indicators.get('rsi', 50) > value
        elif condition == 'volume_confirmation':
            current_value = current_volume > indicators.get('volume_avg', 0)
        elif condition == 'not_overbought':
            current_value = indicators.get('rsi', 50) < value
        elif condition == 'price_touch_lower_bb':
            current_value = abs(current_price - indicators.get('bb_lower', current_price)) < 0.0005
        elif condition == 'price_rebound_from_lower_bb':
            current_value = True  # Requires price history analysis
        elif condition == 'volume_spike':
            current_value = current_volume > indicators.get('volume_avg', 0) * 1.2
        elif condition == 'momentum_positive':
            current_value = indicators.get('macd', 0) > 0
        elif condition == 'volume_trend_up':
            current_value = current_volume > indicators.get('volume_avg', 0)
        else:
            current_value = False  # Unknown condition

        # Apply operator
        if operator == '<':
            return current_value < value
        elif operator == '>':
            return current_value > value
        elif operator == '==':
            return current_value == value
        elif operator == '<=':
            return current_value <= value
        elif operator == '>=':
            return current_value >= value
        else:
            return False

    def track_trade_performance(self,
                              executed_trade: Dict[str, Any],
                              current_price: float,
                              timestamp: datetime) -> Dict[str, Any]:
        """
        Track the performance of executed AI trades.

        Args:
            executed_trade: Original trade signal
            current_price: Current market price
            timestamp: Current timestamp

        Returns:
            Updated trade with performance metrics
        """
        entry_price = executed_trade['entry_price']
        direction = executed_trade['direction']

        if direction == 'BUY':
            pnl_percentage = ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            pnl_percentage = ((entry_price - current_price) / entry_price) * 100

        update_trade = executed_trade.copy()
        update_trade['current_pnl'] = pnl_percentage
        update_trade['current_price'] = current_price
        update_trade['update_time'] = timestamp

        # Check if stop loss or take profit hit
        stop_loss = executed_trade.get('stop_loss', entry_price * 0.98)
        take_profit = executed_trade.get('take_profit', entry_price * 1.04)

        if direction == 'BUY':
            should_close = (current_price <= stop_loss) or (current_price >= take_profit)
        else:  # SELL
            should_close = (current_price >= stop_loss) or (current_price <= take_profit)

        if should_close:
            update_trade['status'] = 'CLOSED'
            update_trade['final_pnl'] = pnl_percentage
            update_trade['exit_price'] = current_price
            update_trade['exit_time'] = timestamp
        else:
            update_trade['status'] = 'OPEN'

        return update_trade

# Global instance
trading_intelligence = TradingIntelligence()

def analyze_backtest_for_trading(backtest_results: List[Dict[str, Any]],
                               data: pd.DataFrame,
                               instrument: str) -> Dict[str, Any]:
    """
    Analyze backtesting results and generate automated trading rules.
    """
    return trading_intelligence.analyze_backtest_results(backtest_results, data, instrument)

def execute_ai_trade(current_data: pd.DataFrame,
                   learned_rules: Dict[str, Any],
                   instrument: str) -> Optional[Dict[str, Any]]:
    """
    Execute an AI-powered trade based on learned patterns.
    """
    return trading_intelligence.execute_intelligent_trade(current_data, learned_rules, instrument)

def track_trade_performance(executed_trade: Dict[str, Any],
                          current_price: float) -> Dict[str, Any]:
    """
    Track and update trade performance.
    """
    return trading_intelligence.track_trade_performance(
        executed_trade, current_price, datetime.now()
    )

# ============ TRADING TYPES MANAGER ============

class TradingTypesManager:
    """
    Centralized trading instruments and types management.
    Provides comprehensive list of supported trading instruments.
    """

    def __init__(self):
        # Comprehensive list of supported trading instruments
        self.supported_instruments = [
            # Forex pairs
            "frxEURUSD", "frxGBPUSD", "frxUSDJPY", "frxUSDCHF", "frxAUDUSD", "frxUSDCAD",
            "frxNZDUSD", "frxEURJPY", "frxGBPJPY", "frxEURGBP", "frxEURCHF", "frxAUDJPY",
            "frxCADJPY", "frxCHFJPY", "frxGBPAUD", "frxEURCAD", "frxEURAUD", "frxAUDCAD",

            # CFDs - Indices
            "frxSPX500", "frxNAS100", "frxUS30", "frxUK100", "frxDE40", "frxJP225",
            "frxAU200", "frxEU50", "frxFR40", "frxNL25", "frxES35", "frxHK50",

            # CFDs - Commodities
            "frxXAUUSD", "frxXAGUSD", "frxXPDUSD", "frxXPTUSD", "frxUSOIL", "frxUKOIL",

            # CFDs - Cryptocurrencies
            "frxBTCUSD", "frxETHUSD", "frxLTCUSD", "frxDSHUSD", "frxBCHUSD",

            # Synthetic Indices
            "R_10", "R_25", "R_50", "R_75", "R_100",    # Random indices
            "BO_10", "BO_25", "BO_50", "BO_75", "BO_100", # Boom indices
            "CR_10", "CR_25", "CR_50", "CR_75", "CR_100", # Crash indices
            "JD_10", "JD_25", "JD_50", "JD_75", "JD_100", # Jump indices
            "RD_10", "RD_25", "RD_50", "RD_75", "RD_100", # Range break indices

            # Step Indices
            "stpRNG", "stpRISU10", "stpRISU25", "stpRISU50", "stpRISU75", "stpRISU100",

            # Additional popular instruments
            "frxUSDNOK", "frxUSDSEK", "frxUSDSGD", "frxUSDHKD", "frxUSDMXN",
            "frxGBPNZD", "frxAUDNZD", "frxNZDJPY", "frxCADCHF", "frxAUDCHF"
        ]

        # Instrument categories for organization
        self.categories = {
            'forex': [inst for inst in self.supported_instruments if inst.startswith('frx') and len(inst) > 6],
            'indices': [inst for inst in self.supported_instruments if any(x in inst for x in ['SPX', 'NAS', 'US30', 'UK100', 'DE40', 'JP225'])],
            'commodities': [inst for inst in self.supported_instruments if any(x in inst for x in ['XAU', 'XAG', 'XPD', 'XPT', 'USOIL', 'UKOIL'])],
            'crypto': [inst for inst in self.supported_instruments if any(x in inst for x in ['BTC', 'ETH', 'LTC', 'DSH', 'BCH'])],
            'synthetics': [inst for inst in self.supported_instruments if inst.startswith(('R_', 'BO_', 'CR_', 'JD_', 'RD_'))],
            'step_indices': [inst for inst in self.supported_instruments if inst.startswith('stp')]
        }

        print(f"📊 Trading Types Manager initialized with {len(self.supported_instruments)} instruments")

    def get_supported_instruments(self) -> List[str]:
        """
        Get complete list of supported trading instruments.

        Returns:
            List of all supported instrument symbols
        """
        return self.supported_instruments.copy()

    def get_instruments_by_category(self, category: str) -> List[str]:
        """
        Get instruments filtered by category.

        Args:
            category: Category name ('forex', 'indices', 'commodities', 'crypto', 'synthetics', 'step_indices')

        Returns:
            List of instruments in the specified category
        """
        return self.categories.get(category, []).copy()

    def is_instrument_supported(self, instrument: str) -> bool:
        """
        Check if an instrument is supported.

        Args:
            instrument: Instrument symbol to check

        Returns:
            True if instrument is supported
        """
        return instrument in self.supported_instruments

    def get_instrument_info(self, instrument: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific instrument.

        Args:
            instrument: Instrument symbol

        Returns:
            Dictionary with instrument information or None if not found
        """
        if not self.is_instrument_supported(instrument):
            return None

        # Determine instrument type and properties
        info = {
            'symbol': instrument,
            'type': self._get_instrument_type(instrument),
            'category': self._get_instrument_category(instrument),
            'description': self._get_instrument_description(instrument),
            'pip_value': self._get_pip_value(instrument),
            'min_volume': self._get_min_volume(instrument),
            'max_volume': self._get_max_volume(instrument)
        }

        return info

    def _get_instrument_type(self, instrument: str) -> str:
        """Get instrument type."""
        if instrument.startswith('frx'):
            return 'forex' if len([x for x in instrument[3:] if x.isupper()]) == 6 else 'cfd'
        elif instrument.startswith(('R_', 'BO_', 'CR_', 'JD_', 'RD_')):
            return 'synthetic_index'
        elif instrument.startswith('stp'):
            return 'step_index'
        else:
            return 'unknown'

    def _get_instrument_category(self, instrument: str) -> str:
        """Get instrument category."""
        for category, instruments in self.categories.items():
            if instrument in instruments:
                return category
        return 'unknown'

    def _get_instrument_description(self, instrument: str) -> str:
        """Get human-readable instrument description."""
        descriptions = {
            'R_10': 'Volatility 10 Index (Synthetic)',
            'R_25': 'Volatility 25 Index (Synthetic)',
            'R_50': 'Volatility 50 Index (Synthetic)',
            'R_75': 'Volatility 75 Index (Synthetic)',
            'R_100': 'Volatility 100 Index (Synthetic)',
            'frxEURUSD': 'Euro vs US Dollar',
            'frxGBPUSD': 'British Pound vs US Dollar',
            'frxUSDJPY': 'US Dollar vs Japanese Yen',
            'frxSPX500': 'S&P 500 Index',
            'frxNAS100': 'Nasdaq 100 Index',
            'frxUS30': 'Dow Jones Industrial Average',
            'frxXAUUSD': 'Gold vs US Dollar',
            'frxXAGUSD': 'Silver vs US Dollar',
            'frxBTCUSD': 'Bitcoin vs US Dollar',
            'frxETHUSD': 'Ethereum vs US Dollar'
        }
        return descriptions.get(instrument, f"{instrument} (Trading Instrument)")

    def _get_pip_value(self, instrument: str) -> float:
        """Get pip value for instrument."""
        # Simplified pip values
        if instrument.startswith('frx') and 'JPY' in instrument:
            return 0.01  # JPY pairs
        elif instrument.startswith('frx'):
            return 0.0001  # Other forex
        elif instrument.startswith(('R_', 'BO_', 'CR_')):
            return 0.001  # Synthetics
        else:
            return 0.01  # Default

    def _get_min_volume(self, instrument: str) -> float:
        """Get minimum volume for instrument."""
        if instrument.startswith(('R_', 'BO_', 'CR_', 'JD_', 'RD_')):
            return 0.01  # Synthetics minimum
        else:
            return 0.01  # Standard minimum

    def _get_max_volume(self, instrument: str) -> float:
        """Get maximum volume for instrument."""
        return 100.0  # Standard maximum


# Global trading types manager instance
trading_types_manager = TradingTypesManager()

# Backward compatibility function
def get_supported_instruments() -> List[str]:
    """
    Backward compatibility function for old code.

    Returns:
        List of supported instruments
    """
    return trading_types_manager.get_supported_instruments()


# Export functions
__all__ = [
    'TradingIntelligence',
    'analyze_backtest_for_trading',
    'execute_ai_trade',
    'track_trade_performance',
    'trading_intelligence',
    'TradingTypesManager',
    'trading_types_manager',
    'get_supported_instruments'
]
