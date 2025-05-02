# src/tokemfx/data.py

import os
import time
import sqlite3
import logging
import pickle
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import redis
from tokemfx.broker import Broker

logger = logging.getLogger(__name__)

# ─── Optional Prometheus instrumentation ────────────────────────────────────
try:
    from prometheus_client import Counter, start_http_server, REGISTRY

    # Try to start metrics endpoint (silent if already bound)
    try:
        start_http_server(8000)
    except OSError as e:
        logger.warning(f"Prometheus HTTP on 8000: {e}")

    def _make_counter(name: str, desc: str) -> Counter:
        try:
            return Counter(name, desc)
        except ValueError:
            # Already registered → reuse
            return REGISTRY._names_to_collectors[name]

    PROM_REDIS_HITS    = _make_counter("dh_redis_hits",    "Redis cache hits")
    PROM_REDIS_MISSES  = _make_counter("dh_redis_misses",  "Redis cache misses")
    PROM_REDIS_STORES  = _make_counter("dh_redis_stores",  "Redis cache stores")
    PROM_SQLITE_HITS   = _make_counter("dh_sqlite_hits",   "SQLite cache hits")
    PROM_SQLITE_MISSES = _make_counter("dh_sqlite_misses", "SQLite cache misses")
    PROM_CSV_HITS      = _make_counter("dh_csv_hits",      "CSV cache hits")
    PROM_CSV_MISSES    = _make_counter("dh_csv_misses",    "CSV cache misses")
    PROM_API_CALLS     = _make_counter("dh_api_calls",     "API calls made")

except ImportError:
    logger.info("prometheus_client not available; skipping metrics")
    class _NoOp:
        def inc(self): pass
    PROM_REDIS_HITS = PROM_REDIS_MISSES = PROM_REDIS_STORES = _NoOp()
    PROM_SQLITE_HITS = PROM_SQLITE_MISSES = _NoOp()
    PROM_CSV_HITS = PROM_CSV_MISSES = _NoOp()
    PROM_API_CALLS = _NoOp()


class DataHandler:
    """
    Fetches & caches OHLCV data via the given Broker, with layers:
      1) Redis (in-memory)
      2) SQLite (on-disk, with backfill)
      3) CSV   (ad-hoc)
      4) Broker fetch (final fallback)

    Exposes Prometheus metrics if available.
    """

    def __init__(
        self,
        broker: Broker,
        cache_dir: str = "cache",
        sqlite_path: str = None,
        redis_url: str = None,
        redis_ttl_historical: int = 3600,
        redis_ttl_latest: int = 300,
        redis_key_prefix: str = "tokemfx",
        retries: int = 3,
        backoff: float = 1.0
    ):
        self.broker               = broker
        self.retries              = retries
        self.backoff              = backoff

        # CSV cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # SQLite cache
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        if self.sqlite_path:
            self._init_db()

        # Redis cache
        self.redis                = None
        self.redis_ttl_historical = redis_ttl_historical
        self.redis_ttl_latest     = redis_ttl_latest
        self.redis_key_prefix     = redis_key_prefix
        if redis_url:
            try:
                self.redis = redis.Redis.from_url(redis_url)
                self.redis.ping()
                logger.info(f"Connected to Redis @ {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}); continuing without it")

    def get_historical(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime = None,
        price: str = "M"
    ) -> pd.DataFrame:
        """
        Return candles between [start → end], using:
          1) Redis
          2) SQLite (with gap backfill)
          3) CSV fallback
          4) Broker fetch
        """
        end = end or datetime.now(timezone.utc)
        key = self._redis_key(
            "historical", instrument, granularity,
            start.isoformat(), end.isoformat()
        )

        # ── 1) Redis ──────────────────────────────────────────────────────────
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    PROM_REDIS_HITS.inc()
                    df = pickle.loads(raw)
                    logger.debug(f"Redis hit: {key}")
                    return df
                else:
                    PROM_REDIS_MISSES.inc()
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}")

        df = pd.DataFrame()

        # ── 2) SQLite with backfill ───────────────────────────────────────────
        if self.sqlite_path:
            df = self._load_db(instrument, granularity, start, end)
            if not df.empty:
                PROM_SQLITE_HITS.inc()
                logger.debug(f"SQLite hit: {len(df)} rows")
            else:
                PROM_SQLITE_MISSES.inc()
                logger.debug("SQLite miss")
            df = self._backfill(instrument, granularity, start, end, df)

        else:
            # ── 3) CSV fallback ────────────────────────────────────────────────
            cache_file = self._cache_path(instrument, granularity, start, end)
            if cache_file.exists():
                PROM_CSV_HITS.inc()
                logger.info(f"CSV hit: {cache_file}")
                return pd.read_csv(cache_file, parse_dates=["time"], index_col="time")
            else:
                PROM_CSV_MISSES.inc()
                logger.info(f"CSV miss: {cache_file}")

        # ── 4) Broker fetch ───────────────────────────────────────────────────
        if df.empty:
            df = self._fetch_all_candles(instrument, granularity, start, end)
            if not df.empty and not self.sqlite_path:
                cache_file = self._cache_path(instrument, granularity, start, end)
                df.to_csv(cache_file)
                logger.info(f"Saved CSV → {cache_file}")

        # ── 5) Populate Redis ─────────────────────────────────────────────────
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_historical)
                PROM_REDIS_STORES.inc()
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

        # Redis
        if self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    PROM_REDIS_HITS.inc()
                    df = pickle.loads(raw)
                    logger.debug(f"Redis hit: {key}")
                    return df
                else:
                    PROM_REDIS_MISSES.inc()
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET latest failed: {e}")

        # Broker fetch
        PROM_API_CALLS.inc()
        df = self.broker.fetch_candles(
            instrument=instrument,
            granularity=granularity,
            count=count
        )

        # Store in Redis
        if self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_latest)
                PROM_REDIS_STORES.inc()
                logger.debug(f"Stored latest in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis SET latest failed: {e}")

        return df

    # ─── Internal Helpers ────────────────────────────────────────────────────────

    def _redis_key(self, kind: str, instrument: str, gran: str, *args) -> str:
        return ":".join([self.redis_key_prefix, kind, instrument, gran]
                        + list(map(str, args)))

    def _cache_path(self, instrument: str, gran: str,
                    start: datetime, end: datetime) -> Path:
        s = start.strftime("%Y%m%dT%H%M")
        e = end.strftime("%Y%m%dT%H%M")
        return self.cache_dir / f"{instrument}_{gran}_{s}_{e}.csv"

    def _fetch_all_candles(
        self, instrument: str, granularity: str,
        start: datetime, end: datetime
    ) -> pd.DataFrame:
        """
        Chunk a long date-range into broker.fetch_candles calls.
        """
        delta = self._gran_to_timedelta(granularity)
        chunks, cursor = [], start

        while True:
            df_chunk = self.broker.fetch_candles(
                instrument=instrument,
                granularity=granularity,
                start=cursor,
                end=end,
                count=None
            )
            if df_chunk.empty:
                break
            chunks.append(df_chunk)
            next_cursor = df_chunk.index[-1] + delta
            if next_cursor >= end:
                break
            cursor = next_cursor
            time.sleep(self.backoff)

        return pd.concat(chunks) if chunks else pd.DataFrame()

    def _gran_to_timedelta(self, gran: str) -> timedelta:
        """
        Convert a granularity string ("M1","H4","D", etc.) to a timedelta.
        A single letter ("D","H","M","S","W") means 1 unit.
        """
        gran = gran.upper()
        if len(gran) == 1:
            unit, val = gran, 1
        else:
            unit, val = gran[0], int(gran[1:])
        mapping = {
            "S": timedelta(seconds=val),
            "M": timedelta(minutes=val),
            "H": timedelta(hours=val),
            "D": timedelta(days=val),
            "W": timedelta(weeks=val),
        }
        if unit not in mapping:
            raise ValueError(f"Bad granularity '{gran}'")
        return mapping[unit]

    # ─── SQLite persistence ───────────────────────────────────────────────────────

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
        logger.info(f"Initialized SQLite cache at {self.sqlite_path}")

    def _load_db(
        self, instrument: str, granularity: str,
        start: datetime, end: datetime
    ) -> pd.DataFrame:
        conn = sqlite3.connect(self.sqlite_path)
        df = pd.read_sql(
            """
            SELECT time, open, high, low, close, volume
              FROM candles
             WHERE instrument=? AND granularity=? 
               AND time BETWEEN ? AND ?
             ORDER BY time
            """,
            conn,
            params=[instrument, granularity, start.isoformat(), end.isoformat()],
            parse_dates=["time"],
            index_col="time"
        )
        conn.close()
        return df

    def _backfill(
        self, instrument: str, granularity: str,
        start: datetime, end: datetime,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fill missing timestamps by fetching segments & writing to SQLite.
        """
        delta    = self._gran_to_timedelta(granularity)
        full_idx = pd.date_range(start=start, end=end, freq=delta)
        missing  = full_idx.difference(df.index)
        if missing.empty:
            return df

        # Group missing into contiguous spans
        segments, seg_start = [], missing[0]
        prev = seg_start
        for ts in missing[1:]:
            if ts - prev == delta:
                prev = ts
            else:
                segments.append((seg_start, prev + delta))
                seg_start = prev = ts
        segments.append((seg_start, prev + delta))

        to_write = []
        for s, e in segments:
            chunk = self._fetch_all_candles(instrument, granularity, s, e)
            if not chunk.empty:
                to_write.append(chunk)

        if to_write:
            new_df = pd.concat(to_write)
            self._write_db(new_df, instrument, granularity)
            return self._load_db(instrument, granularity, start, end)

        return df

    def _write_db(
        self, df: pd.DataFrame, instrument: str, granularity: str
    ):
        conn = sqlite3.connect(self.sqlite_path)
        df_reset = df.reset_index().rename(columns={"index": "time"})
        df_reset["instrument"]  = instrument
        df_reset["granularity"] = granularity
        df_reset.to_sql(
            "candles", conn,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )
        conn.close()
        logger.info(f"Wrote {len(df_reset)} rows to SQLite cache")
