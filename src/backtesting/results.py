"""
TokemFX Backtesting Results Management System
==============================================
Enterprise-grade results storage, retrieval, and analysis system.
Centralized database for backtest results with cross-module integration APIs.
"""

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class BacktestResultRecord:
    """Database record for backtest results."""
    id: str
    session_id: str
    strategy_class: str
    instrument: str
    timeframe: str
    start_date: datetime
    end_date: Optional[datetime]
    parameters: Dict[str, Any]
    basic_metrics: Dict[str, Any]
    advanced_metrics: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    statistical_tests: Dict[str, Any]
    data_quality: Dict[str, Any]
    raw_results: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BacktestResultsDatabase:
    """
    Enterprise-grade SQLite database for backtest results storage and retrieval.
    """

    def __init__(self, db_path: str = "data/backtest_results/results.db"):
        """Initialize database connection and create tables."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        self._create_tables()
        logger.info(f"BacktestResultsDatabase initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    strategy_class TEXT,
                    instrument TEXT,
                    timeframe TEXT,
                    start_date DATETIME,
                    end_date DATETIME,
                    parameters TEXT,  -- JSON
                    basic_metrics TEXT,  -- JSON
                    advanced_metrics TEXT,  -- JSON
                    risk_metrics TEXT,  -- JSON
                    statistical_tests TEXT,  -- JSON
                    data_quality TEXT,  -- JSON
                    raw_results TEXT,  -- JSON
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy ON backtest_results(strategy_class)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_instrument ON backtest_results(instrument)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timeframe ON backtest_results(timeframe)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON backtest_results(created_at)")
            conn.commit()

    def save_result(self, result_data: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        Save backtest result to database.

        Args:
            result_data: Complete backtest result dictionary
            session_id: Optional session identifier

        Returns:
            Result ID
        """
        result_id = str(uuid.uuid4())
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        # Extract key fields
        strategy_class = result_data.get('strategy_class', 'Unknown')
        instruments = result_data.get('instruments', [])
        instrument = instruments[0] if instruments else 'Unknown'
        date_range = result_data.get('date_range', {})
        timeframe = 'Unknown'  # Will be determined from data if available

        # Convert complex objects to JSON
        record = BacktestResultRecord(
            id=result_id,
            session_id=session_id,
            strategy_class=strategy_class,
            instrument=instrument,
            timeframe=timeframe,
            start_date=datetime.fromisoformat(date_range.get('start', datetime.now().isoformat())),
            end_date=datetime.fromisoformat(date_range.get('end', datetime.now().isoformat())) if date_range.get('end') else None,
            parameters=result_data.get('parameters', {}),
            basic_metrics=result_data.get('basic_metrics', {}),
            advanced_metrics=result_data.get('advanced_metrics', {}),
            risk_metrics=result_data.get('risk_metrics', {}),
            statistical_tests=result_data.get('statistical_tests', {}),
            data_quality=result_data.get('data_quality', {}),
            raw_results=result_data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO backtest_results (
                    id, session_id, strategy_class, instrument, timeframe,
                    start_date, end_date, parameters, basic_metrics,
                    advanced_metrics, risk_metrics, statistical_tests,
                    data_quality, raw_results, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.session_id, record.strategy_class, record.instrument, record.timeframe,
                record.start_date, record.end_date,
                json.dumps(record.parameters), json.dumps(record.basic_metrics),
                json.dumps(record.advanced_metrics), json.dumps(record.risk_metrics),
                json.dumps(record.statistical_tests), json.dumps(record.data_quality),
                json.dumps(record.raw_results), record.created_at, record.updated_at
            ))
            conn.commit()

        logger.info(f"Saved backtest result {result_id} for {strategy_class} on {instrument}")
        return result_id

    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific backtest result by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM backtest_results WHERE id = ?", (result_id,)).fetchone()
            if row:
                return self._row_to_dict(row)
        return None

    def get_results_by_strategy(self, strategy_class: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent results for a specific strategy."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM backtest_results
                WHERE strategy_class = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (strategy_class, limit)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_results_by_instrument(self, instrument: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent results for a specific instrument."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM backtest_results
                WHERE instrument = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (instrument, limit)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_recent_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent backtest results."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM backtest_results
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_best_performing_strategy(self, instrument: Optional[str] = None,
                                   metric: str = 'sharpe_ratio',
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get best performing strategies by specified metric.

        Args:
            instrument: Optional instrument filter
            metric: Performance metric to rank by
            limit: Number of results to return
        """
        with self._get_connection() as conn:
            query = """
                SELECT *,
                       json_extract(basic_metrics, ?) as metric_value
                FROM backtest_results
            """
            params = [f'$.{metric}']

            if instrument:
                query += " WHERE instrument = ?"
                params.append(instrument)

            query += " ORDER BY CAST(json_extract(basic_metrics, ?) AS REAL) DESC LIMIT ?"
            params.append(f'$.{metric}')
            params.append(str(limit))

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_portfolio_summary(self, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get portfolio-level performance summary across all backtests."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM backtest_results
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """, (start_date,)).fetchall()

            results = [self._row_to_dict(row) for row in rows]

            if not results:
                return {"error": "No results found in date range"}

            # Aggregate performance metrics
            total_return = sum(r.get('basic_metrics', {}).get('total_return_pct', 0) for r in results)
            avg_sharpe = np.mean([r.get('basic_metrics', {}).get('sharpe_ratio', 0) for r in results if r.get('basic_metrics', {}).get('sharpe_ratio')])
            total_trades = sum(r.get('basic_metrics', {}).get('total_trades', 0) for r in results)

            return {
                'total_results': len(results),
                'date_range': {'start': start_date.isoformat(), 'end': end_date.isoformat() if end_date else None},
                'portfolio_return': total_return,
                'average_sharpe': avg_sharpe,
                'total_trades': total_trades,
                'best_strategy': max(results, key=lambda x: x.get('basic_metrics', {}).get('sharpe_ratio', 0))['strategy_class'],
                'instruments_tested': list(set(r['instrument'] for r in results)),
                'strategies_tested': list(set(r['strategy_class'] for r in results))
            }

    def export_results(self, output_path: str, format: str = 'json',
                      start_date: Optional[datetime] = None,
                      strategy_filter: Optional[str] = None) -> str:
        """Export backtest results to file."""
        with self._get_connection() as conn:
            query = "SELECT * FROM backtest_results WHERE 1=1"
            params = []

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)

            if strategy_filter:
                query += " AND strategy_class = ?"
                params.append(strategy_filter)

            query += " ORDER BY created_at DESC"

            rows = conn.execute(query, params).fetchall()
            results = [self._row_to_dict(row) for row in rows]

        output_file = Path(output_path)
        if format.lower() == 'json':
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif format.lower() == 'csv':
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False)

        logger.info(f"Exported {len(results)} results to {output_file}")
        return str(output_file)

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        result = dict(row)
        # Parse JSON fields
        json_fields = ['parameters', 'basic_metrics', 'advanced_metrics', 'risk_metrics',
                      'statistical_tests', 'data_quality', 'raw_results']

        for field in json_fields:
            if field in result and result[field]:
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    result[field] = {}

        # Convert datetime strings back to datetime objects
        for date_field in ['start_date', 'end_date', 'created_at', 'updated_at']:
            if date_field in result and result[date_field]:
                try:
                    result[date_field] = datetime.fromisoformat(result[date_field])
                except (ValueError, TypeError):
                    pass

        return result


class BacktestResults:
    """
    Enhanced backtest results processing with database integration.
    """

    def __init__(self, results_data: Dict[str, Any], auto_save: bool = True, db: Optional[BacktestResultsDatabase] = None):
        """
        Initialize with raw backtest results data.

        Args:
            results_data: Raw results from BacktestEngine.run()
            auto_save: Whether to automatically save to database
            db: Optional database instance
        """
        self.raw_results = results_data
        self.db = db or BacktestResultsDatabase()
        self.result_id = None

        self._validate_results()
        self._processed_metrics = None
        self._risk_metrics = None

        if auto_save:
            try:
                self.result_id = self.db.save_result(results_data)
                logger.info(f"Auto-saved result with ID: {self.result_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-save result: {e}")

    def _validate_results(self) -> None:
        """Validate that results contain required data"""
        required_keys = ['strategy_class', 'parameters', 'net_profit', 'sharpe_ratio']
        missing_keys = [key for key in required_keys if key not in self.raw_results]

        if missing_keys:
            raise ValueError(f"Results data missing required keys: {missing_keys}")

        if 'error' in self.raw_results:
            raise ValueError(f"Results contain error: {self.raw_results['error']}")

    @property
    def basic_metrics(self) -> Dict[str, Any]:
        """Basic performance metrics"""
        return {
            'strategy': self.raw_results.get('strategy_class', 'Unknown'),
            'start_cash': self.raw_results.get('start_cash', 0),
            'final_value': self.raw_results.get('final_value', 0),
            'net_profit': self.raw_results.get('net_profit', 0),
            'total_return_pct': self.raw_results.get('total_return_pct', 0),
            'sharpe_ratio': self.raw_results.get('sharpe_ratio'),
            'max_drawdown': self.raw_results.get('max_drawdown', 0),
            'win_rate': self.raw_results.get('win_rate', 0),
            'total_trades': self.raw_results.get('total_trades', 0),
            'won_trades': self.raw_results.get('won_trades', 0),
            'lost_trades': self.raw_results.get('lost_trades', 0),
        }

    @property
    def advanced_metrics(self) -> Dict[str, Any]:
        """Advanced performance metrics"""
        return {
            'sortino_ratio': self.raw_results.get('sortino_ratio'),
            'profit_factor': self.raw_results.get('profit_factor'),
            'recovery_factor': self.raw_results.get('recovery_factor'),
            'calmar_ratio': self.raw_results.get('calmar_ratio'),
            'win_loss_ratio': self.raw_results.get('win_loss_ratio'),
            'max_consecutive_wins': self.raw_results.get('max_consecutive_wins'),
            'max_consecutive_losses': self.raw_results.get('max_consecutive_losses'),
        }

    @property
    def statistical_tests(self) -> Dict[str, Any]:
        """Statistical significance tests"""
        stats_tests = self.raw_results.get('statistical_significance', {})
        return {
            'p_value': stats_tests.get('p_value'),
            'is_significant': stats_tests.get('is_significant'),
            'test_type': stats_tests.get('test_type'),
        }

    @property
    def data_quality(self) -> Dict[str, Any]:
        """Data quality assessment"""
        return self.raw_results.get('data_quality', {})

    def get_risk_metrics(self, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics.

        Args:
            confidence_level: Statistical confidence level (0-1)

        Returns:
            Dictionary of risk metrics
        """
        if self._risk_metrics is None:
            # Extract returns series if available, otherwise use basic metrics
            net_profit = self.basic_metrics['net_profit']
            max_dd = self.basic_metrics['max_drawdown']

            # Calculate Value at Risk (VaR) approximation
            avg_trade_return = net_profit / max(self.basic_metrics['total_trades'], 1)

            # Simplified VaR calculation (assuming normal distribution)
            if avg_trade_return != 0:
                volatility = abs(avg_trade_return) * 0.5  # Conservative volatility estimate
                z_score = {0.95: 1.645, 0.99: 2.326}.get(confidence_level, 1.645)

                var_95 = -z_score * volatility * np.sqrt(self.basic_metrics['total_trades'])
                expected_shortfall = var_95 * 1.5 if var_95 < 0 else 0
            else:
                var_95 = 0
                expected_shortfall = 0

            # Risk-adjusted returns
            if abs(max_dd) > 0.001:
                sterling_ratio = net_profit / abs(max_dd)
                burke_ratio = net_profit / (max_dd ** 2) if max_dd > 0 else 0
            else:
                sterling_ratio = float('inf') if net_profit > 0 else 0
                burke_ratio = float('inf') if net_profit > 0 else 0

            self._risk_metrics = {
                'value_at_risk_95': var_95,
                'expected_shortfall': expected_shortfall,
                'sterling_ratio': sterling_ratio,
                'burke_ratio': burke_ratio,
                'ulcer_index': 0.0,  # Placeholder for now
                'downside_deviation': 0.0,  # Placeholder for now
                'tail_ratio': 0.0,  # Placeholder for now
                'confidence_level': confidence_level,
            }

        return self._risk_metrics

    def generate_summary_report(self, include_charts: bool = False) -> str:
        """Generate human-readable summary report."""
        bm = self.basic_metrics
        am = self.advanced_metrics

        report = []
        report.append("=" * 60)
        report.append(f"BACKTEST RESULTS SUMMARY - {bm['strategy']}")
        report.append("=" * 60)

        report.append(f"Period: {self.raw_results.get('date_range', {}).get('start', 'N/A')} to {self.raw_results.get('date_range', {}).get('end', 'N/A')}")
        report.append(f"Instruments: {', '.join(self.raw_results.get('instruments', ['N/A']))}")
        report.append("")

        # Parameters
        report.append("STRATEGY PARAMETERS:")
        params = self.raw_results.get('parameters', {})
        for key, value in params.items():
            report.append(f"  {key}: {value}")
        report.append("")

        # Basic Performance
        report.append("BASIC PERFORMANCE:")
        report.append(f"  Starting Capital: ${bm['start_cash']:,.2f}")
        report.append(f"  Final Value: ${bm['final_value']:,.2f}")
        report.append(f"  Net Profit: ${bm['net_profit']:,.2f}")
        report.append(f"  Total Return: {bm['total_return_pct']:,.2f}%")
        report.append("")

        # Risk Metrics
        report.append("RISK METRICS:")
        report.append(f"  Sharpe Ratio: {bm['sharpe_ratio']:.3f}" if bm['sharpe_ratio'] else "  Sharpe Ratio: N/A")
        report.append(f"  Max Drawdown: {bm['max_drawdown']:,.2f}%" if bm['max_drawdown'] else "  Max Drawdown: N/A")
        report.append(f"  Recovery Factor: {am['recovery_factor']:.3f}" if am['recovery_factor'] else "  Recovery Factor: N/A")
        report.append("")

        # Trading Statistics
        report.append("TRADING STATISTICS:")
        report.append(f"  Total Trades: {bm['total_trades']}")
        report.append(f"  Win Rate: {bm['win_rate']:,.1%}" if bm['win_rate'] else "  Win Rate: N/A")
        report.append(f"  Won Trades: {bm['won_trades']}")
        report.append(f"  Lost Trades: {bm['lost_trades']}")
        report.append("")

        # Advanced Metrics
        report.append("ADVANCED METRICS:")
        if am['sortino_ratio']:
            report.append(f"  Sortino Ratio: {am['sortino_ratio']:,.3f}")
        else:
            report.append("  Sortino Ratio: N/A")

        if am['profit_factor'] and am['profit_factor'] != float('inf'):
            report.append(f"  Profit Factor: {am['profit_factor']:,.3f}")
        else:
            report.append("  Profit Factor: N/A")

        report.append(f"  Max Consecutive Wins: {am['max_consecutive_wins']}")
        report.append(f"  Max Consecutive Losses: {am['max_consecutive_losses']}")
        report.append("")

        # Statistical Tests
        st = self.statistical_tests
        if st.get('p_value') is not None:
            report.append("STATISTICAL SIGNIFICANCE:")
            report.append(f"  Test Type: {st.get('test_type', 'Unknown')}")
            report.append(f"  P-Value: {st['p_value']:.4f}")
            report.append(f"  Significant: {'Yes' if st.get('is_significant') else 'No'}")
            report.append("")

        # Risk Analysis
        risk = self.get_risk_metrics()
        report.append("RISK ANALYSIS:")
        report.append(f"  Value at Risk (95%): ${risk['value_at_risk_95']:,.2f}")
        report.append(f"  Expected Shortfall: ${risk['expected_shortfall']:,.2f}")
        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format"""
        return {
            'timestamp': datetime.now().isoformat(),
            'result_id': self.result_id,
            'basic_metrics': self.basic_metrics,
            'advanced_metrics': self.advanced_metrics,
            'risk_metrics': self.get_risk_metrics(),
            'statistical_tests': self.statistical_tests,
            'data_quality': self.data_quality,
            'raw_results': self.raw_results,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert results to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


# Global database instance
_results_db = None

def get_results_database() -> BacktestResultsDatabase:
    """Get global results database instance."""
    global _results_db
    if _results_db is None:
        _results_db = BacktestResultsDatabase()
    return _results_db

# Integration APIs for other modules
def save_backtest_result(result_data: Dict[str, Any], session_id: Optional[str] = None) -> str:
    """
    Save backtest result to database (for use by backtesting engine).

    Args:
        result_data: Complete backtest result dictionary
        session_id: Optional session identifier

    Returns:
        Result ID
    """
    db = get_results_database()
    return db.save_result(result_data, session_id)

def get_best_strategy_for_instrument(instrument: str, metric: str = 'sharpe_ratio') -> Optional[Dict[str, Any]]:
    """
    Get best performing strategy for an instrument (for decision engine).

    Args:
        instrument: Trading instrument
        metric: Performance metric to optimize for

    Returns:
        Best strategy configuration or None
    """
    db = get_results_database()
    results = db.get_best_performing_strategy(instrument, metric, 1)
    return results[0] if results else None

def get_historical_performance_summary(instrument: Optional[str] = None,
                                     days: int = 30) -> Dict[str, Any]:
    """
    Get historical performance summary (for monitoring and reporting).

    Args:
        instrument: Optional instrument filter
        days: Number of days to look back

    Returns:
        Performance summary dictionary
    """
    db = get_results_database()
    start_date = datetime.now() - timedelta(days=days)
    return db.get_portfolio_summary(start_date)

def get_recent_backtest_results(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent backtest results (for dashboard display).

    Args:
        limit: Maximum number of results to return

    Returns:
        List of recent backtest results
    """
    db = get_results_database()
    return db.get_recent_results(limit)

def export_to_ml_format(results_list: List[BacktestResults],
                       output_path: str,
                       features: Optional[List[str]] = None,
                       targets: Optional[List[str]] = None) -> str:
    """
    Export backtest results in ML-ready format for model training.

    Args:
        results_list: List of BacktestResults objects
        output_path: Path to save the ML dataset
        features: List of parameter names to use as features
        targets: List of metric names to predict

    Returns:
        Path to saved file
    """
    # Default feature and target columns
    if features is None:
        features = ['rsi_period', 'rsi_oversold', 'rsi_overbought', 'fast_period', 'slow_period']

    if targets is None:
        targets = ['sharpe_ratio', 'total_return_pct', 'win_rate', 'net_profit']

    # Extract data
    ml_data = []

    for result in results_list:
        try:
            # Parameters as features
            params = result.raw_results.get('parameters', {})

            # Metrics as targets
            basic_metrics = result.basic_metrics
            advanced_metrics = result.advanced_metrics

            row = {}

            # Add features
            for feature in features:
                row[f'feature_{feature}'] = params.get(feature)

            # Add targets
            for target in targets:
                if target in basic_metrics:
                    row[f'target_{target}'] = basic_metrics[target]
                elif target in advanced_metrics:
                    row[f'target_{target}'] = advanced_metrics[target]
                else:
                    row[f'target_{target}'] = None

            # Add metadata
            row['strategy_class'] = result.raw_results.get('strategy_class')
            row['instrument'] = result.raw_results.get('instruments', [None])[0] if result.raw_results.get('instruments') else None
            row['timeframe'] = result.raw_results.get('date_range', {}).get('start')

            ml_data.append(row)

        except Exception as e:
            logger.warning(f"Failed to process result for ML export: {e}")
            continue

    if not ml_data:
        raise ValueError("No valid data to export for ML training")

    # Create DataFrame and save
    df = pd.DataFrame(ml_data)
    output_file = Path(output_path)

    if output_file.suffix.lower() == '.csv':
        df.to_csv(output_file, index=False)
    elif output_file.suffix.lower() == '.json':
        df.to_json(output_file, orient='records', indent=2, date_format='iso')
    else:
        # Default to CSV
        if not output_file.suffix:
            output_file = output_file.with_suffix('.csv')
        df.to_csv(output_file, index=False)

    logger.info(f"Exported {len(ml_data)} samples to {output_file}")
    return str(output_file)


# Export functions
__all__ = [
    'BacktestResults',
    'BacktestResultsDatabase',
    'save_backtest_result',
    'get_best_strategy_for_instrument',
    'get_historical_performance_summary',
    'get_recent_backtest_results',
    'get_results_database',
    'export_to_ml_format'
]
