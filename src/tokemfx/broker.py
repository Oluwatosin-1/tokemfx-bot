# src/tokemfx/broker.py

import os
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5  # Add this at top

# ——— Abstract interface ———————————————————————————————————————————
class Broker(ABC):
    @abstractmethod
    def fetch_candles(self,
                      instrument: str,
                      granularity: str,
                      start: datetime = None,
                      end: datetime = None,
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
        if count:  params["count"] = count
        if start:  params["from"]  = start.isoformat()
        if end:    params["to"]    = end.isoformat()

        req  = self._inst.InstrumentsCandles(instrument=instrument, params=params)
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
                "instrument":   instrument,
                "units":        str(units),
                "type":         "MARKET",
                "positionFill": "DEFAULT",
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
        # average bid+ask for mid prices
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


# ——— HotForex implementation —————————————————————————————————————
import requests
from tokemfx.config import HF_API_KEY, HF_API_SECRET, HF_ACCOUNT_ID

class HotForexBroker(Broker):
    BASE = "https://api.hotforex.com"  # example; check real base URL

    def __init__(self):
        self.api_key    = HF_API_KEY
        self.secret     = HF_API_SECRET
        self.account_id = HF_ACCOUNT_ID

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HF-Secret":     self.secret,
            "Content-Type":  "application/json",
        }

    def fetch_candles(self, instrument, granularity, start=None, end=None, count=None):
        """
        Hit HotForex OHLC endpoint. Payload keys depend on their spec.
        """
        params = {
            "instrument": instrument,
            "granularity": granularity,
            **({"start": start.isoformat()} if start else {}),
            **({"end":   end.isoformat()}   if end else {}),
            **({"count": count}             if count else {}),
        }
        r = requests.get(f"{self.BASE}/v1/marketdata/candles",
                         headers=self._headers(),
                         params=params,
                         timeout=10)
        r.raise_for_status()
        data = r.json()["candles"]
        rows = []
        for c in data:
            rows.append({
                "time":   pd.to_datetime(c["time"]),
                "open":   float(c["open"]),
                "high":   float(c["high"]),
                "low":    float(c["low"]),
                "close":  float(c["close"]),
                "volume": int(c.get("volume", 0)),
            })
        return pd.DataFrame(rows).set_index("time")

    def place_order(self, instrument, units, **kwargs):
        payload = {
            "accountId":   self.account_id,
            "symbol":      instrument,
            "volume":      abs(units),
            "side":        "buy" if units>0 else "sell",
            "orderType":   "market",
            **kwargs
        }
        r = requests.post(f"{self.BASE}/v1/orders/market",
                          headers=self._headers(),
                          json=payload,
                          timeout=10)
        r.raise_for_status()
        return r.json()


# ——— OctaFX implementation ————————————————————————————————————————
from tokemfx.config import OFX_API_KEY, OFX_API_SECRET, OFX_ACCOUNT_ID

class OctaFXBroker(Broker):
    BASE = "https://api.octafx.com"  # check real base URL!

    def __init__(self):
        self.key        = OFX_API_KEY
        self.secret     = OFX_API_SECRET
        self.account_id = OFX_ACCOUNT_ID

    def _headers(self):
        return {
            "X-API-KEY": self.key,
            "X-API-SECRET": self.secret,
            "Content-Type": "application/json",
        }

    def fetch_candles(self, instrument, granularity, start=None, end=None, count=None):
        params = {
            "symbol": instrument,
            "timeframe": granularity,
            **({"from": start.isoformat()} if start else {}),
            **({"to":   end.isoformat()}   if end else {}),
            **({"limit": count}            if count else {}),
        }
        r = requests.get(f"{self.BASE}/public/market/candles",
                         headers=self._headers(),
                         params=params,
                         timeout=10)
        r.raise_for_status()
        items = r.json()["data"]
        rows = [{
            "time":   pd.to_datetime(i["timestamp"], unit="ms"),
            "open":   float(i["open"]),
            "high":   float(i["high"]),
            "low":    float(i["low"]),
            "close":  float(i["close"]),
            "volume": int(i.get("volume", 0)),
        } for i in items]
        return pd.DataFrame(rows).set_index("time")

    def place_order(self, instrument, units, **kwargs):
        payload = {
            "account":  self.account_id,
            "symbol":   instrument,
            "lots":     abs(units) / 10000,  # depending on OctaFX lot sizing
            "direction": "buy" if units>0 else "sell",
            **kwargs
        }
        r = requests.post(f"{self.BASE}/private/orders/market",
                          headers=self._headers(),
                          json=payload,
                          timeout=10)
        r.raise_for_status()
        return r.json()


# ——— Exness implementation ————————————————————————————————————————
from tokemfx.config import EXNESS_API_KEY, EXNESS_API_SECRET, EXNESS_ACCOUNT_ID

class ExnessBroker(Broker):
    BASE = "https://api.exness.com"  # example

    def __init__(self):
        self.key        = EXNESS_API_KEY
        self.secret     = EXNESS_API_SECRET
        self.account_id = EXNESS_ACCOUNT_ID

    def _headers(self):
        return {
            "API-Key":    self.key,
            "API-Secret": self.secret,
            "Content-Type":"application/json",
        }

    def fetch_candles(self, instrument, granularity, start=None, end=None, count=None):
        params = {
            "symbol": instrument,
            "interval": granularity,
            **({"from": start.isoformat()} if start else {}),
            **({"to":   end.isoformat()}   if end else {}),
            **({"limit": count}            if count else {}),
        }
        r = requests.get(f"{self.BASE}/v1/marketdata/candles",
                         headers=self._headers(),
                         params=params,
                         timeout=10)
        r.raise_for_status()
        data = r.json()["candles"]
        rows = [{
            "time":   pd.to_datetime(c["time"]),
            "open":   float(c["open"]),
            "high":   float(c["high"]),
            "low":    float(c["low"]),
            "close":  float(c["close"]),
            "volume": int(c.get("volume", 0)),
        } for c in data]
        return pd.DataFrame(rows).set_index("time")

    def place_order(self, instrument, units, **kwargs):
        payload = {
            "account_id": self.account_id,
            "symbol":     instrument,
            "volume":     abs(units),
            "side":       "buy" if units>0 else "sell",
            **kwargs
        }
        r = requests.post(f"{self.BASE}/v1/orders",
                          headers=self._headers(),
                          json=payload,
                          timeout=10)
        r.raise_for_status()
        return r.json()
