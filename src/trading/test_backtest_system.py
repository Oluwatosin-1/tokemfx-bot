"""
Backtesting System for Trajectory Prediction and Analysis
==========================================================

This module provides comprehensive backtesting functionality for trading strategies,
including trajectory prediction, performance analysis, and risk assessment.

Features:
- Backtesting engine for various trading strategies
- Performance metrics calculation
- Risk analysis and drawdown calculations
- Sample data generation for testing
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """
    Comprehensive backtesting engine for trading strategies.

    Provides framework for testing trading strategies against historical data,
    calculating performance metrics, and analyzing risk-adjusted returns.
    """

    def __init__(self, initial_balance: float = 10000.0):
        """
        Initialize backtesting engine

        Args:
            initial_balance: Starting portfolio balance for backtesting
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}
        self.portfolio_history = []
        self.trade_history = []

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_return = 0.0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0

        logger.info(f"✅ BacktestingEngine initialized with ${initial_balance:,.0f} balance")

    def run_backtest(self, strategy_function, market_data: pd.DataFrame,
                    strategy_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a backtest using the specified strategy

        Args:
            strategy_function: Trading strategy function
            market_data: Historical market data
            strategy_params: Strategy-specific parameters

        Returns:
            Complete backtest results with performance metrics
        """
        if strategy_params is None:
            strategy_params = {}

        logger.info(f"🏁 Starting backtest with {len(market_data)} data points")

        try:
            # Reset state
            self._reset()

            # Generate signals
            signals = strategy_function(market_data, **strategy_params)

            # Execute trades
            for signal in signals:
                self._execute_trade(signal, market_data)

            # Calculate performance metrics
            results = self._calculate_performance_metrics(market_data)

            logger.info(f"✅ Backtest completed: {self.total_trades} trades, "
                       f"Return: {results.get('total_return_pct', 0):.2%}")

            return results

        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {'error': str(e), 'status': 'FAILED'}

    def _execute_trade(self, signal: Dict[str, Any], market_data: pd.DataFrame):
        """Execute a single trade based on signal"""
        action = signal.get('action', '').upper()
        symbol = signal.get('symbol', 'DEFAULT')
        volume = signal.get('volume', 1.0)

        if action not in ['BUY', 'SELL']:
            return

        # Simplified execution logic
        if action == 'BUY' and self.current_balance > 0:
            # Buy with available balance
            price = signal.get('price', 100.0)
            shares = min(volume, self.current_balance / price)

            if shares > 0:
                cost = shares * price
                self.current_balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + shares

                self.trade_history.append({
                    'action': 'BUY',
                    'symbol': symbol,
                    'shares': shares,
                    'price': price,
                    'timestamp': signal.get('timestamp')
                })

                self.total_trades += 1

    def _calculate_performance_metrics(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""

        # Calculate portfolio value over time
        portfolio_values = []
        for i, (timestamp, row) in enumerate(market_data.iterrows()):
            portfolio_value = self.current_balance

            # Add position values (simplified)
            for symbol, shares in self.positions.items():
                current_price = row.get('close', row.get('price', 100))
                portfolio_value += shares * current_price

            portfolio_values.append(portfolio_value)

        # Calculate returns
        if len(portfolio_values) > 1:
            total_return = (portfolio_values[-1] - self.initial_balance) / self.initial_balance
            returns_series = pd.Series(portfolio_values).pct_change().dropna()

            if len(returns_series) > 0:
                sharpe_ratio = returns_series.mean() / returns_series.std() if returns_series.std() > 0 else 0

                # Calculate drawdown
                cumulative = (1 + returns_series).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min()

                # Calculate win rate
                win_rate = self.winning_trades / max(1, self.total_trades)
            else:
                sharpe_ratio = 0.0
                max_drawdown = 0.0
                win_rate = 0.0
        else:
            total_return = 0.0
            sharpe_ratio = 0.0
            max_drawdown = 0.0
            win_rate = 0.0

        return {
            'initial_balance': self.initial_balance,
            'final_balance': portfolio_values[-1] if portfolio_values else self.initial_balance,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': abs(max_drawdown) * 100,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'portfolio_history': portfolio_values,
            'trade_history': self.trade_history
        }

    def _reset(self):
        """Reset engine state for new backtest"""
        self.current_balance = self.initial_balance
        self.positions = {}
        self.portfolio_history = []
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0


def get_test_backtest_results() -> Dict[str, Any]:
    """
    Get sample backtest results for testing

    Returns:
        Dictionary containing sample backtest data
    """
    sample_results = {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'all_results': [
            # Technical strategies
            {
                'strategy_name': 'MovingAverageCrossStrategy',
                'total_return': 0.125,
                'total_return_pct': 12.5,
                'sharpe_ratio': 1.4,
                'win_rate': 0.65,
                'max_drawdown': -0.042,
                'max_drawdown_pct': -4.2,
                'total_trades': 87,
                'avg_trade_pnl': 2.5,
                'profit_factor': 1.8,
                'category': 'technical'
            },
            {
                'strategy_name': 'RSIReversionStrategy',
                'total_return': 0.083,
                'total_return_pct': 8.3,
                'sharpe_ratio': 1.1,
                'win_rate': 0.58,
                'max_drawdown': -0.061,
                'max_drawdown_pct': -6.1,
                'total_trades': 92,
                'avg_trade_pnl': 1.8,
                'profit_factor': 1.5,
                'category': 'technical'
            },
            {
                'strategy_name': 'BollingerBreakoutStrategy',
                'total_return': 0.157,
                'total_return_pct': 15.7,
                'sharpe_ratio': 1.6,
                'win_rate': 0.62,
                'max_drawdown': -0.058,
                'max_drawdown_pct': -5.8,
                'total_trades': 75,
                'avg_trade_pnl': 3.2,
                'profit_factor': 2.1,
                'category': 'technical'
            },
            {
                'strategy_name': 'ATRBreakoutStrategy',
                'total_return': 0.094,
                'total_return_pct': 9.4,
                'sharpe_ratio': 1.2,
                'win_rate': 0.59,
                'max_drawdown': -0.049,
                'max_drawdown_pct': -4.9,
                'total_trades': 83,
                'avg_trade_pnl': 2.1,
                'profit_factor': 1.6,
                'category': 'technical'
            },
            # Money management strategies (high risk)
            {
                'strategy_name': 'EMARSIHybridStrategy',
                'total_return': 0.182,
                'total_return_pct': 18.2,
                'sharpe_ratio': 1.8,
                'win_rate': 0.67,
                'max_drawdown': -0.037,
                'max_drawdown_pct': -3.7,
                'total_trades': 68,
                'avg_trade_pnl': 4.1,
                'profit_factor': 2.3,
                'category': 'hybrid'
            },
            {
                'strategy_name': 'MACDStrategy',
                'total_return': 0.068,
                'total_return_pct': 6.8,
                'sharpe_ratio': 0.9,
                'win_rate': 0.54,
                'max_drawdown': -0.073,
                'max_drawdown_pct': -7.3,
                'total_trades': 95,
                'avg_trade_pnl': 1.3,
                'profit_factor': 1.3,
                'category': 'technical'
            },
            # Money management strategies (simplified for demo)
            {
                'strategy_name': 'D Alembert Strategy (HIGH RISK)',
                'total_return': -0.15,  # Likely to lose with good money management
                'total_return_pct': -15.0,
                'sharpe_ratio': -1.2,
                'win_rate': 0.48,
                'max_drawdown': -0.35,
                'max_drawdown_pct': -35.0,
                'total_trades': 150,
                'avg_trade_pnl': -1.5,
                'profit_factor': 0.8,
                'category': 'money_management',
                'risk_warning': 'HIGH_RISK'
            },
            {
                'strategy_name': 'Martingale Strategy (VERY HIGH RISK)',
                'total_return': -0.85,  # Almost certain to lose
                'total_return_pct': -85.0,
                'sharpe_ratio': -3.5,
                'win_rate': 0.52,
                'max_drawdown': -1.0,
                'max_drawdown_pct': -100.0,
                'total_trades': 200,
                'avg_trade_pnl': -6.25,
                'profit_factor': 0.2,
                'category': 'money_management',
                'risk_warning': 'VERY_HIGH_RISK'
            }
        ],
        'summary': {
            'total_strategies_tested': 8,
            'profitable_strategies': 5,
            'best_performer': 'EMARSIHybridStrategy',
            'worst_performer': 'Martingale Strategy (VERY HIGH RISK)',
            'avg_return': 0.052,
            'avg_win_rate': 0.58
        }
    }

    return sample_results


def create_sample_ohlc_data(instrument: str = "R_10", periods: int = 500) -> pd.DataFrame:
    """
    Create sample OHLCV data for testing and demonstration

    Args:
        instrument: Trading instrument name
        periods: Number of periods to generate

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)  # For reproducible results

    # Start date for data
    start_date = datetime.now() - timedelta(days=periods)

    # Generate timestamps
    timestamps = [start_date + timedelta(minutes=i) for i in range(periods)]

    # Base price and volatility
    if instrument == "R_10":
        base_price = 100.0
        volatility = 0.02
        drift = 0.0001
    elif instrument.startswith("frx"):
        base_price = 1.0  # Forex near 1.0
        volatility = 0.005
        drift = 0.00005
    else:
        base_price = base_price if 'base_price' in locals() else 100.0
        volatility = 0.015
        drift = 0.00008

    # Generate price series with realistic OHLC
    prices = []
    current_price = base_price

    for i in range(periods):
        # Random walk with drift
        return_pct = np.random.normal(drift, volatility / np.sqrt(1440))  # Daily volatility scaled to minutes
        price_change = current_price * return_pct

        # Generate OHLC around the new price
        body_range = abs(price_change) * (0.7 + np.random.random() * 0.3)  # 70-100% of price change for body

        if price_change >= 0:
            # Up bar
            close = current_price + abs(price_change)
            open_price = current_price + (price_change * np.random.random() * 0.5)
            high = max(open_price, close) + (abs(price_change) * np.random.random() * 0.5)
            low = min(open_price, close) - (abs(price_change) * np.random.random() * 0.3)
        else:
            # Down bar
            close = current_price + price_change
            open_price = current_price + (price_change * np.random.random() * 0.5)
            low = min(open_price, close) - (abs(price_change) * np.random.random() * 0.5)
            high = max(open_price, close) + (abs(price_change) * np.random.random() * 0.3)

            # Ensure OHLC relationships
            high = max(high, max(open_price, close))
            low = min(low, min(open_price, close))

        current_price = close

        # Generate volume based on price movement
        base_volume = 10000 + np.random.lognormal(0, 1) * 90000
        volatility_multiplier = 1 + abs(return_pct) * 20
        volume = int(base_volume * volatility_multiplier)

        prices.append({
            'timestamp': timestamps[i],
            'open': round(open_price, 5),
            'high': round(high, 5),
            'low': round(low, 5),
            'close': round(close, 5),
            'volume': volume
        })

    # Create DataFrame
    df = pd.DataFrame(prices)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    return df


def run_strategy_comparison(strategies: List[str], market_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run comparison analysis across multiple strategies

    Args:
        strategies: List of strategy names
        market_data: Market data for testing

    Returns:
        Comparative analysis results
    """
    results = []
    engine = BacktestingEngine()

    for strategy_name in strategies:
        try:
            # Simplified strategy selection (would be replaced with actual strategy functions)
            if 'MovingAverage' in strategy_name:
                # Simple MA crossover mock
                result = _mock_moving_average_backtest(engine, market_data)
            elif 'RSI' in strategy_name:
                result = _mock_rsi_backtest(engine, market_data)
            elif 'Bollinger' in strategy_name:
                result = _mock_bollinger_backtest(engine, market_data)
            else:
                # Default random strategy
                result = _mock_random_backtest(engine, market_data)

            result['strategy_name'] = strategy_name
            results.append(result)

        except Exception as e:
            logger.warning(f"Failed to test strategy {strategy_name}: {e}")
            results.append({
                'strategy_name': strategy_name,
                'status': 'FAILED',
                'error': str(e)
            })

    # Generate comparison summary
    successful_results = [r for r in results if r.get('status') != 'FAILED']

    if successful_results:
        best_strategy = max(successful_results, key=lambda x: x.get('total_return', 0))
        worst_strategy = min(successful_results, key=lambda x: x.get('total_return', 0))

        summary = {
            'total_strategies_tested': len(strategies),
            'successful_tests': len(successful_results),
            'best_performing_strategy': best_strategy['strategy_name'],
            'best_return': best_strategy.get('total_return_pct', 0),
            'worst_performing_strategy': worst_strategy['strategy_name'],
            'worst_return': worst_strategy.get('total_return_pct', 0),
            'average_return': sum(r.get('total_return_pct', 0) for r in successful_results) / len(successful_results)
        }
    else:
        summary = {'status': 'no_successful_tests'}

    return {
        'strategy_results': results,
        'comparison_summary': summary,
        'test_date': datetime.now().isoformat()
    }


def _mock_moving_average_backtest(engine: BacktestingEngine, data: pd.DataFrame) -> Dict[str, Any]:
    """Mock backtest for moving average strategy"""
    signals = []
    for i in range(50, len(data)):
        fast_ma = data.iloc[i-10:i]['close'].mean()
        slow_ma = data.iloc[i-30:i]['close'].mean()
        price = data.iloc[i]['close']

        if fast_ma > slow_ma and data.iloc[i-1:i]['close'].mean() <= data.iloc[i-31:i-1]['close'].mean():
            signals.append({'action': 'BUY', 'price': price, 'timestamp': data.index[i], 'volume': 1})
        elif fast_ma < slow_ma and data.iloc[i-1:i]['close'].mean() >= data.iloc[i-31:i-1]['close'].mean():
            signals.append({'action': 'SELL', 'price': price, 'timestamp': data.index[i], 'volume': 1})

    return engine.run_backtest(lambda df, **kwargs: signals[:20], data)  # Limit signals for demo


def _mock_rsi_backtest(engine: BacktestingEngine, data: pd.DataFrame) -> Dict[str, Any]:
    """Mock backtest for RSI strategy"""
    signals = []
    for i in range(20, len(data)):
        # Simple RSI approximation
        recent_prices = data.iloc[i-14:i]['close']
        gains = recent_prices[recent_prices > recent_prices.shift(1)].mean()
        losses = abs(recent_prices[recent_prices < recent_prices.shift(1)]).mean()
        rsi = 100 - (100 / (1 + gains/losses)) if losses > 0 else 100

        price = data.iloc[i]['close']
        if rsi < 30:
            signals.append({'action': 'BUY', 'price': price, 'timestamp': data.index[i], 'volume': 1})
        elif rsi > 70:
            signals.append({'action': 'SELL', 'price': price, 'timestamp': data.index[i], 'volume': 1})

    return engine.run_backtest(lambda df, **kwargs: signals[:15], data)


def _mock_bollinger_backtest(engine: BacktestingEngine, data: pd.DataFrame) -> Dict[str, Any]:
    """Mock backtest for Bollinger Band strategy"""
    signals = []
    for i in range(20, len(data)):
        window = data.iloc[i-20:i]['close']
        mean = window.mean()
        std = window.std()
        upper_band = mean + 2 * std
        lower_band = mean - 2 * std
        price = data.iloc[i]['close']

        if price <= lower_band:
            signals.append({'action': 'BUY', 'price': price, 'timestamp': data.index[i], 'volume': 1})
        elif price >= upper_band:
            signals.append({'action': 'SELL', 'price': price, 'timestamp': data.index[i], 'volume': 1})

    return engine.run_backtest(lambda df, **kwargs: signals[:15], data)


def _mock_random_backtest(engine: BacktestingEngine, data: pd.DataFrame) -> Dict[str, Any]:
    """Mock backtest with random signals"""
    signals = []
    for i in range(0, min(20, len(data)), 2):
        action = 'BUY' if np.random.random() > 0.5 else 'SELL'
        price = data.iloc[i]['close']
        signals.append({'action': action, 'price': price, 'timestamp': data.index[i], 'volume': 1})

    return engine.run_backtest(lambda df, **kwargs: signals, data)


# Create aliases for backward compatibility
Backtester = BacktestingEngine

# Initialize global backtesting engine
backtesting_engine = BacktestingEngine()

if __name__ == "__main__":
    # Test the functions
    print("🧪 Testing Backtesting System")
    print("=" * 40)

    # Test sample data generation
    data = create_sample_ohlc_data("R_10", 100)
    print(f"✅ Generated {len(data)} sample data points")
    print(".2f")
    print(".0f")

    # Test backtest results
    results = get_test_backtest_results()
    print(f"✅ Generated {len(results['all_results'])} sample backtest results")
    print(f"🏆 Best strategy: {results['summary']['best_performer']}")

    print("\n✨ Backtesting system ready!")
