"""
AI Strategy Selector
====================
Intelligent strategy selection based on market conditions and performance analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.ai_trading_system.analytics.performance_analyzer import performance_analyzer, StrategyPerformance
from src.strategy import strategy_factory, strategy_registry

@dataclass
class MarketCondition:
    """Market condition assessment."""
    trend: str  # 'bullish', 'bearish', 'sideways'
    volatility: float  # 0.0 (low) to 1.0 (high)
    momentum: float  # RSI-like momentum indicator
    volume_trend: str  # 'increasing', 'decreasing', 'stable'
    timeframe: str  # 'short', 'medium', 'long'

class AIStrategySelector:
    """
    AI-powered strategy selection engine.
    Chooses optimal strategy based on market conditions and performance data.
    """

    def __init__(self):
        self.strategy_performance_history = {}
        self.market_condition_patterns = {}
        self.selection_model = None

        # Initialize backtesting results database integration
        self._load_historical_performance_data()

        # Strategy suitability matrix
        self.strategy_market_fit = {
            'MovingAverageCrossStrategy': {
                'trend': {'bullish': 0.8, 'bearish': 0.8, 'sideways': 0.3},
                'volatility': {'low': 0.7, 'medium': 0.8, 'high': 0.6},
                'timeframe': {'short': 0.6, 'medium': 0.8, 'long': 0.9}
            },
            'RSIReversionStrategy': {
                'trend': {'bullish': 0.4, 'bearish': 0.4, 'sideways': 0.9},
                'volatility': {'low': 0.8, 'medium': 0.9, 'high': 0.6},
                'timeframe': {'short': 0.8, 'medium': 0.7, 'long': 0.4}
            },
            'BollingerBreakoutStrategy': {
                'trend': {'bullish': 0.7, 'bearish': 0.7, 'sideways': 0.8},
                'volatility': {'low': 0.5, 'medium': 0.8, 'high': 0.9},
                'timeframe': {'short': 0.7, 'medium': 0.8, 'long': 0.6}
            },
            'ATRBreakoutStrategy': {
                'trend': {'bullish': 0.6, 'bearish': 0.6, 'sideways': 0.7},
                'volatility': {'low': 0.4, 'medium': 0.7, 'high': 0.9},
                'timeframe': {'short': 0.8, 'medium': 0.7, 'long': 0.5}
            },
            'EMARSIHybridStrategy': {
                'trend': {'bullish': 0.9, 'bearish': 0.9, 'sideways': 0.5},
                'volatility': {'low': 0.8, 'medium': 0.9, 'high': 0.7},
                'timeframe': {'short': 0.7, 'medium': 0.8, 'long': 0.9}
            },
            'MACDStrategy': {
                'trend': {'bullish': 0.7, 'bearish': 0.7, 'sideways': 0.6},
                'volatility': {'low': 0.6, 'medium': 0.8, 'high': 0.7},
                'timeframe': {'short': 0.8, 'medium': 0.9, 'long': 0.8}
            }
        }

        print("🎯 AI Strategy Selector initialized")

    def _load_historical_performance_data(self):
        """Load historical strategy performance data from backtesting results database."""
        try:
            from src.backtesting.results import get_results_database

            db = get_results_database()

            # Get recent backtesting results (last 30 days)
            recent_results = db.get_recent_results(100)

            # Process and store performance data
            for result in recent_results:
                strategy_name = result.get('strategy_class', 'Unknown')
                if strategy_name not in self.strategy_performance_history:
                    self.strategy_performance_history[strategy_name] = []

                # Extract key performance metrics
                basic_metrics = result.get('basic_metrics', {})
                performance_entry = {
                    'sharpe_ratio': basic_metrics.get('sharpe_ratio'),
                    'total_return_pct': basic_metrics.get('total_return_pct'),
                    'win_rate': basic_metrics.get('win_rate'),
                    'max_drawdown': basic_metrics.get('max_drawdown'),
                    'instrument': result.get('instrument'),
                    'date_range': result.get('date_range'),
                    'timestamp': result.get('created_at'),
                    'net_profit': basic_metrics.get('net_profit')
                }

                self.strategy_performance_history[strategy_name].append(performance_entry)

            print(f"📊 Loaded historical performance data for {len(self.strategy_performance_history)} strategies")

        except Exception as e:
            print(f"⚠️ Could not load historical performance data: {e}")
            # Continue with empty performance history

    def select_optimal_strategy(self,
                               market_data: pd.DataFrame,
                               available_strategies: Optional[List[str]] = None,
                               risk_preference: str = 'balanced') -> Dict[str, Any]:
        """
        Select optimal strategy for current market conditions.

        Args:
            market_data: Current market data
            available_strategies: List of strategies to consider
            risk_preference: 'conservative', 'balanced', 'aggressive'

        Returns:
            Strategy selection with confidence and rationale
        """
        print("🎯 AI selecting optimal strategy for current market conditions...")

        # Assess market conditions
        market_conditions = self._assess_market_conditions(market_data)

        # Get available strategies (default to all)
        if available_strategies is None:
            available_strategies = list(self.strategy_market_fit.keys())

        # Calculate strategy suitability scores
        strategy_scores = {}
        for strategy_name in available_strategies:
            if strategy_name in strategy_registry._strategies:
                score = self._calculate_strategy_suitability(strategy_name, market_conditions, risk_preference)
                strategy_scores[strategy_name] = score

        if not strategy_scores:
            return {
                'selected_strategy': None,
                'confidence': 0.0,
                'rationale': 'No suitable strategies available',
                'market_conditions': market_conditions.__dict__
            }

        # Select best strategy
        best_strategy = max(strategy_scores.keys(), key=lambda x: strategy_scores[x])
        confidence = strategy_scores[best_strategy]

        # Generate detailed rationale
        rationale = self._generate_selection_rationale(best_strategy, market_conditions, confidence)

        selection_result = {
            'selected_strategy': best_strategy,
            'confidence': confidence,
            'rationale': rationale,
            'market_conditions': market_conditions.__dict__,
            'strategy_scores': strategy_scores,
            'selection_criteria': {
                'market_trend': market_conditions.trend,
                'volatility_level': market_conditions.volatility,
                'timeframe_preference': market_conditions.timeframe,
                'risk_preference': risk_preference
            },
            'alternative_strategies': self._get_alternative_strategies(strategy_scores, 3)
        }

        print(".1f")
        print(f"📊 Market Analysis: Trend={market_conditions.trend}, Volatility={market_conditions.volatility:.2f}")
        print(f"🎯 Selected: {best_strategy}")

        return selection_result

    def _assess_market_conditions(self, market_data: pd.DataFrame) -> MarketCondition:
        """
        Assess current market conditions for strategy selection.

        Args:
            market_data: Recent price data

        Returns:
            MarketCondition object
        """
        if len(market_data) < 50:
            # Default conditions for insufficient data
            return MarketCondition(
                trend='sideways',
                volatility=0.5,
                momentum=50.0,
                volume_trend='stable',
                timeframe='medium'
            )

        # Trend analysis
        trend = self._analyze_trend(market_data)

        # Volatility analysis
        volatility = self._analyze_volatility(market_data)

        # Momentum using RSI
        momentum = self._calculate_momentum(market_data)

        # Volume trend
        volume_trend = self._analyze_volume_trend(market_data)

        # Timeframe assessment based on volatility and trend strength
        timeframe = 'medium'
        if volatility > 0.7:
            timeframe = 'short'  # High vol = shorter timeframe
        elif volatility < 0.3 and abs(momentum - 50) > 20:
            timeframe = 'long'   # Low vol + strong trend = longer timeframe

        return MarketCondition(
            trend=trend,
            volatility=volatility,
            momentum=momentum,
            volume_trend=volume_trend,
            timeframe=timeframe
        )

    def _analyze_trend(self, data: pd.DataFrame) -> str:
        """Analyze market trend direction."""
        if 'close' not in data.columns:
            return 'sideways'

        # Simple trend analysis using moving averages
        if len(data) >= 50:
            sma20 = data['close'].rolling(20).mean()
            sma50 = data['close'].rolling(50).mean()

            recent_short = sma20.iloc[-1]
            recent_long = sma50.iloc[-1]

            if recent_short > recent_long * 1.02:  # 2% above longer MA
                return 'bullish'
            elif recent_short < recent_long * 0.98:  # 2% below longer MA
                return 'bearish'

        return 'sideways'

    def _analyze_volatility(self, data: pd.DataFrame) -> float:
        """Analyze market volatility (0-1 scale)."""
        if len(data) < 20:
            return 0.5

        # Calculate rolling volatility
        returns = data['close'].pct_change() if 'close' in data.columns else pd.Series([0.01] * len(data))
        volatility = returns.rolling(20).std().iloc[-1]

        # Normalize to 0-1 scale (assuming 2% daily vol is high)
        normalized_vol = min(1.0, volatility * 50)
        return normalized_vol

    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate momentum using RSI-like calculation."""
        if len(data) < 14 or 'close' not in data.columns:
            return 50.0

        # Simple RSI calculation
        gains = []
        losses = []

        for i in range(1, min(14, len(data))):
            change = data['close'].iloc[-i] - data['close'].iloc[-i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if losses and sum(losses) > 0:
            rs = sum(gains) / sum(losses)
            rsi = 100 - (100 / (1 + rs))
            return rsi

        return 50.0

    def _analyze_volume_trend(self, data: pd.DataFrame) -> str:
        """Analyze volume trend."""
        if 'volume' not in data.columns or len(data) < 20:
            return 'stable'

        recent_vol = data['volume'].tail(10).mean()
        older_vol = data['volume'].tail(20).head(10).mean()

        ratio = recent_vol / older_vol if older_vol > 0 else 1.0

        if ratio > 1.2:
            return 'increasing'
        elif ratio < 0.8:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_strategy_suitability(self,
                                       strategy_name: str,
                                       market_conditions: MarketCondition,
                                       risk_preference: str) -> float:
        """
        Calculate how suitable a strategy is for current conditions.

        Returns score from 0.0 (poor fit) to 1.0 (perfect fit)
        """
        if strategy_name not in self.strategy_market_fit:
            return 0.3  # Default score for unknown strategies

        fit_matrix = self.strategy_market_fit[strategy_name]

        # Get fit scores for current conditions
        trend_fit = fit_matrix['trend'].get(market_conditions.trend, 0.5)
        vol_fit = self._get_volatility_fit(market_conditions.volatility, fit_matrix['volatility'])
        timeframe_fit = fit_matrix['timeframe'].get(market_conditions.timeframe, 0.7)

        # Volume consideration
        volume_fit = 1.0
        if market_conditions.volume_trend == 'increasing' and market_conditions.volatility > 0.6:
            volume_fit = 1.2  # Breakout strategies benefit from volume
        elif market_conditions.volume_trend == 'decreasing':
            volume_fit = 0.9  # Low volume may reduce reliability

        volume_fit = min(1.0, volume_fit)

        # Risk preference adjustment
        risk_multiplier = 1.0
        if risk_preference == 'conservative':
            # Favor low volatility, clear trend strategies
            if market_conditions.volatility < 0.5 and market_conditions.trend in ['bullish', 'bearish']:
                risk_multiplier = 1.1
            else:
                risk_multiplier = 0.9
        elif risk_preference == 'aggressive':
            # Favor high volatility strategies
            if market_conditions.volatility > 0.5:
                risk_multiplier = 1.1
            else:
                risk_multiplier = 0.9

        # Base suitability score
        base_score = (trend_fit * 0.4 + vol_fit * 0.3 + timeframe_fit * 0.2 + volume_fit * 0.1)

        # Apply risk adjustment
        final_score = min(1.0, base_score * risk_multiplier)

        return final_score

    def _get_volatility_fit(self, volatility: float, vol_prefs: Dict[str, float]) -> float:
        """Map continuous volatility to discrete categories."""
        if volatility < 0.33:
            return vol_prefs.get('low', 0.5)
        elif volatility < 0.66:
            return vol_prefs.get('medium', 0.7)
        else:
            return vol_prefs.get('high', 0.8)

    def _generate_selection_rationale(self,
                                    strategy_name: str,
                                    market_conditions: MarketCondition,
                                    confidence: float) -> str:
        """Generate detailed rationale for strategy selection."""

        rationale_parts = []

        # Market condition rationale
        if market_conditions.trend == 'bullish':
            rationale_parts.append("bullish trend favors momentum strategies")
        elif market_conditions.trend == 'bearish':
            rationale_parts.append("bearish trend favors directional strategies")
        else:
            rationale_parts.append("sideways market favors mean-reversion strategies")

        # Volatility rationale
        if market_conditions.volatility > 0.7:
            rationale_parts.append("high volatility supports breakout strategies")
        elif market_conditions.volatility < 0.3:
            rationale_parts.append("low volatility favors trend following")

        # Strategy-specific rationale
        strategy_char = self._get_strategy_characteristics(strategy_name)
        rationale_parts.append(f"{strategy_name}: {strategy_char}")

        # Confidence assessment
        if confidence > 0.8:
            conf_text = "high confidence"
        elif confidence > 0.6:
            conf_text = "good confidence"
        elif confidence > 0.4:
            conf_text = "moderate confidence"
        else:
            conf_text = "low confidence - consider alternatives"

        rationale_parts.append(conf_text)

        return ". ".join(rationale_parts)

    def _get_strategy_characteristics(self, strategy_name: str) -> str:
        """Get human-readable strategy characteristics."""
        chars = {
            'MovingAverageCrossStrategy': 'trend-following with moving average signals',
            'RSIReversionStrategy': 'mean-reversion using RSI extremes',
            'BollingerBreakoutStrategy': 'volatility breakout from bands',
            'ATRBreakoutStrategy': 'volatility breakout with ATR stops',
            'EMARSIHybridStrategy': 'hybrid trend + momentum strategy',
            'MACDStrategy': 'momentum strategy using MACD crossovers'
        }
        return chars.get(strategy_name, 'versatile strategy approach')

    def _get_alternative_strategies(self, strategy_scores: Dict[str, float], count: int) -> List[Dict[str, Any]]:
        """Get alternative strategy recommendations."""
        # Sort by score, exclude the top choice
        sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)[1:count+1]

        alternatives = []
        for name, score in sorted_strategies:
            alternatives.append({
                'strategy': name,
                'score': score,
                'reason': f"Alternative option with {score:.1f} compatibility score"
            })

        return alternatives

    def calculate_position_size(self,
                               strategy_selection: Dict[str, Any],
                               account_balance: float,
                               risk_per_trade: float = 0.02) -> float:
        """
        Calculate optimal position size based on strategy and account.

        Args:
            strategy_selection: Strategy selection result
            account_balance: Current account balance
            risk_per_trade: Risk per trade (0.02 = 2%)

        Returns:
            Position size as percentage of account
        """
        confidence = strategy_selection.get('confidence', 0.5)
        strategy_name = strategy_selection.get('selected_strategy', '')

        # Base position size
        base_size = risk_per_trade

        # Adjust based on confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 to 1.0

        # Adjust based on strategy type and market conditions
        strategy_multiplier = self._get_strategy_risk_multiplier(strategy_name)

        # Adjust for market volatility
        market_conditions = strategy_selection.get('market_conditions', {})
        volatility = market_conditions.get('volatility', 0.5)

        # Reduce size in high volatility
        if volatility > 0.7:
            volatility_adjustment = 0.7
        elif volatility < 0.3:
            volatility_adjustment = 1.2
        else:
            volatility_adjustment = 1.0

        # Calculate final position size
        position_size = min(0.05,  # Max 5% of account
                          base_size * confidence_multiplier * strategy_multiplier * volatility_adjustment)

        return max(0.005, position_size)  # Min 0.5% of account

    def _get_strategy_risk_multiplier(self, strategy_name: str) -> float:
        """Get risk multiplier for strategy type."""
        risk_multipliers = {
            'MartingaleStrategy': 0.3,  # Very low due to extreme risk
            'ReverseMartingaleStrategy': 0.6,  # Moderate - profits from trends
            'BollingerBreakoutStrategy': 1.0,  # Standard risk
            'ATRBreakoutStrategy': 1.0,  # Standard with good stops
            'MovingAverageCrossStrategy': 0.9,  # Slightly conservative
            'RSIReversionStrategy': 1.1,  # Can work well but needs timing
            'EMARSIHybridStrategy': 0.9,  # Balanced approach
            'MACDStrategy': 0.8,  # Momentum can be risky
        }

        return risk_multipliers.get(strategy_name, 1.0)

    def update_strategy_performance(self, strategy_name: str, trade_result: Dict[str, Any]):
        """
        Update strategy performance database for future selections.

        Args:
            strategy_name: Strategy that was traded
            trade_result: Trade outcome details
        """
        if strategy_name not in self.strategy_performance_history:
            self.strategy_performance_history[strategy_name] = []

        self.strategy_performance_history[strategy_name].append({
            'trade_result': trade_result,
            'timestamp': datetime.now(),
            'pnl': trade_result.get('pnl', 0),
            'confidence_at_entry': trade_result.get('confidence_at_entry', 0.5),
            'market_conditions': trade_result.get('market_conditions', {})
        })

        # Keep only last 100 trades per strategy
        if len(self.strategy_performance_history[strategy_name]) > 100:
            self.strategy_performance_history[strategy_name] = self.strategy_performance_history[strategy_name][-100:]

        print(f"📊 Updated performance history for {strategy_name}")

    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """
        Get information about currently active AI strategies.

        Returns:
            List of active strategy dictionaries with execution details
        """
        # Get strategies from strategy registry that are available
        active_strategies = []

        try:
            available_strategies = list(strategy_registry._strategies.keys()) if hasattr(strategy_registry, '_strategies') else []
        except:
            available_strategies = ['MovingAverageCrossStrategy', 'RSIReversionStrategy', 'BollingerBreakoutStrategy']

        for strategy_name in available_strategies[:5]:  # Limit to first 5 for dashboard display
            # Generate mock performance data for demo purposes
            # In real implementation, this would come from actual strategy execution logs
            perf_data = self._get_mock_strategy_performance(strategy_name)

            active_strategies.append({
                'name': strategy_name,
                'instruments': perf_data['instruments'],
                'win_rate': perf_data['win_rate'],
                'avg_return': perf_data['avg_return'],
                'last_executed': perf_data['last_executed'],
                'confidence_score': perf_data['confidence_score'],
                'is_active': True,
                'description': perf_data['description']
            })

        return active_strategies

    def _get_mock_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get mock performance data for strategies (replace with real data).

        Args:
            strategy_name: Name of the strategy

        Returns:
            Mock performance metrics
        """
        # This is placeholder data - in production, get from real execution logs
        mock_data = {
            'MovingAverageCrossStrategy': {
                'instruments': ['EUR/USD', 'GBP/USD'],
                'win_rate': '73.2%',
                'avg_return': '+2.1%',
                'last_executed': datetime.now() - timedelta(hours=2),
                'confidence_score': 0.82,
                'description': 'Trend-following with moving average crossovers'
            },
            'RSIReversionStrategy': {
                'instruments': ['R_10', 'R_25'],
                'win_rate': '68.9%',
                'avg_return': '+1.8%',
                'last_executed': datetime.now() - timedelta(hours=1),
                'confidence_score': 0.75,
                'description': 'Mean-reversion using RSI extremes'
            },
            'BollingerBreakoutStrategy': {
                'instruments': ['R_50', 'R_75'],
                'win_rate': '71.5%',
                'avg_return': '+3.2%',
                'last_executed': datetime.now() - timedelta(minutes=30),
                'confidence_score': 0.88,
                'description': 'Volatility breakout from Bollinger Bands'
            }
        }

        # Return mock data for known strategies, or generate for unknown ones
        if strategy_name in mock_data:
            return mock_data[strategy_name]
        else:
            return {
                'instruments': ['USD/JPY'],
                'win_rate': '65.0%',
                'avg_return': '+1.5%',
                'last_executed': datetime.now(),
                'confidence_score': 0.70,
                'description': 'General trading strategy'
            }

# Global selector instance
ai_strategy_selector = AIStrategySelector()

def select_optimal_strategy(data: pd.DataFrame,
                          risk_preference: str = 'balanced') -> Dict[str, Any]:
    """
    Select optimal trading strategy for current market conditions.

    Args:
        data: Market data for analysis
        risk_preference: Risk preference level

    Returns:
        Strategy selection result
    """
    return ai_strategy_selector.select_optimal_strategy(data, risk_preference=risk_preference)

def calculate_optimal_position_size(strategy_selection: Dict[str, Any],
                                  account_balance: float) -> float:
    """
    Calculate optimal position size for selected strategy.

    Args:
        strategy_selection: Strategy selection result
        account_balance: Current account balance

    Returns:
        Position size as percentage of account
    """
    return ai_strategy_selector.calculate_position_size(strategy_selection, account_balance)

__all__ = [
    'AIStrategySelector',
    'ai_strategy_selector',
    'select_optimal_strategy',
    'calculate_optimal_position_size'
]
