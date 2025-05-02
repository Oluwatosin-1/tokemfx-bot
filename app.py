#!/usr/bin/env python3
# app.py

import sys
import os
import math
from datetime import datetime

# ── Make sure Python can see our src/ directory ────────────────────────────────
project_root = os.path.dirname(__file__)
src_path     = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# ── Standard imports ───────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import backtrader as bt

# ── Analytics helpers ─────────────────────────────────────────────────────────
from tokemfx.analysis import (
    compute_returns,
    equity_curve,
    drawdown_series,
    rolling_sharpe as compute_rolling_sharpe,
    performance_summary,
    plot_equity_curve,
    plot_drawdown_curve,
    plot_rolling_sharpe,
)

# ── Core components ───────────────────────────────────────────────────────────
from tokemfx.config  import REDIS_URL
from tokemfx.broker  import OANDABroker, FXCMBroker
from tokemfx.data    import DataHandler
from tokemfx.strategy import (
    MovingAverageCrossStrategy,
    RSIReversionStrategy,
    BollingerBreakoutStrategy,
)

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(layout="wide")
st.title("📊 TokemFX Interactive Backtester & Dashboard")

# ── Sidebar: Backtest Settings ─────────────────────────────────────────────────
st.sidebar.header("Backtest Settings")

# Broker selection
broker_choice = st.sidebar.selectbox(
    "Broker",
    ["OANDA", "FXCM"]
)
if broker_choice == "OANDA":
    broker = OANDABroker()
else:
    broker = FXCMBroker()

# Instruments
available_instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
instruments = st.sidebar.multiselect(
    "Select FX pairs",
    available_instruments,
    default=["EUR_USD"]
)

# Granularity
granularity = st.sidebar.selectbox(
    "Granularity",
    ["M1", "M5", "M15", "H1", "H4", "D"],
    index=3
)

# Date range
today = datetime.utcnow().date()
default_start = today.replace(year=today.year - 1)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date   = st.sidebar.date_input("End Date", today)

# Strategy selection
strategy_map = {
    "Moving Average Cross": MovingAverageCrossStrategy,
    "RSI Reversion":        RSIReversionStrategy,
    "Bollinger Breakout":   BollingerBreakoutStrategy,
}
strategy_name = st.sidebar.selectbox(
    "Strategy",
    list(strategy_map.keys())
)
strategy_cls = strategy_map[strategy_name]

# Strategy parameters
st.sidebar.subheader("Parameters")
params = {}
if strategy_name == "Moving Average Cross":
    params["fast_period"] = st.sidebar.number_input(
        "Fast MA period", min_value=1, value=10
    )
    params["slow_period"] = st.sidebar.number_input(
        "Slow MA period", min_value=1, value=30
    )

elif strategy_name == "RSI Reversion":
    params["rsi_period"]     = st.sidebar.number_input(
        "RSI period", min_value=1, value=14
    )
    params["rsi_oversold"]   = st.sidebar.number_input(
        "Oversold level", min_value=1, max_value=100, value=30
    )
    params["rsi_overbought"] = st.sidebar.number_input(
        "Overbought level", min_value=1, max_value=100, value=70
    )
    params["period_hold"]    = st.sidebar.number_input(
        "Bars to hold", min_value=1, value=5
    )

else:  # Bollinger Breakout
    params["bb_period"] = st.sidebar.number_input(
        "BB period", min_value=1, value=20
    )
    params["bb_dev"]    = st.sidebar.number_input(
        "BB dev factor", min_value=0.1, value=2.0, step=0.1
    )
    params["size"]      = st.sidebar.number_input(
        "Order size (units)", min_value=1, value=1000
    )

st.sidebar.header("Execute")
run_bt = st.sidebar.button("Run Backtest")

# ── Main ─────────────────────────────────────────────────────────────────────
if run_bt:
    st.markdown("## Running Backtest…")
    # 1) Instantiate DataHandler
    dh = DataHandler(
        broker=broker,
        cache_dir="cache",
        sqlite_path="cache/candles.db",
        redis_url=REDIS_URL,
    )

    # 2) Set up Backtrader engine
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10_000)
    cerebro.broker.setcommission(commission=0.0002)
    cerebro.broker.set_slippage_perc(0.0001)
    cerebro.addstrategy(strategy_cls, **params)

    # Add analyzers
    cerebro.addanalyzer(
        bt.analyzers.TimeReturn,
        _name="timereturn",
        timeframe=bt.TimeFrame.NoTimeFrame
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name="sharpe",
        timeframe=bt.TimeFrame.Days,
        annualize=True
    )

    # 3) Load and add data feeds
    for inst in instruments:
        df = dh.get_historical(
            instrument=inst,
            granularity=granularity,
            start=pd.to_datetime(start_date),
            end=pd.to_datetime(end_date)
        )
        if df.empty:
            st.warning(f"No data for {inst} in the selected range.")
            continue
        cerebro.adddata(
            bt.feeds.PandasData(dataname=df, name=inst)
        )

    # 4) Run backtest
    strat = cerebro.run()[0]

    # 5) Compute analysis
    tr      = strat.analyzers.timereturn.get_analysis()  # dict[dt->ret]
    returns = compute_returns(pd.Series(tr).sort_index())
    equity  = equity_curve(returns, initial_capital=10_000)
    drawdn  = drawdown_series(equity)
    roll_sh = compute_rolling_sharpe(returns, window=20)

    # 6) Summary metrics
    summary = performance_summary(equity)
    with st.expander("▶️ Summary Metrics", expanded=True):
        st.json(summary)

    # 7) Plots
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Equity Curve")
        fig_eq = plot_equity_curve(equity)
        st.pyplot(fig_eq)
    with col2:
        st.subheader("Drawdown Curve")
        fig_dd = plot_drawdown_curve(drawdn)
        st.pyplot(fig_dd)

    st.subheader("Rolling Sharpe (20-period)")
    fig_rs = plot_rolling_sharpe(returns, window=20)
    st.pyplot(fig_rs)
