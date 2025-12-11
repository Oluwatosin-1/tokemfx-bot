"""
Risk Calculator Module
======================
Advanced risk calculations and quantitative analysis for trading positions.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats
from math import sqrt

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Comprehensive risk calculation engine providing quantitative risk metrics
    for portfolios and individual positions.
    """

    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.returns_cache = {}

        logger.info(f"RiskCalculator initialized with {confidence_level*100:.1f}% confidence level")

    def calculate_value_at_risk(self,
                               returns: Union[List[float], pd.Series, np.ndarray],
                               time_horizon: int = 1,
                               method: str = "historical") -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) using different methodologies.

        Args:
            returns: Historical returns data
            time_horizon: Time horizon in days
            method: VaR calculation method ('historical', 'parametric', 'monte_carlo')

        Returns:
            VaR calculation results
        """
        try:
            # Convert to numpy array
            if isinstance(returns, (pd.Series, list)):
                returns = np.array(returns)

            returns = returns[~np.isnan(returns)]  # Remove NaN values

            if len(returns) < 30:
                return {'error': 'Insufficient data for VaR calculation (need at least 30 observations)'}

            if method == "historical":
                var = self._historical_var(returns, time_horizon)
            elif method == "parametric":
                var = self._parametric_var(returns, time_horizon)
            elif method == "monte_carlo":
                var = self._monte_carlo_var(returns, time_horizon)
            else:
                return {'error': f'Unknown VaR method: {method}'}

            return var

        except Exception as e:
            logger.error(f"VaR calculation error: {e}")
            return {'error': str(e)}

    def _historical_var(self, returns: np.ndarray, time_horizon: int) -> Dict[str, Any]:
        """
        Calculate Historical Simulation VaR.

        Args:
            returns: Historical returns array
            time_horizon: Time horizon

        Returns:
            Historical VaR results
        """
        # Sort returns in ascending order (worst to best)
        sorted_returns = np.sort(returns)

        # Find the VaR percentile
        var_index = int(len(sorted_returns) * (1 - self.confidence_level))
        var_value = sorted_returns[var_index]

        # Scale for time horizon (square root of time assumption)
        time_scaled_var = var_value * sqrt(time_horizon)

        return {
            'method': 'historical',
            'confidence_level': self.confidence_level,
            'time_horizon': time_horizon,
            'value_at_risk': var_value,
            'time_scaled_var': time_scaled_var,
            'expected_shortfall': np.mean(sorted_returns[:var_index]),  # CVaR
            'data_points': len(returns)
        }

    def _parametric_var(self, returns: np.ndarray, time_horizon: int) -> Dict[str, Any]:
        """
        Calculate Parametric (Normal Distribution) VaR.

        Args:
            returns: Historical returns array
            time_horizon: Time horizon

        Returns:
            Parametric VaR results
        """
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Calculate z-score for confidence level
        z_score = stats.norm.ppf(1 - self.confidence_level)

        # Standard parametric VaR
        var_value = -(mean_return + z_score * std_return)

        # Time-scaled VaR
        volatility = std_return * sqrt(time_horizon)
        time_scaled_var = -(mean_return * time_horizon + z_score * volatility)

        return {
            'method': 'parametric',
            'confidence_level': self.confidence_level,
            'time_horizon': time_horizon,
            'value_at_risk': var_value,
            'time_scaled_var': time_scaled_var,
            'expected_shortfall': None,  # Not easily calculated for parametric
            'mean_return': mean_return,
            'volatility': std_return,
            'z_score': z_score,
            'data_points': len(returns)
        }

    def _monte_carlo_var(self, returns: np.ndarray, time_horizon: int, n_simulations: int = 10000) -> Dict[str, Any]:
        """
        Calculate Monte Carlo Simulation VaR.

        Args:
            returns: Historical returns array
            time_horizon: Time horizon
            n_simulations: Number of Monte Carlo simulations

        Returns:
            Monte Carlo VaR results
        """
        # Fit distribution to returns
        mu, sigma = np.mean(returns), np.std(returns)

        # Generate random returns
        simulated_returns = np.random.normal(mu, sigma, (n_simulations, time_horizon))

        # Calculate portfolio returns for each path
        portfolio_returns = np.sum(simulated_returns, axis=1)

        # Sort and find VaR
        sorted_portfolio_returns = np.sort(portfolio_returns)
        var_index = int(n_simulations * (1 - self.confidence_level))
        var_value = -sorted_portfolio_returns[var_index]  # Negative because VaR is loss

        # Expected Shortfall (CVaR)
        expected_shortfall = -np.mean(sorted_portfolio_returns[:var_index])

        return {
            'method': 'monte_carlo',
            'confidence_level': self.confidence_level,
            'time_horizon': time_horizon,
            'value_at_risk': var_value,
            'expected_shortfall': expected_shortfall,
            'n_simulations': n_simulations,
            'mean_simulated': np.mean(portfolio_returns),
            'std_simulated': np.std(portfolio_returns)
        }

    def calculate_sharpe_ratio(self,
                              returns: Union[List[float], pd.Series],
                              risk_free_rate: float = 0.02) -> Dict[str, Any]:
        """
        Calculate Sharpe ratio and related risk-adjusted return metrics.

        Args:
            returns: Historical returns
            risk_free_rate: Annualized risk-free rate (e.g., 0.02 for 2%)

        Returns:
            Sharpe ratio analysis
        """
        try:
            if isinstance(returns, list):
                returns = pd.Series(returns)

            returns = returns.dropna()

            if len(returns) < 2:
                return {'error': 'Insufficient data for Sharpe ratio calculation'}

            # Annualized metrics (assuming daily returns)
            annual_return = np.mean(returns) * 252
            annual_volatility = np.std(returns) * sqrt(252)
            annual_risk_free = risk_free_rate

            sharpe_ratio = (annual_return - annual_risk_free) / annual_volatility if annual_volatility > 0 else 0

            # Sortino ratio (downside deviation only)
            downside_returns = returns[returns < 0]
            downside_volatility = np.std(downside_returns) * sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = (annual_return - annual_risk_free) / downside_volatility if downside_volatility > 0 else 0

            return {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'annual_return': annual_return,
                'annual_volatility': annual_volatility,
                'annual_risk_free': annual_risk_free,
                'excess_return': annual_return - annual_risk_free,
                'downside_volatility': downside_volatility,
                'information_ratio': sharpe_ratio,  # Simplified
                'data_points': len(returns)
            }

        except Exception as e:
            logger.error(f"Sharpe ratio calculation error: {e}")
            return {'error': str(e)}

    def calculate_maximum_drawdown(self,
                                  prices: Union[List[float], pd.Series]) -> Dict[str, Any]:
        """
        Calculate Maximum Drawdown and drawdown statistics.

        Args:
            prices: Price series data

        Returns:
            Drawdown analysis results
        """
        try:
            if isinstance(prices, list):
                prices = pd.Series(prices)

            prices = prices.dropna()

            if len(prices) < 2:
                return {'error': 'Insufficient data for drawdown calculation'}

            # Calculate peak values
            peak = prices.expanding(min_periods=1).max()

            # Calculate drawdowns
            drawdowns = (prices - peak) / peak

            # Maximum drawdown
            max_drawdown = drawdowns.min()
            max_drawdown_idx = drawdowns.idxmin()

            # Recovery analysis
            peak_before_drawdown = peak.iloc[max_drawdown_idx]
            recovery_prices = prices.iloc[max_drawdown_idx:]

            # Find recovery point
            recovery_idx = None
            for i, price in enumerate(recovery_prices):
                if price >= peak_before_drawdown:
                    recovery_idx = max_drawdown_idx + i
                    break

            recovery_time = recovery_idx - max_drawdown_idx if recovery_idx else len(prices) - max_drawdown_idx

            # Drawdown distribution
            severe_drawdowns = len(drawdowns[drawdowns < -0.1])  # >10% drawdowns
            avg_drawdown = drawdowns.mean()

            return {
                'maximum_drawdown': max_drawdown,
                'max_drawdown_index': max_drawdown_idx,
                'recovery_time': recovery_time,
                'avg_drawdown': avg_drawdown,
                'severe_drawdowns_count': severe_drawdowns,
                'current_drawdown': drawdowns.iloc[-1],
                'drawdown_distribution': {
                    'min': drawdowns.min(),
                    'max': drawdowns.max(),
                    'median': drawdowns.median(),
                    'std': drawdowns.std()
                },
                'peak_value': peak_before_drawdown,
                'trough_value': prices.iloc[max_drawdown_idx],
                'data_points': len(prices)
            }

        except Exception as e:
            logger.error(f"Maximum drawdown calculation error: {e}")
            return {'error': str(e)}

    def calculate_beta_correlation(self,
                                  asset_returns: Union[List[float], pd.Series],
                                  market_returns: Union[List[float], pd.Series],
                                  risk_free_rate: float = 0.0) -> Dict[str, Any]:
        """
        Calculate Beta, correlation, and market relationship metrics.

        Args:
            asset_returns: Asset return series
            market_returns: Market/benchmark return series
            risk_free_rate: Risk-free rate for Jensen's alpha

        Returns:
            Beta and correlation analysis
        """
        try:
            if isinstance(asset_returns, list):
                asset_returns = pd.Series(asset_returns)
            if isinstance(market_returns, list):
                market_returns = pd.Series(market_returns)

            # Align series
            common_data = pd.concat([asset_returns, market_returns], axis=1).dropna()
            asset_ret = common_data.iloc[:, 0]
            market_ret = common_data.iloc[:, 1]

            if len(asset_ret) < 30:
                return {'error': 'Insufficient data for beta calculation (need at least 30 observations)'}

            # Calculate beta
            covariance = np.cov(asset_ret, market_ret)[0, 1]
            market_variance = np.var(market_ret)
            beta = covariance / market_variance if market_variance > 0 else 0

            # Correlation coefficient
            correlation = np.corrcoef(asset_ret, market_ret)[0, 1]

            # Jensen's alpha (simplified)
            asset_return = np.mean(asset_ret) * 252  # Annualized
            market_return = np.mean(market_ret) * 252
            alpha = asset_return - (risk_free_rate + beta * (market_return - risk_free_rate))

            # R-squared
            r_squared = correlation ** 2

            return {
                'beta': beta,
                'correlation': correlation,
                'r_squared': r_squared,
                'alpha': alpha,
                'asset_expected_return': asset_return,
                'market_expected_return': market_return,
                'covariance': covariance,
                'market_variance': market_variance,
                'data_points': len(asset_ret),
                'beta_interpretation': self._interpret_beta(beta),
                'correlation_interpretation': self._interpret_correlation(correlation)
            }

        except Exception as e:
            logger.error(f"Beta calculation error: {e}")
            return {'error': str(e)}

    def _interpret_beta(self, beta: float) -> str:
        """Interpret beta values."""
        if beta > 1.2:
            return "Highly volatile (aggressive)"
        elif beta > 1.0:
            return "More volatile than market"
        elif beta > 0.8:
            return "Slightly more volatile than market"
        elif beta > 0.2:
            return "Less volatile than market (defensive)"
        else:
            return "Very low volatility"

    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation values."""
        abs_corr = abs(correlation)
        if abs_corr > 0.8:
            return f"Very strong {'positive' if correlation > 0 else 'negative'} relationship"
        elif abs_corr > 0.6:
            return f"Strong {'positive' if correlation > 0 else 'negative'} relationship"
        elif abs_corr > 0.3:
            return f"Moderate {'positive' if correlation > 0 else 'negative'} relationship"
        elif abs_corr > 0.1:
            return f"Weak {'positive' if correlation > 0 else 'negative'} relationship"
        else:
            return "Very weak or no relationship"

    def calculate_optimal_kelly_bet(self,
                                   win_probability: float,
                                   win_loss_ratio: float) -> Dict[str, Any]:
        """
        Calculate optimal position size using Kelly criterion.

        Args:
            win_probability: Probability of winning (0-1)
            win_loss_ratio: Average win amount / average loss amount

        Returns:
            Kelly criterion calculations
        """
        try:
            if not (0 < win_probability < 1):
                return {'error': 'Win probability must be between 0 and 1'}

            if win_loss_ratio <= 1:
                return {'error': 'Win/loss ratio must be greater than 1 for positive edge'}

            # Basic Kelly formula
            kelly_fraction = (win_probability * win_loss_ratio - 1) / (win_loss_ratio - 1)

            # Fractional Kelly (half Kelly)
            fractional_kelly = kelly_fraction / 2

            # Conservative Kelly (quarter Kelly)
            conservative_kelly = kelly_fraction / 4

            # Edge calculation
            edge = win_probability - (1 / win_loss_ratio)

            return {
                'full_kelly': kelly_fraction,
                'fractional_kelly': fractional_kelly,
                'conservative_kelly': conservative_kelly,
                'win_probability': win_probability,
                'win_loss_ratio': win_loss_ratio,
                'edge': edge,
                'recommended_bet_size': fractional_kelly,
                'risk_assessment': self._assess_kelly_risk(kelly_fraction)
            }

        except Exception as e:
            logger.error(f"Kelly criterion calculation error: {e}")
            return {'error': str(e)}

    def _assess_kelly_risk(self, kelly_fraction: float) -> str:
        """Assess risk level of Kelly bet size."""
        if kelly_fraction > 0.1:
            return "Very High Risk"
        elif kelly_fraction > 0.05:
            return "High Risk"
        elif kelly_fraction > 0.02:
            return "Moderate Risk"
        elif kelly_fraction > 0.01:
            return "Low Risk"
        else:
            return "Very Low Risk"

    def calculate_portfolio_metrics(self,
                                   positions: List[Dict[str, Any]],
                                   market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio risk metrics.

        Args:
            positions: List of position dictionaries
            market_data: Optional market data for correlations

        Returns:
            Portfolio analytics
        """
        try:
            if not positions:
                return {'error': 'No positions provided'}

            # Extract position data
            weights = []
            expected_returns = []
            position_data = []

            total_value = 0
            for pos in positions:
                size = pos.get('size', 0)
                entry_price = pos.get('entry_price', 0)
                position_value = size * entry_price
                total_value += position_value

                position_data.append({
                    'symbol': pos.get('instrument', 'Unknown'),
                    'weight': position_value,
                    'return': pos.get('expected_return', 0),
                    'volatility': pos.get('volatility', 0.02),
                    **pos
                })

            # Calculate weights
            for pos in position_data:
                pos['weight'] = pos['weight'] / total_value if total_value > 0 else 0
                weights.append(pos['weight'])
                expected_returns.append(pos['return'])

            # Portfolio expected return
            portfolio_return = np.dot(weights, expected_returns)

            # Calculate correlation matrix if market data provided
            correlation_matrix = None
            if market_data:
                correlation_matrix = self._calculate_correlation_matrix(position_data, market_data)

            return {
                'total_portfolio_value': total_value,
                'positions': position_data,
                'portfolio_expected_return': portfolio_return,
                'portfolio_volatility': np.std(expected_returns),  # Simplified
                'positions_count': len(positions),
                'diversification_ratio': len(positions),  # Number of positions as proxy
                'correlation_matrix': correlation_matrix
            }

        except Exception as e:
            logger.error(f"Portfolio metrics calculation error: {e}")
            return {'error': str(e)}

    def _calculate_correlation_matrix(self,
                                    position_data: List[Dict[str, Any]],
                                    market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate correlation matrix for portfolio positions.

        Args:
            position_data: Position information
            market_data: Market data dictionary

        Returns:
            Correlation matrix
        """
        try:
            # This would calculate actual correlations from price data
            # Simplified implementation
            return {'note': 'Correlation calculation requires price time series data'}
        except Exception:
            return None


# Convenience functions
def calculate_var(returns: Union[List[float], pd.Series],
                 confidence_level: float = 0.95,
                 method: str = "historical") -> Dict[str, Any]:
    """
    Convenience function for VaR calculation.

    Args:
        returns: Historical returns
        confidence_level: Confidence level (0-1)
        method: Calculation method

    Returns:
        VaR results
    """
    calculator = RiskCalculator(confidence_level)
    return calculator.calculate_value_at_risk(returns, time_horizon=1, method=method)


def calculate_sharpe(returns: Union[List[float], pd.Series],
                    risk_free_rate: float = 0.02) -> float:
    """
    Convenience function for Sharpe ratio.

    Args:
        returns: Historical returns
        risk_free_rate: Risk-free rate

    Returns:
        Sharpe ratio value
    """
    calculator = RiskCalculator()
    result = calculator.calculate_sharpe_ratio(returns, risk_free_rate)
    return result.get('sharpe_ratio', 0)


def calculate_max_dd(prices: Union[List[float], pd.Series]) -> float:
    """
    Convenience function for maximum drawdown.

    Args:
        prices: Price series

    Returns:
        Maximum drawdown value
    """
    calculator = RiskCalculator()
    result = calculator.calculate_maximum_drawdown(prices)
    return result.get('maximum_drawdown', 0)


def create_risk_calculator(confidence_level: float = 0.95) -> RiskCalculator:
    """
    Create and return a risk calculator instance.

    Args:
        confidence_level: Confidence level for calculations

    Returns:
        Configured RiskCalculator instance
    """
    return RiskCalculator(confidence_level)


__all__ = [
    'RiskCalculator',
    'calculate_var',
    'calculate_sharpe',
    'calculate_max_dd',
    'create_risk_calculator'
]
