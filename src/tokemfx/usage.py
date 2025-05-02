from datetime import datetime, timedelta
from tokemfx.config import REDIS_URL
from tokemfx.data import DataHandler
from tokemfx.backtest import BacktestEngine
from tokemfx.strategy import MovingAverageCrossStrategy
from datetime import datetime, timedelta
from tokemfx.data import DataHandler
from tokemfx.backtest import BacktestEngine
from tokemfx.strategy import MovingAverageCrossStrategy
from datetime import datetime, timedelta
from tokemfx.data import DataHandler
from tokemfx.backtest import BacktestEngine
from tokemfx.strategy import MovingAverageCrossStrategy

dh     = DataHandler(cache_dir="cache", sqlite_path="cache/db.sqlite")
engine = BacktestEngine(data_handler=dh, cash=20_000)

# 1) Multi-symbol single backtest
stats = engine.run(
    MovingAverageCrossStrategy,
    {"fast_period":5, "slow_period":20},
    instruments=["EUR_USD", "GBP_USD"],
    granularity="H1",
    start=datetime.utcnow() - timedelta(days=180)
)

# 2) Walk-forward testing (3m train, 1m test, step=1m)
wf = engine.walk_forward(
    MovingAverageCrossStrategy,
    {"fast_period":[5,10], "slow_period":[20,30]},
    instruments="EUR_USD",
    granularity="H1",
    overall_start=datetime(2024,1,1),
    overall_end=datetime(2024,7,1),
    train_window=timedelta(days=90),
    test_window=timedelta(days=30),
    step=timedelta(days=30)
)

# 3) Hyperopt continuous search over integer periods
from hyperopt import hp
space = {
    "fast_period": hp.quniform("fast", 5, 20, 1),
    "slow_period": hp.quniform("slow", 20, 50, 1),
}
best = engine.hyperopt_optimize(
    MovingAverageCrossStrategy,
    param_space=space,
    instruments="EUR_USD",
    granularity="H1",
    start=datetime.utcnow() - timedelta(days=365),
    max_evals=100
)

# Init data & engine
dh = DataHandler(cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
engine = BacktestEngine(data_handler=dh, cash=20_000, commission_perc=0.0001, slippage_perc=0.00005)

# Single backtest
start = datetime.utcnow() - timedelta(days=365)
stats = engine.run(
    MovingAverageCrossStrategy,
    {"fast_period": 5, "slow_period": 20},
    instrument="EUR_USD",
    granularity="H1",
    start=start
)
print(stats)

# Grid-search on MA periods
grid = {"fast_period": [5,10,15], "slow_period": [30,50]}
results = engine.optimize(
    MovingAverageCrossStrategy,
    grid,
    instrument="EUR_USD",
    granularity="H1",
    start=start
)
for r in results:
    print(r["params"], "→", r["sharpe_ratio"])

# Init data & engine
dh = DataHandler(cache_dir="cache", sqlite_path="cache/candles.db", redis_url=REDIS_URL)
engine = BacktestEngine(data_handler=dh, cash=20_000, commission_perc=0.0001, slippage_perc=0.00005)

# Single backtest
start = datetime.utcnow() - timedelta(days=365)
stats = engine.run(
    MovingAverageCrossStrategy,
    {"fast_period": 5, "slow_period": 20},
    instrument="EUR_USD",
    granularity="H1",
    start=start
)
print(stats)

# Grid-search on MA periods
grid = {"fast_period": [5,10,15], "slow_period": [30,50]}
results = engine.optimize(
    MovingAverageCrossStrategy,
    grid,
    instrument="EUR_USD",
    granularity="H1",
    start=start
)
for r in results:
    print(r["params"], "→", r["sharpe_ratio"])
