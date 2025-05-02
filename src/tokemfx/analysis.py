# src/tokemfx/analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Union, Dict, Any


def load_results(path: str) -> pd.DataFrame:
    """
    Load backtest/optimization results from CSV or JSON.
    """
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    if path.lower().endswith(".json"):
        return pd.read_json(path, orient="records", convert_dates=False)
    raise ValueError(f"Unsupported extension for {path!r}")


def filter_results(df: pd.DataFrame, **params) -> pd.DataFrame:
    """
    Filter a results DataFrame by strategy parameters, e.g.
        filter_results(df, fast_period=10, slow_period=30)
    """
    mask = pd.Series(True, index=df.index)
    for k, v in params.items():
        if k not in df.columns:
            raise KeyError(f"Parameter {k!r} not in DataFrame columns")
        mask &= (df[k] == v)
    return df.loc[mask]


def compute_returns(equity: pd.Series) -> pd.Series:
    """
    Compute period returns from an equity curve.
    """
    return equity.pct_change().fillna(0.0)


def equity_curve(returns: pd.Series, initial_capital: float = 1.0) -> pd.Series:
    """
    Build an equity curve from returns series.
    """
    return (returns + 1.0).cumprod() * initial_capital


def drawdown_series(equity: pd.Series) -> pd.Series:
    """
    Compute drawdown series from an equity curve.
    """
    peak = equity.cummax()
    return (equity / peak) - 1.0


def max_drawdown(drawdown: pd.Series) -> float:
    """
    Return the maximum drawdown (most negative value).
    """
    return float(drawdown.min())


def cagr(equity: pd.Series) -> float:
    """
    Compute Compound Annual Growth Rate from an equity curve.
    """
    start, end = equity.index[0], equity.index[-1]
    total_years = (end - start).days / 365.25
    if total_years <= 0:
        return np.nan
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / total_years) - 1.0


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Compute annualized volatility of returns.
    """
    return float(returns.std(ddof=0) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Compute annualized Sharpe Ratio (assumes returns are per-period).
    """
    excess = returns - risk_free_rate / periods_per_year
    ann_ret = excess.mean() * periods_per_year
    ann_vol = annualized_volatility(returns, periods_per_year)
    return float(ann_ret / ann_vol) if ann_vol != 0 else np.nan


def sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Compute annualized Sortino Ratio.
    """
    excess = returns - risk_free_rate / periods_per_year
    ann_ret = excess.mean() * periods_per_year
    negative = excess[excess < 0]
    dd_vol = np.sqrt((negative ** 2).mean() * periods_per_year)
    return float(ann_ret / dd_vol) if dd_vol != 0 else np.nan


def calmar_ratio(equity: pd.Series) -> float:
    """
    Compute Calmar Ratio = CAGR / max drawdown.
    """
    dd = max_drawdown(drawdown_series(equity))
    c = cagr(equity)
    return float(c / abs(dd)) if dd != 0 else np.nan


def performance_summary(
    equity: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> Dict[str, Any]:
    """
    Compute a dictionary of key performance metrics from an equity curve.
    """
    returns = compute_returns(equity)
    dd = drawdown_series(equity)
    return {
        "Start Value":    float(equity.iloc[0]),
        "End Value":      float(equity.iloc[-1]),
        "Net Profit":     float(equity.iloc[-1] - equity.iloc[0]),
        "Total Return":   float(equity.iloc[-1] / equity.iloc[0] - 1),
        "CAGR":           cagr(equity),
        "Volatility":     annualized_volatility(returns, periods_per_year),
        "Sharpe Ratio":   sharpe_ratio(returns, risk_free_rate, periods_per_year),
        "Sortino Ratio":  sortino_ratio(returns, risk_free_rate, periods_per_year),
        "Max Drawdown":   float(dd.min()),
        "Calmar Ratio":   calmar_ratio(equity),
    }


# ─── Plotting utilities ─────────────────────────────────────────────────────────


def plot_equity_curve(equity: pd.Series):
    """
    Plot the equity curve.
    """
    fig, ax = plt.subplots()
    equity.plot(ax=ax)
    ax.set_title("Equity Curve")
    ax.set_xlabel("Time")
    ax.set_ylabel("Equity")
    return fig


def plot_drawdown_curve(drawdown: pd.Series):
    """
    Plot drawdown over time.
    """
    fig, ax = plt.subplots()
    drawdown.plot(ax=ax)
    ax.set_title("Drawdown Curve")
    ax.set_xlabel("Time")
    ax.set_ylabel("Drawdown")
    return fig


def plot_rolling_sharpe(
    returns: pd.Series,
    window: int = 20,
    periods_per_year: int = 252
):
    """
    Plot rolling Sharpe ratio over a moving window.
    """
    roll_sh = returns.rolling(window).mean() / returns.rolling(window).std()
    roll_sh *= np.sqrt(periods_per_year)
    fig, ax = plt.subplots()
    roll_sh.plot(ax=ax)
    ax.set_title(f"Rolling Sharpe (window={window})")
    ax.set_xlabel("Time")
    ax.set_ylabel("Sharpe")
    return fig


def plot_rolling_volatility(
    returns: pd.Series,
    window: int = 20,
    periods_per_year: int = 252
):
    """
    Plot rolling annualized volatility.
    """
    roll_vol = returns.rolling(window).std() * np.sqrt(periods_per_year)
    fig, ax = plt.subplots()
    roll_vol.plot(ax=ax)
    ax.set_title(f"Rolling Volatility (window={window})")
    ax.set_xlabel("Time")
    ax.set_ylabel("Volatility")
    return fig


def plot_parameter_heatmap(
    df: pd.DataFrame,
    param_x: str,
    param_y: str,
    metric: str
):
    """
    Plot a heatmap of a performance metric across two parameters.
    """
    pivot = df.pivot_table(
        index=param_y,
        columns=param_x,
        values=metric,
        aggfunc="mean"
    ).sort_index(ascending=True)
    fig, ax = plt.subplots()
    cax = ax.imshow(pivot.values, aspect="auto", origin="lower")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns], rotation=45)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([str(i) for i in pivot.index])
    ax.set_xlabel(param_x)
    ax.set_ylabel(param_y)
    ax.set_title(f"{metric} Heatmap ({param_x} vs {param_y})")
    fig.colorbar(cax, ax=ax, label=metric)
    plt.tight_layout()
    return fig
