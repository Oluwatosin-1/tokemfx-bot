# src/tokemfx/strategy.py

import backtrader as bt

class BaseStrategy(bt.Strategy):
    """
    Base class for all strategies.
    Simply inherits from bt.Strategy; override next() in subclasses.
    """
    # no abstractmethod here—just a conceptual base class
    pass


class MovingAverageCrossStrategy(BaseStrategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()


class RSIReversionStrategy(BaseStrategy):
    params = (
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("period_hold", 5),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.hold_counter = 0

    def next(self):
        if not self.position:
            if self.rsi < self.p.rsi_oversold:
                self.buy()
                self.hold_counter = 0
            elif self.rsi > self.p.rsi_overbought:
                self.sell()
                self.hold_counter = 0
        else:
            self.hold_counter += 1
            if self.hold_counter >= self.p.period_hold:
                self.close()


class BollingerBreakoutStrategy(BaseStrategy):
    params = (
        ("bb_period", 20),
        ("bb_dev", 2.0),
        ("size", 1000),
    )

    def __init__(self):
        bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.bb_period,
            devfactor=self.p.bb_dev,
        )
        self.bb_high = bb.top
        self.bb_low  = bb.bot

    def next(self):
        if not self.position:
            if self.data.close[0] > self.bb_high[0]:
                self.buy(size=self.p.size)
            elif self.data.close[0] < self.bb_low[0]:
                self.sell(size=self.p.size)
        else:
            if self.position.size > 0 and self.data.close[0] < self.bb_high[0]:
                self.close()
            elif self.position.size < 0 and self.data.close[0] > self.bb_low[0]:
                self.close()
