import backtrader as bt
from tokemfx.data import DataHandler

class Backtester:
    def __init__(self, strategy_cls, data_handler: DataHandler, cash=10_000):
        self.strategy_cls = strategy_cls
        self.data_handler = data_handler
        self.cash = cash

    def run(self, instrument, granularity, start, end):
        # 1. Fetch historical data
        df = self.data_handler.get_historical(instrument, granularity, start, end)

        # 2. Feed to Backtrader
        cerebro = bt.Cerebro()
        data_feed = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data_feed)
        cerebro.addstrategy(self.strategy_cls)
        cerebro.broker.setcash(self.cash)

        # 3. Run & return results
        result = cerebro.run()[0]
        stats = {
            "final_value": cerebro.broker.getvalue(),
            "starting_cash": self.cash,
        }
        return stats
