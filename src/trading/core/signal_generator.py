"""
Signal Generator Module
=======================
Technical signal generation and automated trade signal creation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from src.charts.indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_moving_averages
from src.charts.fibonacci import calculate_fibonacci_retracements, find_pivot_points
from src.charts.patterns import detect_candlestick_patterns, detect_chart_patterns
from src.strategy import StrategyFactory
from .trading_intelligence import TradingIntelligence

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Advanced signal generation engine that combines technical analysis
    with AI insights to generate high-quality trading signals.
    """

    def __init__(self, strategy_factory: Optional[StrategyFactory] = None):
        self.strategy_factory = strategy_factory or StrategyFactory()
        self.available_strategies = self.strategy_factory.get_available_strategies()

        # Signal generation parameters
        self.min_confidence_threshold = 0.5  # Minimum confidence for signal generation
        self.max_signals_per_instrument = 3  # Limit signals per instrument
        self.signal_cooldown_seconds = 300  # 5 minutes between signals for same instrument

        # Track generated signals to prevent over-signaling
        self.recent_signals = {}  # instrument -> (timestamp, signal_count)

        logger.info(f"SignalGenerator initialized with {len(self.available_strategies)} strategies")

    def generate_signals(self,
                        instruments: List[str],
                        market_data: Dict[str, pd.DataFrame],
                        risk_tolerance: str = "medium") -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate trading signals for multiple instruments.

        Args:
            instruments: List of trading instruments
            market_data: Dictionary of instrument -> OHLC DataFrame
            risk_tolerance: Risk tolerance level ('low', 'medium', 'high')

        Returns:
            Dictionary of instrument -> list of signals
        """
        all_signals = {}

        for instrument in instruments:
            if instrument not in market_data:
                logger.warning(f"No data available for {instrument}")
                continue

            # Check cooldown period
            if self._is_on_cooldown(instrument):
                continue

            try:
                signals = self._generate_instrument_signals(instrument, market_data[instrument], risk_tolerance)
                if signals:
                    all_signals[instrument] = signals
                    self._update_signal_tracking(instrument, len(signals))

            except Exception as e:
                logger.error(f"Error generating signals for {instrument}: {e}")

        return all_signals

    def _generate_instrument_signals(self,
                                   instrument: str,
                                   data: pd.DataFrame,
                                   risk_tolerance: str) -> List[Dict[str, Any]]:
        """
        Generate signals for a single instrument.

        Args:
            instrument: Trading instrument
            data: OHLC DataFrame
            risk_tolerance: Risk tolerance level

        Returns:
            List of trading signals
        """
        signals = []

        if len(data) < 50:  # Require minimum data points
            return signals

        # Calculate technical indicators
        indicators = self._calculate_technical_indicators(data)

        # Generate signals from different sources
        technical_signals = self._generate_technical_signals(instrument, data, indicators)
        pattern_signals = self._generate_pattern_signals(instrument, data)
        strategy_signals = self._generate_strategy_signals(instrument, data, risk_tolerance)

        # Combine and filter signals
        all_candidates = technical_signals + pattern_signals + strategy_signals

        # Remove conflicting signals and apply confidence filtering
        filtered_signals = self._filter_and_rank_signals(all_candidates, risk_tolerance)

        # Limit to max signals per instrument
        signals = filtered_signals[:self.max_signals_per_instrument]

        return signals

    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive technical indicators.

        Args:
            data: OHLC DataFrame

        Returns:
            Dictionary of calculated indicators
        """
        try:
            indicators = {}

            # Trend indicators
            indicators['sma'] = calculate_moving_averages(data, [20, 50, 200])
            indicators['ema'] = calculate_moving_averages(data, [12, 26], method='ema')

            # Momentum indicators
            rsi_result = calculate_rsi(data, 14)
            indicators['rsi'] = rsi_result.iloc[-1] if not rsi_result.empty else 50

            # MACD
            macd_result = calculate_macd(data)
            macd, signal, histogram = macd_result
            indicators['macd'] = macd.iloc[-1] if not macd.empty else 0
            indicators['macd_signal'] = signal.iloc[-1] if not signal.empty else 0
            indicators['macd_histogram'] = histogram.iloc[-1] if not histogram.empty else 0

            # Bollinger bands
            bb_result = calculate_bollinger_bands(data)
            indicators['bb_upper'] = bb_result[0].iloc[-1] if not bb_result[0].empty else data['close'].iloc[-1]
            indicators['bb_middle'] = bb_result[1].iloc[-1] if not bb_result[1].empty else data['close'].iloc[-1]
            indicators['bb_lower'] = bb_result[2].iloc[-1] if not bb_result[2].empty else data['close'].iloc[-1]

            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def _generate_technical_signals(self,
                                   instrument: str,
                                   data: pd.DataFrame,
                                   indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate signals from technical indicators.

        Args:
            instrument: Trading instrument
            data: OHLC DataFrame
            indicators: Technical indicators

        Returns:
            List of technical signals
        """
        signals = []
        current_price = data['close'].iloc[-1]

        # RSI-based signals
        rsi = indicators.get('rsi', 50)
        if rsi > 70:  # Overbought - potential SELL
            signals.append({
                'instrument': instrument,
                'direction': 'SELL',
                'type': 'technical',
                'indicator': 'RSI',
                'reason': f'RSI overbought at {rsi:.1f}',
                'entry_price': current_price,
                'confidence': min(rsi / 100, 1.0),
                'strength': 'strong' if rsi > 80 else 'moderate'
            })
        elif rsi < 30:  # Oversold - potential BUY
            signals.append({
                'instrument': instrument,
                'direction': 'BUY',
                'type': 'technical',
                'indicator': 'RSI',
                'reason': f'RSI oversold at {rsi:.1f}',
                'entry_price': current_price,
                'confidence': min((100-rsi) / 100, 1.0),
                'strength': 'strong' if rsi < 20 else 'moderate'
            })

        # MACD signals
        macd_hist = indicators.get('macd_histogram', 0)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)

        if macd > macd_signal and macd_hist > 0:  # Bullish divergence
            signals.append({
                'instrument': instrument,
                'direction': 'BUY',
                'type': 'technical',
                'indicator': 'MACD',
                'reason': f'MACD bullish crossover',
                'entry_price': current_price,
                'confidence': min(abs(macd_hist) * 10, 1.0),
                'strength': 'strong' if abs(macd_hist) > 0.01 else 'moderate'
            })
        elif macd < macd_signal and macd_hist < 0:  # Bearish divergence
            signals.append({
                'instrument': instrument,
                'direction': 'SELL',
                'type': 'technical',
                'indicator': 'MACD',
                'reason': f'MACD bearish crossover',
                'entry_price': current_price,
                'confidence': min(abs(macd_hist) * 10, 1.0),
                'strength': 'strong' if abs(macd_hist) > 0.01 else 'moderate'
            })

        # Bollinger Band signals
        bb_upper = indicators.get('bb_upper', current_price)
        bb_lower = indicators.get('bb_lower', current_price)

        if abs(current_price - bb_lower) < current_price * 0.001:  # Near lower band - potential BUY
            signals.append({
                'instrument': instrument,
                'direction': 'BUY',
                'type': 'technical',
                'indicator': 'Bollinger Bands',
                'reason': f'Price near lower Bollinger Band',
                'entry_price': current_price,
                'confidence': 0.7,
                'strength': 'moderate'
            })
        elif abs(current_price - bb_upper) < current_price * 0.001:  # Near upper band - potential SELL
            signals.append({
                'instrument': instrument,
                'direction': 'SELL',
                'type': 'technical',
                'indicator': 'Bollinger Bands',
                'reason': f'Price near upper Bollinger Band',
                'entry_price': current_price,
                'confidence': 0.7,
                'strength': 'moderate'
            })

        return signals

    def _generate_pattern_signals(self,
                                 instrument: str,
                                 data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generate signals from chart patterns.

        Args:
            instrument: Trading instrument
            data: OHLC DataFrame

        Returns:
            List of pattern signals
        """
        signals = []
        current_price = data['close'].iloc[-1]

        try:
            # Detect candlestick patterns
            candle_patterns = detect_candlestick_patterns(data)
            chart_patterns = detect_chart_patterns(data)

            # Look for bullish patterns
            if candle_patterns.get('bullish'):
                for pattern in candle_patterns['bullish'][-5:]:  # Recent patterns
                    signals.append({
                        'instrument': instrument,
                        'direction': 'BUY',
                        'type': 'pattern',
                        'indicator': 'Candlestick',
                        'reason': f'Bullish {pattern} pattern detected',
                        'entry_price': current_price,
                        'confidence': 0.8,
                        'strength': 'strong'
                    })

            # Look for bearish patterns
            if candle_patterns.get('bearish'):
                for pattern in candle_patterns['bearish'][-5:]:  # Recent patterns
                    signals.append({
                        'instrument': instrument,
                        'direction': 'SELL',
                        'type': 'pattern',
                        'indicator': 'Candlestick',
                        'reason': f'Bearish {pattern} pattern detected',
                        'entry_price': current_price,
                        'confidence': 0.8,
                        'strength': 'strong'
                    })

            # Fibonacci retracements (simplified)
            if len(data) > 50:
                high_swing = data['high'].rolling(20).max().iloc[-1]
                low_swing = data['low'].rolling(20).min().iloc[-1]
                current_position = (current_price - low_swing) / (high_swing - low_swing)

                # Near key fib levels
                if abs(current_position - 0.236) < 0.05:  # Near 23.6% retracement
                    signals.append({
                        'instrument': instrument,
                        'direction': 'BUY',
                        'type': 'fibonacci',
                        'indicator': 'Retracement',
                        'reason': f'Price near 23.6% Fibonacci retracement level',
                        'entry_price': current_price,
                        'confidence': 0.6,
                        'strength': 'moderate'
                    })
                elif abs(current_position - 0.618) < 0.05:  # Near 61.8% retracement
                    signals.append({
                        'instrument': instrument,
                        'direction': 'SELL',
                        'type': 'fibonacci',
                        'indicator': 'Retracement',
                        'reason': f'Price near 61.8% Fibonacci retracement level',
                        'entry_price': current_price,
                        'confidence': 0.6,
                        'strength': 'moderate'
                    })

        except Exception as e:
            logger.error(f"Error generating pattern signals: {e}")

        return signals

    def _generate_strategy_signals(self,
                                  instrument: str,
                                  data: pd.DataFrame,
                                  risk_tolerance: str) -> List[Dict[str, Any]]:
        """
        Generate signals from trading strategies.

        Args:
            instrument: Trading instrument
            data: OHLC DataFrame
            risk_tolerance: Risk tolerance level

        Returns:
            List of strategy-generated signals
        """
        signals = []
        current_price = data['close'].iloc[-1]

        try:
            # Get strategies based on risk tolerance
            strategy_names = self._select_strategies_for_risk(risk_tolerance)

            for strategy_name in strategy_names[:2]:  # Limit to 2 strategies per instrument
                try:
                    strategy = self.available_strategies.get(strategy_name)
                    if strategy:
                        # Run strategy analysis (simplified - would create strategy instance with parameters)
                        signal = self._run_strategy_analysis(strategy_name, strategy, data, current_price)
                        if signal:
                            signals.append(signal)

                except Exception as e:
                    logger.debug(f"Strategy {strategy_name} failed for {instrument}: {e}")

        except Exception as e:
            logger.error(f"Error generating strategy signals: {e}")

        return signals

    def _run_strategy_analysis(self,
                              strategy_name: str,
                              strategy_class: Any,
                              data: pd.DataFrame,
                              current_price: float) -> Optional[Dict[str, Any]]:
        """
        Run individual strategy analysis.

        Args:
            strategy_name: Name of strategy
            strategy_class: Strategy class
            data: Market data
            current_price: Current price

        Returns:
            Signal dictionary if strategy generates one
        """
        try:
            # Create strategy instance with default parameters
            strategy_instance = strategy_class()

            # Analyze recent data
            signal = None

            # Simple buy/sell signal based on strategy type
            if 'rsi' in strategy_name.lower():
                # RSI strategy typically sells when overbought, buys when oversold
                if len(data) > 20:
                    recent_rsi = calculate_rsi(data.iloc[-20:], 14)
                    if not recent_rsi.empty and recent_rsi.iloc[-1] < 30:
                        signal = {
                            'instrument': 'placeholder',  # Will be filled by caller
                            'direction': 'BUY',
                            'type': 'strategy',
                            'indicator': strategy_name,
                            'reason': f'{strategy_name} RSI oversold signal',
                            'entry_price': current_price,
                            'confidence': 0.7,
                            'strength': 'moderate'
                        }
                    elif not recent_rsi.empty and recent_rsi.iloc[-1] > 70:
                        signal = {
                            'instrument': 'placeholder',  # Will be filled by caller
                            'direction': 'SELL',
                            'type': 'strategy',
                            'indicator': strategy_name,
                            'reason': f'{strategy_name} RSI overbought signal',
                            'entry_price': current_price,
                            'confidence': 0.7,
                            'strength': 'moderate'
                        }

            elif 'ma' in strategy_name.lower() or 'moving' in strategy_name.lower():
                # Moving average crossover strategy
                if len(data) > 50:
                    sma20 = data['close'].rolling(20).mean()
                    sma50 = data['close'].rolling(50).mean()

                    if (sma20.iloc[-2] < sma50.iloc[-2] and
                        sma20.iloc[-1] > sma50.iloc[-1]):  # Golden cross
                        signal = {
                            'instrument': 'placeholder',  # Will be filled by caller
                            'direction': 'BUY',
                            'type': 'strategy',
                            'indicator': strategy_name,
                            'reason': f'{strategy_name} golden crossover signal',
                            'entry_price': current_price,
                            'confidence': 0.8,
                            'strength': 'strong'
                        }
                    elif (sma20.iloc[-2] > sma50.iloc[-2] and
                          sma20.iloc[-1] < sma50.iloc[-1]):  # Death cross
                        signal = {
                            'instrument': 'placeholder',  # Will be filled by caller
                            'direction': 'SELL',
                            'type': 'strategy',
                            'indicator': strategy_name,
                            'reason': f'{strategy_name} death crossover signal',
                            'entry_price': current_price,
                            'confidence': 0.8,
                            'strength': 'strong'
                        }

            return signal

        except Exception as e:
            logger.error(f"Strategy analysis failed for {strategy_name}: {e}")
            return None

    def _select_strategies_for_risk(self, risk_tolerance: str) -> List[str]:
        """
        Select appropriate strategies based on risk tolerance.

        Args:
            risk_tolerance: Risk tolerance level

        Returns:
            List of strategy names
        """
        if risk_tolerance == 'low':
            return ['📈 MA Cross', '📊 RSI Reversal']
        elif risk_tolerance == 'high':
            return ['💰 Martingale (HIGH RISK)', '⚡ ATR Breakout']
        else:  # medium
            return ['🎯 Bollinger Breakout', '🔄 EMA + RSI', '🌊 SuperTrend']

    def _filter_and_rank_signals(self,
                               signals: List[Dict[str, Any]],
                               risk_tolerance: str) -> List[Dict[str, Any]]:
        """
        Filter conflicting signals and rank by confidence.

        Args:
            signals: Raw signals
            risk_tolerance: Risk tolerance level

        Returns:
            Filtered and ranked signals
        """
        if not signals:
            return signals

        # Remove low confidence signals
        confidence_threshold = {
            'low': 0.7,
            'medium': 0.6,
            'high': 0.5
        }.get(risk_tolerance, 0.6)

        filtered_signals = [s for s in signals if s['confidence'] >= confidence_threshold]

        # Sort by confidence (best first)
        filtered_signals.sort(key=lambda x: x['confidence'], reverse=True)

        return filtered_signals

    def _is_on_cooldown(self, instrument: str) -> bool:
        """
        Check if instrument is on signal cooldown.

        Args:
            instrument: Trading instrument

        Returns:
            True if on cooldown
        """
        if instrument not in self.recent_signals:
            return False

        timestamp, count = self.recent_signals[instrument]
        time_diff = (datetime.now() - timestamp).total_seconds()

        return (time_diff < self.signal_cooldown_seconds and
                count >= self.max_signals_per_instrument)

    def _update_signal_tracking(self, instrument: str, signal_count: int):
        """
        Update signal tracking for cooldown management.

        Args:
            instrument: Trading instrument
            signal_count: Number of signals generated
        """
        self.recent_signals[instrument] = (datetime.now(), signal_count)

    def get_signal_statistics(self) -> Dict[str, Any]:
        """
        Get signal generation statistics.

        Returns:
            Statistics dictionary
        """
        total_signals = sum(count for _, count in self.recent_signals.values())

        return {
            'total_instruments_tracked': len(self.recent_signals),
            'total_signals_generated': total_signals,
            'average_signals_per_instrument': total_signals / len(self.recent_signals) if self.recent_signals else 0,
            'instruments_on_cooldown': len([i for i, (_, count) in self.recent_signals.items() if count >= self.max_signals_per_instrument])
        }


# Convenience function
def create_signal_generator(strategy_factory: Optional[StrategyFactory] = None) -> SignalGenerator:
    """
    Create and return a signal generator instance.

    Args:
        strategy_factory: Optional strategy factory

    Returns:
        Configured SignalGenerator instance
    """
    return SignalGenerator(strategy_factory)


__all__ = [
    'SignalGenerator',
    'create_signal_generator'
]
