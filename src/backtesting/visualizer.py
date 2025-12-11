"""
TokemFX Backtesting Visualization
=================================
Comprehensive charting and visualization for backtest results and optimization analysis.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def plot_equity_curve(results_data: Dict[str, Any],
                     title: str = "Equity Curve",
                     height: int = 500) -> go.Figure:
    """
    Plot equity curve from backtest results.

    Args:
        results_data: Backtest results dictionary
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    try:
        # For now, create a simplified equity curve based on final value
        # In a full implementation, this would extract actual portfolio values over time

        start_cash = results_data.get('start_cash', 10000)
        final_value = results_data.get('final_value', start_cash)
        net_profit = results_data.get('net_profit', 0)

        # Create a simple two-point equity curve
        fig = go.Figure()

        # Add equity line
        fig.add_trace(go.Scatter(
            x=['Start', 'End'],
            y=[start_cash, final_value],
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#00C853', width=3),
            marker=dict(size=8)
        ))

        # Add horizontal start line
        fig.add_hline(y=start_cash, line_dash="dash", line_color="gray",
                     annotation_text=f"Start: ${start_cash:,.0f}", annotation_position="top left")

        # Add final value annotation
        fig.add_annotation(
            x='End', y=final_value,
            text=f"${final_value:,.0f}",
            showarrow=True,
            arrowhead=1,
            ax=50, ay=-30
        )

        # Performance indicators
        performance_color = '#00C853' if net_profit >= 0 else '#D32F2F'
        fig.add_annotation(
            x=0.02, y=0.98,
            text=f"Net P&L: ${net_profit:,.0f} ({net_profit/start_cash*100:.1f}%)",
            xref="paper", yref="paper",
            showarrow=False,
            bgcolor=performance_color,
            font=dict(color='white', size=12),
            bordercolor=performance_color,
            borderwidth=1,
            borderpad=4
        )

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Portfolio Value ($)",
            height=height,
            template='plotly_white',
            showlegend=False
        )

        return fig

    except Exception as e:
        logger.error(f"Failed to create equity curve: {e}")
        return _create_error_figure("Equity Curve Creation Failed", str(e))


def plot_drawdown(results_data: Dict[str, Any],
                 title: str = "Drawdown Analysis",
                 height: int = 400) -> go.Figure:
    """
    Plot drawdown chart from backtest results.

    Args:
        results_data: Backtest results dictionary
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    try:
        max_dd = results_data.get('max_drawdown', 0)

        if max_dd == 0:
            # No drawdown data, show message
            fig = go.Figure()
            fig.add_annotation(
                text="No drawdown data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            fig.update_layout(title=title, height=height)
            return fig

        # Create a simple bar chart showing max drawdown
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=['Maximum Drawdown'],
            y=[max_dd],
            marker_color='#D32F2F',
            name='Drawdown',
            showlegend=False
        ))

        # Add reference line at 0
        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

        # Add value annotation
        fig.add_annotation(
            x='Maximum Drawdown', y=max_dd,
            text=f"{max_dd:.2f}%",
            showarrow=True,
            arrowhead=1,
            ax=0, ay=-40,
            font=dict(size=14, color='#D32F2F')
        )

        fig.update_layout(
            title=title,
            xaxis_title="Drawdown Type",
            yaxis_title="Drawdown (%)",
            height=height,
            template='plotly_white',
        )

        return fig

    except Exception as e:
        logger.error(f"Failed to create drawdown chart: {e}")
        return _create_error_figure("Drawdown Chart Creation Failed", str(e))


def create_summary_report(results_list: List[Dict[str, Any]],
                         title: str = "Backtest Summary Report",
                         save_path: Optional[str] = None) -> go.Figure:
    """
    Create a comprehensive summary report with multiple charts.

    Args:
        results_list: List of backtest result dictionaries
        title: Report title
        save_path: Optional path to save the report

    Returns:
        Plotly figure with multiple subplots
    """
    try:
        if not results_list:
            return _create_error_figure("No Data", "No backtest results to display")

        # Extract metrics for comparison
        strategies = []
        sharpe_ratios = []
        total_returns = []
        win_rates = []
        max_drawdowns = []

        for result in results_list:
            strategies.append(result.get('strategy_class', 'Unknown'))
            sharpe_ratios.append(result.get('sharpe_ratio'))
            total_returns.append(result.get('total_return_pct', 0))
            win_rates.append(result.get('win_rate', 0))
            max_drawdowns.append(result.get('max_drawdown', 0))

        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Sharpe Ratios', 'Total Returns', 'Win Rates', 'Max Drawdowns'),
            vertical_spacing=0.1
        )

        # Sharpe Ratios
        valid_sharpe = [(s, sr) for s, sr in zip(strategies, sharpe_ratios) if sr is not None]
        if valid_sharpe:
            s_names, s_values = zip(*valid_sharpe)
            fig.add_trace(go.Bar(
                x=s_names, y=s_values,
                marker_color='#2196F3',
                name='Sharpe Ratio',
                showlegend=False
            ), row=1, col=1)

        # Total Returns
        fig.add_trace(go.Bar(
            x=strategies, y=total_returns,
            marker_color='#4CAF50',
            name='Total Return (%)',
            showlegend=False
        ), row=1, col=2)

        # Win Rates
        fig.add_trace(go.Bar(
            x=strategies, y=win_rates,
            marker_color='#FF9800',
            name='Win Rate',
            showlegend=False
        ), row=2, col=1)

        # Max Drawdowns
        fig.add_trace(go.Bar(
            x=strategies, y=max_drawdowns,
            marker_color='#F44336',
            name='Max Drawdown (%)',
            showlegend=False
        ), row=2, col=2)

        fig.update_layout(
            title=title,
            height=800,
            template='plotly_white',
            showlegend=False
        )

        # Update y-axis labels
        fig.update_yaxes(title_text="Sharpe Ratio", row=1, col=1)
        fig.update_yaxes(title_text="Return (%)", row=1, col=2)
        fig.update_yaxes(title_text="Win Rate", row=2, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=2)

        return fig

    except Exception as e:
        logger.error(f"Failed to create summary report: {e}")
        return _create_error_figure("Summary Report Creation Failed", str(e))


def plot_optimization_results(optimization_data: Dict[str, Any],
                            x_param: str = "param_1",
                            y_param: str = "param_2",
                            color_by: str = "sharpe_ratio",
                            title: str = "Optimization Results",
                            height: int = 600) -> go.Figure:
    """
    Plot optimization results in 2D parameter space.

    Args:
        optimization_data: Optimization results dictionary
        x_param: Parameter name for x-axis
        y_param: Parameter name for y-axis
        color_by: Metric to color points by
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    try:
        results = optimization_data.get('all_results', [])
        if not results:
            return _create_error_figure("No Optimization Data", "No optimization results to display")

        # Extract parameter values and metrics
        x_values = []
        y_values = []
        colors = []
        texts = []

        for result in results:
            if isinstance(result, dict) and 'parameters' in result:
                params = result['parameters']

                # Get x and y parameter values
                x_val = params.get(x_param)
                y_val = params.get(y_param)

                if x_val is not None and y_val is not None:
                    x_values.append(x_val)
                    y_values.append(y_val)

                    # Get color value (metric to color by)
                    if color_by in result:
                        colors.append(result[color_by])
                    else:
                        colors.append(0)

                    # Create hover text
                    hover_text = f"{x_param}: {x_val}<br>{y_param}: {y_val}<br>"
                    for metric in ['sharpe_ratio', 'total_return_pct', 'win_rate']:
                        if metric in result and result[metric] is not None:
                            hover_text += f"{metric}: {result[metric]:.3f}<br>"
                    texts.append(hover_text)

        if not x_values:
            return _create_error_figure("No Parameter Data", f"Parameters {x_param} or {y_param} not found in results")

        # Create scatter plot
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers',
            marker=dict(
                size=10,
                color=colors,
                colorscale='Viridis',
                colorbar=dict(title=color_by.replace('_', ' ').title()),
                showscale=True,
            ),
            text=texts,
            hovertemplate='%{text}<extra></extra>',
            name='Optimization Points'
        ))

        fig.update_layout(
            title=f"{title} - {color_by.replace('_', ' ').title()}",
            xaxis_title=x_param.replace('_', ' ').title(),
            yaxis_title=y_param.replace('_', ' ').title(),
            height=height,
            template='plotly_white'
        )

        return fig

    except Exception as e:
        logger.error(f"Failed to create optimization plot: {e}")
        return _create_error_figure("Optimization Plot Creation Failed", str(e))


def plot_walk_forward_results(wf_data: Dict[str, Any],
                           title: str = "Walk-Forward Analysis",
                           height: int = 600) -> go.Figure:
    """
    Plot walk-forward analysis results.

    Args:
        wf_data: Walk-forward analysis results
        title: Chart title
        height: Chart height

    Returns:
        Plotly figure
    """
    try:
        window_results = wf_data.get('window_results', [])

        if not window_results:
            return _create_error_figure("No Walk-Forward Data", "No walk-forward results to display")

        # Extract data
        window_indices = [w['window_index'] for w in window_results]
        train_fitness = [w['train_fitness'] for w in window_results]
        test_fitness = [w['test_fitness'] for w in window_results]
        overfitting_scores = [w['overfitting_score'] for w in window_results]

        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Fitness Scores by Window', 'Overfitting Analysis'),
            vertical_spacing=0.1
        )

        # Fitness scores
        fig.add_trace(go.Bar(
            x=window_indices,
            y=train_fitness,
            name='Training Fitness',
            marker_color='#2196F3',
            offsetgroup=0
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=window_indices,
            y=test_fitness,
            name='Test Fitness',
            marker_color='#4CAF50',
            offsetgroup=1
        ), row=1, col=1)

        # Overfitting scores
        fig.add_trace(go.Scatter(
            x=window_indices,
            y=overfitting_scores,
            mode='lines+markers',
            name='Overfitting Score',
            line=dict(color='#F44336', width=3),
            marker=dict(size=8)
        ), row=2, col=1)

        # Add reference line at y=0 for overfitting
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

        # Summary statistics
        avg_test_fitness = wf_data.get('average_test_fitness', 0)
        avg_overfitting = wf_data.get('average_overfitting', 0)
        robustness = wf_data.get('robustness_score', 0)

        summary_text = f"""
        Average Test Fitness: {avg_test_fitness:.3f}<br>
        Average Overfitting: {avg_overfitting:.3f}<br>
        Robustness Score: {robustness:.1%}
        """

        fig.add_annotation(
            x=0.02, y=0.98,
            text=summary_text,
            xref="paper", yref="paper",
            showarrow=False,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1,
            borderpad=4
        )

        fig.update_layout(
            title=title,
            height=height,
            template='plotly_white',
            showlegend=True
        )

        fig.update_yaxes(title_text="Fitness Score", row=1, col=1)
        fig.update_yaxes(title_text="Overfitting Score", row=2, col=1)
        fig.update_xaxes(title_text="Window Number", row=2, col=1)

        return fig

    except Exception as e:
        logger.error(f"Failed to create walk-forward plot: {e}")
        return _create_error_figure("Walk-Forward Plot Creation Failed", str(e))


def _create_error_figure(title: str, message: str) -> go.Figure:
    """Create an error figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"{title}<br><br>{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(
        title=title,
        template='plotly_white'
    )
    return fig


def export_chart_to_html(fig: go.Figure, filename: str, include_plotlyjs: bool = True) -> str:
    """
    Export chart to standalone HTML file.

    Args:
        fig: Plotly figure
        filename: Output filename
        include_plotlyjs: Include Plotly.js library

    Returns:
        Path to saved HTML file
    """
    try:
        if not filename.endswith('.html'):
            filename += '.html'

        fig.write_html(filename, include_plotlyjs=include_plotlyjs, full_html=True)
        logger.info(f"Chart exported to {filename}")
        return filename

    except Exception as e:
        logger.error(f"Failed to export chart to HTML: {e}")
        return ""
