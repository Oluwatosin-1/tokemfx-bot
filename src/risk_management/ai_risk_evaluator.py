"""
AI Risk Evaluator
=================
AI-powered risk assessment and evaluation for trading operations.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AIRiskEvaluator:
    """
    AI-powered risk evaluator for trading operations.
    """

    def __init__(self):
        self.risk_thresholds = {
            'max_daily_loss': 5.0,
            'max_single_position': 10.0,
            'max_total_exposure': 100.0,
            'max_consecutive_losses': 5
        }

    def assess_overall_risk(self) -> Dict[str, Any]:
        """
        Assess overall trading risk using historical backtesting data.

        Returns:
            Risk assessment with levels and recommendations
        """
        try:
            # Get historical backtesting performance data
            backtest_summary = self._get_backtesting_risk_metrics()

            # Calculate risk metrics from historical data
            risk_metrics = self._calculate_historical_risk_metrics(backtest_summary)

            # Determine risk level based on historical performance
            risk_level = self._determine_risk_level(risk_metrics)

            # Generate dynamic recommendations
            recommendations = self._generate_risk_recommendations(risk_metrics, risk_level)

            assessment = {
                'risk_level': risk_level,
                'confidence_interval': risk_metrics.get('confidence_interval', 5.2),
                'daily_loss_limit': f"${risk_metrics.get('daily_loss_limit', 500):.2f}",
                'position_size_limit': f"${risk_metrics.get('position_size_limit', 1000):.2f}",
                'total_exposure_limit': f"${risk_metrics.get('total_exposure_limit', 10000):.2f}",
                'current_risk_score': risk_metrics.get('current_risk_score', 4.7),
                'backtest_based': True,
                'historical_data_points': backtest_summary.get('total_results', 0),
                'avg_sharpe_ratio': backtest_summary.get('average_sharpe', 0),
                'max_drawdown_avg': risk_metrics.get('max_drawdown_avg', 0),
                'recommendations': recommendations
            }
            return assessment
        except Exception as e:
            logger.error(f"Error assessing overall risk: {e}")
            # Fallback to basic assessment
            return {
                'risk_level': 'Medium',
                'confidence_interval': 5.2,
                'daily_loss_limit': '$500.00',
                'position_size_limit': '$1,000.00',
                'total_exposure_limit': '$10,000.00',
                'current_risk_score': 4.7,
                'backtest_based': False,
                'recommendations': [
                    'Monitor stop-loss levels closely',
                    'Consider reducing position sizes in volatile periods',
                    'Implement trailing stops for profitable trades'
                ]
            }

    def _get_backtesting_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics from historical backtesting results."""
        try:
            from src.backtesting.results import get_historical_performance_summary
            return get_historical_performance_summary(days=30)
        except Exception as e:
            logger.warning(f"Could not load backtesting risk metrics: {e}")
            return {'total_results': 0, 'average_sharpe': 0}

    def _calculate_historical_risk_metrics(self, backtest_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk metrics from historical backtesting data."""
        try:
            # Extract key metrics
            total_results = backtest_summary.get('total_results', 0)
            avg_sharpe = backtest_summary.get('average_sharpe', 0)
            portfolio_return = backtest_summary.get('portfolio_return', 0)

            # Calculate confidence interval based on historical volatility
            confidence_interval = 5.2  # Base value
            if total_results > 10:
                # Adjust confidence based on consistency of results
                confidence_interval = max(3.0, min(8.0, 5.2 + (avg_sharpe * 0.5)))

            # Calculate dynamic limits based on historical performance
            base_capital = 10000  # Assume $10k base

            # Daily loss limit: 5% of expected daily volatility
            daily_loss_limit = base_capital * 0.05 * max(0.5, min(2.0, 1.0 / max(0.1, abs(avg_sharpe))))

            # Position size limit: Based on Sharpe ratio and drawdown history
            position_size_limit = base_capital * 0.10 * max(0.5, min(1.5, avg_sharpe / 2.0))

            # Total exposure limit: Conservative multiple of position size
            total_exposure_limit = position_size_limit * 10

            # Current risk score: Lower is better (0-10 scale)
            risk_score = 5.0
            if avg_sharpe > 2.0:
                risk_score -= 1.0  # Good Sharpe reduces risk
            if portfolio_return > 10.0:
                risk_score -= 0.5  # Good returns reduce risk
            if total_results > 50:
                risk_score -= 0.5  # More data reduces uncertainty

            risk_score = max(1.0, min(9.0, risk_score))

            return {
                'confidence_interval': confidence_interval,
                'daily_loss_limit': daily_loss_limit,
                'position_size_limit': position_size_limit,
                'total_exposure_limit': total_exposure_limit,
                'current_risk_score': risk_score,
                'max_drawdown_avg': 8.5,  # Placeholder - would calculate from actual data
                'volatility_adjustment': max(0.5, min(1.5, 1.0 / max(0.1, abs(avg_sharpe)))),
                'data_confidence': min(1.0, total_results / 100.0)
            }

        except Exception as e:
            logger.error(f"Error calculating historical risk metrics: {e}")
            return {
                'confidence_interval': 5.2,
                'daily_loss_limit': 500,
                'position_size_limit': 1000,
                'total_exposure_limit': 10000,
                'current_risk_score': 4.7,
                'max_drawdown_avg': 8.5,
                'volatility_adjustment': 1.0,
                'data_confidence': 0.0
            }

    def _determine_risk_level(self, risk_metrics: Dict[str, Any]) -> str:
        """Determine overall risk level based on metrics."""
        risk_score = risk_metrics.get('current_risk_score', 5.0)
        data_confidence = risk_metrics.get('data_confidence', 0.0)

        # Adjust risk level based on data confidence
        if data_confidence < 0.3:
            # Low confidence in data, be more conservative
            risk_score += 0.5

        if risk_score < 3.5:
            return 'Low'
        elif risk_score < 6.5:
            return 'Medium'
        else:
            return 'High'

    def _generate_risk_recommendations(self, risk_metrics: Dict[str, Any], risk_level: str) -> List[str]:
        """Generate dynamic risk recommendations based on historical data."""
        recommendations = []

        risk_score = risk_metrics.get('current_risk_score', 5.0)
        avg_sharpe = risk_metrics.get('avg_sharpe_ratio', 0)
        data_confidence = risk_metrics.get('data_confidence', 0.0)

        # Base recommendations
        if risk_level == 'Low':
            recommendations.extend([
                'Current risk profile is favorable for increased exposure',
                'Consider scaling up position sizes within defined limits',
                'Monitor for changes in market volatility'
            ])
        elif risk_level == 'Medium':
            recommendations.extend([
                'Maintain current risk management protocols',
                'Regular portfolio rebalancing recommended',
                'Monitor stop-loss levels closely'
            ])
        else:  # High risk
            recommendations.extend([
                'URGENT: Reduce position sizes immediately',
                'Implement stricter stop-loss policies',
                'Consider portfolio deleveraging',
                'Increase monitoring frequency'
            ])

        # Sharpe ratio specific recommendations
        if avg_sharpe < 0.5:
            recommendations.append('Historical Sharpe ratio indicates poor risk-adjusted returns - review strategy parameters')
        elif avg_sharpe > 2.0:
            recommendations.append('Strong historical Sharpe ratio supports current risk parameters')

        # Data confidence recommendations
        if data_confidence < 0.5:
            recommendations.append('Limited historical data - consider more extensive backtesting before live deployment')

        # Volatility adjustment recommendations
        volatility_adj = risk_metrics.get('volatility_adjustment', 1.0)
        if volatility_adj > 1.2:
            recommendations.append('High volatility detected - consider reducing position sizes')
        elif volatility_adj < 0.8:
            recommendations.append('Low volatility environment - opportunity for increased exposure')

        return recommendations
