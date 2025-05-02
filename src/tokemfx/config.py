import os
from dotenv import load_dotenv, find_dotenv

# Load .env into environment variables
load_dotenv(find_dotenv())

# ─── API Credentials ─────────────────────────────────────────────────────────────
# src/tokemfx/config.py

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# raw env string
_env = os.getenv("OANDA_ENV", "practice").lower()
if _env in ("practice", "sandbox"):
    OANDA_ENV = "practice"
elif _env == "live":
    OANDA_ENV = "live"
else:
    raise ValueError("OANDA_ENV must be ‘practice’ or ‘live’")

OANDA_API_KEY    = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
# … rest of your config …

# ─── Redis Settings ──────────────────────────────────────────────────────────────
# URL of your Redis instance, e.g. redis://localhost:6379/0
REDIS_URL                = os.getenv("REDIS_URL", None)
# separate TTLs (in seconds) for historical vs latest endpoints
REDIS_TTL_HISTORICAL     = int(os.getenv("REDIS_TTL_HISTORICAL", "3600"))
REDIS_TTL_LATEST         = int(os.getenv("REDIS_TTL_LATEST",     "300"))

# ─── General Settings ────────────────────────────────────────────────────────────
# e.g. "DEBUG", "INFO", "WARNING", "ERROR"
LOG_LEVEL          = os.getenv("LOG_LEVEL", "INFO").upper()
