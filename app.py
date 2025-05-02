# app.py
import sys, os

# ── Make sure Python can see our src/ directory ────────────────────────────────
project_root = os.path.dirname(__file__)
src_path     = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# ── Now imports will work ──────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import backtrader as bt
import math
from datetime import datetime
from tokemfx.config import REDIS_URL
from tokemfx.data import DataHandler
from tokemfx.strategy import (
    MovingAverageCrossStrategy,
    RSIReversionStrategy,
    BollingerBreakoutStrategy,
)

st.set_page_config(layout="wide")
st.title("📊 TokemFX Interactive Backtester & Dashboard")

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.header("Backtest Settings")

# Instruments
available_instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
instruments = st.sidebar.multiselect(
    "Select FX pairs", available_instruments, default=["EUR_USD"]
)

# Granularity
granularity = st.sidebar.selectbox(
    "Granularity", ["M1", "M5", "M15", "H1", "H4", "D"], index=3
)

# Date range
today = datetime.utcnow().date()
default_start = today.replace(year=today.year - 1)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", today)

# Strategy selection
strategy_map = {
    "Moving Average Cross": MovingAverageCrossStrategy,
    "RSI Reversion":       RSIReversionStrategy,
    "Bollinger Breakout":  BollingerBreakoutStrategy,
}
strategy_name = st.sidebar.selectbox("Strategy", list(strategy_map.keys()))
strategy_cls  = strategy_map[strategy_name]

# Strategy parameters
st.sidebar.subheader("Parameters")
params = {}
if strategy_name == "Moving Average Cross":
    params["fast_period"] = st.sidebar.number_input("Fast MA period", min_value=1, value=10)
    params["slow_period"] = st.sidebar.number_input("Slow MA period", min_value=1, value=30)

elif strategy_name == "RSI Reversion":
    params["rsi_period"]    = st.sidebar.number_input("RSI period", min_value=1, value=14)
    params["rsi_oversold"]  = st.sidebar.number_input("Oversold level", 1, 100, 30)
    params["rsi_overbought"]= st.sidebar.number_input("Overbought level", 1, 100, 70)
    params["period_hold"]   = st.sidebar.number_input("Bars to hold", min_value=1, value=5)

else:  # Bollinger Breakout
    params["bb_period"]     = st.sidebar.number_input("BB period", min_value=1, value=20)
    params["bb_dev"]        = st.sidebar.number_input("BB dev factor", min_value=0.1, value=2.0, step=0.1)
    params["size"]          = st.sidebar.number_input("Order size (units)", min_value=1, value=1000)

st.sidebar.header("Execute")
run_bt = st.sidebar.button("Run Backtest")

# ── Main ─────────────────────────────────────────────────────────────────────
if run_bt:
    st.markdown("## Running Backtest…")
    # 1) Set up data handler and cerebro
    dh = DataHandler(
        cache_dir="cache",
        sqlite_path="cache/candles.db",
        redis_url=REDIS_URL
    )
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(10_000)
    cerebro.broker.setcommission(commission=0.0002)
    cerebro.broker.set_slippage_perc(0.0001)
    cerebro.addstrategy(strategy_cls, **params)

    # Add analyzers for returns, drawdown, Sharpe
    cerebro.addanalyzer(
        bt.analyzers.TimeReturn,
        _name="timereturn",
        timeframe=bt.TimeFrame.NoTimeFrame
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown,    _name="drawdown")
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name="sharpe",
        timeframe=bt.TimeFrame.Days,
        annualize=True
    )

    # 2) Fetch & add each data feed
    for inst in instruments:
        df = dh.get_historical(
            instrument=inst,
            granularity=granularity,
            start=pd.to_datetime(start_date),
            end=pd.to_datetime(end_date),
        )
        cerebro.adddata(bt.feeds.PandasData(dataname=df, name=inst))

    # 3) Run
    strat = cerebro.run()[0]

    # 4) Build equity curve
    tr = strat.analyzers.timereturn.get_analysis()      # dict[datetime→return]
    returns = pd.Series(tr).sort_index()
    equity  = (returns + 1).cumprod() * 10_000
    drawdown = equity / equity.cummax() - 1

    # 5) Rolling Sharpe (20-bar window)
    rolling_window = 20
    rolling_sharpe = (
        returns.rolling(window=rolling_window).mean()
        / returns.rolling(window=rolling_window).std()
        * math.sqrt(252)
    )

    # ── Display metrics ────────────────────────────────────────────────────────
    with st.beta_expander("▶️ Summary Metrics", expanded=True):
        mrt = strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]
        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
        st.write({
            "Final Portfolio Value": f"{equity.iloc[-1]:.2f}",
            "Net Profit":            f"{equity.iloc[-1] - 10_000:.2f}",
            "Max Drawdown (%)":      f"{mrt:.2f}%",
            "Sharpe Ratio":          f"{sharpe:.2f}"
        })

    # ── Plots ─────────────────────────────────────────────────────────────────
    col1, col2 = st.beta_columns(2)

    with col1:
        st.subheader("Equity Curve")
        st.line_chart(equity)

    with col2:
        st.subheader("Drawdown Curve")
        st.line_chart(drawdown)

    st.subheader(f"Rolling Sharpe (window={rolling_window})")
    st.line_chart(rolling_sharpe)
