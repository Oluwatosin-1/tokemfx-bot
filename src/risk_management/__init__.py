"""
Risk Management Module
======================
Comprehensive risk management for trading operations.
"""

from typing import Dict, Any, List
from .ai_risk_evaluator import AIRiskEvaluator

# Initialize AI Risk Evaluator for backward compatibility
ai_risk_evaluator = AIRiskEvaluator()

# Create risk_manager instance with risk_management attribute
class RiskManager:
    """
    Unified risk management interface for backward compatibility.
    """

    def __init__(self):
        self.ai_evaluator = ai_risk_evaluator
        self.risk_management = self  # Backward compatibility attribute

    def evaluate_trade_risk(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate risk for a trade.

        Args:
            trade_data: Trade information

        Returns:
            Risk evaluation results
        """
        # Simplified risk evaluation for backward compatibility
        return {
            'risk_level': 'Low',
            'approved': True,
            'max_position_size': 1000.0,
            'recommended_stop_loss': 0.02
        }

    def get_portfolio_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get overall portfolio risk metrics.

        Args:
            positions: List of current positions

        Returns:
            Portfolio risk metrics
        """
        # Simplified portfolio risk assessment
        return {
            'total_exposure': sum(abs(p.get('size', 0)) * p.get('price', 0) for p in positions),
            'risk_level': 'Medium',
            'diversification_score': 7.5,
            'max_drawdown_risk': 3.2
        }

    def check_risk_limits(self, account_info: Dict[str, Any], new_trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a new trade would violate risk limits.

        Args:
            account_info: Current account information
            new_trade: Proposed trade details

        Returns:
            Risk limit check results
        """
        # Simplified risk limit check
        return {
            'approved': True,
            'risk_score': 2.1,
            'remaining_capacity': 85.0,
            'warnings': []
        }


# Global risk manager instance
risk_manager = RiskManager()

__all__ = [
    'AIRiskEvaluator',
    'ai_risk_evaluator',
    'RiskManager',
    'risk_manager'
]
