"""
TokemFX Backtesting Analysis
============================
Advanced statistical analysis and walk-forward analysis functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StatisticalSummary:
    """Container for statistical analysis results"""
    metric_name: str
    mean: float
    std: float
    min: float
    max: float
    skewness: float
    kurtosis: float
    confidence_interval: Tuple[float, float]


@dataclass
class WalkForwardAnalysisResult:
    """Walk-forward analysis results"""
    windows: int
    train_fitness_avg: float
    test_fitness_avg: float
    overfitting_score: float
    robustness_rating: str
    out_of_sample_performance: float
    confidence_level: float


def calculate_advanced_statistics(returns: pd.Series,
                                risk_free_rate: float = 0.03,
                                confidence_level: float = 0.95) -> Dict[str, StatisticalSummary]:
    """
    Calculate comprehensive statistical metrics for returns analysis.

    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate (decimal)
        confidence_level: Statistical confidence level

    Returns:
        Dictionary of statistical summaries
    """
    if returns.empty:
        return {}

    # Convert to numpy for calculations
    returns_array = returns.dropna().values

    if len(returns_array) == 0:
        return {}

    # Annualize risk-free rate for daily returns
    daily_rf = risk_free_rate / 252  # Assuming 252 trading days
    excess_returns = returns_array - daily_rf

    # Sharpe Ratio
    sharpe = float(calculate_sharpe_ratio(returns_array, daily_rf))

    # Sortino Ratio (downside deviation only)
    downside_returns = returns_array[returns_array < 0]
    downside_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 1e-8
    sortino = float(np.mean(returns_array) / downside_std)

    # Max Drawdown
    cumulative = np.cumprod(1 + returns_array)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_dd = float(np.min(drawdowns))

    # Recovery Time (simplified)
    underwater = drawdowns < 0
    recovery_time = 0
    if underwater.any():
        recovery_streaks = []
        current_streak = 0
        for under in underwater:
            if under:
                current_streak += 1
            else:
                if current_streak > 0:
                    recovery_streaks.append(current_streak)
                    current_streak = 0
        if current_streak > 0:
            recovery_streaks.append(current_streak)
        recovery_time = np.mean(recovery_streaks) if recovery_streaks else 0

    # Value at Risk (VaR) - Historical simulation
    var_95 = float(np.percentile(returns_array, (1 - confidence_level) * 100))
    var_99 = float(np.percentile(returns_array, (1 - 0.99) * 100))

    # Expected Shortfall (CVaR)
    cvar_95 = float(np.mean(returns_array[returns_array <= var_95]))
    cvar_99 = float(np.mean(returns_array[returns_array <= var_99]))

    # Calculate confidence intervals
    mean_return = float(np.mean(returns_array))
    std_error = float(np.std(returns_array) / np.sqrt(len(returns_array)))

    # Critical value from t-distribution
    from scipy import stats
    critical_value = float(stats.t.ppf((1 + confidence_level) / 2, len(returns_array) - 1))

    ci_lower = float(mean_return - critical_value * std_error)
    ci_upper = float(mean_return + critical_value * std_error)

    # Create statistical summaries
    stats_dict = {
        'sharpe_ratio': StatisticalSummary(
            metric_name='Sharpe Ratio',
            mean=sharpe,
            std=0.0,  # Single value
            min=sharpe,
            max=sharpe,
            skewness=0.0,
            kurtosis=0.0,
            confidence_interval=(sharpe, sharpe)
        ),
        'sortino_ratio': StatisticalSummary(
            metric_name='Sortino Ratio',
            mean=sortino,
            std=0.0,
            min=sortino,
            max=sortino,
            skewness=0.0,
            kurtosis=0.0,
            confidence_interval=(sortino, sortino)
        ),
        'max_drawdown': StatisticalSummary(
            metric_name='Max Drawdown',
            mean=max_dd,
            std=0.0,
            min=max_dd,
            max=max_dd,
            skewness=0.0,
            kurtosis=0.0,
            confidence_interval=(max_dd, max_dd)
        ),
        'value_at_risk_95': StatisticalSummary(
            metric_name='VaR 95%',
            mean=var_95,
            std=0.0,
            min=var_95,
            max=var_95,
            skewness=0.0,
            kurtosis=0.0,
            confidence_interval=(var_95, var_95)
        ),
        'expected_shortfall_95': StatisticalSummary(
            metric_name='CVaR 95%',
            mean=cvar_95,
            std=0.0,
            min=cvar_95,
            max=cvar_95,
            skewness=0.0,
            kurtosis=0.0,
            confidence_interval=(cvar_95, cvar_95)
        ),
        'confidence_interval_return': StatisticalSummary(
            metric_name='Average Return',
            mean=mean_return,
            std=std_error,
            min=ci_lower,
            max=ci_upper,
            skewness=float(stats.skew(returns_array)),
            kurtosis=float(stats.kurtosis(returns_array)),
            confidence_interval=(ci_lower, ci_upper)
        )
    }

    return stats_dict


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.03) -> float:
    """
    Calculate Sharpe Ratio.

    Args:
        returns: Array of returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0

    # Annualize risk-free rate
    daily_rf = risk_free_rate / 252

    # Calculate excess returns
    excess_returns = returns - daily_rf

    # Sharpe ratio
    if np.std(excess_returns) > 0:
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    else:
        return 0.0


def perform_walk_forward_analysis(strategy_results: List[Dict[str, Any]],
                                train_months: int = 12,
                                test_months: int = 3,
                                step_months: int = 1,
                                fitness_metric: str = 'sharpe_ratio') -> WalkForwardAnalysisResult:
    """
    Perform walk-forward analysis on strategy results.

    Args:
        strategy_results: List of backtest results with date ranges
        train_months: Months for training window
        test_months: Months for testing window
        step_months: Months to step forward each window
        fitness_metric: Metric to use for fitness scoring

    Returns:
        Walk-forward analysis results
    """
    if not strategy_results:
        return WalkForwardAnalysisResult(
            windows=0, train_fitness_avg=0.0, test_fitness_avg=0.0,
            overfitting_score=0.0, robustness_rating='N/A',
            out_of_sample_performance=0.0, confidence_level=0.0
        )

    # Extract and sort by date
    results_with_dates = []
    for result in strategy_results:
        try:
            date_range = result.get('date_range', {})
            start = date_range.get('start')
            end = date_range.get('end')

            if start and end:
                results_with_dates.append({
                    'start': pd.to_datetime(start),
                    'end': pd.to_datetime(end),
                    'fitness': result.get(fitness_metric, 0),
                    'result': result
                })
        except Exception as e:
            logger.warning(f"Could not process result dates: {e}")
            continue

    if not results_with_dates:
        return WalkForwardAnalysisResult(
            windows=0, train_fitness_avg=0.0, test_fitness_avg=0.0,
            overfitting_score=0.0, robustness_rating='N/A',
            out_of_sample_performance=0.0, confidence_level=0.0
        )

    # Sort by start date
    results_with_dates.sort(key=lambda x: x['start'])

    # Create walk-forward windows
    windows = []
    start_date = results_with_dates[0]['start']
    end_date = results_with_dates[-1]['end']

    current = start_date
    while current + timedelta(days=train_months*30) + timedelta(days=test_months*30) <= end_date:
        train_start = current
        train_end = train_start + timedelta(days=train_months*30)
        test_start = train_end
        test_end = test_start + timedelta(days=test_months*30)

        # Get training data (results ending before test period)
        train_results = [r for r in results_with_dates if r['end'] <= train_end]

        # Get test results (results starting in test period)
        test_results = [r for r in results_with_dates if r['start'] >= test_start and r['end'] <= test_end]

        if train_results and test_results:
            train_fitness = np.mean([r['fitness'] for r in train_results])
            test_fitness = np.mean([r['fitness'] for r in test_results])

            windows.append({
                'train_fitness': train_fitness,
                'test_fitness': test_fitness,
                'overfitting': max(0, train_fitness - test_fitness)
            })

        current += timedelta(days=step_months*30)

    if not windows:
        return WalkForwardAnalysisResult(
            windows=0, train_fitness_avg=0.0, test_fitness_avg=0.0,
            overfitting_score=0.0, robustness_rating='N/A',
            out_of_sample_performance=0.0, confidence_level=0.0
        )

    # Calculate summary statistics
    train_fitnesses = [w['train_fitness'] for w in windows]
    test_fitnesses = [w['test_fitness'] for w in windows]
    overfitting_scores = [w['overfitting'] for w in windows]

    avg_train_fitness = np.mean(train_fitnesses)
    avg_test_fitness = np.mean(test_fitnesses)
    avg_overfitting = np.mean(overfitting_scores)

    # Assess robustness
    test_consistency = np.std(test_fitnesses) / max(abs(np.mean(test_fitnesses)), 1e-8)

    if avg_overfitting < 0.2 and test_consistency < 0.3:
        robustness = 'EXCELLENT'
        confidence = 0.95
    elif avg_overfitting < 0.5 and test_consistency < 0.5:
        robustness = 'GOOD'
        confidence = 0.80
    elif avg_overfitting < 0.8 and test_consistency < 0.7:
        robustness = 'FAIR'
        confidence = 0.60
    else:
        robustness = 'POOR'
        confidence = 0.30

    return WalkForwardAnalysisResult(
        windows=len(windows),
        train_fitness_avg=float(avg_train_fitness),
        test_fitness_avg=float(avg_test_fitness),
        overfitting_score=float(avg_overfitting),
        robustness_rating=robustness,
        out_of_sample_performance=float(avg_test_fitness),
        confidence_level=confidence
    )


def calculate_strategy_comparison(results_list: List[Dict[str, Any]],
                                metrics: List[str] = None,
                                benchmark_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compare multiple strategy results against each other and optionally a benchmark.

    Args:
        results_list: List of strategy results
        metrics: Metrics to compare
        benchmark_result: Optional benchmark to compare against

    Returns:
        Comparison analysis
    """
    if metrics is None:
        metrics = ['sharpe_ratio', 'total_return_pct', 'win_rate', 'max_drawdown']

    if not results_list:
        return {'error': 'No results to compare'}

    # Extract comparison data
    comparison_data = []
    for i, result in enumerate(results_list):
        strategy_data = {
            'strategy_id': i,
            'strategy_name': result.get('strategy_class', f'Strategy {i+1}'),
            'parameters': result.get('parameters', {}),
        }

        for metric in metrics:
            strategy_data[metric] = result.get(metric, 0)

        comparison_data.append(strategy_data)

    # Find best performers
    best_results = {}
    for metric in metrics:
        values = [r[metric] for r in comparison_data]

        # Determine if higher or lower is better
        higher_is_better = metric not in ['max_drawdown']

        if higher_is_better:
            best_idx = np.argmax(values)
            best_value = max(values)
        else:
            best_idx = np.argmin(values)
            best_value = min(values)

        best_results[metric] = {
            'strategy': comparison_data[best_idx]['strategy_name'],
            'value': best_value,
            'strategy_id': best_idx
        }

    # Statistical significance testing
    significance_tests = {}
    if len(results_list) >= 2:
        for metric in metrics:
            values = [r.get(metric, 0) for r in results_list]

            # Test if all strategies are significantly different from each other
            if len(set(values)) > 1:  # Not all identical
                try:
                    # ANOVA test for multiple group comparison
                    groups = [[v] * len(values) for v in values]  # Create groups for each strategy
                    from scipy import stats
                    f_stat, p_value = stats.f_oneway(*groups)
                    significance_tests[metric] = {
                        'f_statistic': float(f_stat),
                        'p_value': float(p_value),
                        'significant': p_value < 0.05,
                        'test_type': 'ANOVA'
                    }
                except Exception:
                    significance_tests[metric] = {'error': 'Could not perform statistical test'}

    # Performance ranking
    rankings = {}
    for metric in metrics:
        strategy_scores = [(r['strategy_name'], r[metric]) for r in comparison_data]
        higher_is_better = metric not in ['max_drawdown']

        # Sort by performance
        ranked = sorted(strategy_scores, key=lambda x: x[1], reverse=higher_is_better)
        rankings[metric] = {
            'rankings': [(rank, name, score) for rank, (name, score) in enumerate(ranked, 1)],
            'higher_is_better': higher_is_better
        }

    return {
        'comparison_data': comparison_data,
        'best_performers': best_results,
        'statistical_tests': significance_tests,
        'rankings': rankings,
        'metrics_compared': metrics,
        'total_strategies': len(results_list)
    }


def calculate_monthly_performance(returns: pd.Series,
                                start_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate monthly performance breakdown.

    Args:
        returns: Daily returns series with datetime index
        start_date: Optional start date for analysis

    Returns:
        Monthly performance summary
    """
    if returns.empty:
        return {'error': 'No returns data provided'}

    # Ensure we have a datetime index
    if not isinstance(returns.index, pd.DatetimeIndex):
        try:
            returns.index = pd.to_datetime(returns.index)
        except Exception:
            return {'error': 'Could not parse datetime index'}

    # Filter by date if provided
    if start_date:
        returns = returns[returns.index >= pd.Timestamp(start_date)]

    if returns.empty:
        return {'error': 'No data after date filtering'}

    # Resample to monthly
    monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

    # Calculate monthly statistics
    monthly_stats = {
        'total_months': len(monthly_returns),
        'positive_months': int((monthly_returns > 0).sum()),
        'negative_months': int((monthly_returns < 0).sum()),
        'best_month': {
            'return': float(monthly_returns.max()),
            'date': monthly_returns.idxmax().strftime('%Y-%m-%d') if monthly_returns.idxmax() else None
        },
        'worst_month': {
            'return': float(monthly_returns.min()),
            'date': monthly_returns.idxmin().strftime('%Y-%m-%d') if monthly_returns.idxmin() else None
        },
        'average_monthly_return': float(monthly_returns.mean()),
        'monthly_volatility': float(monthly_returns.std()),
        'win_rate': float((monthly_returns > 0).mean()),
        'consecutive_wins': int(_find_consecutive_streaks(monthly_returns > 0)['max_win_streak']),
        'consecutive_losses': int(_find_consecutive_streaks(monthly_returns < 0)['max_loss_streak']),
    }

    # Monthly breakdown by year
    by_year = {}
    monthly_years = monthly_returns.index.year
    for year in monthly_years.unique():
        year_data = monthly_returns[monthly_years == year]
        by_year[str(year)] = {
            'monthly_returns': year_data.values.tolist(),
            'average': float(year_data.mean()),
            'total_return': float((1 + year_data).prod() - 1),
            'positive_months': int((year_data > 0).sum()),
            'best_month': float(year_data.max()),
            'worst_month': float(year_data.min())
        }

    monthly_stats['by_year'] = by_year

    # Sharpe ratio (monthly)
    risk_free_monthly = 0.03 / 12  # Monthly risk-free rate
    monthly_std = float(monthly_returns.std())
    if monthly_std > 0:
        sharpe_monthly = (monthly_returns.mean() - risk_free_monthly) / monthly_std
        monthly_stats['monthly_sharpe'] = float(sharpe_monthly)
    else:
        monthly_stats['monthly_sharpe'] = 0.0

    return monthly_stats


def _find_consecutive_streaks(bool_series: pd.Series) -> Dict[str, int]:
    """Find maximum consecutive True/False streaks in boolean series"""
    if bool_series.empty:
        return {'max_win_streak': 0, 'max_loss_streak': 0}

    # Find streaks
    streaks = bool_series * (bool_series.groupby((bool_series != bool_series.shift()).cumsum()).cumsum())

    return {
        'max_win_streak': int(streaks.max()) if streaks.max() > 0 else 0,
        'max_loss_streak': 0  # Simplified for now
    }


def calculate_robustness_metrics(results_list: List[Dict[str, Any]],
                               parameter_variations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Calculate robustness metrics across multiple parameter configurations.

    Args:
        results_list: List of backtest results from different parameter sets
        parameter_variations: Optional parameter variations used

    Returns:
        Robustness analysis
    """
    if not results_list or len(results_list) < 3:
        return {
            'error': 'Need at least 3 results for robustness analysis',
            'sample_size': len(results_list)
        }

    # Extract key metrics
    sharpe_ratios = [r.get('sharpe_ratio', 0) for r in results_list]
    returns = [r.get('total_return_pct', 0) for r in results_list]
    win_rates = [r.get('win_rate', 0) for r in results_list]
    max_drawdowns = [r.get('max_drawdown', 0) for r in results_list]

    # Calculate stability metrics (coefficient of variation)
    def coefficient_of_variation(values):
        if not values or np.std(values) == 0:
            return 0.0
        return np.std(values) / abs(np.mean(values))

    robustness = {
        'sharpe_stability': 1 / (1 + coefficient_of_variation(sharpe_ratios)),
        'return_stability': 1 / (1 + coefficient_of_variation(returns)),
        'win_rate_stability': 1 / (1 + coefficient_of_variation(win_rates)),
        'drawdown_stability': 1 / (1 + coefficient_of_variation(max_drawdowns)),
    }

    # Overall robustness score (0-1, higher is better)
    robustness['overall_robustness'] = np.mean(list(robustness.values()))

    # Classify robustness
    if robustness['overall_robustness'] >= 0.8:
        robustness['rating'] = 'EXCELLENT'
        robustness['interpretation'] = 'Highly robust across parameter variations'
    elif robustness['overall_robustness'] >= 0.6:
        robustness['rating'] = 'GOOD'
        robustness['interpretation'] = 'Reasonably robust, some parameter sensitivity'
    elif robustness['overall_robustness'] >= 0.4:
        robustness['rating'] = 'FAIR'
        robustness['interpretation'] = 'Moderate robustness, parameter tuning important'
    else:
        robustness['rating'] = 'POOR'
        robustness['interpretation'] = 'Parameter sensitive, requires careful optimization'

    # Statistical confidence in robustness assessment
    robustness['confidence_score'] = min(1.0, len(results_list) / 20)  # Based on sample size
    robustness['sample_size'] = len(results_list)

    return robustness


def perform_sensitivity_analysis(base_params: Dict[str, Any],
                               param_ranges: Dict[str, List[Any]],
                               evaluation_function: Callable,
                               sensitivity_threshold: float = 0.1) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on strategy parameters.

    Args:
        base_params: Base parameter set
        param_ranges: Parameter ranges to test
        evaluation_function: Function to evaluate parameter sets
        sensitivity_threshold: Minimum sensitivity to report

    Returns:
        Sensitivity analysis results
    """
    if not param_ranges:
        return {'error': 'No parameter ranges provided'}

    base_fitness = evaluation_function(base_params)
    sensitivity_results = {}

    for param_name, param_values in param_ranges.items():
        if param_name not in base_params:
            continue

        param_sensitivities = []

        for value in param_values:
            if value == base_params[param_name]:
                continue  # Skip base value

            # Test parameter variation
            test_params = base_params.copy()
            test_params[param_name] = value

            try:
                fitness = evaluation_function(test_params)
                sensitivity = abs(fitness - base_fitness) / max(abs(base_fitness), 1e-8)
                param_sensitivities.append({
                    'value': value,
                    'fitness': fitness,
                    'sensitivity': sensitivity
                })
            except Exception as e:
                logger.warning(f"Failed to evaluate {param_name}={value}: {e}")

        if param_sensitivities:
            # Find most sensitive variations
            significant_changes = [s for s in param_sensitivities if s['sensitivity'] >= sensitivity_threshold]
            max_sensitivity = max([s['sensitivity'] for s in param_sensitivities])

            sensitivity_results[param_name] = {
                'base_value': base_params[param_name],
                'max_sensitivity': max_sensitivity,
                'significant_variations': len(significant_changes),
                'most_sensitive_value': max(param_sensitivities, key=lambda x: x['sensitivity'])['value'],
                'variation_summary': param_sensitivities[:5]  # Top 5 variations
            }

    # Overall sensitivity assessment
    if sensitivity_results:
        avg_sensitivity = np.mean([r['max_sensitivity'] for r in sensitivity_results.values()])

        overall_assessment = {
            'overall_sensitivity': avg_sensitivity,
            'most_sensitive_parameter': max(sensitivity_results.keys(),
                                          key=lambda k: sensitivity_results[k]['max_sensitivity']),
            'stable_parameters': [k for k, v in sensitivity_results.items()
                                if v['max_sensitivity'] < sensitivity_threshold],
        }

        if avg_sensitivity < 0.1:
            overall_assessment['rating'] = 'LOW SENSITIVITY'
        elif avg_sensitivity < 0.3:
            overall_assessment['rating'] = 'MODERATE SENSITIVITY'
        else:
            overall_assessment['rating'] = 'HIGH SENSITIVITY'

        sensitivity_results['overall_assessment'] = overall_assessment

    return sensitivity_results
