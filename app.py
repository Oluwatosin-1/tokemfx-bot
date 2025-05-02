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
from tokemfx.config    import REDIS_URL
from tokemfx.broker    import OANDABroker, FXCMBroker
from tokemfx.data      import DataHandler
from tokemfx.backtest  import BacktestEngine
from tokemfx.strategy  import (
    ATRBreakoutStrategy,
    EMARSIHybridStrategy,
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
broker_choice = st.sidebar.selectbox("Broker", ["OANDA", "FXCM"])
broker = OANDABroker() if broker_choice == "OANDA" else FXCMBroker()

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
end_date   = st.sidebar.date_input("End Date", today)

# Strategy selection
strategy_map = {
    "MA Cross": MovingAverageCrossStrategy,
    "RSI Rev":  RSIReversionStrategy,
    "BBreak":   BollingerBreakoutStrategy,
    "ATR BO":   ATRBreakoutStrategy,
    "EMA+RSI":  EMARSIHybridStrategy,
}
strategy_name = st.sidebar.selectbox("Strategy", list(strategy_map.keys()))
strategy_cls  = strategy_map[strategy_name]

# Strategy parameters
st.sidebar.subheader("Parameters")
params = {}
if strategy_name == "MA Cross":
    params["fast_period"] = st.sidebar.number_input("Fast MA period", min_value=1, value=10)
    params["slow_period"] = st.sidebar.number_input("Slow MA period", min_value=1, value=30)

elif strategy_name == "RSI Rev":
    params["rsi_period"]     = st.sidebar.number_input("RSI period", min_value=1, value=14)
    params["rsi_oversold"]   = st.sidebar.number_input("RSI oversold", min_value=1, max_value=100, value=30)
    params["rsi_overbought"] = st.sidebar.number_input("RSI overbought", min_value=1, max_value=100, value=70)
    params["period_hold"]    = st.sidebar.number_input("Bars to hold", min_value=1, value=5)

elif strategy_name == "BBreak":
    params["bb_period"] = st.sidebar.number_input("BB period", min_value=1, value=20)
    params["bb_dev"]    = st.sidebar.number_input("BB dev factor", min_value=0.1, value=2.0, step=0.1)
    params["size"]      = st.sidebar.number_input("Order size", min_value=1, value=1000)

elif strategy_name == "ATR BO":
    params["donchian_period"] = st.sidebar.number_input("Donchian period", min_value=1, value=20)
    params["atr_multiplier"]  = st.sidebar.number_input("ATR multiplier", min_value=0.1, value=1.0, step=0.1)
    params["risk_reward"]     = st.sidebar.number_input("Risk/Reward", min_value=1.0, value=2.0, step=0.1)
    params["size"]            = st.sidebar.number_input("Order size", min_value=1, value=1000)

else:  # EMA+RSI
    params["fast_ema"]        = st.sidebar.number_input("Fast EMA", min_value=1, value=10)
    params["slow_ema"]        = st.sidebar.number_input("Slow EMA", min_value=1, value=30)
    params["rsi_period"]      = st.sidebar.number_input("RSI period", min_value=1, value=14)
    params["rsi_oversold"]    = st.sidebar.number_input("RSI oversold", min_value=1, max_value=100, value=30)
    params["rsi_overbought"]  = st.sidebar.number_input("RSI overbought", min_value=1, max_value=100, value=70)
    params["atr_multiplier"]  = st.sidebar.number_input("ATR multiplier", min_value=0.1, value=1.5, step=0.1)
    params["size"]            = st.sidebar.number_input("Order size", min_value=1, value=1000)

st.sidebar.header("Execute")
run_bt = st.sidebar.button("Run Backtest")

# ── Main ─────────────────────────────────────────────────────────────────────
if run_bt:
    st.markdown("## Running Backtest…")

    # 1) Setup DataHandler & Engine
    dh     = DataHandler(broker=broker, cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
    engine = BacktestEngine(data_handler=dh, cash=10_000, commission_perc=0.0002, slippage_perc=0.0001)

    # 2) Execute backtest
    stats = engine.run(
        strategy_cls,
        params,
        instruments,
        granularity,
        start=pd.to_datetime(start_date),
        end=pd.to_datetime(end_date)
    )

    # 3) Load a single series for plotting (first instrument)
    if instruments:
        df0     = dh.get_historical(instruments[0], granularity,
                                    start=pd.to_datetime(start_date),
                                    end=pd.to_datetime(end_date))
        returns = compute_returns(df0["close"].pct_change().fillna(0.0))
        equity  = equity_curve(returns, initial_capital=stats["start_cash"])
        drawdn  = drawdown_series(equity)
        roll_sh = compute_rolling_sharpe(returns, window=20)
    else:
        st.error("No instruments selected!")
        st.stop()

    # 4) Display summary metrics
    with st.expander("▶️ Summary Metrics", expanded=True):
        st.json(stats)

    # 5) Plot results
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Equity Curve")
        st.pyplot(plot_equity_curve(equity))
    with col2:
        st.subheader("Drawdown Curve")
        st.pyplot(plot_drawdown_curve(drawdn))

    st.subheader("Rolling Sharpe (20-period)")
    st.pyplot(plot_rolling_sharpe(returns, window=20))
