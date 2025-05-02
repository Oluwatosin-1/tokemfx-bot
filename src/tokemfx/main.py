#!/usr/bin/env python3
import sys
import os
import logging
import argparse

from tokemfx.config import (
    LOG_LEVEL,
    REDIS_URL,
)
from tokemfx.config import (
    OANDA_API_KEY,
    OANDA_ACCOUNT_ID,
    FXCM_TOKEN,
)
from tokemfx.broker import OANDABroker, FXCMBroker
from tokemfx.data import DataHandler
from tokemfx.executor import Executor

def setup_logging():
    """Configure root logger with timestamp, level, and message."""
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="TokemFX — a Python Forex trading bot"
    )
    parser.add_argument(
        "--broker",
        choices=["oanda", "fxcm"],
        default="oanda",
        help="Which broker to use (default: oanda)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode (otherwise paper/demo)",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Directory for CSV cache (default: cache)",
    )
    parser.add_argument(
        "--sqlite-path",
        default="cache/candles.db",
        help="Path for SQLite cache DB (default: cache/candles.db)",
    )
    parser.add_argument(
        "--redis-url",
        default=REDIS_URL,
        help="Redis URL for in-memory cache (default from config)",
    )
    parser.add_argument(
        "--redis-ttl-historical",
        type=int,
        default=3600,
        help="TTL for historical data in Redis, seconds (default: 3600)",
    )
    parser.add_argument(
        "--redis-ttl-latest",
        type=int,
        default=300,
        help="TTL for latest-bar data in Redis, seconds (default: 300)",
    )
    parser.add_argument(
        "--redis-key-prefix",
        default="tokemfx",
        help="Prefix for Redis keys (default: tokemfx)",
    )
    args = parser.parse_args()

    # ── Choose broker ────────────────────────────────────────────────────────────
    if args.broker == "oanda":
        if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
            logger.error("OANDA_API_KEY and OANDA_ACCOUNT_ID must be set for OANDA broker")
            sys.exit(1)
        broker = OANDABroker()
        logger.info("Using OANDA broker")
    else:  # fxcm
        if not FXCM_TOKEN:
            logger.error("FXCM_TOKEN must be set for FXCM broker")
            sys.exit(1)
        broker = FXCMBroker()
        logger.info("Using FXCM broker")

    # ── Initialize DataHandler ──────────────────────────────────────────────────
    dh = DataHandler(
        broker=broker,
        cache_dir=args.cache_dir,
        sqlite_path=args.sqlite_path,
        redis_url=args.redis_url,
        redis_ttl_historical=args.redis_ttl_historical,
        redis_ttl_latest=args.redis_ttl_latest,
        redis_key_prefix=args.redis_key_prefix,
        retries=3,
        backoff=1.0,
    )

    # ── Start the Executor ──────────────────────────────────────────────────────
    executor = Executor(broker=broker, data_handler=dh, live=args.live)
    mode = "LIVE" if args.live else "PAPER"
    logger.info(f"Starting Executor in {mode} mode")
    executor.start()

if __name__ == "__main__":
    main()
