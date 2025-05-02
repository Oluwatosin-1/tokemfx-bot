#!/usr/bin/env python3
# app.py

import sys
import os
from datetime import datetime, timezone
from multiprocessing import cpu_count

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
    performance_summary,
    plot_equity_curve,
    plot_drawdown_curve,
    plot_rolling_sharpe,
    plot_parameter_heatmap,
)

# ── Core components ───────────────────────────────────────────────────────────
from tokemfx.config   import REDIS_URL
from tokemfx.broker   import ExnessBroker, HotForexBroker, OANDABroker, FXCMBroker, OctaFXBroker
from tokemfx.data     import DataHandler
from tokemfx.backtest import BacktestEngine
from tokemfx.executor import Executor
from tokemfx.strategy import (
    ATRBreakoutStrategy,
    EMARSIHybridStrategy,
    MovingAverageCrossStrategy,
    RSIReversionStrategy,
    BollingerBreakoutStrategy,
)

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(layout="wide")
st.title("📊 TokemFX Interactive Backtester & Live Dashboard")

# ── Mode Selector ─────────────────────────────────────────────────────────────
mode = st.sidebar.radio("Mode", ["Backtest", "Grid Search", "Live", "Monitor"])

# ── Broker selection ─────────────────────────────────────────────────────────
broker_map = {
    "OANDA":      OANDABroker,
    "FXCM":       FXCMBroker,
    "HotForex":   HotForexBroker,
    "OctaFX":     OctaFXBroker,
    "Exness":     ExnessBroker,
}
broker_choice = st.sidebar.selectbox("Broker", list(broker_map.keys()))
broker        = broker_map[broker_choice]()

# ── Instruments ───────────────────────────────────────────────────────────────
try:
    # If your Broker subclass exposes a method to list pairs:
    available_instruments = broker.get_available_instruments()
except Exception:
    # Fallback static list
    available_instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]

if mode in ("Backtest", "Grid Search"):
    instruments = st.sidebar.multiselect(
        "Select FX pairs", available_instruments,
        default=[available_instruments[0]]
    )
else:
    instruments = [st.sidebar.selectbox("Instrument", available_instruments)]

# ── Granularity ───────────────────────────────────────────────────────────────
granularity = st.sidebar.selectbox(
    "Granularity", ["M1","M5","M15","H1","H4","D"], index=3
)

# ── Date range (Backtest / Grid) ──────────────────────────────────────────────
if mode in ("Backtest", "Grid Search"):
    today         = datetime.now(timezone.utc).date()
    default_start = today.replace(year=today.year - 1)
    start_date    = st.sidebar.date_input("Start Date", default_start)
    end_date      = st.sidebar.date_input("End Date", today)

# ── Strategy selection ────────────────────────────────────────────────────────
strategy_map  = {
    "MA Cross": MovingAverageCrossStrategy,
    "RSI Rev":  RSIReversionStrategy,
    "BBreak":   BollingerBreakoutStrategy,
    "ATR BO":   ATRBreakoutStrategy,
    "EMA+RSI":  EMARSIHybridStrategy,
}
strategy_name = st.sidebar.selectbox("Strategy", list(strategy_map.keys()))
strategy_cls  = strategy_map[strategy_name]

# ── Strategy parameters ───────────────────────────────────────────────────────
st.sidebar.subheader("Parameters")
params = {}
if strategy_name == "MA Cross":
    params["fast_period"] = st.sidebar.number_input("Fast MA", 1, 100, 10)
    params["slow_period"] = st.sidebar.number_input("Slow MA", 1, 200, 30)

elif strategy_name == "RSI Rev":
    params["rsi_period"]     = st.sidebar.number_input("RSI period", 1, 100, 14)
    params["rsi_oversold"]   = st.sidebar.number_input("Oversold", 1,100,30)
    params["rsi_overbought"] = st.sidebar.number_input("Overbought",1,100,70)
    params["period_hold"]    = st.sidebar.number_input("Hold Bars",1,50,5)

elif strategy_name == "BBreak":
    params["bb_period"] = st.sidebar.number_input("BB period", 1,100,20)
    params["bb_dev"]    = st.sidebar.number_input("BB dev", 0.1,5.0,2.0, step=0.1)
    params["size"]      = st.sidebar.number_input("Size", 1,10_000,1000)

elif strategy_name == "ATR BO":
    params["donchian_period"] = st.sidebar.number_input("Donchian", 1,100,20)
    params["atr_multiplier"]  = st.sidebar.number_input("ATR mult",0.1,5.0,1.0, step=0.1)
    params["risk_reward"]     = st.sidebar.number_input("RR",1.0,10.0,2.0, step=0.1)
    params["size"]            = st.sidebar.number_input("Size",1,10_000,1000)

else:  # EMA+RSI
    params["fast_ema"]       = st.sidebar.number_input("Fast EMA",1,100,10)
    params["slow_ema"]       = st.sidebar.number_input("Slow EMA",1,200,30)
    params["rsi_period"]     = st.sidebar.number_input("RSI period",1,100,14)
    params["rsi_oversold"]   = st.sidebar.number_input("RSI oversold",1,100,30)
    params["rsi_overbought"] = st.sidebar.number_input("RSI overbought",1,100,70)
    params["atr_multiplier"] = st.sidebar.number_input("ATR mult",0.1,5.0,1.5,step=0.1)
    params["size"]           = st.sidebar.number_input("Size",1,10_000,1000)

# ── Execution controls ─────────────────────────────────────────────────────────
def gran_to_seconds(gr: str) -> float:
    unit = gr[-1]; val = int(gr[:-1])
    return {"M":60,"H":3600,"D":86400}[unit] * val

if mode == "Backtest":
    run_bt  = st.sidebar.button("Run Backtest")
elif mode == "Grid Search":
    run_grid = st.sidebar.button("Run Grid Search")
    workers  = st.sidebar.number_input("Workers", min_value=1, max_value=cpu_count(), value=1)
elif mode == "Live":
    if "executor" not in st.session_state:
        st.session_state.executor = None
    start_live = st.sidebar.button("Start Live")
    stop_live  = st.sidebar.button("Stop Live")

# ── BACKTEST ──────────────────────────────────────────────────────────────────
if mode == "Backtest" and run_bt:
    st.markdown("## Running Backtest…")
    dh     = DataHandler(broker=broker, cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
    engine = BacktestEngine(data_handler=dh, cash=10_000, commission_perc=0.0002, slippage_perc=0.0001)

    stats = engine.run(
        strategy_cls, params, instruments, granularity,
        start=pd.to_datetime(start_date).tz_localize(timezone.utc),
        end=pd.to_datetime(end_date).tz_localize(timezone.utc)
    )

    # Plot first pair
    df0     = dh.get_historical(instruments[0], granularity,
                start=pd.to_datetime(start_date).tz_localize(timezone.utc),
                end=pd.to_datetime(end_date).tz_localize(timezone.utc))
    returns = compute_returns(df0["close"].pct_change().fillna(0))
    equity  = equity_curve(returns, initial_capital=stats["start_cash"])
    drawdn  = drawdown_series(equity)

    with st.expander("▶️ Summary Metrics", expanded=True):
        st.json(stats)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Equity Curve")
        st.pyplot(plot_equity_curve(equity))
    with c2:
        st.subheader("Drawdown Curve")
        st.pyplot(plot_drawdown_curve(drawdn))

    st.subheader("Rolling Sharpe (20)")
    st.pyplot(plot_rolling_sharpe(returns, window=20))

# ── GRID SEARCH ───────────────────────────────────────────────────────────────
elif mode == "Grid Search" and run_grid:
    st.markdown("## Running Grid Search…")
    dh     = DataHandler(broker=broker, cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
    engine = BacktestEngine(data_handler=dh, cash=10_000, commission_perc=0.0002, slippage_perc=0.0001)

    # Build simple grid: each param must be a comma-list in the sidebar text_input
    grid = {}
    for p in params:
        vals = st.sidebar.text_input(f"Values for {p} (comma separated)", str(params[p]))
        # cast back to param’s type
        typ = type(params[p])
        grid[p] = [typ(v.strip()) for v in vals.split(",") if v.strip()]

    results = engine.optimize(
        strategy_cls, grid, instruments, granularity,
        start=pd.to_datetime(start_date).tz_localize(timezone.utc),
        end=pd.to_datetime(end_date).tz_localize(timezone.utc),
        num_workers=workers
    )
    df_res = pd.DataFrame(results)
    st.subheader("Top 10 by Sharpe")
    st.dataframe(df_res.nlargest(10, "sharpe_ratio"))

    if len(grid) >= 2:
        x, y = list(grid.keys())[:2]
        st.subheader(f"Heatmap: {y} vs {x}")
        fig = plot_parameter_heatmap(df_res, x, y, "sharpe_ratio")
        st.pyplot(fig)

# ── LIVE ──────────────────────────────────────────────────────────────────────
elif mode == "Live":
    st.markdown("## Live Trading Executor")
    if start_live and st.session_state.executor is None:
        dh = DataHandler(broker=broker, cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
        ex = Executor(
            broker=broker,
            data_handler=dh,
            strategy_cls=strategy_cls,
            strategy_params=params,
            instrument=instruments[0],
            granularity=granularity,
            cash=10_000,
            poll_interval=gran_to_seconds(granularity),
            paper=True
        )
        ex.start()
        st.session_state.executor = ex
        st.success("Executor started (paper)")

    if stop_live and st.session_state.executor:
        st.session_state.executor.stop()
        st.session_state.executor = None
        st.warning("Executor stopped")

    if st.session_state.executor:
        st.info("Executor running…")

# ── MONITOR ───────────────────────────────────────────────────────────────────
elif mode == "Monitor":
    st.markdown("## Live Monitor")
    ex = st.session_state.executor
    if not ex:
        st.info("Start the Executor in Live mode first.")
    else:
        # 1) Account equity & P&L
        eq  = ex._cerebro.broker.getvalue()
        pnl = eq - ex.cash
        st.metric("Account Equity", f"{eq:.2f}", delta=f"{pnl:.2f}")

        # 2) Open position
        feed = ex._strategy.datas[0]
        pos  = ex._cerebro.broker.getposition(feed)
        bar  = ex.dh.get_latest(ex.instrument, ex.granularity, count=1).iloc[-1]
        unreal = pos.size * (bar.close - pos.price)
        pos_df = pd.DataFrame([{
            "Instrument": ex.instrument,
            "Size":        pos.size,
            "Entry":       f"{pos.price:.5f}",
            "Current":     f"{bar.close:.5f}",
            "Unrealized":  f"{unreal:.2f}"
        }])
        st.table(pos_df)

        # 3) Intraday equity curve
        today   = datetime.now(timezone.utc).date()
        df_hist = ex.dh.get_historical(
            ex.instrument, ex.granularity,
            start=pd.to_datetime(today).tz_localize(timezone.utc),
            end=pd.to_datetime(today).tz_localize(timezone.utc)
        )
        intr_rt = compute_returns(df_hist["close"].pct_change().fillna(0))
        intr_eq = equity_curve(intr_rt, initial_capital=ex.cash)
        st.subheader("Intraday Equity Curve")
        st.line_chart(intr_eq)
