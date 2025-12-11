"""
Test Backtest System Module
============================
Provides testing and development utilities for backtesting functionality.

This module offers:
- Sample OHLC data generation for testing
- Mock trading results and performance metrics
- Testing utilities for backtest compliance
- Development helper functions for strategy testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def create_sample_ohlc_data(instrument: str = "R_10",
                           periods: int = 1000,
                           start_price: float = 100.0) -> pd.DataFrame:
    """
    Create sample OHLC data for testing purposes.

    Args:
        instrument: Trading instrument symbol
        periods: Number of periods to generate
        start_price: Starting price for the data

    Returns:
        DataFrame with OHLC and volume data
    """
    try:
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periods//24 if periods > 1000 else 30)
        dates = pd.date_range(start_date, end_date, periods=periods)

        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results

        # Create price series with realistic volatility
        returns = np.random.normal(0.0001, 0.02, periods)  # Mean return, volatility

        # Add some autocorrelation for more realistic behavior
        for i in range(1, len(returns)):
            returns[i] += 0.2 * returns[i-1]  # Momentum effect

        prices = start_price * np.exp(np.cumsum(returns))

        # Create OHLC data with realistic spreads
        ohlcv_data = []

        for i, price in enumerate(prices):
            volatility = abs(returns[i]) * 2 + 0.005  # Higher vol = wider spreads

            open_price = price
            high_price = price * (1 + volatility * np.random.uniform(0.5, 1.5))
            low_price = price * (1 - volatility * np.random.uniform(0.5, 1.5))
            close_price = high_price * np.random.uniform(0.3, 0.7) + low_price * np.random.uniform(0.3, 0.7)

            # Ensure OHLC logic
            high_price = max(open_price, high_price, close_price)
            low_price = min(open_price, low_price, close_price)

            # Generate volume with realistic variability
            base_volume = 1000000 if instrument.startswith('R_') else 50000
            volume_variability = np.random.uniform(0.5, 2.0)
            volume = int(base_volume * volume_variability)

            ohlcv_data.append({
                'timestamp': dates[i],
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5),
                'volume': volume,
                'instrument': instrument
            })

        df = pd.DataFrame(ohlcv_data)
        df = df.set_index('timestamp')
        df.index.name = 'timestamp'

        logger.info(f"Generated {len(df)} periods of sample data for {instrument}")
        return df

    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        return pd.DataFrame()

def get_test_backtest_results(num_strategies: int = 5,
                             instruments: List[str] = None) -> Dict[str, Any]:
    """
    Generate mock backtest results for testing purposes.

    Args:
        num_strategies: Number of strategies to simulate
        instruments: List of instruments tested

    Returns:
        Dictionary containing backtest results
    """
    if instruments is None:
        instruments = ["R_10", "R_25", "R_50"]

    try:
        strategies = [
            "MA Crossover Strategy",
            "RSI Reversal Strategy",
            "Bollinger Bands Strategy",
            "ATR Breakout Strategy",
            "MACD Strategy",
            "Support Resistance Strategy",
            "Fibonacci Retracement Strategy",
            "Momentum Strategy",
            "Mean Reversion Strategy",
            "Volume Price Analysis Strategy"
        ][:num_strategies]

        all_results = []

        for i, strategy_name in enumerate(strategies):
            # Generate realistic backtest metrics
            sharpe_ratio = np.random.uniform(0.5, 2.5)
            total_return = sharpe_ratio * np.random.uniform(15, 50) * np.random.choice([-1, 1], p=[0.3, 0.7])
            win_rate = np.random.uniform(0.45, 0.75)
            max_drawdown = abs(np.random.uniform(5, 25))
            total_trades = int(np.random.uniform(50, 300))
            avg_trade_return = total_return / total_trades

            # Calculate additional metrics
            profit_factor = 1.5 + sharpe_ratio * 0.8
            calmar_ratio = total_return / max_drawdown
            sortino_ratio = sharpe_ratio * np.random.uniform(1.1, 1.3)

            strategy_result = {
                'strategy_name': strategy_name,
                'strategy_type': strategy_name.split()[0],
                'instrument': np.random.choice(instruments),
                'total_return': float(total_return),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'calmar_ratio': float(calmar_ratio),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate),
                'total_trades': total_trades,
                'avg_trade_return': float(avg_trade_return),
                'profit_factor': float(profit_factor),
                'max_consecutive_wins': int(np.random.uniform(5, total_trades//10)),
                'max_consecutive_losses': int(np.random.uniform(3, total_trades//20)),
                'avg_win_loss_ratio': float(np.random.uniform(1.2, 3.0)),
                'volatility': float(np.random.uniform(0.05, 0.25)),
                'risk_adjusted_return': float(total_return / max_drawdown),
                'start_date': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'total_days': 365,
                'daily_return_avg': float(total_return / 365),
                'daily_return_std': float(np.random.uniform(0.01, 0.04))
            }

            all_results.append(strategy_result)

        # Sort by total return descending
        all_results.sort(key=lambda x: x['total_return'], reverse=True)

        # Find best strategy
        best_strategy = max(all_results, key=lambda x: x['sharpe_ratio'])

        result = {
            'all_results': all_results,
            'best_strategy': best_strategy,
            'total_strategies_tested': len(all_results),
            'test_timestamp': datetime.now().isoformat(),
            'test_duration_hours': np.random.uniform(1, 24),
            'instruments_tested': instruments,
            'backtest_engine': 'TokemFX Backtesting Engine v2.0',
            'performance_summary': {
                'avg_return': float(np.mean([r['total_return'] for r in all_results])),
                'avg_sharpe': float(np.mean([r['sharpe_ratio'] for r in all_results])),
                'avg_win_rate': float(np.mean([r['win_rate'] for r in all_results])),
                'avg_max_drawdown': float(np.mean([r['max_drawdown'] for r in all_results])),
                'total_trades_all_strategies': sum([r['total_trades'] for r in all_results]),
                'best_performing_strategy': best_strategy['strategy_name'],
                'worst_performing_strategy': min(all_results, key=lambda x: x['total_return'])['strategy_name']
            }
        }

        logger.info(f"Generated mock backtest results for {len(all_results)} strategies")
        return result

    except Exception as e:
        logger.error(f"Error generating mock backtest results: {e}")
        return {'error': str(e), 'all_results': []}

def generate_mock_trading_data(days: int = 30,
                              trades_per_day: int = 10,
                              instruments: List[str] = None) -> pd.DataFrame:
    """
    Generate mock trading data for testing dashboard functionality.

    Args:
        days: Number of days of data to generate
        trades_per_day: Average trades per day
        instruments: List of instruments

    Returns:
        DataFrame with mock trading data
    """
    if instruments is None:
        instruments = ["R_10", "R_25", "R_50", "frxEURUSD"]

    try:
        trading_data = []

        for day in range(days):
            date = datetime.now() - timedelta(days=day)

            # Generate variable number of trades per day
            num_trades = int(np.random.poisson(trades_per_day))

            for _ in range(num_trades):
                # Generate realistic trade data
                instrument = np.random.choice(instruments)
                direction = np.random.choice(['BUY', 'SELL'])
                size = np.random.uniform(1, 100)

                # Simulate entry and exit prices with spread
                base_price = np.random.uniform(1.05, 1.15)
                spread = 0.0001 if 'frx' in instrument else 0.001

                entry_price = base_price
                exit_price = base_price * (1 + np.random.normal(0, 0.01))

                if direction == 'SELL':
                    exit_price = base_price * (1 + np.random.normal(0, 0.01))

                # Calculate P&L
                pnl = (exit_price - entry_price) * size if direction == 'BUY' else (entry_price - exit_price) * size

                trade_record = {
                    'timestamp': date + timedelta(
                        hours=np.random.randint(9, 17),
                        minutes=np.random.randint(0, 60)
                    ),
                    'instrument': instrument,
                    'direction': direction,
                    'size': float(size),
                    'entry_price': float(entry_price),
                    'exit_price': float(exit_price),
                    'pnl': float(pnl),
                    'commission': float(abs(pnl) * 0.001),
                    'spread_cost': float(spread * size),
                    'is_winner': pnl > 0,
                    'strategy': f"Strategy_{np.random.randint(1, 6)}"
                }

                trading_data.append(trade_record)

        df = pd.DataFrame(trading_data).sort_values('timestamp', ascending=False)
        logger.info(f"Generated {len(df)} mock trading records")
        return df

    except Exception as e:
        logger.error(f"Error generating mock trading data: {e}")
        return pd.DataFrame()

def create_performance_summary(backtest_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a performance summary from backtest results.

    Args:
        backtest_results: List of backtest result dictionaries

    Returns:
        Performance summary statistics
    """
    if not backtest_results:
        return {'error': 'No backtest results provided'}

    try:
        # Extract key metrics
        returns = [r.get('total_return', 0) for r in backtest_results]
        sharpes = [r.get('sharpe_ratio', 0) for r in backtest_results]
        win_rates = [r.get('win_rate', 0) for r in backtest_results]
        max_drawdowns = [r.get('max_drawdown', 0) for r in backtest_results]

        summary = {
            'total_strategies': len(backtest_results),
            'best_return': float(max(returns)),
            'worst_return': float(min(returns)),
            'avg_return': float(np.mean(returns)),
            'median_return': float(np.median(returns)),
            'return_std': float(np.std(returns)),
            'best_sharpe': float(max(sharpes)),
            'avg_sharpe': float(np.mean(sharpes)),
            'best_win_rate': float(max(win_rates)),
            'avg_win_rate': float(np.mean(win_rates)),
            'worst_drawdown': float(max(max_drawdowns)),
            'avg_drawdown': float(np.mean(max_drawdowns)),
            'profitable_strategies': len([r for r in returns if r > 0]),
            'loss_making_strategies': len([r for r in returns if r < 0]),
            'very_profitable_strategies': len([r for r in returns if r > 20]),
            'high_risk_strategies': len([r for r in max_drawdowns if r > 15]),
            'summary_generated_at': datetime.now().isoformat()
        }

        return summary

    except Exception as e:
        logger.error(f"Error creating performance summary: {e}")
        return {'error': str(e)}

def validate_backtest_integrity(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the integrity of backtest results.

    Args:
        results: Backtest results to validate

    Returns:
        Validation report
    """
    validation_report = {
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'integrity_score': 100
    }

    try:
        # Check required fields
        required_fields = ['total_return', 'sharpe_ratio', 'win_rate', 'max_drawdown']

        for i, result in enumerate(results.get('all_results', [])):
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)

            if missing_fields:
                validation_report['errors'].append(
                    f"Strategy {i+1}: Missing required fields {missing_fields}"
                )
                validation_report['integrity_score'] -= 10

        # Check for unrealistic values
        for i, result in enumerate(results.get('all_results', [])):
            if result.get('sharpe_ratio', 0) > 5:
                validation_report['warnings'].append(
                    f"Strategy {i+1}: Unrealistically high Sharpe ratio ({result['sharpe_ratio']:.2f})"
                )
                validation_report['integrity_score'] -= 5

            if result.get('win_rate', 0) > 0.9:
                validation_report['warnings'].append(
                    f"Strategy {i+1}: Unrealistically high win rate ({result['win_rate']:.2f})"
                )
                validation_report['integrity_score'] -= 5

        # Determine overall validity
        if validation_report['errors']:
            validation_report['is_valid'] = False
        elif validation_report['warnings']:
            validation_report['is_valid'] = True  # Warnings don't invalidate

        logger.info(f"Backtest validation completed with score: {validation_report['integrity_score']}")
        return validation_report

    except Exception as e:
        logger.error(f"Error validating backtest integrity: {e}")
        return {
            'is_valid': False,
            'errors': [str(e)],
            'integrity_score': 0
        }


# Testing utility functions
def create_mock_api_response(success: bool = True,
                           error_message: str = None) -> Dict[str, Any]:
    """
    Create mock API response for testing.

    Args:
        success: Whether the mock response should be successful
        error_message: Error message if success=False

    Returns:
        Mock API response dictionary
    """
    if success:
        return {
            'success': True,
            'data': {
                'balance': '10002.89',
                'currency': 'USD',
                'account_type': 'DEMO'
            }
        }
    else:
        return {
            'success': False,
            'error': {
                'code': 'TEST_ERROR',
                'message': error_message or 'Mock error for testing'
            }
        }

# Export functions
__all__ = [
    'create_sample_ohlc_data',
    'get_test_backtest_results',
    'generate_mock_trading_data',
    'create_performance_summary',
    'validate_backtest_integrity',
    'create_mock_api_response'
]
