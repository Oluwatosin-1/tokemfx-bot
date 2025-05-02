# src/tokemfx/backtest.py

import backtrader as bt
from datetime import datetime, timedelta
from itertools import product
from multiprocessing import Pool, cpu_count
from typing import Type, Dict, Any, List, Union, Tuple

from hyperopt import fmin, tpe, hp, Trials, STATUS_OK

from tokemfx.data import DataHandler
from tokemfx.strategy import BaseStrategy
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def _optimize_worker(args):
    """
    Top-level worker for parallel optimize.
    Rebuilds its own DataHandler & Engine to avoid pickling issues.
    """
    (strat_cls, strat_kwargs,
     instruments, granularity, start, end,
     dh_conf, eng_conf) = args

    dh = DataHandler(**dh_conf)
    engine = BacktestEngine(data_handler=dh, **eng_conf)
    res = engine.run(strat_cls, strat_kwargs, instruments, granularity, start, end)
    res["params"] = strat_kwargs
    return res


class BacktestEngine:
    """
    Backtest engine with:
      • multi‐symbol support
      • commission/slippage
      • analyzers (Sharpe, DrawDown, Trades)
      • parallel grid‐search optimize
      • parallel walk‐forward
      • Hyperopt tuning
    """

    def __init__(
        self,
        data_handler: DataHandler,
        cash: float = 10_000.0,
        commission_perc: float = 0.0002,
        slippage_perc: float = 0.0001,
    ):
        self.dh   = data_handler
        self.cash = cash
        self.comm = commission_perc
        self.slip = slippage_perc

    def _prepare_cerebro(
        self,
        strat_cls: Type[BaseStrategy],
        strat_kwargs: Dict[str, Any],
    ) -> bt.Cerebro:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.cash)
        cerebro.broker.setcommission(commission=self.comm)
        cerebro.broker.set_slippage_perc(self.slip)
        cerebro.addstrategy(strat_cls, **strat_kwargs)

        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe",
                            timeframe=bt.TimeFrame.Days, annualize=True)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        return cerebro

    def run(
        self,
        strat_cls: Type[BaseStrategy],
        strat_kwargs: Dict[str, Any],
        instruments: Union[str, List[str]],
        granularity: str,
        start: datetime,
        end: datetime = None
    ) -> Dict[str, Any]:
        if isinstance(instruments, str):
            instruments = [instruments]

        cerebro = self._prepare_cerebro(strat_cls, strat_kwargs)

        # 1) add each data feed
        for inst in instruments:
            df = self.dh.get_historical(inst, granularity, start, end)
            feed = bt.feeds.PandasData(dataname=df, name=inst)
            cerebro.adddata(feed)

        # 2) run
        results = cerebro.run()
        strat   = results[0]

        # 3) collect stats
        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio")
        dd     = strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]
        trades = strat.analyzers.trades.get_analysis()
        total  = trades["total"]["total"]
        won    = trades["won"]["total"]
        lost   = trades["lost"]["total"]

        return {
            "start_cash":   self.cash,
            "final_value":  cerebro.broker.getvalue(),
            "net_profit":   cerebro.broker.getvalue() - self.cash,
            "sharpe_ratio": sharpe,
            "max_drawdown": dd,
            "total_trades": total,
            "win_rate":     (won/total if total>0 else None),
            "won_trades":   won,
            "lost_trades":  lost,
        }

    def optimize(
        self,
        strat_cls: Type[BaseStrategy],
        param_grid: Dict[str, List[Any]],
        instruments: Union[str, List[str]],
        granularity: str,
        start: datetime,
        end: datetime = None,
        num_workers: int = 1,
        save_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Grid‐search. If num_workers>1, uses a process pool.
        Optionally saves results to CSV/JSON.
        """
        # build all combinations
        keys   = list(param_grid.keys())
        combos = [dict(zip(keys, vals)) for vals in product(*(param_grid[k] for k in keys))]

        # prepare configs for workers
        dh_conf = dict(
            cache_dir=self.dh.cache_dir,
            sqlite_path=getattr(self.dh, "sqlite_path", None),
            redis_url=getattr(self.dh, "redis").connection_pool.connection_kwargs.get("url", None) if getattr(self.dh, "redis", None) else None,
            redis_ttl_historical=getattr(self.dh, "redis_ttl_historical", None),
            redis_ttl_latest=getattr(self.dh, "redis_ttl_latest", None),
            redis_key_prefix=getattr(self.dh, "redis_key_prefix", None),
            retries=self.dh.retries,
            backoff=self.dh.backoff
        )
        eng_conf = dict(
            cash=self.cash,
            commission_perc=self.comm,
            slippage_perc=self.slip
        )

        if num_workers and num_workers > 1:
            logger.info(f"Parallel optimize with {num_workers} workers over {len(combos)} combos")
            args_list = [
                (strat_cls, combo, instruments, granularity, start, end, dh_conf, eng_conf)
                for combo in combos
            ]
            with Pool(processes=num_workers) as pool:
                results = pool.map(_optimize_worker, args_list)
        else:
            results = []
            for combo in combos:
                res = self.run(strat_cls, combo, instruments, granularity, start, end)
                res["params"] = combo
                results.append(res)

        if save_path:
            df = pd.DataFrame(results)
            if save_path.lower().endswith(".json"):
                df.to_json(save_path, orient="records", date_format="iso")
            else:
                df.to_csv(save_path, index=False)
            logger.info(f"Saved optimization results to {save_path}")

        return results

    def walk_forward(
        self,
        strat_cls: Type[BaseStrategy],
        param_grid: Dict[str, List[Any]],
        instruments: Union[str, List[str]],
        granularity: str,
        overall_start: datetime,
        overall_end: datetime,
        train_window: timedelta,
        test_window: timedelta,
        step: timedelta = None,
        num_workers: int = 1,
        save_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Walk-forward testing: for each rolling train/test slice:
          1) optimize (parallelizable via num_workers)
          2) pick best Sharpe
          3) test out-of-sample
        Saves results if save_path given.
        """
        step = step or test_window
        slices: List[Tuple[datetime,datetime,datetime,datetime]] = []
        cursor = overall_start
        while cursor + train_window + test_window <= overall_end:
            ts, te = cursor, cursor + train_window
            test_start, test_end = te, te + test_window
            slices.append((ts, te, test_start, test_end))
            cursor += step

        results = []
        for train_start, train_end, test_start, test_end in slices:
            train_res = self.optimize(
                strat_cls, param_grid, instruments, granularity,
                train_start, train_end, num_workers=num_workers
            )
            # select best Sharpe
            best = max(train_res, key=lambda r: r["sharpe_ratio"] or -999)
            test_stats = self.run(
                strat_cls, best["params"], instruments, granularity,
                test_start, test_end
            )
            results.append({
                "train_period":   (train_start.isoformat(), train_end.isoformat()),
                "test_period":    (test_start.isoformat(), test_end.isoformat()),
                "chosen_params":  best["params"],
                **{f"test_{k}": v for k, v in test_stats.items()}
            })

        if save_path:
            df = pd.DataFrame(results)
            if save_path.lower().endswith(".json"):
                df.to_json(save_path, orient="records", date_format="iso")
            else:
                df.to_csv(save_path, index=False)
            logger.info(f"Saved walk-forward results to {save_path}")

        return results

    def hyperopt_optimize(
        self,
        strat_cls: Type[BaseStrategy],
        param_space: Dict[str, Any],
        instruments: Union[str, List[str]],
        granularity: str,
        start: datetime,
        end: datetime = None,
        max_evals: int = 50
    ) -> Dict[str, Any]:
        """
        Hyperopt continuous search (sequential).
        """
        def objective(params):
            stats = self.run(strat_cls, params, instruments, granularity, start, end)
            loss = - (stats.get("sharpe_ratio") or 0)
            return {"loss": loss, "status": STATUS_OK, "params": params}

        trials = Trials()
        best = fmin(
            fn=objective,
            space=param_space,
            algo=tpe.suggest,
            max_evals=max_evals,
            trials=trials
        )
        best_trial = sorted(trials.results, key=lambda r: r["loss"])[0]
        return {"best_params": best_trial["params"], **best_trial}
