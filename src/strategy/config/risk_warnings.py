"""
Risk Warnings and Strategy Classification
========================================
Risk assessment system for trading strategies.

This module provides:
- Risk level classification
- Strategy warnings and recommendations
- User education and safety features
"""

from typing import Dict, Any, Optional


# Risk level definitions
RISK_LEVELS = {
    'LOW': {
        'level': 1,
        'description': 'Low risk strategies with conservative approaches',
        'max_drawdown_warning': 0.05,
        'recommended_capital': 'Any',
        'suitable_users': ['beginners', 'conservative', 'preservation']
    },
    'MEDIUM': {
        'level': 2,
        'description': 'Balanced strategies with moderate risk exposure',
        'max_drawdown_warning': 0.10,
        'recommended_capital': 'Medium',
        'suitable_users': ['intermediate', 'balanced', 'experienced']
    },
    'HIGH': {
        'level': 3,
        'description': 'High risk strategies requiring careful management',
        'max_drawdown_warning': 0.20,
        'recommended_capital': 'High',
        'suitable_users': ['advanced', 'high_risk_tolerance']
    },
    'EXTREME': {
        'level': 4,
        'description': 'Extreme risk strategies - can lead to total loss',
        'max_drawdown_warning': 0.50,
        'recommended_capital': 'Very High',
        'suitable_users': ['professional', 'extreme_risk_tolerance']
    }
}

# Strategy-specific risk warnings
RISK_WARNINGS = {
    # Martingale strategies - EXTREME RISK
    'MartingaleStrategy': {
        'risk_level': 'EXTREME',
        'description': 'Doubles stake after each loss. Statistically proven to lose over time.',
        'recommended': 'Demo trading only. Never use real money.',
        'max_stakes': 'Set realistic stake limits to prevent bankruptcy.',
        'educational_note': '''
        ⚠️ MARTINGALE WARNING:
        The Martingale system is mathematically flawed. While it may work in short-term,
        the probability of consecutive losses increases exponentially, leading to
        catastrophic losses. Even with unlimited capital, the edge is against you.
        ''',
        'alternative_suggestions': ['Fixed Fractional', 'Kelly Criterion', 'Percentage Risk']
    },

    'ReverseMartingaleStrategy': {
        'risk_level': 'HIGH',
        'description': 'Doubles stake after wins. Can create large profitable streaks but risky.',
        'recommended': 'Strict stop-loss and stake limits. Monitor drawdown carefully.',
        'max_stakes': 'Set maximum stake and consecutive win limits.',
        'educational_note': '''
        🔄 REVERSE MARTINGALE CONSIDERATIONS:
        This "anti-Martingale" increases stake during winning streaks but can lead to
        large losses if the trend reverses. Requires excellent timing and discipline.
        ''',
        'alternative_suggestions': ['Fixed staking', 'Position sizing based on volatility']
    },

    # Progressive/Gambling strategies
    'DAlembertStrategy': {
        'risk_level': 'MEDIUM',
        'description': 'Increases stake by unit after loss, decreases after win.',
        'recommended': 'Conservative unit sizes and session limits.',
        'max_stakes': 'Set maximum stake and reset triggers.',
        'educational_note': '''
        🎰 D'ALEMBERT STRATEGY:
        A more conservative progressive system, but still carries risk of accumulated losses.
        Better than Martingale but still not recommended for serious trading.
        ''',
        'alternative_suggestions': ['Fixed staking', 'Percentage of account']
    },

    'OscarsGrindStrategy': {
        'risk_level': 'MEDIUM',
        'description': 'Aims for 1 unit profit per session through progressive staking.',
        'recommended': 'Define clear session goals and reset conditions.',
        'max_stakes': 'Monitor maximum stake per trade.',
        'educational_note': '''
        🎯 OSCAR'S GRIND APPROACH:
        Conservative system designed for steady, small profits. Can be effective
        in ranging markets but may struggle in strong trends.
        ''',
        'alternative_suggestions': ['Daily profit targets', 'Session-based money management']
    },

    # Technical strategies - generally lower risk
    'MovingAverageCrossStrategy': {
        'risk_level': 'MEDIUM',
        'description': 'Basic trend-following with moving average crossovers.',
        'recommended': 'Suitable for trending markets. Combine with filters.',
        'max_stakes': 'Standard position sizing applies.',
        'educational_note': '''
        📈 MOVING AVERAGE CROSSES:
        Basic trend-following strategy. Works well in strong trends but can give
        false signals in ranging markets. Consider adding confirmation signals.
        ''',
        'alternative_suggestions': ['Add RSI filter', 'Multiple timeframe confirmation']
    },

    'RSIReversionStrategy': {
        'risk_level': 'HIGH',
        'description': 'Mean reversion using RSI extreme levels.',
        'recommended': 'Works best in ranging markets. Risk of continuation moves.',
        'max_stakes': 'Smaller position sizes due to reversal failure risk.',
        'educational_note': '''
        📊 RSI REVERSAL TRADING:
        Assumes price will revert from extremes. Works in ranging markets but
        can fail spectacularly in strong trends, leading to large losses.
        ''',
        'alternative_suggestions': ['Add trend filter', 'Wait for confirmation candles']
    },

    'BollingerBreakoutStrategy': {
        'risk_level': 'HIGH',
        'description': 'Trades breakouts from Bollinger Band squeezes.',
        'recommended': 'Use in trending markets. Risk of false breakouts.',
        'max_stakes': 'Moderate position sizes with stop-loss protection.',
        'educational_note': '''
        🎯 BOLLINGER BREAKOUTS:
        Capitalizes on volatility expansion after contraction. High win rate but
        requires careful entry timing and strong risk management.
        ''',
        'alternative_suggestions': ['Volume confirmation', 'Multiple timeframe analysis']
    },

    # Machine Learning strategies
    'MLForestStrategy': {
        'risk_level': 'HIGH',
        'description': 'Uses machine learning for signal generation.',
        'recommended': 'Test extensively. ML models can overfit.',
        'max_stakes': 'Conservative sizing until proven.',
        'educational_note': '''
        🤖 MACHINE LEARNING TRADING:
        Can adapt to market conditions but subject to overfitting and changing
        market dynamics. Requires continuous model validation and retraining.
        ''',
        'alternative_suggestions': ['Ensemble methods', 'Feature engineering', 'Walk-forward testing']
    }
}


def get_strategy_risk_info(strategy_class) -> Dict[str, Any]:
    """
    Get risk warning information for a strategy.

    Args:
        strategy_class: Strategy class or class name

    Returns:
        Dictionary with risk information
    """
    strategy_name = getattr(strategy_class, '__name__', str(strategy_class))

    # Check for exact match first
    if strategy_name in RISK_WARNINGS:
        return RISK_WARNINGS[strategy_name]

    # Check for partial matches (useful for inheritance)
    for key in RISK_WARNINGS:
        if key in strategy_name:
            return RISK_WARNINGS[key]

    # Return default risk info
    return {
        'risk_level': 'MEDIUM',
        'description': 'Standard strategy with moderate risk.',
        'recommended': 'Test thoroughly before live trading.',
        'max_stakes': 'Follow proper risk management.',
        'educational_note': '''
        📊 STRATEGY RISK ASSESSMENT:
        This is a technical trading strategy. All strategies carry risk.
        Always use proper position sizing and risk management.
        ''',
        'alternative_suggestions': ['Diversification', 'Multiple strategies', 'Risk limits']
    }


def get_risk_level_details(risk_level: str) -> Dict[str, Any]:
    """
    Get detailed information about a risk level.

    Args:
        risk_level: Risk level name

    Returns:
        Dictionary with risk level details
    """
    return RISK_LEVELS.get(risk_level, RISK_LEVELS['MEDIUM'])


def assess_portfolio_risk(strategy_weights: Dict[str, float]) -> Dict[str, Any]:
    """
    Assess portfolio risk based on strategy allocation.

    Args:
        strategy_weights: Dictionary of strategy_name -> weight

    Returns:
        Portfolio risk assessment
    """
    total_risk_score = 0
    risk_breakdown = {}
    high_risk_strategies = []

    for strategy_name, weight in strategy_weights.items():
        risk_info = get_strategy_risk_info(strategy_name)
        risk_level = risk_info['risk_level']
        risk_score = RISK_LEVELS[risk_level]['level']

        weighted_risk = risk_score * weight
        total_risk_score += weighted_risk

        risk_breakdown[strategy_name] = {
            'risk_level': risk_level,
            'weight': weight,
            'weighted_risk': weighted_risk
        }

        if risk_score >= 3:  # HIGH or EXTREME
            high_risk_strategies.append(strategy_name)

    # Determine overall portfolio risk
    avg_risk = total_risk_score / len(strategy_weights) if strategy_weights else 0

    if avg_risk >= 3.5:
        portfolio_risk = 'EXTREME'
    elif avg_risk >= 2.5:
        portfolio_risk = 'HIGH'
    elif avg_risk >= 1.5:
        portfolio_risk = 'MEDIUM'
    else:
        portfolio_risk = 'LOW'

    return {
        'portfolio_risk': portfolio_risk,
        'average_risk_score': avg_risk,
        'high_risk_strategies': high_risk_strategies,
        'strategy_breakdown': risk_breakdown,
        'recommendations': _get_portfolio_recommendations(portfolio_risk, high_risk_strategies)
    }


def _get_portfolio_recommendations(portfolio_risk: str, high_risk_strategies: list) -> list:
    """Generate portfolio risk reduction recommendations."""
    recommendations = []

    if portfolio_risk in ['EXTREME', 'HIGH']:
        recommendations.append("⚠️ Reduce allocation to high-risk strategies")
        recommendations.append("📊 Increase diversification across multiple strategies")
        recommendations.append("🛡️ Implement stricter risk management (stop-losses, position limits)")
        recommendations.append("💰 Use demo trading to test strategy combinations")

    if high_risk_strategies:
        recommendations.append(f"🎯 Review high-risk strategies: {', '.join(high_risk_strategies[:3])}")

    if portfolio_risk == 'LOW':
        recommendations.append("✅ Portfolio risk is well-managed")

    if not high_risk_strategies:
        recommendations.append("🟢 No extreme risk strategies detected")

    return recommendations


def require_risk_acknowledgment(strategy_name: str, user_experience: str = 'intermediate') -> bool:
    """
    Determine if a strategy requires risk acknowledgment.

    Args:
        strategy_name: Name of the strategy
        user_experience: User's experience level ('beginner', 'intermediate', 'advanced')

    Returns:
        True if risk acknowledgment is required
    """
    risk_info = get_strategy_risk_info(strategy_name)
    risk_level = risk_info['risk_level']

    experience_map = {
        'beginner': ['HIGH', 'EXTREME'],
        'intermediate': ['EXTREME'],
        'advanced': []  # Advanced users can handle all risks
    }

    return risk_level in experience_map.get(user_experience, [])


def get_strategy_disclaimers(strategy_name: str) -> Dict[str, Any]:
    """
    Get all disclaimers and warnings for a strategy.

    Args:
        strategy_name: Name of the strategy

    Returns:
        Dictionary with disclaimer information
    """
    risk_info = get_strategy_risk_info(strategy_name)

    return {
        'risk_level': risk_info['risk_level'],
        'main_warning': risk_info['description'],
        'educational_note': risk_info['educational_note'].strip(),
        'recommended_capital': RISK_LEVELS[risk_info['risk_level']]['recommended_capital'],
        'suitable_users': RISK_LEVELS[risk_info['risk_level']]['suitable_users'],
        'alternative_strategies': risk_info.get('alternative_suggestions', []),
        'risk_score': RISK_LEVELS[risk_info['risk_level']]['level']
    }
