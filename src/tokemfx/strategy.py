# src/tokemfx/strategy.py

import backtrader as bt

class BaseStrategy(bt.Strategy):
    """
    Base class for all strategies.
    Simply inherits from bt.Strategy; override next() in subclasses.
    """
    pass


class MovingAverageCrossStrategy(BaseStrategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.fast_ma    = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma    = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover  = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

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
        self.rsi          = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
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


# ─── New: ATR Breakout with Bracket Orders ────────────────────────────────────
class ATRBreakoutStrategy(BaseStrategy):
    params = (
        ("donchian_period", 20),
        ("atr_period", 14),
        ("atr_multiplier", 1.0),
        ("risk_reward", 2.0),   # take-profit multiple of ATR
        ("size", 1000),
    )

    def __init__(self):
        self.don_high = bt.indicators.Highest(self.data.high, period=self.p.donchian_period)
        self.atr      = bt.indicators.ATR(self.data, period=self.p.atr_period)

    def next(self):
        if not self.position:
            # break above prior Donchian high
            if self.data.close[0] > self.don_high[-1]:
                entry = self.data.close[0]
                atr   = self.atr[0] * self.p.atr_multiplier
                stop  = entry - atr
                limit = entry + atr * self.p.risk_reward

                # bracket order: entry + stop-loss + take-profit
                self.buy_bracket(
                    size=self.p.size,
                    price=entry,
                    stopprice=stop,
                    limitprice=limit
                )
        else:
            # position is managed by bracket orders automatically
            pass


# ─── New: EMA + RSI Hybrid with ATR Trailing Stop ─────────────────────────────
class EMARSIHybridStrategy(BaseStrategy):
    params = (
        ("fast_ema", 10),
        ("slow_ema", 30),
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("atr_period", 14),
        ("atr_multiplier", 1.5),
        ("size", 1000),
    )

    def __init__(self):
        self.ema_fast = bt.indicators.EMA(self.data.close, period=self.p.fast_ema)
        self.ema_slow = bt.indicators.EMA(self.data.close, period=self.p.slow_ema)
        self.rsi      = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.atr      = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.entry_order = None

    def next(self):
        # no open position: look for signal
        if not self.position:
            # long signal: EMA fast > slow and RSI oversold
            if self.ema_fast[0] > self.ema_slow[0] and self.rsi[0] < self.p.rsi_oversold:
                entry = self.data.close[0]
                atr   = self.atr[0] * self.p.atr_multiplier
                stop  = entry - atr

                # buy and place a stop-loss order
                self.entry_order = self.buy(size=self.p.size)
                self.sell(
                    exectype=bt.Order.Stop,
                    price=stop,
                    size=self.p.size,
                    parent=self.entry_order
                )

            # short signal: EMA fast < slow and RSI overbought
            elif self.ema_fast[0] < self.ema_slow[0] and self.rsi[0] > self.p.rsi_overbought:
                entry = self.data.close[0]
                atr   = self.atr[0] * self.p.atr_multiplier
                stop  = entry + atr

                self.entry_order = self.sell(size=self.p.size)
                self.buy(
                    exectype=bt.Order.Stop,
                    price=stop,
                    size=self.p.size,
                    parent=self.entry_order
                )

        # position exists: exit on cross or RSI extreme
        else:
            # if long and EMA cross down or RSI overbought, close
            if self.position.size > 0:
                if self.ema_fast[0] < self.ema_slow[0] or self.rsi[0] > self.p.rsi_overbought:
                    self.close()
            # if short and EMA cross up or RSI oversold, close
            elif self.position.size < 0:
                if self.ema_fast[0] > self.ema_slow[0] or self.rsi[0] < self.p.rsi_oversold:
                    self.close()
