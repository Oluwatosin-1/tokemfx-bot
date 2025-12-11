"""
TokemFX Strategy Optimizer
==========================
Advanced parameter optimization with grid search, Bayesian optimization, and walk-forward analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Type, Dict, Any, List, Union, Tuple, Optional, Callable
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

try:
    from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
    _HYPEROPT_AVAILABLE = True
except ImportError:
    _HYPEROPT_AVAILABLE = False
    fmin = tpe = hp = Trials = STATUS_OK = None

from .engine import BacktestEngine
from src.trading.execution.data_handler import DataHandler
from src.strategy.base.base_strategy import BaseStrategy


@dataclass
class OptimizationResult:
    """Container for optimization results"""
    parameters: Dict[str, Any]
    fitness_score: float
    metrics: Dict[str, Any]
    rank: int


@dataclass
class WalkForwardWindow:
    """Walk-forward analysis window"""
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    optimized_params: Dict[str, Any]
    test_fitness: float
    overfitting_score: float


def optimize_strategy(
    strategy_class: Type[BaseStrategy],
    parameter_grid: Dict[str, List[Any]],
    instruments: Union[str, List[str]],
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    data_handler: DataHandler,
    method: str = "grid",
    max_evaluations: int = 100,
    optimization_target: str = "sharpe_ratio",
    constraint_function: Optional[Callable] = None,
    **engine_kwargs
) -> Dict[str, Any]:
    """
    Advanced strategy optimization with multiple algorithms.

    Args:
        strategy_class: The strategy class to optimize
        parameter_grid: Dictionary of parameter names to lists of values
        instruments: Trading instruments to use
        timeframe: Chart timeframe
        start_date: Start of optimization period
        end_date: End of optimization period
        data_handler: Data handler instance
        method: Optimization method ('grid', 'random', 'bayesian')
        max_evaluations: Maximum evaluations for non-grid methods
        optimization_target: Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate')
        constraint_function: Optional constraint function
        **engine_kwargs: Additional backtest engine parameters

    Returns:
        Dictionary with optimization results
    """
    logger.info(f"Starting {method} optimization for {strategy_class.__name__}")

    # Create backtest engine
    engine = BacktestEngine(data_handler=data_handler, **engine_kwargs)

    results = []

    if method == "grid":
        results = _grid_search_optimization(
            engine, strategy_class, parameter_grid,
            instruments, timeframe, start_date, end_date,
            optimization_target, constraint_function
        )

    elif method == "random":
        results = _random_search_optimization(
            engine, strategy_class, parameter_grid,
            instruments, timeframe, start_date, end_date,
            max_evaluations, optimization_target, constraint_function
        )

    elif method == "bayesian":
        if not _HYPEROPT_AVAILABLE:
            raise ImportError("Bayesian optimization requires hyperopt. Install with: pip install hyperopt")
        results = _bayesian_optimization(
            engine, strategy_class, parameter_grid,
            instruments, timeframe, start_date, end_date,
            max_evaluations, optimization_target, constraint_function
        )

    else:
        raise ValueError(f"Unknown optimization method: {method}")

    if not results:
        return {"error": "No optimization results generated"}

    # Sort results by fitness score (best first)
    results.sort(key=lambda x: x.fitness_score, reverse=True)

    # Add ranking to results
    for i, result in enumerate(results):
        result.rank = i + 1

    best_result = results[0]

    optimization_summary = {
        "method": method,
        "total_evaluations": len(results),
        "best_parameters": best_result.parameters,
        "best_fitness": best_result.fitness_score,
        "optimization_target": optimization_target,
        "all_results": [result.__dict__ for result in results],
        "convergence_analysis": _analyze_convergence(results),
        "parameter_importance": _analyze_parameter_importance(results),
    }

    logger.info(f"Optimization completed. Best {optimization_target}: {best_result.fitness_score:.4f}")
    return optimization_summary


def _grid_search_optimization(
    engine: BacktestEngine,
    strategy_class: Type[BaseStrategy],
    param_grid: Dict[str, List[Any]],
    instruments: Union[str, List[str]],
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    target_metric: str,
    constraint_func: Optional[Callable]
) -> List[OptimizationResult]:
    """Perform grid search optimization"""
    from itertools import product

    param_names = list(param_grid.keys())
    param_combinations = list(product(*[param_grid[name] for name in param_names]))

    logger.info(f"Grid search: {len(param_combinations)} parameter combinations")

    results = []
    for i, param_values in enumerate(param_combinations):
        params = dict(zip(param_names, param_values))

        # Apply constraints if provided
        if constraint_func and not constraint_func(params):
            continue

        try:
            logger.debug(f"Evaluating combination {i+1}/{len(param_combinations)}: {params}")
            backtest_result = engine.run(
                strategy_class, params, instruments, timeframe, start_date, end_date
            )

            if "error" in backtest_result:
                logger.warning(f"Backtest failed for params {params}: {backtest_result['error']}")
                continue

            fitness_score = _calculate_fitness_score(backtest_result, target_metric)
            metrics = _extract_key_metrics(backtest_result)

            results.append(OptimizationResult(
                parameters=params,
                fitness_score=fitness_score,
                metrics=metrics,
                rank=0  # Will be set later
            ))

        except Exception as e:
            logger.error(f"Optimization iteration failed: {e}")
            continue

    return results


def _random_search_optimization(
    engine: BacktestEngine,
    strategy_class: Type[BaseStrategy],
    param_grid: Dict[str, List[Any]],
    instruments: Union[str, List[str]],
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    max_evals: int,
    target_metric: str,
    constraint_func: Optional[Callable]
) -> List[OptimizationResult]:
    """Perform random search optimization"""
    logger.info(f"Random search: {max_evals} evaluations")

    results = []
    eval_count = 0

    while eval_count < max_evals:
        # Sample random parameters
        params = {}
        for param_name, param_values in param_grid.items():
            params[param_name] = np.random.choice(param_values)

        # Apply constraints if provided
        if constraint_func and not constraint_func(params):
            continue

        # Check for duplicate parameters (avoid re-testing same combo)
        if any(r.parameters == params for r in results):
            continue

        try:
            logger.debug(f"Evaluating random combination {eval_count+1}/{max_evals}: {params}")
            backtest_result = engine.run(
                strategy_class, params, instruments, timeframe, start_date, end_date
            )

            if "error" in backtest_result:
                logger.warning(f"Backtest failed for params {params}: {backtest_result['error']}")
                eval_count += 1
                continue

            fitness_score = _calculate_fitness_score(backtest_result, target_metric)
            metrics = _extract_key_metrics(backtest_result)

            results.append(OptimizationResult(
                parameters=params,
                fitness_score=fitness_score,
                metrics=metrics,
                rank=0
            ))

            eval_count += 1

        except Exception as e:
            logger.error(f"Random search iteration failed: {e}")
            eval_count += 1
            continue

    return results


def _bayesian_optimization(
    engine: BacktestEngine,
    strategy_class: Type[BaseStrategy],
    param_grid: Dict[str, List[Any]],
    instruments: Union[str, List[str]],
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    max_evals: int,
    target_metric: str,
    constraint_func: Optional[Callable]
) -> List[OptimizationResult]:
    """Perform Bayesian optimization using hyperopt"""
    logger.info(f"Bayesian optimization: {max_evals} evaluations")

    # Convert parameter grid to hyperopt space
    space = {}
    for param_name, param_values in param_grid.items():
        if isinstance(param_values[0], int):
            space[param_name] = hp.choice(param_name, param_values)
        elif isinstance(param_values[0], float):
            space[param_name] = hp.choice(param_name, param_values)
        else:
            # For non-numeric parameters
            space[param_name] = hp.choice(param_name, param_values)

    def objective(params):
        # Apply constraints
        if constraint_func and not constraint_func(params):
            return {'loss': float('inf'), 'status': STATUS_OK}

        try:
            backtest_result = engine.run(
                strategy_class, params, instruments, timeframe, start_date, end_date
            )

            if "error" in backtest_result:
                return {'loss': float('inf'), 'status': STATUS_OK, 'params': params}

            fitness_score = _calculate_fitness_score(backtest_result, target_metric)
            loss = -fitness_score  # Minimize negative fitness

            return {
                'loss': loss,
                'status': STATUS_OK,
                'params': params,
                'backtest_result': backtest_result
            }

        except Exception as e:
            logger.error(f"Bayesian optimization objective failed: {e}")
            return {'loss': float('inf'), 'status': STATUS_OK, 'params': params}

    # Run optimization
    trials = Trials()
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=max_evals,
        trials=trials
    )

    # Convert results to OptimizationResult objects
    results = []
    for trial in trials.results:
        if trial['status'] == STATUS_OK and 'backtest_result' in trial:
            backtest_result = trial['backtest_result']
            fitness_score = _calculate_fitness_score(backtest_result, target_metric)
            metrics = _extract_key_metrics(backtest_result)

            results.append(OptimizationResult(
                parameters=trial['params'],
                fitness_score=fitness_score,
                metrics=metrics,
                rank=0
            ))

    return results


def walk_forward_analysis(
    strategy_class: Type[BaseStrategy],
    parameter_grid: Dict[str, List[Any]],
    instruments: Union[str, List[str]],
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    data_handler: DataHandler,
    train_months: int = 12,
    test_months: int = 3,
    step_months: int = 1,
    optimization_target: str = "sharpe_ratio",
    **engine_kwargs
) -> Dict[str, Any]:
    """
    Perform walk-forward analysis for strategy validation.

    Args:
        strategy_class: The strategy class to analyze
        parameter_grid: Dictionary of parameter names to lists of values
        instruments: Trading instruments
        timeframe: Chart timeframe
        start_date: Start of analysis period
        end_date: End of analysis period
        data_handler: Data handler instance
        train_months: Months for training/optimization
        test_months: Months for testing/validation
        step_months: Months to step forward each iteration
        optimization_target: Metric to optimize during training
        **engine_kwargs: Additional backtest engine parameters

    Returns:
        Dictionary with walk-forward analysis results
    """
    logger.info(f"Starting walk-forward analysis for {strategy_class.__name__}")

    engine = BacktestEngine(data_handler=data_handler, **engine_kwargs)

    train_window = timedelta(days=train_months * 30)
    test_window = timedelta(days=test_months * 30)
    step = timedelta(days=step_months * 30)

    windows = []
    current = start_date

    # Generate walk-forward windows
    while current + train_window + test_window <= end_date:
        train_start = current
        train_end = train_start + train_window
        test_start = train_end
        test_end = test_start + test_window

        windows.append(WalkForwardWindow(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            optimized_params={},
            test_fitness=0.0,
            overfitting_score=0.0
        ))

        current += step

    logger.info(f"Generated {len(windows)} walk-forward windows")

    window_results = []

    for i, window in enumerate(windows):
        logger.info(f"Processing window {i+1}/{len(windows)}: Train {window.train_start.date()} to {window.train_end.date()}, Test {window.test_start.date()} to {window.test_end.date()}")

        try:
            # Optimize on training data
            train_optimization = optimize_strategy(
                strategy_class=strategy_class,
                parameter_grid=parameter_grid,
                instruments=instruments,
                timeframe=timeframe,
                start_date=window.train_start,
                end_date=window.train_end,
                data_handler=data_handler,
                method="grid",
                optimization_target=optimization_target,
                **engine_kwargs
            )

            if "error" in train_optimization:
                logger.warning(f"Training optimization failed for window {i+1}: {train_optimization['error']}")
                continue

            best_params = train_optimization["best_parameters"]
            train_fitness = train_optimization["best_fitness"]

            # Test on out-of-sample data
            test_result = engine.run(
                strategy_class, best_params, instruments, timeframe,
                window.test_start, window.test_end
            )

            if "error" in test_result:
                logger.warning(f"Testing failed for window {i+1}: {test_result['error']}")
                continue

            test_fitness = _calculate_fitness_score(test_result, optimization_target)

            # Calculate overfitting
            overfitting_score = max(0, train_fitness - test_fitness)

            # Store results
            window.optimized_params = best_params
            window.test_fitness = test_fitness
            window.overfitting_score = overfitting_score

            window_results.append({
                "window_index": i + 1,
                "train_period": {"start": window.train_start.isoformat(), "end": window.train_end.isoformat()},
                "test_period": {"start": window.test_start.isoformat(), "end": window.test_end.isoformat()},
                "optimized_parameters": best_params,
                "train_fitness": train_fitness,
                "test_fitness": test_fitness,
                "overfitting_score": overfitting_score,
                "test_metrics": _extract_key_metrics(test_result),
            })

        except Exception as e:
            logger.error(f"Walk-forward window {i+1} failed: {e}")
            continue

    # Analyze overall results
    analysis = {
        "total_windows": len(windows),
        "successful_windows": len(window_results),
        "average_test_fitness": np.mean([w["test_fitness"] for w in window_results]) if window_results else 0,
        "average_overfitting": np.mean([w["overfitting_score"] for w in window_results]) if window_results else 0,
        "fitness_stability": np.std([w["test_fitness"] for w in window_results]) if window_results else 0,
        "robustness_score": _calculate_robustness_score(window_results),
        "window_results": window_results,
    }

    logger.info(f"Walk-forward analysis completed. Average test fitness: {analysis['average_test_fitness']:.4f}")
    return analysis


def _calculate_fitness_score(backtest_result: Dict[str, Any], target_metric: str) -> float:
    """Calculate fitness score based on target metric"""
    if target_metric == "sharpe_ratio":
        return backtest_result.get("sharpe_ratio", -999)
    elif target_metric == "total_return_pct":
        return backtest_result.get("total_return_pct", -999)
    elif target_metric == "win_rate":
        return backtest_result.get("win_rate", -999)
    elif target_metric == "profit_factor":
        pf = backtest_result.get("profit_factor", 1)
        return pf if pf != float('inf') else 999
    elif target_metric == "net_profit":
        return backtest_result.get("net_profit", -999)
    elif target_metric == "sortino_ratio":
        return backtest_result.get("sortino_ratio", -999)
    else:
        # Composite score
        sharpe = backtest_result.get("sharpe_ratio", 0)
        returns = backtest_result.get("total_return_pct", 0) / 100  # Convert to decimal
        win_rate = backtest_result.get("win_rate", 0)
        return (sharpe * 0.4 + returns * 0.3 + win_rate * 0.3)


def _extract_key_metrics(backtest_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key performance metrics from backtest results"""
    return {
        "sharpe_ratio": backtest_result.get("sharpe_ratio"),
        "total_return_pct": backtest_result.get("total_return_pct"),
        "net_profit": backtest_result.get("net_profit"),
        "max_drawdown": backtest_result.get("max_drawdown"),
        "win_rate": backtest_result.get("win_rate"),
        "total_trades": backtest_result.get("total_trades"),
        "profit_factor": backtest_result.get("profit_factor"),
        "sortino_ratio": backtest_result.get("sortino_ratio"),
        "recovery_factor": backtest_result.get("recovery_factor"),
    }


def _analyze_convergence(results: List[OptimizationResult]) -> Dict[str, Any]:
    """Analyze optimization convergence"""
    if not results:
        return {"error": "No results to analyze"}

    fitness_scores = [r.fitness_score for r in results]
    best_scores = []
    current_best = float('-inf')

    for score in sorted(results, key=lambda x: -x.fitness_score):
        current_best = max(current_best, score.fitness_score)
        best_scores.append(current_best)

    return {
        "final_best_score": max(fitness_scores),
        "convergence_rate": len([s for s in fitness_scores if s > np.mean(fitness_scores)]) / len(fitness_scores),
        "score_distribution": {
            "mean": np.mean(fitness_scores),
            "std": np.std(fitness_scores),
            "min": min(fitness_scores),
            "max": max(fitness_scores),
        }
    }


def _analyze_parameter_importance(results: List[OptimizationResult]) -> Dict[str, Any]:
    """Analyze which parameters have the most impact on performance"""
    if not results:
        return {"error": "No results to analyze"}

    # Simple parameter importance analysis
    param_importance = {}

    for result in results:
        for param_name, param_value in result.parameters.items():
            if param_name not in param_importance:
                param_importance[param_name] = []

            param_importance[param_name].append((param_value, result.fitness_score))

    # Calculate importance scores
    importance_scores = {}
    for param_name, param_scores in param_importance.items():
        if len(set([v[0] for v in param_scores])) > 1:  # Only if parameter varies
            scores_by_value = {}
            for value, score in param_scores:
                if value not in scores_by_value:
                    scores_by_value[value] = []
                scores_by_value[value].append(score)

            # Calculate variance in performance across parameter values
            value_means = [np.mean(scores) for scores in scores_by_value.values()]
            importance_scores[param_name] = np.var(value_means)

    # Normalize importance scores
    if importance_scores:
        max_importance = max(importance_scores.values())
        for param in importance_scores:
            importance_scores[param] /= max_importance

    return importance_scores


def _calculate_robustness_score(window_results: List[Dict]) -> float:
    """Calculate overall robustness score from walk-forward results"""
    if not window_results:
        return 0.0

    test_fitnesses = [w["test_fitness"] for w in window_results]
    overfitting_scores = [w["overfitting_score"] for w in window_results]

    # Robustness is high when consistency is good and overfitting is low
    fitness_consistency = 1.0 / (1.0 + np.std(test_fitnesses))  # Lower std = higher consistency
    low_overfitting = 1.0 / (1.0 + np.mean(overfitting_scores))  # Lower overfitting = higher robustness

    return (fitness_consistency * 0.6 + low_overfitting * 0.4)
