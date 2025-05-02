# src/tokemfx/data.py

import logging
import sqlite3
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import redis

from tokemfx.config import (
    REDIS_URL,
    REDIS_TTL_HISTORICAL,
    REDIS_TTL_LATEST,
)
from tokemfx.broker import Broker

logger = logging.getLogger(__name__)

class DataHandler:
    """
    Caches any Broker.fetch_candles in three layers:
      1) Redis (in-memory) — fastest, short TTLs
      2) SQLite (disk)    — robust storage & automatic backfill
      3) CSV   (disk)    — ad-hoc fallback

    Also tracks simple metrics on cache/API usage.
    """

    def __init__(
        self,
        broker: Broker,
        cache_dir: str = "cache",
        sqlite_path: Optional[str] = None,
        redis_url: Optional[str] = REDIS_URL,
        redis_ttl_historical: int = REDIS_TTL_HISTORICAL,
        redis_ttl_latest: int     = REDIS_TTL_LATEST,
        redis_key_prefix: str     = "tokemfx",
        retries: int              = 3,
        backoff: float            = 1.0,
    ):
        self.broker = broker
        self.retries = retries
        self.backoff = backoff

        # ── Redis layer ───────────────────────────────────────────
        self.redis = None
        if redis_url:
            try:
                self.redis = redis.Redis.from_url(redis_url)
                self.redis.ping()
                logger.info(f"✅ Connected to Redis @ {redis_url}")
            except Exception as e:
                logger.warning(f"⚠️ Redis unavailable ({e}), skipping layer")
        self.redis_ttl_historical = redis_ttl_historical
        self.redis_ttl_latest     = redis_ttl_latest
        self.redis_key_prefix     = redis_key_prefix

        # ── SQLite layer ──────────────────────────────────────────
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        if self.sqlite_path:
            self._init_db()

        # ── CSV fallback ──────────────────────────────────────────
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ── Metrics ───────────────────────────────────────────────
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
        """Return accumulated metrics."""
        return dict(self.metrics)

    # ── Public API ──────────────────────────────────────────────────────────────

    def get_historical(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch candles between start→end (inclusive), with caching layers.
        """
        end = end or datetime.utcnow()
        key = self._redis_key("hist", instrument, granularity, start, end)

        # 1) Redis
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    self.metrics["redis_hits"] += 1
                    logger.debug(f"Redis HIT {key}")
                    return pickle.loads(raw)
                else:
                    self.metrics["redis_misses"] += 1
                    logger.debug(f"Redis MISS {key}")
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}")

        df = pd.DataFrame()

        # 2) SQLite
        if self.sqlite_path:
            df = self._load_db(instrument, granularity, start, end)
            if not df.empty:
                self.metrics["sqlite_hits"] += 1
            else:
                self.metrics["sqlite_misses"] += 1

            df = self._backfill(instrument, granularity, start, end, df)

        # 3) CSV fallback
        if df.empty and not self.sqlite_path:
            path = self.cache_dir / f"{instrument}_{granularity}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
            if path.exists():
                self.metrics["csv_hits"] += 1
                logger.debug(f"CSV HIT {path}")
                df = pd.read_csv(path, parse_dates=["time"], index_col="time")
            else:
                self.metrics["csv_misses"] += 1
                logger.debug(f"CSV MISS {path}")

        # 4) Broker/API fetch in chunks
        if df.empty:
            df = self._fetch_all(instrument, granularity, start, end)
            # persist to CSV if no SQLite
            if not self.sqlite_path:
                path = self.cache_dir / f"{instrument}_{granularity}_{start:%Y%m%d}_{end:%Y%m%d}.csv"
                df.to_csv(path)

        # 5) Write to SQLite
        if self.sqlite_path and not df.empty:
            self._write_db(df, instrument, granularity)

        # 6) Store to Redis
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_historical)
                self.metrics["redis_stores"] += 1
            except Exception as e:
                logger.warning(f"Redis SET failed: {e}")

        return df

    def get_latest(
        self,
        instrument: str,
        granularity: str,
        count: int = 500
    ) -> pd.DataFrame:
        """
        Fetch the most recent count bars, with Redis caching.
        """
        key = self._redis_key("latest", instrument, granularity, count)

        # Redis
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    self.metrics["redis_hits"] += 1
                    return pickle.loads(raw)
                else:
                    self.metrics["redis_misses"] += 1
            except Exception as e:
                logger.warning(f"Redis GET latest failed: {e}")

        # API
        self.metrics["api_calls"] += 1
        df = self.broker.fetch_candles(
            instrument, granularity, count=count
        )  # Broker returns full DataFrame

        # Cache
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_latest)
                self.metrics["redis_stores"] += 1
            except Exception as e:
                logger.warning(f"Redis SET latest failed: {e}")

        return df

    # ── Internal helpers ─────────────────────────────────────────────────────────

    def _redis_key(self, kind, instr, gran, *args) -> str:
        parts = [self.redis_key_prefix, kind, instr, gran] + [str(a) for a in args]
        return ":".join(parts)

    def _fetch_all(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """
        Breaks a large historical request into chunks and concatenates them.
        """
        max_count = 5000
        delta = self._gran_to_timedelta(granularity)
        chunks, cursor = [], start

        while True:
            cnt = None if end else max_count
            df_chunk = self.broker.fetch_candles(
                instrument,
                granularity,
                start=cursor,
                end=end if end else None,
                count=cnt
            )
            if df_chunk.empty:
                break
            chunks.append(df_chunk)
            last = df_chunk.index[-1] + delta
            if end and last >= end:
                break
            if not end and len(df_chunk) < max_count:
                break
            cursor = last
            time.sleep(self.backoff)

        return pd.concat(chunks) if chunks else pd.DataFrame()

    def _gran_to_timedelta(self, gran: str) -> timedelta:
        unit = gran[-1].upper()
        val  = int(gran[:-1])
        mapping = {
            "S": timedelta(seconds=val),
            "M": timedelta(minutes=val),
            "H": timedelta(hours=val),
            "D": timedelta(days=val),
            "W": timedelta(weeks=val),
        }
        if unit not in mapping:
            raise ValueError(f"Unsupported granularity: {gran}")
        return mapping[unit]

    # ── SQLite persistence ───────────────────────────────────────────────────────

    def _init_db(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                instrument TEXT NOT NULL,
                granularity TEXT NOT NULL,
                time        TEXT NOT NULL,
                open        REAL,
                high        REAL,
                low         REAL,
                close       REAL,
                volume      INTEGER,
                PRIMARY KEY(instrument, granularity, time)
            );
        """)
        conn.commit()
        conn.close()
        logger.info(f"Initialized SQLite cache @ {self.sqlite_path}")

    def _load_db(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        conn = sqlite3.connect(self.sqlite_path)
        sql = """
            SELECT time, open, high, low, close, volume
              FROM candles
             WHERE instrument=? AND granularity=?
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
        return df

    def _backfill(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Find gaps in the DataFrame’s index and fill them via broker calls.
        """
        if df.empty:
            return df

        delta = self._gran_to_timedelta(granularity)
        full_idx = pd.date_range(start=start, end=end, freq=delta)
        missing = full_idx.difference(df.index)

        if missing.empty:
            return df

        segments, seg_start = [], missing[0]
        prev = seg_start
        for ts in missing[1:]:
            if ts - prev == delta:
                prev = ts
            else:
                segments.append((seg_start, prev + delta))
                seg_start = prev = ts
        segments.append((seg_start, prev + delta))

        to_store = []
        for s, e in segments:
            chunk = self._fetch_all(instrument, granularity, s, e)
            if not chunk.empty:
                to_store.append(chunk)

        if not to_store:
            return df

        new_df = pd.concat(to_store)
        merged = pd.concat([df, new_df]).sort_index()
        self._write_db(new_df, instrument, granularity)
        return merged

    def _write_db(
        self,
        df: pd.DataFrame,
        instrument: str,
        granularity: str
    ):
        conn = sqlite3.connect(self.sqlite_path)
        df_reset = df.reset_index().rename(columns={"index": "time"})
        df_reset["instrument"]  = instrument
        df_reset["granularity"] = granularity
        df_reset.to_sql(
            "candles",
            conn,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )
        conn.close()
        logger.debug(f"Wrote {len(df_reset)} new rows to SQLite")
