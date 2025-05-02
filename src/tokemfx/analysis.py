# src/tokemfx/analysis.py

import pandas as pd
import matplotlib.pyplot as plt
from typing import Union

def load_results(path: str) -> pd.DataFrame:
    """
    Load backtest/optimization results from CSV or JSON.
    """
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    if path.lower().endswith(".json"):
        return pd.read_json(path, orient="records", convert_dates=False)
    raise ValueError(f"Unsupported extension for {path!r}")

def top_strategies(df: pd.DataFrame, by: str = "sharpe_ratio", n: int = 10) -> pd.DataFrame:
    """
    Return the top-n rows sorted by a performance column.
    """
    return df.sort_values(by, ascending=False).head(n)

def plot_distribution(df: pd.DataFrame, column: str, bins: int = 30):
    """
    Plot a histogram of any numeric result column.
    Returns the matplotlib Figure.
    """
    fig, ax = plt.subplots()
    df[column].hist(bins=bins, ax=ax)
    ax.set_title(f"Distribution of {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    return fig

def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute aggregate statistics across your backtests.
    """
    stats = {
        "mean": df.mean(numeric_only=True),
        "std":  df.std(numeric_only=True),
        "min":  df.min(numeric_only=True),
        "max":  df.max(numeric_only=True),
    }
    return pd.concat(stats, axis=1).T
