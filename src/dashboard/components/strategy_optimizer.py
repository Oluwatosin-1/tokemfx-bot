"""
Strategy Optimizer Component
===========================
Advanced strategy parameter optimization interface with real hyperopt integration.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import json
import logging

logger = logging.getLogger(__name__)

def render_strategy_optimizer():
    """Render strategy optimization interface with real optimization engine."""
    st.header("⚡ **Advanced Strategy Optimization Center**")

    # Check if optimization engine is available
    try:
        from src.backtesting.optimizer import optimize_strategy, walk_forward_analysis
        from src.backtesting.engine import BacktestEngine
        from src.trading.execution.data_handler import DataHandler
        from src.trading.execution.broker import DerivBroker
        OPTIMIZER_AVAILABLE = True
    except ImportError as e:
        st.error(f"❌ Optimization engine not available: {e}")
        st.info("Please ensure all required packages are installed and the project structure is correct.")
        OPTIMIZER_AVAILABLE = False
        return
    except Exception as e:
        st.error(f"❌ Unexpected error loading optimization engine: {e}")
        OPTIMIZER_AVAILABLE = False
        return

    if not OPTIMIZER_AVAILABLE:
        st.error("Strategy optimization requires backtesting engine")
        return

    # Initialize components
    try:
        data_handler = DataHandler(cache_dir="cache")
        engine = BacktestEngine(data_handler=data_handler, cash=10000)
        st.success("✅ Optimization engine initialized")
    except Exception as e:
        st.error(f"❌ Failed to initialize optimization engine: {e}")
        st.info("This may be due to missing dependencies or configuration issues.")
        return

    # Main optimization interface
    col_setup, col_params, col_results = st.columns([1, 1, 1])

    with col_setup:
        st.subheader("🎯 Optimization Setup")

        # Strategy selection
        try:
            from src.strategy import STRATEGY_MAP, STRATEGY_MAP_UI, get_strategy_health_status
            strategy_names = list(STRATEGY_MAP.keys())
            strategy_display_names = list(STRATEGY_MAP_UI.keys())
        except ImportError as e:
            st.error(f"❌ Strategy registry not available: {e}")
            st.info("Cannot load strategy optimizer without strategy definitions.")
            return
        except Exception as e:
            st.error(f"❌ Error loading strategies: {e}")
            return

        selected_strategy_display = st.selectbox(
            "Select Strategy",
            strategy_display_names,
            key="opt_strategy_select"
        )

        # Extract actual strategy name from display name
        selected_strategy = None
        for display_name, strategy_class in STRATEGY_MAP_UI.items():
            if display_name == selected_strategy_display:
                selected_strategy = strategy_class.__name__
                break

        # Fallback if strategy not found
        if not selected_strategy:
            st.error("❌ Selected strategy not found in registry")
            return

        # Instrument selection
        instruments = ["R_10", "R_25", "R_50", "R_75", "R_100", "frxEURUSD", "frxUSDJPY", "frxGBPUSD"]
        selected_instrument = st.selectbox(
            "Instrument",
            instruments,
            index=0,
            key="opt_instrument_select"
        )

        # Timeframe selection
        timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D"]
        selected_timeframe = st.selectbox(
            "Timeframe",
            timeframes,
            index=4,  # Default to H1
            key="opt_timeframe_select"
        )

        # Optimization method
        opt_methods = ["grid", "random", "bayesian"]
        opt_method_names = ["Grid Search", "Random Search", "Bayesian Optimization"]
        selected_method = st.selectbox(
            "Optimization Method",
            opt_method_names,
            key="opt_method_select"
        )
        method = opt_methods[opt_method_names.index(selected_method)]

        # Iterations/Max evaluations
        if method == "grid":
            st.info("Grid search evaluates all parameter combinations")
            max_evals = None
        else:
            max_evals = st.slider("Max Evaluations", 50, 500, 100, key="opt_evals_slider")

    with col_params:
        st.subheader("⚙️ Parameter Ranges")

        # Get strategy class and define parameter ranges
        strategy_class = STRATEGY_MAP.get(selected_strategy)

        # Dynamic parameter selection based on strategy
        param_ranges = get_strategy_parameters(selected_strategy)

        # Display and allow editing of parameter ranges
        st.write("**Parameters to Optimize:**")
        selected_params = {}

        for param_name, param_info in param_ranges.items():
            if st.checkbox(f"Optimize {param_name}", value=True, key=f"opt_{param_name}_check"):
                if param_info['type'] == 'int':
                    min_val, max_val = param_info['range']
                    selected_params[param_name] = list(range(min_val, max_val + 1, param_info.get('step', 1)))
                    st.caption(f"Range: {min_val} - {max_val}")
                elif param_info['type'] == 'float':
                    min_val, max_val = param_info['range']
                    # For continuous parameters, create discrete steps
                    steps = min(20, max_val - min_val + 1)
                    step_size = (max_val - min_val) / (steps - 1)
                    selected_params[param_name] = [round(min_val + i * step_size, 2) for i in range(steps)]
                    st.caption(f"Range: {min_val} - {max_val} ({steps} steps)")

        if not selected_params:
            st.warning("Select at least one parameter to optimize")

    with col_results:
        st.subheader("📊 Optimization Target")
        target_options = ["sharpe_ratio", "total_return_pct", "win_rate", "profit_factor"]
        target_labels = ["Sharpe Ratio", "Total Return %", "Win Rate", "Profit Factor"]
        selected_target_idx = st.selectbox(
            "Optimization Target",
            target_labels,
            key="opt_target_select"
        )
        optimization_target = target_options[target_labels.index(selected_target_idx)]

        st.subheader("📅 Date Range")
        col_dates1, col_dates2 = st.columns(2)
        with col_dates1:
            start_date = st.date_input(
                "Start",
                datetime.now().date() - timedelta(days=365),
                key="opt_start_date"
            )
        with col_dates2:
            end_date = st.date_input(
                "End",
                datetime.now().date(),
                key="opt_end_date"
            )

        # Execute optimization button
        if st.button("🚀 **START OPTIMIZATION**", type="primary", use_container_width=True):
            if not selected_params:
                st.error("Please select at least one parameter to optimize")
                return

            run_real_optimization(
                strategy_class=strategy_class,
                strategy_name=selected_strategy,
                instrument=selected_instrument,
                timeframe=selected_timeframe,
                param_grid=selected_params,
                method=method,
                optimization_target=optimization_target,
                start_date=start_date,
                end_date=end_date,
                max_evaluations=max_evals if max_evals else 100,
                data_handler=data_handler
            )

    # Display previous optimization results if available
    if 'optimization_results' in st.session_state:
        display_optimization_results(st.session_state.optimization_results)

def get_strategy_parameters(strategy_name: str) -> dict:
    """Get parameter ranges for different strategies."""
    base_params = {
        "MA Crossover Strategy": {
            "fast_period": {"type": "int", "range": (5, 50), "step": 5},
            "slow_period": {"type": "int", "range": (20, 200), "step": 10}
        },
        "RSI Reversal Strategy": {
            "rsi_period": {"type": "int", "range": (7, 21), "step": 2},
            "rsi_oversold": {"type": "int", "range": (20, 40), "step": 5},
            "rsi_overbought": {"type": "int", "range": (60, 90), "step": 5}
        },
        "Bollinger Bands Strategy": {
            "bb_period": {"type": "int", "range": (10, 50), "step": 5},
            "bb_dev": {"type": "float", "range": (1.5, 3.0)}
        },
        "ATR Breakout Strategy": {
            "atr_period": {"type": "int", "range": (7, 28), "step": 7},
            "atr_multiplier": {"type": "float", "range": (1.0, 3.0)}
        }
    }

    return base_params.get(strategy_name, base_params["MA Crossover Strategy"])

def run_real_optimization(strategy_class, strategy_name: str, instrument: str, timeframe: str,
                         param_grid: dict, method: str, optimization_target: str,
                         start_date, end_date, max_evaluations: int, data_handler):
    """Run real strategy optimization using the backtesting engine."""

    with st.spinner(f"🔬 Running {method} optimization for {strategy_name}..."):

        try:
            # Import optimization function
            from src.backtesting.optimizer import optimize_strategy

            # Convert dates to datetime objects
            start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

            # Run optimization
            results = optimize_strategy(
                strategy_class=strategy_class,
                parameter_grid=param_grid,
                instruments=instrument,
                timeframe=timeframe,
                start_date=start_dt,
                end_date=end_dt,
                data_handler=data_handler,
                method=method,
                max_evaluations=max_evaluations,
                optimization_target=optimization_target
            )

            if "error" in results:
                st.error(f"❌ Optimization failed: {results['error']}")
                return

            # Store results in session state
            st.session_state.optimization_results = results

            st.success("✅ **OPTIMIZATION COMPLETED SUCCESSFULLY!**")
            st.info(f"Evaluated {results.get('total_evaluations', 0)} parameter combinations")
            st.info(f"Best {optimization_target.replace('_', ' ').title()}: {results.get('best_fitness', 0):.4f}")

        except NameError as e:
            if "optimize_strategy" in str(e):
                st.error("❌ Optimization function not available. Please restart the dashboard.")
                logger.error("optimize_strategy function not found - import failed")
            else:
                st.error(f"❌ Name error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Optimization execution failed: {str(e)}")
            logger.error(f"Optimization error: {e}", exc_info=True)

def display_optimization_results(results: dict):
    """Display optimization results in an organized format."""

    st.header("📊 **Optimization Results**")

    # Summary metrics
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Method", results.get('method', 'Unknown').title())
    with summary_cols[1]:
        st.metric("Evaluations", results.get('total_evaluations', 0))
    with summary_cols[2]:
        best_fitness = results.get('best_fitness')
        if best_fitness is not None:
            st.metric("Best Fitness", f"{best_fitness:.4f}")
    with summary_cols[3]:
        target = results.get('optimization_target', 'Unknown').replace('_', ' ').title()
        st.metric("Target Metric", target)

    # Best parameters
    st.subheader("🏆 **Best Parameters Found**")
    best_params = results.get('best_parameters', {})
    if best_params:
        params_df = pd.DataFrame(list(best_params.items()), columns=['Parameter', 'Value'])
        st.dataframe(params_df, use_container_width=True, hide_index=True)
    else:
        st.info("No best parameters available")

    # All results table
    st.subheader("📋 **All Optimization Results**")
    all_results = results.get('all_results', [])
    results_data = []  # Initialize outside the if block
    if all_results:
        # Convert to DataFrame for better display
        for result in all_results:
            row = {
                'Rank': result.get('rank', 0),
                'Fitness': result.get('fitness_score'),
            }
            # Add parameters
            params = result.get('parameters', {})
            row.update(params)
            results_data.append(row)

        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.info("No detailed results available")

    # Convergence analysis (if available)
    convergence = results.get('convergence_analysis', {})
    if convergence:
        st.subheader("📈 **Convergence Analysis**")
        conv_cols = st.columns(3)
        with conv_cols[0]:
            st.metric("Final Best Score", f"{convergence.get('final_best_score', 0):.4f}")
        with conv_cols[1]:
            st.metric("Convergence Rate", f"{convergence.get('convergence_rate', 0):.2%}")
        with conv_cols[2]:
            std_dev = convergence.get('score_distribution', {}).get('std', 0)
            st.metric("Score Std Dev", f"{std_dev:.4f}")

    # Parameter importance (if available)
    param_importance = results.get('parameter_importance', {})
    if param_importance:
        st.subheader("🎯 **Parameter Importance**")
        importance_data = []
        for param, importance in param_importance.items():
            importance_data.append({
                'Parameter': param.replace('_', ' ').title(),
                'Importance': importance,
                'Importance %': f"{importance:.1%}"
            })

        importance_df = pd.DataFrame(importance_data)
        st.dataframe(importance_df, use_container_width=True, hide_index=True)

    # Export functionality
    st.subheader("💾 **Export Results**")
    export_cols = st.columns(2)
    with export_cols[0]:
        if st.button("📄 Export to JSON"):
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with export_cols[1]:
        if st.button("📊 Export to CSV") and all_results:
            csv_data = pd.DataFrame(results_data).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    st.success("✅ **Optimization analysis complete!** Use the best parameters found for your trading strategy.")
