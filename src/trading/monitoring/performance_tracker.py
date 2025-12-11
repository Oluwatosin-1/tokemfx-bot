"""
Performance Tracker Module
==========================
Comprehensive trading performance tracking and analytics system.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import json
import os

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Advanced performance tracking system for trading strategies and portfolios.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "cache/performance_data.json"
        self.performance_data = {}
        self.trade_history = []
        self.strategy_metrics = {}
        self.portfolio_metrics = {}

        # Create storage directory if it doesn't exist
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        # Load existing data
        self._load_performance_data()

        logger.info("PerformanceTracker initialized")

    def record_trade(self,
                    trade_id: str,
                    instrument: str,
                    direction: str,
                    entry_price: float,
                    exit_price: float,
                    quantity: int,
                    entry_time: datetime,
                    exit_time: datetime,
                    strategy_name: str,
                    pnl: float,
                    commission: float = 0.0,
                    notes: str = "") -> bool:
        """
        Record a completed trade for performance tracking.

        Args:
            trade_id: Unique trade identifier
            instrument: Trading instrument
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            exit_price: Exit price
            quantity: Position quantity
            entry_time: Trade entry timestamp
            exit_time: Trade exit timestamp
            strategy_name: Name of strategy used
            pnl: Profit/loss amount
            commission: Trading commission
            notes: Additional trade notes

        Returns:
            Success status
        """
        try:
            trade_record = {
                'trade_id': trade_id,
                'instrument': instrument,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'strategy_name': strategy_name,
                'pnl': pnl,
                'commission': commission,
                'net_pnl': pnl - commission,
                'profit_pct': ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0,
                'hold_time_seconds': (exit_time - entry_time).total_seconds(),
                'notes': notes,
                'recorded_at': datetime.now()
            }

            self.trade_history.append(trade_record)

            # Update strategy metrics
            self._update_strategy_metrics(strategy_name, trade_record)

            # Auto-save if configured
            if len(self.trade_history) % 10 == 0:  # Save every 10 trades
                self.save_performance_data()

            logger.info(f"Recorded trade {trade_id}: {pnl:.2f} PNL ({strategy_name})")

            return True

        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            return False

    def _update_strategy_metrics(self, strategy_name: str, trade_record: Dict[str, Any]):
        """
        Update performance metrics for a specific strategy.

        Args:
            strategy_name: Name of the strategy
            trade_record: Trade record dictionary
        """
        if strategy_name not in self.strategy_metrics:
            self.strategy_metrics[strategy_name] = {
                'trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'total_commission': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'avg_trade_duration': 0.0,
                'last_updated': datetime.now()
            }

        metrics = self.strategy_metrics[strategy_name]
        pnl = trade_record['net_pnl']

        # Update basic counters
        metrics['trades'] += 1
        metrics['total_pnl'] += pnl
        metrics['total_commission'] += trade_record['commission']

        if pnl > 0:
            metrics['winning_trades'] += 1
            metrics['largest_win'] = max(metrics['largest_win'], pnl)
        else:
            metrics['losing_trades'] += 1
            metrics['largest_loss'] = min(metrics['largest_loss'], pnl)

        # Update averages
        if metrics['winning_trades'] > 0:
            metrics['avg_win'] = metrics['total_pnl'] / metrics['winning_trades'] if metrics['total_pnl'] > 0 else 0
        if metrics['losing_trades'] > 0:
            metrics['avg_loss'] = abs(metrics['total_pnl']) / metrics['losing_trades'] if metrics['total_pnl'] < 0 else 0

        # Calculate ratios
        metrics['win_rate'] = metrics['winning_trades'] / metrics['trades'] if metrics['trades'] > 0 else 0

        total_wins = metrics['avg_win'] * metrics['winning_trades']
        total_losses = abs(metrics['avg_loss']) * metrics['losing_trades']
        metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else float('inf')

        # Update average trade duration
        total_duration = sum(trade_record['hold_time_seconds'] for trade in self.trade_history
                           if trade['strategy_name'] == strategy_name)
        metrics['avg_trade_duration'] = total_duration / metrics['trades'] if metrics['trades'] > 0 else 0

        metrics['last_updated'] = datetime.now()

    def get_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for a specific strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Performance metrics dictionary
        """
        if strategy_name not in self.strategy_metrics:
            return {'error': f'Strategy {strategy_name} not found'}

        metrics = self.strategy_metrics[strategy_name].copy()

        # Calculate additional derived metrics
        if metrics['trades'] > 0:
            # P&L per trade
            metrics['pnl_per_trade'] = metrics['total_pnl'] / metrics['trades']

            # Return on risk metrics
            if metrics['avg_loss'] != 0:
                metrics['kelly_criterion'] = (metrics['win_rate'] - ((1 - metrics['win_rate']) / abs(metrics['total_pnl'] / metrics['trades'] / metrics['avg_loss']))) if metrics['avg_loss'] != 0 else 0
        else:
            metrics['pnl_per_trade'] = 0.0
            metrics['kelly_criterion'] = 0.0

        return {
            'strategy_name': strategy_name,
            'metrics': metrics,
            'grade': self._grade_strategy_performance(metrics)
        }

    def get_portfolio_performance(self,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate overall portfolio performance metrics.

        Args:
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)

        Returns:
            Portfolio performance metrics
        """
        try:
            # Filter trades by date range
            filtered_trades = self._filter_trades_by_date(start_date, end_date)

            if not filtered_trades:
                return {'error': 'No trades found in specified date range'}

            # Calculate portfolio metrics
            total_pnl = sum(trade['net_pnl'] for trade in filtered_trades)
            total_commission = sum(trade['commission'] for trade in filtered_trades)
            winning_trades = len([t for t in filtered_trades if t['net_pnl'] > 0])
            losing_trades = len([t for t in filtered_trades if t['net_pnl'] <= 0])

            # Calculate returns series for advanced metrics
            pnl_series = self._calculate_pnl_series(filtered_trades)

            return {
                'total_trades': len(filtered_trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': winning_trades / len(filtered_trades) if filtered_trades else 0,
                'total_pnl': total_pnl,
                'total_commission': total_commission,
                'net_pnl': total_pnl - total_commission,
                'avg_trade_pnl': total_pnl / len(filtered_trades) if filtered_trades else 0,
                'largest_win': max([t['net_pnl'] for t in filtered_trades]) if filtered_trades else 0,
                'largest_loss': min([t['net_pnl'] for t in filtered_trades]) if filtered_trades else 0,
                'profit_factor': self._calculate_profit_factor(filtered_trades),
                'sharpe_ratio': self._calculate_sharpe_ratio(pnl_series),
                'max_drawdown': self._calculate_max_drawdown(pnl_series),
                'recovery_factor': self._calculate_recovery_factor(pnl_series),
                'date_range': {
                    'start': start_date or filtered_trades[0]['entry_time'],
                    'end': end_date or filtered_trades[-1]['exit_time']
                }
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}")
            return {'error': str(e)}

    def _filter_trades_by_date(self,
                             start_date: Optional[datetime],
                             end_date: Optional[datetime]) -> List[Dict[str, Any]]:
        """
        Filter trades by date range.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Filtered trades
        """
        if not start_date and not end_date:
            return self.trade_history

        filtered = []
        for trade in self.trade_history:
            trade_date = trade['exit_time']
            if ((not start_date or trade_date >= start_date) and
                (not end_date or trade_date <= end_date)):
                filtered.append(trade)

        return filtered

    def _calculate_pnl_series(self, trades: List[Dict[str, Any]]) -> pd.Series:
        """
        Calculate cumulative P&L series from trades.

        Args:
            trades: List of trade records

        Returns:
            P&L series indexed by date
        """
        # Group trades by date and calculate daily P&L
        pnl_by_date = {}
        for trade in trades:
            date_key = trade['exit_time'].date()
            if date_key not in pnl_by_date:
                pnl_by_date[date_key] = 0.0
            pnl_by_date[date_key] += trade['net_pnl']

        # Create pandas series
        dates = sorted(pnl_by_date.keys())
        pnl_values = [pnl_by_date[date] for date in dates]

        return pd.Series(pnl_values, index=dates)

    def _calculate_profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate profit factor from trades.

        Args:
            trades: List of trade records

        Returns:
            Profit factor
        """
        winning_pnl = sum(t['net_pnl'] for t in trades if t['net_pnl'] > 0)
        losing_pnl = abs(sum(t['net_pnl'] for t in trades if t['net_pnl'] < 0))

        return winning_pnl / losing_pnl if losing_pnl > 0 else float('inf')

    def _calculate_sharpe_ratio(self, pnl_series: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate annualized Sharpe ratio.

        Args:
            pnl_series: P&L series
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(pnl_series) < 2:
            return 0.0

        # Calculate daily returns
        returns = pnl_series.pct_change().dropna()

        if len(returns) < 2 or returns.std() == 0:
            return 0.0

        # Annualize metrics
        annual_return = returns.mean() * 252
        annual_volatility = returns.std() * np.sqrt(252)

        return (annual_return - risk_free_rate) / annual_volatility

    def _calculate_max_drawdown(self, pnl_series: pd.Series) -> float:
        """
        Calculate maximum drawdown from P&L series.

        Args:
            pnl_series: P&L series

        Returns:
            Maximum drawdown
        """
        if len(pnl_series) < 2:
            return 0.0

        cumulative = pnl_series.cumsum()
        running_max = cumulative.expanding().max()
        drawdowns = cumulative - running_max

        return drawdowns.min()

    def _calculate_recovery_factor(self, pnl_series: pd.Series) -> float:
        """
        Calculate recovery factor (net profit / max drawdown).

        Args:
            pnl_series: P&L series

        Returns:
            Recovery factor
        """
        if len(pnl_series) < 2:
            return 0.0

        net_profit = pnl_series.sum()
        max_dd = self._calculate_max_drawdown(pnl_series)

        return net_profit / abs(max_dd) if max_dd != 0 else 0.0

    def _grade_strategy_performance(self, metrics: Dict[str, Any]) -> str:
        """
        Grade strategy performance based on metrics.

        Args:
            metrics: Performance metrics

        Returns:
            Performance grade (A+, A, B, C, D, F)
        """
        score = 0

        # Win rate scoring (max 25 points)
        if metrics['win_rate'] >= 0.6:
            score += 25
        elif metrics['win_rate'] >= 0.5:
            score += 20
        elif metrics['win_rate'] >= 0.4:
            score += 15

        # Profit factor scoring (max 25 points)
        if metrics['profit_factor'] >= 2.0:
            score += 25
        elif metrics['profit_factor'] >= 1.5:
            score += 20
        elif metrics['profit_factor'] >= 1.2:
            score += 15

        # Sharpe ratio scoring (max 25 points)
        if metrics.get('sharpe_ratio', 0) >= 2.0:
            score += 25
        elif metrics.get('sharpe_ratio', 0) >= 1.5:
            score += 20
        elif metrics.get('sharpe_ratio', 0) >= 1.0:
            score += 15

        # Maximum drawdown scoring (max 25 points)
        if abs(metrics.get('max_drawdown', 0)) <= 0.1:  # <= 10%
            score += 25
        elif abs(metrics.get('max_drawdown', 0)) <= 0.2:  # <= 20%
            score += 20
        elif abs(metrics.get('max_drawdown', 0)) <= 0.3:  # <= 30%
            score += 15

        # Convert score to grade
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

    def get_trade_history(self,
                         strategy_name: Optional[str] = None,
                         instrument: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get filtered trade history.

        Args:
            strategy_name: Filter by strategy
            instrument: Filter by instrument
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of trades to return

        Returns:
            Filtered trade history
        """
        trades = self.trade_history

        # Apply filters
        if strategy_name:
            trades = [t for t in trades if t['strategy_name'] == strategy_name]
        if instrument:
            trades = [t for t in trades if t['instrument'] == instrument]
        if start_date:
            trades = [t for t in trades if t['exit_time'] >= start_date]
        if end_date:
            trades = [t for t in trades if t['exit_time'] <= end_date]

        # Sort by exit time (most recent first) and limit
        trades.sort(key=lambda x: x['exit_time'], reverse=True)
        return trades[:limit]

    def save_performance_data(self) -> bool:
        """
        Save performance data to disk.

        Returns:
            Success status
        """
        try:
            data = {
                'trade_history': self.trade_history,
                'strategy_metrics': self.strategy_metrics,
                'portfolio_metrics': self.portfolio_metrics,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Performance data saved to {self.storage_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
            return False

    def _load_performance_data(self) -> bool:
        """
        Load performance data from disk.

        Returns:
            Success status
        """
        try:
            if not os.path.exists(self.storage_path):
                logger.info(f"Performance data file does not exist: {self.storage_path}")
                return False

            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Convert datetime strings back to datetime objects
            for trade in data.get('trade_history', []):
                for date_field in ['entry_time', 'exit_time', 'recorded_at']:
                    if date_field in trade and trade[date_field]:
                        trade[date_field] = datetime.fromisoformat(trade[date_field])

            self.trade_history = data.get('trade_history', [])
            self.strategy_metrics = data.get('strategy_metrics', {})
            self.portfolio_metrics = data.get('portfolio_metrics', {})

            logger.info(f"Loaded {len(self.trade_history)} trades and {len(self.strategy_metrics)} strategies")
            return True

        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
            return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary.

        Returns:
            Performance summary dictionary
        """
        try:
            portfolio_perf = self.get_portfolio_performance()

            strategy_summaries = []
            for strategy_name in self.strategy_metrics.keys():
                strategy_summaries.append(self.get_strategy_performance(strategy_name))

            return {
                'overall_portfolio': portfolio_perf,
                'strategy_summaries': strategy_summaries,
                'total_strategies': len(self.strategy_metrics),
                'total_trades': len(self.trade_history),
                'data_quality_score': self._calculate_data_quality_score(),
                'performance_grade': self._grade_overall_performance(portfolio_perf, strategy_summaries),
                'generated_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}

    def _calculate_data_quality_score(self) -> float:
        """
        Calculate data quality score based on completeness and consistency.

        Returns:
            Quality score (0-1)
        """
        if not self.trade_history:
            return 0.0

        total_trades = len(self.trade_history)
        required_fields = ['trade_id', 'instrument', 'entry_price', 'exit_price', 'pnl']

        complete_records = 0
        for trade in self.trade_history:
            if all(field in trade for field in required_fields):
                complete_records += 1

        return complete_records / total_trades if total_trades > 0 else 0.0

    def _grade_overall_performance(self,
                                 portfolio_perf: Dict[str, Any],
                                 strategy_summaries: List[Dict[str, Any]]) -> str:
        """
        Grade overall system performance.

        Args:
            portfolio_perf: Portfolio performance metrics
            strategy_summaries: Individual strategy summaries

        Returns:
            Overall performance grade
        """
        if 'error' in portfolio_perf:
            return 'Incomplete Data'

        score = 0

        # Portfolio-level scoring
        if portfolio_perf.get('win_rate', 0) >= 0.55:
            score += 30
        elif portfolio_perf.get('win_rate', 0) >= 0.45:
            score += 20

        if portfolio_perf.get('profit_factor', 0) >= 1.5:
            score += 25
        elif portfolio_perf.get('profit_factor', 0) >= 1.2:
            score += 15

        if portfolio_perf.get('sharpe_ratio', 0) >= 1.5:
            score += 25
        elif portfolio_perf.get('sharpe_ratio', 0) >= 1.0:
            score += 15

        if abs(portfolio_perf.get('max_drawdown', 0)) <= 0.15:
            score += 20
        elif abs(portfolio_perf.get('max_drawdown', 0)) <= 0.25:
            score += 10

        # Convert score to grade
        if score >= 90:
            return 'A+ (Exceptional)'
        elif score >= 80:
            return 'A (Excellent)'
        elif score >= 70:
            return 'B (Good)'
        elif score >= 60:
            return 'C (Fair)'
        elif score >= 50:
            return 'D (Poor)'
        else:
            return 'F (Failing)'


# Convenience function
def create_performance_tracker(storage_path: Optional[str] = None) -> PerformanceTracker:
    """
    Create and return a performance tracker instance.

    Args:
        storage_path: Path to store performance data

    Returns:
        Configured PerformanceTracker instance
    """
    return PerformanceTracker(storage_path)


__all__ = [
    'PerformanceTracker',
    'create_performance_tracker'
]
