import os
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

# ——— Abstract interface ———————————————————————————————————————————
class Broker(ABC):
    @abstractmethod
    def fetch_candles(self, instrument: str, granularity: str,
                      start: datetime = None, end: datetime = None,
                      count: int = None) -> pd.DataFrame:
        """Return OHLCV DataFrame indexed by timestamp."""

    @abstractmethod
    def place_order(self, instrument: str, units: int, **kwargs):
        """Execute a market order. Broker‐specific kwargs allowed."""


# ——— OANDA implementation —————————————————————————————————————————
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
from tokemfx.config import OANDA_API_KEY, OANDA_ENV, OANDA_ACCOUNT_ID

class OANDABroker(Broker):
    def __init__(self):
        self.api = API(access_token=OANDA_API_KEY, environment=OANDA_ENV)
        self._inst = instruments

    def fetch_candles(self, instrument, granularity, start=None, end=None, count=None):
        params = {"granularity": granularity, "price": "M"}
        if count:  params["count"]  = count
        if start:  params["from"]   = start.isoformat()
        if end:    params["to"]     = end.isoformat()

        req = self._inst.InstrumentsCandles(instrument=instrument, params=params)
        resp = self.api.request(req)
        rows = []
        for c in resp.get("candles", []):
            mid = c["mid"]
            rows.append({
                "time":   pd.to_datetime(c["time"]),
                "open":   float(mid["o"]),
                "high":   float(mid["h"]),
                "low":    float(mid["l"]),
                "close":  float(mid["c"]),
                "volume": int(c.get("volume", 0)),
            })
        return pd.DataFrame(rows).set_index("time")

    def place_order(self, instrument, units, **kwargs):
        from oandapyV20.endpoints.orders import OrderCreate
        account = kwargs.pop("account_id", OANDA_ACCOUNT_ID)
        data = {
            "order": {
                "instrument":    instrument,
                "units":         str(units),
                "type":          "MARKET",
                "positionFill":  "DEFAULT",
                **kwargs
            }
        }
        req = OrderCreate(accountID=account, data=data)
        return self.api.request(req)


# ——— FXCM implementation —————————————————————————————————————————
import fxcmpy
from tokemfx.config import FXCM_TOKEN, FXCM_HOST, FXCM_PORT

class FXCMBroker(Broker):
    def __init__(self):
        self.conn = fxcmpy.fxcmpy(
            access_token=FXCM_TOKEN,
            server=os.getenv("FXCM_HOST", FXCM_HOST),
            port=int(os.getenv("FXCM_PORT", FXCM_PORT))
        )

    def fetch_candles(self, instrument, granularity, start=None, end=None, count=None):
        period_map = {
            "M1": "m1", "M5": "m5", "M15": "m15",
            "H1": "H1", "H4": "H4", "D": "D1"
        }
        df = self.conn.get_candles(
            instrument,
            period=period_map[granularity],
            number=count,
            start=start,
            end=end
        )
        # average bid & ask for true mid
        df["open"]   = (df["bidopen"] + df["askopen"]) / 2
        df["high"]   = (df["bidhigh"] + df["askhigh"]) / 2
        df["low"]    = (df["bidlow"] + df["asklow"]) / 2
        df["close"]  = (df["bidclose"] + df["askclose"]) / 2
        df["volume"] = df["tickqty"]
        return df[["open", "high", "low", "close", "volume"]]

    def place_order(self, instrument, units, **kwargs):
        return self.conn.open_trade(
            symbol=instrument,
            is_buy=(units > 0),
            amount=abs(units),
            **kwargs
        )
