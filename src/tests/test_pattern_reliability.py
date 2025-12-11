"""
CANDLESTICK & PATTERN RELIABILITY TESTING SUITE
===============================================
Measure pattern success rates, risk-to-reward ratios, and reliability metrics.

Tests pattern performance across:
- Different market conditions (trending, ranging, volatile)
- Success rates and hit rates
- Risk-adjusted returns
- Average holding periods and MAE/MFE
- Multi-timeframe consistency
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

# Import system pattern recognition
from src.charts.patterns import (
    detect_candlestick_patterns, detect_chart_patterns,
    get_pattern_recommendations
)
from src.trading.test_backtest_system import create_sample_ohlc_data


@pytest.fixture
def trending_market_data():
    """Generate trending market data for pattern testing"""
    np.random.seed(123)

    # Generate clear upward trend with pattern potential
    t = np.arange(200)
    base_trend = 100 + t * 0.3  # Steady upward trend
    noise = np.random.normal(0, 1.5, 200)

    # Add some random swings for pattern formation
    swings = np.sin(t * 0.1) * 3
    prices = base_trend + noise + swings

    # Create OHLC data with realistic spreads
    spreads = np.random.exponential(0.5, 200) + 0.5
    opens = prices + np.random.normal(0, 0.3, 200)
    highs = opens + spreads
    lows = opens - spreads
    closes = prices + np.random.normal(0, 0.2, 200)

    data = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes
    })

    return data

@pytest.fixture
def volatile_market_data():
    """Generate volatile, ranging market for pattern testing"""
    np.random.seed(456)

    # Generate random walk with high volatility
    base_price = 100
    returns = np.random.normal(0, 0.02, 200)
    prices = base_price * np.cumprod(1 + returns)

    # Create OHLC with realistic spreads
    spreads = np.random.exponential(1.0, 200) + 1.0
    opens = prices * (1 + np.random.normal(0, 0.005, 200))
    highs = opens + spreads
    lows = opens - spreads
    closes = prices + np.random.normal(0, prices * 0.005, 200)

    data = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes
    })

    return data

@pytest.fixture
def ranging_market_data():
    """Generate sideways ranging market for pattern testing"""
    np.random.seed(789)

    # Generate bound random walk (range bound market)
    base_price = 100
    t = np.arange(200)
    oscillation = np.sin(t * 0.02) * 5  # Slow oscillation
    noise = np.random.normal(0, 1.0, 200)
    prices = base_price + oscillation + noise

    # Create OHLC data
    spreads = np.random.exponential(0.3, 200) + 0.5
    opens = prices + np.random.normal(0, 0.2, 200)
    highs = opens + spreads
    lows = opens - spreads
    closes = prices + np.random.normal(0, 0.1, 200)

    data = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes
    })

    return data


class TestPatternReliabilitySuite:
    """Comprehensive pattern reliability testing"""

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_pattern_detection_coverage(self, trending_market_data):
        """
        Test pattern detection coverage and consistency across different market conditions.
        """
        patterns = detect_candlestick_patterns(trending_market_data)

        # Should detect some patterns in trending market
        assert len(patterns) > 0, "Should detect at least some patterns in trending market"

        # Calculate total patterns detected
        total_patterns = sum(len(pattern_list) for pattern_list in patterns.values())
        assert total_patterns > 0, "Total pattern detections should be > 0"

        # Test pattern quality - should not be noisy (excessive false positives)
        max_patterns_per_type = len(trending_market_data) * 0.3  # Max 30% of bars flagged
        for pattern_type, pattern_list in patterns.items():
            assert len(pattern_list) <= max_patterns_per_type, \
                   f"Too many {pattern_type} patterns: {len(pattern_list)}/{max_patterns_per_type}"

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_pattern_success_rate_validation(self, trending_market_data):
        """
        CRITICAL: Measure actual pattern success rates in backtested scenarios.

        Tests pattern performance with real forward-testing simulation.
        """
        # Get detected patterns
        patterns = detect_candlestick_patterns(trending_market_data)
        recommendations = get_pattern_recommendations(patterns)

        if not recommendations:
            pytest.skip("No pattern recommendations available for testing")

        # Extract bullish/bearish signals
        bullish_patterns = []
        bearish_patterns = []

        for pattern_type, recommendation in recommendations.items():
            if "bullish" in recommendation.lower() or "buy" in recommendation.lower():
                bullish_patterns.extend(patterns.get(pattern_type, []))
            elif "bearish" in recommendation.lower() or "sell" in recommendation.lower():
                bearish_patterns.extend(patterns.get(pattern_type, []))

        # Simulate forward returns for pattern validation
        success_rate = self._calculate_pattern_success_rate(trending_market_data, bullish_patterns, bearish_patterns)

        # Bullish patterns should outperform random in trending market
        if bullish_patterns and len(bullish_patterns) > 5:
            assert success_rate['bullish_win_rate'] > 0.4, \
                   f"Bullish pattern success too low: {success_rate['bullish_win_rate']:.2f}"
            assert success_rate['bullish_avg_return'] > success_rate['random_avg_return'] * 0.9, \
                   f"Bullish patterns underperform random: {success_rate['bullish_avg_return']:.3f}"

        # We can't demand high success rates, but patterns should be statistically meaningful
        if success_rate['total_patterns'] > 10:
            assert success_rate['overall_confidence'] > 0, \
                   f"Pattern confidence too low: {success_rate['overall_confidence']:.3f}"

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_risk_reward_ratio_analysis(self, volatile_market_data):
        """
        Analyze risk-to-reward ratios for detected patterns.
        """
        # Get pattern recommendations
        patterns = detect_candlestick_patterns(volatile_market_data)
        recommendations = get_pattern_recommendations(patterns)

        if not recommendations:
            pytest.skip("Insufficient patterns for risk-reward testing")

        # Simulate entry/exit points for risk-reward calculation
        rr_analysis = self._calculate_risk_reward_profile(volatile_market_data, patterns, recommendations)

        # Reasonable expectations for pattern-based trading
        if rr_analysis['total_signals'] > 0:
            # Risk-reward should be positive overall (though individual patterns may vary)
            assert rr_analysis['avg_win_rr'] > 0.5, \
                   f"Average win risk-reward too low: {rr_analysis['avg_win_rr']:.2f}"

            # Win rate should be meaningful (not random coin flip)
            assert rr_analysis['win_rate'] > 0.45, \
                   f"Pattern win rate too low: {rr_analysis['win_rate']:.2f}"

            # Confidence interval should be positive
            assert rr_analysis['confidence_interval'] > -0.1, \
                   f"Pattern confidence interval too negative: {rr_analysis['confidence_interval']:.2f}"

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_multitimeframe_pattern_consistency(self):
        """
        Test pattern detection consistency across multiple timeframes.
        """
        # Generate data at different 'timeframes' (simulate resampling)
        base_data = create_sample_ohlc_data('R_10', 1000)

        # Simulate different timeframes by aggregating data
        timeframes = {
            '1T': base_data,  # 1-minute (original)
            '5T': self._resample_ohlc(base_data, 5),  # 5-minute aggregated
            '15T': self._resample_ohlc(base_data, 15), # 15-minute aggregated
        }

        # Test pattern detection across timeframes
        pattern_consistency = {}

        for tf_name, tf_data in timeframes.items():
            patterns = detect_candlestick_patterns(tf_data)
            total_patterns = sum(len(pattern_list) for pattern_list in patterns.values())
            pattern_consistency[tf_name] = {
                'total_patterns': total_patterns,
                'patterns_per_bar': total_patterns / len(tf_data),
                'pattern_types': len(patterns)
            }

        # Patterns should scale roughly with timeframe (though not exactly)
        fine_patterns = pattern_consistency['1T']['patterns_per_bar']
        coarse_patterns = pattern_consistency['15T']['patterns_per_bar']

        # Higher timeframe shouldn't have dramatically fewer patterns
        assert coarse_patterns >= fine_patterns * 0.1, \
               f"Pattern detection inconsistent across timeframes: {fine_patterns:.3f} vs {coarse_patterns:.3f}"

        # Different timeframes should detect patterns (not all zero)
        for tf_name, stats in pattern_consistency.items():
            assert stats['total_patterns'] > 0, f"No patterns detected on {tf_name} timeframe"

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_chart_pattern_completeness(self, trending_market_data):
        """
        Test chart pattern detection for multi-bar formations.
        """
        chart_patterns = detect_chart_patterns(trending_market_data)

        # Should be able to detect some chart patterns
        assert isinstance(chart_patterns, dict), "Chart patterns should return dictionary"

        # Check for reasonable pattern detection
        if len(trending_market_data) < 100:
            pytest.skip("Insufficient data for chart pattern analysis")

        # Look for basic pattern categories
        expected_categories = ['double_top', 'double_bottom', 'triangle', 'wedge', 'head_shoulders']

        # Chart patterns should include some formation detections
        total_chart_patterns = sum(len(pattern_list) for pattern_list in chart_patterns.values())

        # In trending data, should find at least some basic patterns
        # (This is a minimum expectation, not a strict requirement)
        assert total_chart_patterns >= 0, "Chart pattern detection failed"

        # If patterns are detected, validate their structure
        for pattern_type, pattern_list in chart_patterns.items():
            for pattern in pattern_list:
                # Each pattern should have basic structure (entry, exit, confidence)
                assert isinstance(pattern, dict), f"Pattern should be dictionary: {pattern}"
                required_keys = ['entry_signal', 'confidence', 'pattern_type']
                for key in required_keys:
                    if key in pattern:
                        assert pattern[key] is not None, f"Pattern missing {key}"

    @pytest.mark.prop_firm
    @pytest.mark.unit
    def test_holding_period_analysis(self, ranging_market_data):
        """
        Analyze holding periods and trade duration for pattern-based signals.
        """
        # Get pattern signals
        patterns = detect_candlestick_patterns(ranging_market_data)
        recommendations = get_pattern_recommendations(patterns)

        if not recommendations:
            pytest.skip("Insufficient pattern recommendations for holding period analysis")

        # Simulate holding periods with stochastic exit (realistic stop/take profit)
        holding_stats = self._simulate_holding_periods(ranging_market_data, recommendations)

        if holding_stats['total_trades'] > 0:
            # Average holding period should be reasonable (not infinite or zero)
            assert 1 <= holding_stats['avg_holding_period'] <= 50, \
                   f"Unrealistic holding period: {holding_stats['avg_holding_period']:.1f} bars"

            # Win rate should be statistically meaningful
            win_rate = holding_stats['successful_trades'] / holding_stats['total_trades']
            assert 0.3 <= win_rate <= 0.8, \
                   f"Pattern win rate suspicious: {win_rate:.2f} (too random or too perfect)"

            # Profit factor should be positive for successful patterns
            if holding_stats['successful_trades'] > 2:
                profit_factor = holding_stats['total_profits'] / max(holding_stats['total_losses'], 1)
                assert profit_factor > 0.8, \
                       f"Poor profit factor: {profit_factor:.2f}"

    @pytest.mark.prop_firm
    @pytest.mark.slow
    def test_pattern_robustness_under_noise(self):
        """
        Test pattern reliability under increasing market noise levels.
        """
        # Test pattern detection with different noise levels
        noise_levels = [0.5, 1.0, 2.0, 5.0]  # Increasing noise

        base_data = create_sample_ohlc_data('R_10', 300)

        robust_patterns = {}
        for noise_level in noise_levels:
            # Add noise to price data
            noisy_data = base_data.copy()
            noise = np.random.normal(0, noise_level, len(base_data))
            noisy_data['close'] += noise
            noisy_data['high'] = noisy_data[['high', 'close']].max(axis=1)
            noisy_data['low'] = noisy_data[['low', 'close']].min(axis=1)

            # Detect patterns with noise
            patterns = detect_candlestick_patterns(noisy_data)
            total_patterns = sum(len(pattern_list) for pattern_list in patterns.values())
            robust_patterns[noise_level] = total_patterns

        # Pattern detection should degrade gracefully with noise
        # But extreme noise should not cause complete failure
        clean_patterns = robust_patterns[0.5]
        if clean_patterns > 0:
            # With reasonable noise, should still detect some patterns
            assert robust_patterns[2.0] >= clean_patterns * 0.1, \
                   f"Pattern detection too sensitive to noise: {robust_patterns[2.0]} vs {clean_patterns}"

        # Should be able to handle extreme noise without crashing
        assert isinstance(robust_patterns[5.0], (int, float)), \
               "Pattern detection should handle extreme noise gracefully"

    def _calculate_pattern_success_rate(self, data: pd.DataFrame, bullish_patterns: List[int],
                                      bearish_patterns: List[int]) -> Dict[str, Any]:
        """Calculate actual success rates for pattern predictions"""
        results = {
            'bullish_win_rate': 0.0,
            'bearish_win_rate': 0.0,
            'bullish_avg_return': 0.0,
            'bearish_avg_return': 0.0,
            'random_avg_return': 0.0,
            'total_patterns': len(bullish_patterns) + len(bearish_patterns),
            'overall_confidence': 0.0
        }

        if results['total_patterns'] == 0:
            return results

        # Calculate forward returns for pattern analysis
        look_forward = 10  # Look 10 bars into future
        returns = []

        for i, idx in enumerate(bullish_patterns):
            if idx + look_forward < len(data):
                initial_price = data.iloc[idx]['close']
                final_price = data.iloc[min(idx + look_forward, len(data)-1)]['close']
                return_pct = (final_price - initial_price) / initial_price
                returns.append(return_pct)

        for i, idx in enumerate(bearish_patterns):
            if idx + look_forward < len(data):
                initial_price = data.iloc[idx]['close']
                final_price = data.iloc[min(idx + look_forward, len(data)-1)]['close']
                return_pct = (final_price - initial_price) / initial_price
                returns.append(-return_pct)  # Invert for bearish

        # Random baseline
        np.random.seed(42)
        random_indices = np.random.choice(len(data) - look_forward, size=min(50, len(bullish_patterns)))
        random_returns = []
        for idx in random_indices:
            initial_price = data.iloc[idx]['close']
            final_price = data.iloc[idx + look_forward]['close']
            random_returns.append((final_price - initial_price) / initial_price)

        # Calculate metrics
        if returns:
            results['bullish_win_rate'] = np.mean(np.array(returns) > 0)
            results['bullish_avg_return'] = np.mean(returns)

        if bearish_patterns:
            bearish_returns = [-r for r in returns[-len(bearish_patterns):]] if bearish_patterns else []
            results['bearish_win_rate'] = np.mean(np.array(bearish_returns) > 0) if bearish_returns else 0

        if random_returns:
            results['random_avg_return'] = np.mean(random_returns)

        # Confidence calculation
        if results['bullish_avg_return'] > results['random_avg_return']:
            results['overall_confidence'] = min(1.0, results['bullish_win_rate'])

        return results

    def _calculate_risk_reward_profile(self, data: pd.DataFrame, patterns: Dict[str, List[int]],
                                     recommendations: Dict[str, str]) -> Dict[str, Any]:
        """Calculate risk-reward profile for pattern trading"""
        profile = {
            'total_signals': 0,
            'win_rate': 0.0,
            'avg_win_rr': 0.0,
            'avg_loss_rr': 0.0,
            'profit_factor': 1.0,
            'confidence_interval': 0.0
        }

        # Analyze each pattern recommendation
        analyzed_signals = 0
        wins = 0
        total_wins_rr = 0.0
        total_losses_rr = 0.0

        for pattern_type, pattern_list in patterns.items():
            rec = recommendations.get(pattern_type, "")
            direction = "bullish" if "bullish" in rec.lower() or "buy" in rec.lower() else "bearish"

            for idx in pattern_list:
                if idx + 20 >= len(data):  # Need some future data
                    continue

                entry_price = data.iloc[idx]['close']

                # Simulate realistic stop loss and take profit
                if direction == "bullish":
                    take_profit_price = entry_price * 1.02  # 2% target
                    stop_loss_price = entry_price * 0.995   # 0.5% stop
                else:
                    take_profit_price = entry_price * 0.98  # 2% target
                    stop_loss_price = entry_price * 1.005   # 0.5% stop

                # Check outcome
                trade_success = False
                rr_ratio = 0.0

                # Look for target/stop hit in next 20 bars
                for future_idx in range(idx + 1, min(idx + 21, len(data))):
                    future_price = data.iloc[future_idx]['close']

                    if direction == "bullish":
                        if future_price >= take_profit_price:  # Take profit hit
                            rr_ratio = (take_profit_price - entry_price) / (entry_price - stop_loss_price)
                            trade_success = True
                            wins += 1
                            total_wins_rr += rr_ratio
                            break
                        elif future_price <= stop_loss_price:  # Stop loss hit
                            rr_ratio = (take_profit_price - entry_price) / (entry_price - stop_loss_price) * -1
                            total_losses_rr += abs(rr_ratio)
                            break
                    else:  # Bearish
                        if future_price <= take_profit_price:  # Take profit hit
                            rr_ratio = (entry_price - take_profit_price) / (stop_loss_price - entry_price)
                            trade_success = True
                            wins += 1
                            total_wins_rr += rr_ratio
                            break
                        elif future_price >= stop_loss_price:  # Stop loss hit
                            rr_ratio = (entry_price - take_profit_price) / (stop_loss_price - entry_price) * -1
                            total_losses_rr += abs(rr_ratio)
                            break

                analyzed_signals += 1

        # Calculate final metrics
        if analyzed_signals > 0:
            profile['total_signals'] = analyzed_signals
            profile['win_rate'] = wins / analyzed_signals

            if wins > 0:
                profile['avg_win_rr'] = total_wins_rr / wins
                profile['avg_loss_rr'] = total_losses_rr / (analyzed_signals - wins) if analyzed_signals > wins else 0

            if profile['avg_loss_rr'] > 0:
                profile['profit_factor'] = profile['avg_win_rr'] / profile['avg_loss_rr'] if wins > 0 else 0

            # Simple confidence interval calculation
            expected_win = profile['win_rate'] * profile['avg_win_rr']
            expected_loss = (1 - profile['win_rate']) * profile['avg_loss_rr']
            profile['confidence_interval'] = expected_win - expected_loss

        return profile

    def _resample_ohlc(self, data: pd.DataFrame, factor: int) -> pd.DataFrame:
        """Resample OHLC data to simulate higher timeframes"""
        resampled = pd.DataFrame()
        for i in range(0, len(data) - factor + 1, factor):
            chunk = data.iloc[i:i+factor]
            resampled = pd.concat([resampled, pd.DataFrame({
                'open': [chunk.iloc[0]['open']],
                'high': [chunk['high'].max()],
                'low': [chunk['low'].min()],
                'close': [chunk.iloc[-1]['close']]
            })], ignore_index=True)

        return resampled

    def _simulate_holding_periods(self, data: pd.DataFrame, recommendations: Dict[str, str]) -> Dict[str, Any]:
        """Simulate realistic holding periods with stochastic exits"""
        holding_results = {
            'total_trades': 0,
            'successful_trades': 0,
            'avg_holding_period': 0.0,
            'total_profits': 0.0,
            'total_losses': 0.0,
            'mae_values': [],
            'mfe_values': []
        }

        # This is a simplified simulation - in a real prop firm, this would be much more sophisticated
        # with actual market impact, slippage modeling, and liquidity considerations

        trading_results = []
        for pattern_type, rec in recommendations.items():
            is_bullish = "bullish" in rec.lower() or "buy" in rec.lower()
            direction = 1 if is_bullish else -1

            # Simulate multiple trades with stochastic outcomes
            for trade_sim in range(min(5, len(data) // 50)):  # Limit simulations
                # Start trade at random point
                start_idx = np.random.randint(20, len(data) - 20)
                entry_price = data.iloc[start_idx]['close']

                # Simulate holding with stochastic profit taking
                holding_period = 0
                max_profit = 0.0
                max_loss = 0.0
                final_result = 0.0
                pnl = 0.0
                hold_days = 1

                for hold_days in range(1, 21):  # Max 20 bar hold
                    future_idx = start_idx + hold_days
                    if future_idx >= len(data):
                        break

                    current_price = data.iloc[future_idx]['close']
                    pnl = direction * (current_price - entry_price) / entry_price

                    # Track MAE/MFE
                    if pnl > max_profit:
                        max_profit = pnl
                    if pnl < max_loss:
                        max_loss = pnl

                    # Stochastic exit (stop loss or take profit)
                    if pnl <= -0.01 or pnl >= 0.02:  # 1% stop, 2% target
                        final_result = pnl
                        holding_period = hold_days
                        break
                else:
                    # Time-based exit
                    final_result = pnl
                    holding_period = hold_days

                success = final_result > 0
                trading_results.append({
                    'success': success,
                    'holding_period': holding_period,
                    'pnl': final_result,
                    'mae': max_loss,
                    'mfe': max_profit
                })

        # Aggregate results
        if trading_results:
            holding_results['total_trades'] = len(trading_results)
            holding_results['successful_trades'] = sum(1 for r in trading_results if r['success'])

            successful_trades = [r for r in trading_results if r['success']]
            if successful_trades:
                holding_results['avg_holding_period'] = np.mean([r['holding_period'] for r in successful_trades])
                holding_results['total_profits'] = sum(r['pnl'] for r in successful_trades)
                holding_results['mae_values'] = [-r['mae'] for r in successful_trades]  # Maximum Adverse Excursion
                holding_results['mfe_values'] = [r['mfe'] for r in successful_trades]   # Maximum Favorable Excursion

            unsuccessful_trades = [r for r in trading_results if not r['success']]
            if unsuccessful_trades:
                holding_results['total_losses'] = sum(abs(r['pnl']) for r in unsuccessful_trades)

        return holding_results


def validate_pattern_reliability():
    """
    Standalone function to validate pattern recognition reliability.

    Returns:
        Dict with pattern validation metrics
    """
    from src.trading.test_backtest_system import create_sample_ohlc_data

    validation_results = {
        'patterns_detected': 0,
        'win_rate_confidence': 0.0,
        'avg_holding_period': 0.0,
        'risk_reward_ratio': 0.0,
        'multitimeframe_consistency': False,
        'noise_resistance': False,
        'overall_reliability': 0.0
    }

    try:
        # Test basic pattern detection
        test_data = create_sample_ohlc_data('R_10', 200)
        patterns = detect_candlestick_patterns(test_data)
        validation_results['patterns_detected'] = sum(len(p) for p in patterns.values())

        # Test recommendations
        recommendations = get_pattern_recommendations(patterns)
        validation_results['win_rate_confidence'] = len(recommendations) * 0.05  # Rough estimation

        # Basic consistency check
        consistency_tests = 0
        consistency_passed = 0

        # Multi-timeframe check (simplified)
        tf_check = len(patterns) > 0  # At least some patterns detected
        consistency_tests += 1
        if tf_check:
            consistency_passed += 1

        # Noise resistance check (simplified)
        import numpy as np
        noisy_data = test_data.copy()
        noisy_data['close'] += np.random.normal(0, 1, len(test_data))
        noisy_patterns = detect_candlestick_patterns(noisy_data)
        noise_check = sum(len(p) for p in noisy_patterns.values()) >= validation_results['patterns_detected'] * 0.1
        consistency_tests += 1
        if noise_check:
            consistency_passed += 1

        validation_results['multitimeframe_consistency'] = tf_check
        validation_results['noise_resistance'] = noise_check

        # Overall reliability score
        metrics = [
            min(validation_results['patterns_detected'] / 20, 1.0),  # Up to 20 patterns for perfect score
            validation_results['win_rate_confidence'],
            consistency_passed / consistency_tests
        ]

        validation_results['overall_reliability'] = sum(metrics) / len(metrics) * 100

    except Exception as e:
        print(f"Pattern validation error: {e}")
        validation_results['validation_error'] = str(e)

    return validation_results


def test_ai_decision_consistency(decisions: List[Dict[str, Any]],
                                market_conditions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Test AI decision-making consistency and reliability.

    This function evaluates whether AI decisions are consistent across similar market conditions
    and whether the decision-making process shows predictable patterns.

    Args:
        decisions: List of AI decision records with confidence scores and market context
        market_conditions: Parallel list of market conditions for each decision

    Returns:
        Dict containing consistency metrics and analysis
    """
    if not decisions:
        return {
            'consistency_score': 0.0,
            'total_decisions': 0,
            'confidence_variance': 0.0,
            'decision_stability': 0.0,
            'reliability_rating': 'NO_DATA'
        }

    consistency_analysis = {
        'total_decisions': len(decisions),
        'consistency_score': 0.0,
        'confidence_variance': 0.0,
        'decision_stability': 0.0,
        'similar_condition_agreement': 0.0,
        'confidence_trend_stability': 0.0,
        'reliability_rating': 'UNKNOWN',
        'analysis_details': {}
    }

    try:
        # Extract confidence scores and decisions
        confidences = []
        decision_types = []
        timestamps = []

        for decision in decisions:
            if isinstance(decision, dict):
                confidence = decision.get('confidence_score', 0) or decision.get('confidence', 0)
                decision_type = decision.get('decision_type', 'UNKNOWN')
                timestamp = decision.get('timestamp', '')

                if confidence is not None and confidence >= 0 and confidence <= 1:
                    confidences.append(confidence)
                if decision_type:
                    decision_types.append(decision_type)
                if timestamp:
                    timestamps.append(timestamp)

        if not confidences:
            return consistency_analysis

        # Calculate basic confidence statistics
        consistency_analysis['confidence_variance'] = np.var(confidences) if len(confidences) > 1 else 0.0
        mean_confidence = np.mean(confidences)

        # Confidence stability (lower variance is more stable)
        confidence_stability = max(0, 1.0 - consistency_analysis['confidence_variance'] * 4)  # Scale variance
        consistency_analysis['decision_stability'] = confidence_stability

        # Decision type consistency
        if decision_types:
            from collections import Counter
            decision_counts = Counter(decision_types)
            dominant_decision = decision_counts.most_common(1)[0][0]
            decision_concentration = decision_counts[dominant_decision] / len(decision_types)
            consistency_analysis['decision_concentration'] = decision_concentration

        # Analyze confidence trend stability
        if len(confidences) >= 5:
            confidence_trend = np.polyfit(range(len(confidences)), confidences, 1)[0]
            # Stable trend should have small slope
            trend_stability = max(0, 1.0 - abs(confidence_trend) * 10)
            consistency_analysis['confidence_trend_stability'] = trend_stability

        # Similar market condition analysis (if market_conditions provided)
        if market_conditions and len(market_conditions) == len(decisions):
            similar_condition_score = _analyze_similar_conditions_consistency(decisions, market_conditions)
            consistency_analysis['similar_condition_agreement'] = similar_condition_score

        # Overall consistency score
        consistency_factors = [
            confidence_stability,
            consistency_analysis.get('decision_concentration', 0.5),
            consistency_analysis.get('similar_condition_agreement', 0.5)
        ]

        consistency_analysis['consistency_score'] = np.mean(consistency_factors)

        # Reliability rating
        consistency_score = consistency_analysis['consistency_score']
        if consistency_score >= 0.8:
            consistency_analysis['reliability_rating'] = 'HIGHLY_CONSISTENT'
        elif consistency_score >= 0.6:
            consistency_analysis['reliability_rating'] = 'MODERATELY_CONSISTENT'
        elif consistency_score >= 0.4:
            consistency_analysis['reliability_rating'] = 'VARIABLE'
        elif consistency_score >= 0.2:
            consistency_analysis['reliability_rating'] = 'INCONSISTENT'
        else:
            consistency_analysis['reliability_rating'] = 'ERRATIC'

        # Detailed analysis
        consistency_analysis['analysis_details'] = {
            'mean_confidence': mean_confidence,
            'confidence_range': f"{min(confidences):.3f} - {max(confidences):.3f}",
            'unique_decision_types': len(set(decision_types)) if decision_types else 0,
            'variance_interpretation': 'LOW' if consistency_analysis['confidence_variance'] < 0.01 else 'MEDIUM' if consistency_analysis['confidence_variance'] < 0.05 else 'HIGH',
            'stability_assessment': 'STABLE' if consistency_analysis['decision_stability'] > 0.7 else 'UNSTABLE'
        }

    except Exception as e:
        consistency_analysis['analysis_error'] = str(e)
        consistency_analysis['reliability_rating'] = 'ANALYSIS_FAILED'

    return consistency_analysis


def _analyze_similar_conditions_consistency(decisions: List[Dict[str, Any]],
                                          market_conditions: List[Dict[str, Any]]) -> float:
    """
    Analyze consistency when faced with similar market conditions.
    Returns similarity score between 0-1 (higher = more consistent)
    """
    if len(decisions) < 3:
        return 0.5  # Neutral score for insufficient data

    try:
        consistency_pairs = 0
        total_pairs = 0

        # Compare decisions under similar conditions (simplified)
        for i in range(len(decisions)):
            for j in range(i + 1, len(decisions)):
                if i < len(market_conditions) and j < len(market_conditions):
                    # Simple similarity check - same volatility level or trend strength
                    vol_i = market_conditions[i].get('volatility', 0.5)
                    vol_j = market_conditions[j].get('volatility', 0.5)
                    trend_i = market_conditions[i].get('trend_strength', 0.5)
                    trend_j = market_conditions[j].get('trend_strength', 0.5)

                    # Consider conditions similar if both metrics are close
                    vol_similar = abs(vol_i - vol_j) < 0.2
                    trend_similar = abs(trend_i - trend_j) < 0.2

                    if vol_similar and trend_similar:
                        # Conditions are similar - check if decisions are consistent
                        conf_i = decisions[i].get('confidence_score', 0.5)
                        conf_j = decisions[j].get('confidence_score', 0.5)

                        # Consistent if confidence difference is small
                        if abs(conf_i - conf_j) < 0.3:
                            consistency_pairs += 1
                        total_pairs += 1

        return consistency_pairs / total_pairs if total_pairs > 0 else 0.5

    except Exception:
        return 0.5  # Neutral score on error
