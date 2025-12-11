import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from src.test_utils import create_sample_ohlc_data
from src.backtesting.data_handler import BacktestDataHandler
from src.trading.execution.broker import DerivBroker as OANDABroker

@pytest.fixture
def dh(tmp_path, monkeypatch):
    # force CSV-only, no Redis/SQLite
    return BacktestDataHandler()

def test_csv_fallback(tmp_path, dh, monkeypatch):
    # prepare a small CSV
    instr, gran = "EUR_USD", "M1"
    start = datetime(2022,1,1)
    end   = datetime(2022,1,1,0,4)
    idx   = pd.date_range(start, end, freq="1T")
    df    = pd.DataFrame({"open":1,"high":1,"low":1,"close":1,"volume":0}, index=idx)
    path  = tmp_path/"cache"/f"{instr}_{gran}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
    path.parent.mkdir()
    df.to_csv(path)

    out = dh.get_historical(instr, gran, start, end, cache_dir=str(tmp_path/"cache"))
    assert isinstance(out, pd.DataFrame)
    assert len(out) == len(idx)
