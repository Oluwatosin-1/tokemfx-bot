import os
from dotenv import load_dotenv, find_dotenv

# ─── Load environment variables from .env ───────────────────────────────────────
load_dotenv(find_dotenv())

# ─── OANDA Settings ────────────────────────────────────────────────────────────
_env = os.getenv("OANDA_ENV", "practice").lower()
if _env in ("practice", "sandbox"):
    OANDA_ENV = "practice"
elif _env == "live":
    OANDA_ENV = "live"
else:
    raise ValueError("OANDA_ENV must be 'practice' or 'live'")

OANDA_API_KEY    = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
OANDA_API_SECRET = os.getenv("OANDA_API_SECRET", "")  # if using CCXT

# ─── FXCM Settings ─────────────────────────────────────────────────────────────
FXCM_TOKEN       = os.getenv("FXCM_TOKEN")
FXCM_HOST        = os.getenv("FXCM_HOST", "demo")   # "demo" or "real"
FXCM_PORT        = os.getenv("FXCM_PORT", "443")

# ─── Redis Settings ────────────────────────────────────────────────────────────
REDIS_URL            = os.getenv("REDIS_URL", None)
REDIS_TTL_HISTORICAL = int(os.getenv("REDIS_TTL_HISTORICAL", "3600"))
REDIS_TTL_LATEST     = int(os.getenv("REDIS_TTL_LATEST",     "300"))
REDIS_KEY_PREFIX     = os.getenv("REDIS_KEY_PREFIX", "tokemfx")

# ─── General Settings ──────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
