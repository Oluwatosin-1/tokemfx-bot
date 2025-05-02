import pytest
import pandas as pd
from datetime import datetime, timedelta
from tokemfx.data import DataHandler
from tokemfx.broker import OANDABroker

@pytest.fixture
def dh(tmp_path, monkeypatch):
    # force CSV-only, no Redis/SQLite
    return DataHandler(
        broker=OANDABroker(),
        cache_dir=str(tmp_path/"cache"),
        sqlite_path=None,
        redis_url=None
    )

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

    out = dh.get_historical(instr, gran, start, end)
    assert isinstance(out, pd.DataFrame)
    assert len(out) == len(idx)
