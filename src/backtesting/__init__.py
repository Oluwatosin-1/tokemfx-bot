"""
TokemFX Backtesting Module
==========================
Complete backtesting framework with optimization and analysis tools.

This module provides:
- BacktestEngine: Core backtesting functionality
- Parameter optimization (grid search, Bayesian)
- Performance analytics and visualization
- ML-ready data export
- Walk-forward analysis
- Statistical validation
"""

# Core backtesting functionality - always available
from .engine import BacktestEngine, validate_market_data, statistical_significance_test

# Optional imports with fallbacks for missing dependencies
try:
    from .optimizer import optimize_strategy, walk_forward_analysis
    _OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Optimizer module not available: {e}")
    optimize_strategy = None
    walk_forward_analysis = None
    _OPTIMIZER_AVAILABLE = False

try:
    from .results import BacktestResults, export_to_ml_format
    _RESULTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Results module not available: {e}")
    BacktestResults = None
    export_to_ml_format = None
    _RESULTS_AVAILABLE = False

try:
    from .visualizer import plot_equity_curve, plot_drawdown, create_summary_report
    _VISUALIZER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Visualizer module not available: {e}")
    plot_equity_curve = None
    plot_drawdown = None
    create_summary_report = None
    _VISUALIZER_AVAILABLE = False

__all__ = [
    # Core functionality - always available
    'BacktestEngine',
    'validate_market_data',
    'statistical_significance_test',
]

# Add optional functionality if available
if _OPTIMIZER_AVAILABLE:
    __all__.extend(['optimize_strategy', 'walk_forward_analysis'])

if _RESULTS_AVAILABLE:
    __all__.extend(['BacktestResults', 'export_to_ml_format'])

if _VISUALIZER_AVAILABLE:
    __all__.extend(['plot_equity_curve', 'plot_drawdown', 'create_summary_report'])

__version__ = "1.0.0"
