"""
Data Handler for TokemFX Trading Module
========================================
Handles historical and real-time data fetching, caching, and management.

This module provides a unified interface for:
- OHLCV data retrieval from brokers
- Multi-layer caching (Redis, SQLite, CSV)
- Data validation and gap-filling
- Performance metrics and monitoring
"""

import os
import time
import sqlite3
import logging
import pickle
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import redis

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
    Fetches & caches OHLCV data via broker integration, with layers:
      1) Redis (in-memory, fast access)
      2) SQLite (on-disk persistence with backfill)
      3) CSV (fallback, simple file-based)
      4) Broker API (final fallback, live data)

    Supports multiple data formats and automatic gap-filling.
    Exposes Prometheus metrics when available.
    """

    def __init__(
        self,
        broker=None,
        cache_dir: str = "cache",
        sqlite_path: Optional[str] = None,
        redis_url: Optional[str] = None,
        redis_ttl_historical: int = 3600,
        redis_ttl_latest: int = 300,
        redis_key_prefix: str = "tokemfx",
        retries: int = 3,
        backoff: float = 1.0,
        enable_metrics: bool = True
    ):
        """
        Initialize DataHandler with configurable caching layers.

        Args:
            broker: TradingBroker instance for data fetching
            cache_dir: Directory for CSV file caching
            sqlite_path: Path to SQLite database (None disables SQLite)
            redis_url: Redis connection URL (None disables Redis)
            redis_ttl_historical: Seconds to cache historical data
            redis_ttl_latest: Seconds to cache live data
            redis_key_prefix: Redis key namespace prefix
            retries: Number of API retry attempts
            backoff: Seconds between retry attempts
            enable_metrics: Enable performance monitoring
        """
        self.broker = broker
        self.retries = retries
        self.backoff = backoff
        self.enable_metrics = enable_metrics

        # CSV cache setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # SQLite cache setup
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        if self.sqlite_path and sqlite_path:
            self._init_db()

        # Redis cache setup
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
                logger.warning(f"Redis connection failed ({e}); continuing without Redis cache")

    def get_historical(
        self,
        instrument: str,
        granularity: str,
        start: datetime,
        end: datetime = None,
        price: str = "M",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Return OHLCV candles between start/end using multi-layer cache.

        Cache hierarchy:
        1. Redis (fast, in-memory)
        2. SQLite (persistent, with gap-filling)
        3. CSV (simple file fallback)
        4. Broker API (live data fetch)

        Args:
            instrument: Trading instrument symbol
            granularity: Timeframe ('M1', 'H1', 'D', etc.)
            start: Start datetime (timezone-aware preferred)
            end: End datetime (defaults to now)
            price: Price type ('M' for mid, 'B' for bid, 'A' for ask)
            use_cache: Whether to use caching layers

        Returns:
            DataFrame with OHLCV columns indexed by timestamp
        """
        end = end or datetime.now(timezone.utc)

        # Generate cache key
        key = self._redis_key(
            "historical", instrument, granularity,
            start.isoformat(), end.isoformat()
        )

        # ── 1) Redis cache lookup ──────────────────────────────────────────────
        if use_cache and self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    if self.enable_metrics: PROM_REDIS_HITS.inc()
                    df = pickle.loads(raw)
                    logger.debug(f"Redis hit: {key}")
                    return df
                else:
                    if self.enable_metrics: PROM_REDIS_MISSES.inc()
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}")

        df = pd.DataFrame()

        # ── 2) SQLite with backfill ───────────────────────────────────────────
        if use_cache and self.sqlite_path:
            df = self._load_db(instrument, granularity, start, end)
            if not df.empty:
                if self.enable_metrics: PROM_SQLITE_HITS.inc()
                logger.debug(f"SQLite hit: {len(df)} rows")
            else:
                if self.enable_metrics: PROM_SQLITE_MISSES.inc()
                logger.debug("SQLite miss")

            # Fill any gaps in the data
            df = self._backfill(instrument, granularity, start, end, df)

        elif use_cache:
            # ── 3) CSV fallback ───────────────────────────────────────────────
            cache_file = self._cache_path(instrument, granularity, start, end)
            if cache_file.exists():
                if self.enable_metrics: PROM_CSV_HITS.inc()
                logger.info(f"CSV hit: {cache_file}")
                df = pd.read_csv(cache_file, parse_dates=["time"], index_col="time")
            else:
                if self.enable_metrics: PROM_CSV_MISSES.inc()
                logger.info(f"CSV miss: {cache_file}")

        # ── 4) Broker API fetch ───────────────────────────────────────────────
        if df.empty:
            if not self.broker:
                logger.error("No data source available - neither cache nor broker configured")
                return pd.DataFrame()

            if self.enable_metrics: PROM_API_CALLS.inc()
            df = self._fetch_all_candles(instrument, granularity, start, end)

            # Save to CSV if no SQLite
            if not self.sqlite_path and not df.empty:
                cache_file = self._cache_path(instrument, granularity, start, end)
                df.to_csv(cache_file)
                logger.info(f"Saved CSV → {cache_file}")

        # ── 5) Store in Redis ─────────────────────────────────────────────────
        if use_cache and self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_historical)
                if self.enable_metrics: PROM_REDIS_STORES.inc()
                logger.debug(f"Stored in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis SET failed: {e}")

        return df

    def get_latest(
        self,
        instrument: str,
        granularity: str,
        count: int = 500,
        price: str = "M",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch the most recent candles for an instrument.

        Args:
            instrument: Trading instrument symbol
            granularity: Timeframe ('M1', 'H1', 'D', etc.)
            count: Number of candles to fetch
            price: Price type ('M', 'B', 'A')
            use_cache: Whether to use Redis caching

        Returns:
            DataFrame with recent OHLCV data
        """
        if not self.broker:
            logger.error("No broker configured for data fetching")
            return pd.DataFrame()

        key = self._redis_key("latest", instrument, granularity, count)

        # ── Redis lookup ──────────────────────────────────────────────────────
        if use_cache and self.redis:
            try:
                raw = self.redis.get(key)
                if raw:
                    if self.enable_metrics: PROM_REDIS_HITS.inc()
                    df = pickle.loads(raw)
                    logger.debug(f"Redis hit: {key}")
                    return df
                else:
                    if self.enable_metrics: PROM_REDIS_MISSES.inc()
                    logger.debug(f"Redis miss: {key}")
            except Exception as e:
                logger.warning(f"Redis GET latest failed: {e}")

        # ── Broker fetch ──────────────────────────────────────────────────────
        if self.enable_metrics: PROM_API_CALLS.inc()
        df = self.broker.fetch_candles(
            instrument=instrument,
            granularity=granularity,
            count=count
        )

        # ── Store in Redis ────────────────────────────────────────────────────
        if use_cache and self.redis and not df.empty:
            try:
                self.redis.set(key, pickle.dumps(df), ex=self.redis_ttl_latest)
                if self.enable_metrics: PROM_REDIS_STORES.inc()
                logger.debug(f"Stored latest in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis SET latest failed: {e}")

        return df

    def validate_data(self, df: pd.DataFrame, instrument: str) -> Dict[str, Any]:
        """
        Validate data quality and return metrics.

        Args:
            df: DataFrame to validate
            instrument: Instrument name for logging

        Returns:
            Dictionary with validation results
        """
        if df.empty:
            return {'valid': False, 'errors': ['DataFrame is empty']}

        results = {
            'valid': True,
            'row_count': len(df),
            'columns': list(df.columns),
            'date_range': None,
            'gaps': 0,
            'outliers': 0,
            'errors': []
        }

        # Check required columns
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                results['errors'].append(f"Missing required column: {col}")
                results['valid'] = False

        if not results['valid']:
            return results

        # Check date range
        if isinstance(df.index, pd.DatetimeIndex) and not df.index.empty:
            results['date_range'] = {
                'start': df.index.min(),
                'end': df.index.max()
            }

            # Check for gaps (if we can determine expected frequency)
            if len(df) > 1:
                try:
                    # Calculate expected frequency from first few intervals
                    time_diffs = df.index[1:5] - df.index[:4]
                    avg_interval = time_diffs.mean()

                    # Find gaps larger than 1.5x the average interval
                    gaps = (df.index[1:] - df.index[:-1]) > (avg_interval * 1.5)
                    results['gaps'] = int(gaps.sum())
                except Exception as e:
                    logger.debug(f"Could not calculate gaps: {e}")

        return results

    def clear_cache(self, instrument: Optional[str] = None, granularity: Optional[str] = None):
        """
        Clear cache entries for specified criteria.

        Args:
            instrument: Specific instrument to clear (None for all)
            granularity: Specific granularity to clear (None for all)
        """
        # Redis cache
        if self.redis:
            pattern = f"{self.redis_key_prefix}:*"
            if instrument:
                pattern += f"{instrument}*"
            if granularity and instrument:
                pattern += f"{granularity}*"

            try:
                keys_to_delete = self.redis.keys(pattern)
                if keys_to_delete:
                    self.redis.delete(*keys_to_delete)
                    logger.info(f"Cleared {len(keys_to_delete)} Redis cache entries")
            except Exception as e:
                logger.warning(f"Redis cache clear failed: {e}")

        # SQLite cache - would require more complex logic to selectively clear
        # For now, we leave it as persistent cache

        logger.info("Cache clearing completed")

    # ─── Private helper methods ──────────────────────────────────────────────

    def _redis_key(self, kind: str, instrument: str, granularity: str, *args) -> str:
        """Generate Redis cache key."""
        return ":".join([self.redis_key_prefix, kind, instrument, granularity]
                        + list(map(str, args)))

    def _cache_path(self, instrument: str, granularity: str,
                    start: datetime, end: datetime) -> Path:
        """Generate CSV cache file path."""
        s = start.strftime("%Y%m%dT%H%M")
        e = end.strftime("%Y%m%dT%H%M")
        return self.cache_dir / f"{instrument}_{granularity}_{s}_{e}.csv"

    def _fetch_all_candles(
        self, instrument: str, granularity: str,
        start: datetime, end: datetime
    ) -> pd.DataFrame:
        """
        Fetch candles in chunks to handle long date ranges.
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
            if self.backoff > 0:
                time.sleep(self.backoff)

        return pd.concat(chunks) if chunks else pd.DataFrame()

    def _gran_to_timedelta(self, granularity: str) -> timedelta:
        """
        Convert granularity string to timedelta - supports multiple input formats.

        Supports formats:
        - 'M1', 'H4', 'D' (unit first, then number)
        - '1M', '4H', '1D' (number first, then unit)
        - 'D', 'H', 'M' (single letter = 1 unit)

        Args:
            granularity: Timeframe string in various formats

        Returns:
            Corresponding timedelta object

        Raises:
            ValueError: If granularity format is unsupported
        """
        if not granularity:
            raise ValueError("Granularity cannot be empty")

        granularity = granularity.upper().strip()

        # Check for single character formats (D, H, M, S, W)
        if len(granularity) == 1:
            unit, val = granularity, 1
        else:
            # Try to auto-detect format: unit first vs number first
            first_char = granularity[0]
            last_char = granularity[-1]

            # If first character is a digit, assume number-first format (e.g., '1H', '5M')
            if first_char.isdigit():
                # Number-first format: '1H', '4H', '5M', '15M', '1D'
                if last_char.isdigit():
                    raise ValueError(f"Invalid granularity format '{granularity}'. "
                                   f"Cannot have digits at both ends.")

                # Extract number and unit
                number_str = granularity[:-1]  # Everything except last character
                unit = last_char

                try:
                    val = int(number_str)
                except ValueError:
                    raise ValueError(f"Invalid number in granularity '{granularity}'. "
                                   f"Could not parse '{number_str}' as integer.")

            # If last character is not a digit, assume unit-first format (e.g., 'H1', 'M5', 'D')
            elif not last_char.isdigit():
                # Standard unit-first format: 'H1', 'M5', 'D', etc.
                unit = first_char
                val_str = granularity[1:]

                # Handle special cases like 'H4' which might be ambiguous
                if len(granularity) == 2 and val_str.isdigit():
                    # This could be legacy format like 'H4' for 4 hours
                    val = int(val_str)
                    if val > 1:
                        logger.info(f"Interpreting '{granularity}' as {val}-{unit} format (legacy compatibility)")
                elif val_str:
                    try:
                        val = int(val_str)
                    except ValueError:
                        raise ValueError(f"Invalid number in granularity '{granularity}'. "
                                       f"Could not parse '{val_str}' as integer.")
                else:
                    # Single character like 'H' = 1 hour
                    val = 1

            else:
                # Last character is digit, first is not - this shouldn't happen in valid formats
                raise ValueError(f"Invalid granularity format '{granularity}'. "
                               f"Unexpected digit at end.")

        # Validate unit and value
        valid_units = {
            "S": "seconds",
            "M": "minutes",
            "H": "hours",
            "D": "days",
            "W": "weeks"
        }

        if unit not in valid_units:
            raise ValueError(f"Unsupported time unit '{unit}' in granularity '{granularity}'. "
                           f"Supported units: {list(valid_units.keys())} (for {', '.join(valid_units.values())})")

        if val <= 0:
            raise ValueError(f"Invalid value {val} in granularity '{granularity}'. "
                           f"Value must be positive.")

        # Convert to timedelta
        mapping = {
            "S": timedelta(seconds=val),
            "M": timedelta(minutes=val),
            "H": timedelta(hours=val),
            "D": timedelta(days=val),
            "W": timedelta(weeks=val),
        }

        result = mapping[unit]
        logger.debug(f"Converted granularity '{granularity}' to timedelta: {result}")
        return result

    # ─── SQLite persistence methods ─────────────────────────────────────────

    def _init_db(self):
        """Initialize SQLite database schema."""
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
        """Load cached data from SQLite."""
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
        Identify and fill gaps in cached data by fetching missing segments.
        """
        delta = self._gran_to_timedelta(granularity)
        full_idx = pd.date_range(start=start, end=end, freq=delta)
        missing = full_idx.difference(df.index)

        if missing.empty:
            return df

        # Group missing timestamps into contiguous segments
        segments, seg_start = [], missing[0]
        prev = seg_start

        for ts in missing[1:]:
            if ts - prev == delta:
                prev = ts
            else:
                segments.append((seg_start, prev + delta))
                seg_start = prev = ts

        segments.append((seg_start, prev + delta))

        # Fetch and store missing segments
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
        """Write data chunk to SQLite database."""
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
