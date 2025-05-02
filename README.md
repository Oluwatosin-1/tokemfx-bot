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