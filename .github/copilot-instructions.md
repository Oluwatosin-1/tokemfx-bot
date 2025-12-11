# TokemFX Bot - Copilot Instructions

## Architecture Overview

TokemFX is a modular Python Forex trading bot using the Backtrader framework. Core modules are in `src/tokemfx/`:
- **strategy.py**: Trading strategies inheriting `bt.Strategy`
- **backtest.py**: BacktestEngine with grid search, walk-forward, and Hyperopt
- **executor.py**: Live trading loop with real-time polling
- **data.py**: Multi-layer caching (Redis → SQLite → CSV → broker API)
- **broker.py**: Abstract broker interfaces (Deriv WebSocket implementation)
- **app.py**: Streamlit UI for configuration and monitoring

## Key Patterns

### Strategy Development
Subclass `BaseStrategy` (which inherits `bt.Strategy`). Define `params` as tuples:

```python
class MyStrategy(BaseStrategy):
    params = (
        ("param_name", default_value),
        # Add more params here
    )

    def __init__(self):
        # Initialize indicators here
        self.my_indicator = bt.indicators.SMA(self.data.close, period=self.p.param_name)

    def next(self):
        # Trading logic here
        if condition:
            self.buy()
        elif condition:
            self.sell()
```

Explicitly set position sizes in strategy params; avoid backtrader's built-in sizers.

### Broker Integration
Implement `broker.py`'s abstract `Broker` class:

```python
class MyBroker(Broker):
    def fetch_candles(self, instrument: str, granularity: str, start=None, end=None, count=None) -> pd.DataFrame:
        # API call to fetch data
        # Return DF with columns: open, high, low, close, volume
        # Indexed by 'time' datetime

    def place_order(self, instrument: str, units: int, **kwargs):
        # Execute order via broker API
```

Define broker configurations in `config.py` using `os.getenv()` for `.env` loading. For Deriv, use:

```python
DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
DERIV_ACCOUNT_ID = os.getenv("DERIV_ACCOUNT_ID")
```

### Data Handling
Use `DataHandler` for all data access. It manages caching layers automatically:

```python
dh = DataHandler(broker=broker, redis_url="redis://localhost:6379")
df = dh.get_historical("EUR_USD", "H1", start=datetime(2023,1,1), end=datetime(2023,1,31))
latest_bars = dh.get_latest("EUR_USD", "M5", count=500)
```

### Live Trading
`Executor` runs strategies in real-time. Initialize with historical priming, then poll for latest bars every `poll_interval` seconds. Handles alerts (email/Telegram) and Prometheus metrics.

### Positioning Sizing
Use Kelly criterion or fixed fraction from `config.py`. Computed dynamically in `Executor._compute_position_size()`.

### Configuration
Load from `.env` using `python-dotenv`. Example Deriv setup:

```ini
DERIV_APP_ID=1089
DERIV_API_TOKEN=your_deriv_api_token
DERIV_ACCOUNT_ID=your_deriv_account_id
```

### Common Commands
- `streamlit run app.py`: Launch UI (backtest on port 8501)
- `python -m tokemfx.main --instrument R_10 --strategy MA`: Paper trading on Deriv demo
- `python -m tokemfx.main --instrument R_10 --strategy MA --live`: Live trading on Deriv
- `pytest src/tests/`: Run tests (requires Redis)

Prefer Backtrader's `bt.indicators.CrossOver()` for signal generation over manual comparison. Use instrument granularity mappings from `FXCMBroker`/`OANDABroker` for API calls.

Focus on `tokemfx/` module structure; all trading logic should integrate with existing broker/data abstractions.
