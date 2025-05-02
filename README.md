to run the project run the command 

#streamlit run app.py
# Paper/demo mode on OANDA (default)
python -m tokemfx.main

# Live mode on FXCM
python -m tokemfx.main --broker fxcm --live

# Customize caches
python -m tokemfx.main --cache-dir=~/tokemfx_cache --sqlite-path=~/tokemfx_cache/db.sqlite

# #run the command below to run project
# # paper trading (default)
# python -m tokemfx.main

# # live trading
# python -m tokemfx.main --live
With these files in place, your TokemFX project is fully integrated:

Config centralized

Broker abstraction for OANDA & FXCM

Data layer with Redis/SQLite/CSV caching & gap-fill

Strategies: basic + ATR breakout + EMA/RSI hybrid

Backtest engine: run, optimize, walk-forward, hyperopt

Analysis: returns, equity, drawdown, Sharpe/Sortino/Calmar

Streamlit app: interactive GUI to pick broker, pairs, timeframe, strategy & params, and visualize results