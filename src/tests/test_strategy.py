import pandas as pd
import backtrader as bt
from datetime import datetime
from tokemfx.strategy import MovingAverageCrossStrategy

def test_ma_cross():
    # build a DataFrame that crosses
    dates = pd.date_range("2022-01-01", periods=50, freq="D")
    price = pd.Series(range(50), index=dates).astype(float)
    df    = pd.DataFrame({"close":price})
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MovingAverageCrossStrategy, fast_period=3, slow_period=5)
    feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(feed)
    cerebro.run()
    # no exception is success
