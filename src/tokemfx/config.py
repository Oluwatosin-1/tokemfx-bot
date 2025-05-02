# src/tokemfx/config.py

import os
from dotenv import load_dotenv, find_dotenv

# ─── Load .env ────────────────────────────────────────────────────────────────
load_dotenv(find_dotenv())

# ─── OANDA Settings ────────────────────────────────────────────────────────────
_env = os.getenv("OANDA_ENV", "practice").lower()
if _env in ("practice", "sandbox"):
    OANDA_ENV = "practice"
elif _env == "live":
    OANDA_ENV = "live"
else:
    raise ValueError("OANDA_ENV must be 'practice' or 'live'")

OANDA_API_KEY     = os.getenv("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID  = os.getenv("OANDA_ACCOUNT_ID", "")
OANDA_API_SECRET  = os.getenv("OANDA_API_SECRET", "")

# ─── FXCM Settings ─────────────────────────────────────────────────────────────
FXCM_TOKEN        = os.getenv("FXCM_TOKEN", "")
FXCM_HOST         = os.getenv("FXCM_HOST", "demo")   # "demo" or "real"
FXCM_PORT         = os.getenv("FXCM_PORT", "443")

# ─── Redis Settings ────────────────────────────────────────────────────────────
REDIS_URL            = os.getenv("REDIS_URL", None)
REDIS_TTL_HISTORICAL = int(os.getenv("REDIS_TTL_HISTORICAL", "3600"))
REDIS_TTL_LATEST     = int(os.getenv("REDIS_TTL_LATEST",     "300"))
REDIS_KEY_PREFIX     = os.getenv("REDIS_KEY_PREFIX", "tokemfx")

# ─── General Settings ──────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ─── Slack Alerts ──────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL    = os.getenv("SLACK_WEBHOOK_URL", "")
DRAW_ALERT_THRESHOLD = float(os.getenv("DRAW_ALERT_THRESHOLD", "0.05"))

# ─── Email Alerts ──────────────────────────────────────────────────────────────
SMTP_HOST   = os.getenv("SMTP_HOST", "")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))    # or 465
SMTP_USER   = os.getenv("SMTP_USER", "")
SMTP_PASS   = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

# ─── Position Sizing ───────────────────────────────────────────────────────────
POSITION_SIZING_METHOD    = os.getenv("POSITION_SIZING_METHOD", "fixed").lower()
FIXED_FRACTION            = float(os.getenv("FIXED_FRACTION", "0.01"))
KELLY_WIN_RATE            = float(os.getenv("KELLY_WIN_RATE", "0.5"))
KELLY_PAYOFF_RATIO        = float(os.getenv("KELLY_PAYOFF_RATIO", "1.5"))
KELLY_FRACTION_MULTIPLIER = float(os.getenv("KELLY_FRACTION_MULTIPLIER", "1.0"))
