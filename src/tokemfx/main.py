# src/tokemfx/main.py

import logging
import sys
import argparse

from tokemfx.config import (
    OANDA_API_KEY,
    OANDA_ACCOUNT_ID,
    OANDA_ENV,
    LOG_LEVEL,
)
from tokemfx.executor import Executor  # your execution engine
from tokemfx.data import DataHandler
from tokemfx.config import REDIS_URL

dh = DataHandler(
    cache_dir="cache",
    sqlite_path="cache/candles.db",
    redis_url=REDIS_URL,
    redis_ttl_historical=1800,  # 30 min
    redis_ttl_latest=60,        # 1 min
    redis_key_prefix="tokemfx"
)


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

    # sanity-check credentials
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        logger.error(
            "Missing OANDA_API_KEY or OANDA_ACCOUNT_ID – "
            "please check your .env file"
        )
        sys.exit(1)

    logger.info("Starting TokemFX Bot", environment=OANDA_ENV)

    parser = argparse.ArgumentParser(
        description="TokemFX — a Python Forex trading bot"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live mode (default is paper/demo)",
    )
    args = parser.parse_args()

    mode = "live" if args.live else "paper"
    logger.info("Mode selected", mode=mode)

    # pass live flag into your Executor
    executor = Executor(live=args.live)
    executor.start()

if __name__ == "__main__":
    main()

# #run the command below to run project
# # paper trading (default)
# python -m tokemfx.main

# # live trading
# python -m tokemfx.main --live
