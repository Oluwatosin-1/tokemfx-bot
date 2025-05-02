to run the project run the command 

#streamlit run app.py
# Paper/demo mode on OANDA (default)
python -m tokemfx.main

# Live mode on FXCM
python -m tokemfx.main --broker fxcm --live

# Customize caches
python -m tokemfx.main --cache-dir=~/tokemfx_cache --sqlite-path=~/tokemfx_cache/db.sqlite

# #run the command below to run project
# # paper trading (default)
# python -m tokemfx.main

# # live trading
# python -m tokemfx.main --live
# TokemFX Bot

A battle-ready Python Forex trading bot with full backtesting, live (paper/demo) execution, real-time monitoring, alerts, and analytics.

---

## 🚀 Features

- **Backtest Engine**  
  • Multi-symbol, multi-timeframe support  
  • Commission & slippage modeling  
  • Walk-forward and Hyperopt tuning  
  • Grid-search from the UI with heatmaps  

- **Live Execution (paper/demo)**  
  • OANDA & FXCM brokers  
  • Flexible position sizing (fixed-fraction, Kelly criterion)  
  • E-mail & Slack alerts on fills, errors, drawdown breaches  
  • Drawdown threshold monitoring  

- **Monitoring Dashboard**  
  • Real-time equity & P&L metrics  
  • Open position details & unrealized P&L  
  • Intraday equity curve  

- **Prometheus Metrics**  
  • Cache hits/misses (Redis, SQLite, CSV)  
  • API call counts  
  • Live equity & drawdown gauges  
  • Trade execution counters  

- **Extensible Analytics**  
  • Equity-curve, drawdown, rolling Sharpe, and more  
  • Utility functions for parameter tuning and result analysis  

- **Containerized**  
  • Dockerfile for the app  
  • `docker-compose.yml` to spin up Redis + the Streamlit app  

- **CI/CD Ready**  
  • Linting with Flake8  
  • Tests with pytest  
  • GitHub Actions pipeline to build & push Docker image  

---

## 📂 Project Structure

tokemfx-bot/
├── README.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app.py ← Streamlit UI (Backtest, Live, Monitor)
└── src/
└── tokemfx/
├── analysis.py ← Performance & plotting helpers
├── backtest.py ← BacktestEngine (grid, walk-forward, Hyperopt)
├── broker.py ← OANDA & FXCM broker interfaces
├── config.py ← Load .env & global settings
├── data.py ← DataHandler with Redis/SQLite/CSV + Prometheus
├── executor.py ← Live execution loop with alerts & sizing
├── strategy.py ← Built-in strategies (MA, RSI, BB, ATR, EMA+RSI)
└── tests/ ← pytest unit & integration tests

makefile
Copy
Edit

---

## 🛠️ Prerequisites

- Python 3.10+  
- Docker & Docker Compose (for containerized setup)  
- Redis (if running locally without Docker)  
- Broker accounts & API tokens (OANDA, FXCM)  
- SMTP credentials (for e-mail alerts)  
- Slack Incoming Webhook URL (optional)  

---

## ⚙️ Configuration

Create a `.env` file at the project root:

```ini
# OANDA
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
OANDA_ENV=practice

# FXCM
FXCM_TOKEN=your_fxcm_token
FXCM_HOST=demo
FXCM_PORT=443

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_HISTORICAL=3600
REDIS_TTL_LATEST=300
REDIS_KEY_PREFIX=tokemfx

# Email alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASS=your_email_password
ALERT_EMAIL=alerts@example.com

# Slack alerts (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXXX/XXXX/XXXX
DRAW_ALERT_THRESHOLD=0.05

# Position sizing
POSITION_SIZING_METHOD=fixed   # "fixed" or "kelly"
FIXED_FRACTION=0.01
KELLY_WIN_RATE=0.5
KELLY_PAYOFF_RATIO=1.5
KELLY_FRACTION_MULTIPLIER=1.0

# General
LOG_LEVEL=INFO
🐳 Containerized Deployment
Build and start with Docker Compose:

bash
Copy
Edit
docker-compose up --build
Redis runs on port 6379

Streamlit app runs on http://localhost:8501

Prometheus metrics exposed on port 8000 (http://localhost:8000/metrics)

💻 Running Locally (without Docker)
Create & activate a virtual environment:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Start a local Redis server:

bash
Copy
Edit
redis-server
Fill in your .env as above.

Launch the Streamlit app:

bash
Copy
Edit
streamlit run app.py
👩‍💻 Using the Streamlit Dashboard
Backtest:

Select one or more FX pairs, timeframe, date range.

Choose a strategy and set its parameters.

(Optionally) enable “Grid Search” to sweep multiple parameter values.

View summary metrics, equity/drawdown curves, and heatmaps.

Live:

Pick a single instrument, timeframe, and strategy.

Click “Start Live” to spin up the Executor in paper/demo mode.

Alerts will be sent via e-mail and Slack on each fill, error, or drawdown breach.

Monitor:

View real-time account equity & P&L.

Inspect your open position (entry, current price, unrealized P&L).

See the intraday equity curve updated bar-by-bar.

📊 Prometheus & Grafana
Metrics endpoint: http://<host>:8000/metrics

Sample Grafana dashboard: track dh_redis_hits, dh_api_calls, exec_equity, exec_drawdown, exec_trades_total.

🧪 Testing
Run unit & integration tests with pytest:

bash
Copy
Edit
pytest tests/ --maxfail=1 -q
🤝 CI/CD
Included .github/workflows/ci.yml to:

Lint with Flake8

Test with pytest (spins up Redis service)

Build & push Docker image on main branch

Set the following GitHub secrets:

DOCKER_USERNAME & DOCKER_PASSWORD

Any env vars needed for tests (e.g. dummy API keys)

🔧 Extending TokemFX
Add strategies in strategy.py — just subclass bt.Strategy.

New brokers: implement the Broker interface in broker.py.

More alerts: extend Executor._send_slack or add new channels (Telegram, SMS).

Advanced analytics: drop in new functions in analysis.py and call them from the UI.

Hyperopt UI: wire up BacktestEngine.hyperopt_optimize to a Streamlit form.

📜 License
MIT License — see LICENSE for details.

Built for reliability, transparency, and ease of extension. Happy trading!
 
