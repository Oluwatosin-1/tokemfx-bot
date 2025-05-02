# src/tokemfx/data.py

import os
import time
import sqlite3
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import redis
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles

from tokemfx.config import OANDA_API_KEY, OANDA_ENV

logger = logging.getLogger(__name__)


class DataHandler:
    """
    Fetches & caches candles from OANDA, with layers:
      1) Redis (in-memory) — configurable key prefix & TTLs
      2) SQLite (disk) — robust storage & backfill
      3) CSV   (disk) — ad-hoc caching

    Also collects simple metrics on cache hits/misses and API calls.
    """

    def __init__(
        self,
        cache_dir: str = "cache",
        sqlite_path: str = None,
        redis_url: str = None,
        redis_ttl_historical: int = 3600,
        redis_ttl_latest: int = 300,
        redis_key_prefix: str = "tokemfx",
        retries: int = 3,
        backoff: float = 1.0
    ):
        # REST client
        self.api = API(access_token=OANDA_API_KEY, environment=OANDA_ENV)
        self.retries = retries
        self.backoff = backoff

        # CSV cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # SQLite cache
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        if self.sqlite_path:
            self._init_db()

        # Redis cache
        self.redis = None
        self.redis_ttl_historical = redis_ttl_historical
        self.redis_ttl_latest = redis_ttl_latest
        self.redis_key_prefix = redis_key_prefix
        if redis_url:
            try:
                self.redis = redis.Redis.from_url(redis_url)
                self.redis.ping()
                logger.info(f"Connected to Redis @ {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}); continuing without it")

        # Metrics
        self.metrics = {
            "redis_hits": 0,
            "redis_misses": 0,
            "redis_stores": 0,
            "sqlite_hits": 0,
            "sqlite_misses": 0,
            "csv_hits": 0,
            "csv_misses": 0,
            "api_calls": 0,
        }

    def get_metrics(self) -> dict:
        """Return current cache/API metrics."""
        return dict(self.metrics)

    def get_historical(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime = None,
        price: str = "M"
    ) -> pd.DataFrame:
        """
        Return candles from [start → end], with:
          • Redis (if enabled)
          • SQLite backfill (if enabled)
          • CSV fallback
        """
        end = end or datetime.utcnow()
        key = self._redis_key("historical", instrument, granularity, start, end)

        # 1) Redis
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    self.metrics["redis_hits"] += 1
                    logger.debug(f"Redis hit: {key}")
                    return pickle.loads(raw)
                else:
                    self.metrics["redis_misses"] += 1
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}")

        # 2) SQLite
        df = pd.DataFrame()
        if self.sqlite_path:
            df = self._load_from_db(instrument, granularity, start, end)
            if not df.empty:
                self.metrics["sqlite_hits"] += 1
            else:
                self.metrics["sqlite_misses"] += 1

            df = self._backfill_db_gaps(df, instrument, granularity, start, end, price)
        else:
            # 3) CSV
            cache_file = self._cache_path(instrument, granularity, start, end)
            if cache_file.exists():
                self.metrics["csv_hits"] += 1
                logger.info(f"CSV hit: {cache_file}")
                return pd.read_csv(cache_file, parse_dates=["time"], index_col="time")
            else:
                self.metrics["csv_misses"] += 1
                logger.info(f"CSV miss, fetching API for {instrument}/{granularity}")

        # After we have df (from SQLite or fetched), store CSV if needed
        if df.empty and not self.sqlite_path:
            df = self._fetch_all_candles(instrument, granularity, start, end, price)
            if not df.empty:
                df.to_csv(cache_file)
                logger.info(f"Saved CSV → {cache_file}")

        # 4) Populate Redis
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_historical)
                self.metrics["redis_stores"] += 1
                logger.debug(f"Stored in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis SET failed: {e}")

        return df

    def get_latest(
        self,
        instrument: str,
        granularity: str,
        count: int = 500,
        price: str = "M"
    ) -> pd.DataFrame:
        """
        Fetch the most recent `count` candles, with Redis caching.
        """
        key = self._redis_key("latest", instrument, granularity, count)

        # 1) Redis
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    self.metrics["redis_hits"] += 1
                    logger.debug(f"Redis hit: {key}")
                    return pickle.loads(raw)
                else:
                    self.metrics["redis_misses"] += 1
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET latest failed: {e}")

        # 2) API
        self.metrics["api_calls"] += 1
        logger.info(f"Fetching latest {count} bars for {instrument}/{granularity}")
        params = {"granularity": granularity, "price": price, "count": count}
        df = self._request_to_df(instrument, params)

        # 3) Store in Redis
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_latest)
                self.metrics["redis_stores"] += 1
                logger.debug(f"Stored latest in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis SET latest failed: {e}")

        return df

    def _redis_key(self, kind: str, instrument: str, granularity: str, *args) -> str:
        """
        Build a Redis key like:
          {prefix}:{kind}:{instrument}:{granularity}:{args...}
        """
        parts = [self.redis_key_prefix, kind, instrument, granularity] + [str(a) for a in args]
        return ":".join(parts)

    # ─── SQLite helpers ───────────────────────────────────────────────────────────

    def _init_db(self):
        "Create the SQLite `candles` table if it doesn't exist."
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                instrument TEXT NOT NULL,
                granularity TEXT NOT NULL,
                time      TEXT NOT NULL,
                open      REAL,
                high      REAL,
                low       REAL,
                close     REAL,
                volume    INTEGER,
                PRIMARY KEY(instrument, granularity, time)
            );
        """)
        conn.commit()
        conn.close()
        logger.info(f"Initialized SQLite cache at {self.sqlite_path}")

    def _load_from_db(
        self, instrument: str, granularity: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        "Load any existing rows for [start,end] from SQLite."
        conn = sqlite3.connect(self.sqlite_path)
        sql = """
            SELECT time, open, high, low, close, volume
            FROM candles
            WHERE instrument = ?
              AND granularity = ?
              AND time BETWEEN ? AND ?
            ORDER BY time
        """
        df = pd.read_sql(
            sql, conn,
            params=[instrument, granularity, start.isoformat(), end.isoformat()],
            parse_dates=["time"],
            index_col="time"
        )
        conn.close()
        if not df.empty:
            logger.info(f"Loaded {len(df)} rows from SQLite for {instrument}/{granularity}")
        return df

    def _backfill_db_gaps(
        self,
        df: pd.DataFrame,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime,
        price: str
    ) -> pd.DataFrame:
        """
        Detect missing timestamps in df for the requested range, fetch them,
        insert into DB, and return the merged, complete DataFrame.
        """
        # Build full expected index
        delta = self._granularity_to_timedelta(granularity)
        full_idx = pd.date_range(start=start, end=end, freq=delta)
        missing_idx = full_idx.difference(df.index)

        if missing_idx.empty:
            return df

        # Group missing timestamps into contiguous segments
        segments = []
        seg_start = prev = missing_idx[0]
        for ts in missing_idx[1:]:
            if ts - prev == delta:
                prev = ts
                continue
            segments.append((seg_start, prev + delta))
            seg_start = prev = ts
        segments.append((seg_start, prev + delta))

        # Fetch & insert each missing block
        to_insert = []
        for seg_s, seg_e in segments:
            logger.info(f"Backfilling {instrument} [{granularity}] {seg_s} → {seg_e}")
            chunk = self._fetch_all_candles(instrument, granularity, seg_s, seg_e, price)
            if not chunk.empty:
                to_insert.append(chunk)

        if to_insert:
            all_new = pd.concat(to_insert)
            self._write_to_db(all_new, instrument, granularity)
            # reload full DF from DB
            return self._load_from_db(instrument, granularity, start, end)

        return df

    def _write_to_db(
        self, df: pd.DataFrame, instrument: str, granularity: str
    ):
        "Bulk upsert into SQLite."
        conn = sqlite3.connect(self.sqlite_path)
        df = df.reset_index().rename(columns={"index": "time"})
        df["instrument"]  = instrument
        df["granularity"] = granularity
        df.to_sql(
            "candles", conn,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )
        conn.close()
        logger.info(f"Wrote {len(df)} rows to SQLite cache")

    # ─── Original CSV & API logic ────────────────────────────────────────────────

    def _cache_path(self, instrument, granularity, start, end):
        s = start.strftime("%Y%m%dT%H%M")
        e = end.strftime("%Y%m%dT%H%M")
        return self.cache_dir / f"{instrument}_{granularity}_{s}_{e}.csv"

    def _fetch_all_candles(
        self, instrument, granularity, start, end, price="M"
    ) -> pd.DataFrame:
        max_per = 5000
        delta  = self._granularity_to_timedelta(granularity)
        chunks = []
        current = start

        while True:
            params = {"granularity": granularity, "price": price, "from": current.isoformat()}
            if end:
                params["to"] = end.isoformat()
            else:
                params["count"] = max_per

            df_chunk = self._request_to_df(instrument, params)
            if df_chunk.empty:
                break

            chunks.append(df_chunk)
            last_ts = df_chunk.index[-1]
            current = last_ts + delta

            if end and current >= end:
                break
            if not end and len(df_chunk) < max_per:
                break

            time.sleep(self.backoff)

        return pd.concat(chunks) if chunks else pd.DataFrame()

    def _request_to_df(self, instrument, params):
        for i in range(1, self.retries + 1):
            try:
                req = InstrumentsCandles(instrument=instrument, params=params)
                resp = self.api.request(req)
                rows = [{
                    "time": pd.to_datetime(c["time"]),
                    "open":  float(c["mid"]["o"]),
                    "high":  float(c["mid"]["h"]),
                    "low":   float(c["mid"]["l"]),
                    "close": float(c["mid"]["c"]),
                    "volume": int(c.get("volume", 0))
                } for c in resp.get("candles", [])]
                return pd.DataFrame(rows).set_index("time")
            except Exception as e:
                logger.warning(f"API fetch failed ({i}/{self.retries}): {e}")
                time.sleep(self.backoff * i)
        raise RuntimeError(f"Failed to fetch after {self.retries} retries")

    @staticmethod
    def _granularity_to_timedelta(gran: str) -> timedelta:
        unit, val = gran[-1].upper(), int(gran[:-1])
        return {
            "S": timedelta(seconds=val),
            "M": timedelta(minutes=val),
            "H": timedelta(hours=val),
            "D": timedelta(days=val),
            "W": timedelta(weeks=val),
        }.get(unit) or (_ for _ in ()).throw(ValueError(f"Bad granularity '{gran}'"))
