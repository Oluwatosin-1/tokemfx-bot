# src/tokemfx/executor.py

import time
import logging
import smtplib
import ssl
import requests

from email.mime.text import MIMEText
from datetime import datetime, timedelta
from threading import Event, Thread
from typing import Type, Dict, Any

import backtrader as bt

from tokemfx.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL,
    POSITION_SIZING_METHOD, FIXED_FRACTION,
    KELLY_WIN_RATE, KELLY_PAYOFF_RATIO, KELLY_FRACTION_MULTIPLIER,
    SLACK_WEBHOOK_URL, DRAW_ALERT_THRESHOLD
)
from tokemfx.data     import DataHandler
from tokemfx.broker   import Broker
from tokemfx.strategy import BaseStrategy
from tokemfx.analysis import compute_returns, equity_curve, drawdown_series

logger = logging.getLogger(__name__)

# ─── Optional Prometheus instrumentation ─────────────────────────────────────
try:
    from prometheus_client import Counter, Gauge, start_http_server
    start_http_server(8000)
    PROM_TRADES   = Counter("exec_trades_total", "Number of trades executed")
    PROM_EQUITY   = Gauge  ("exec_equity",       "Current account equity")
    PROM_DRAWDOWN = Gauge  ("exec_drawdown",     "Current drawdown")
except ImportError:
    logger.warning("prometheus_client not installed; executor metrics disabled")
    class _NoOp:
        def inc(self): pass
        def set(self, v): pass
    PROM_TRADES = PROM_EQUITY = PROM_DRAWDOWN = _NoOp()


class Executor:
    """
    Live/paper trading loop with:
      • email + Slack alerts
      • drawdown threshold notifications
      • position sizing (fixed or Kelly)
      • optional Prometheus metrics
    """
    def __init__(
        self,
        broker: Broker,
        data_handler: DataHandler,
        strategy_cls: Type[BaseStrategy],
        strategy_params: Dict[str, Any],
        instrument: str,
        granularity: str,
        cash: float = 10_000,
        poll_interval: float = 60.0,
        paper: bool = True
    ):
        self.broker          = broker
        self.dh              = data_handler
        self.strategy_cls    = strategy_cls
        self.strategy_params = strategy_params.copy()
        self.instrument      = instrument
        self.granularity     = granularity
        self.cash            = cash
        self.poll_interval   = poll_interval
        self.paper           = paper

        self._cerebro    = None
        self._strategy   = None
        self._stop_event = Event()

    def _send_email(self, subject: str, body: str):
        """Send an alert email."""
        if not SMTP_HOST or not ALERT_EMAIL:
            return
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = ALERT_EMAIL

        try:
            ctx = ssl.create_default_context()
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as srv:
                    srv.login(SMTP_USER, SMTP_PASS)
                    srv.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
                    srv.starttls(context=ctx)
                    srv.login(SMTP_USER, SMTP_PASS)
                    srv.send_message(msg)
            logger.info("Email alert sent: %s", subject)
        except Exception as e:
            logger.error("Failed to send email alert: %s", e)

    def _send_slack(self, text: str):
        """Post a message to Slack via webhook."""
        if not SLACK_WEBHOOK_URL:
            return
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=5)
            logger.info("Slack alert sent.")
        except Exception as e:
            logger.error("Failed to send Slack alert: %s", e)

    def _compute_position_size(self, last_price: float) -> int:
        """Compute position size by fixed or Kelly fraction."""
        equity = self._cerebro.broker.getvalue() if self._cerebro else self.cash
        method = POSITION_SIZING_METHOD.lower()

        if method == "kelly":
            p      = KELLY_WIN_RATE
            q      = 1 - p
            b      = KELLY_PAYOFF_RATIO
            f_star = p - q / b
            f_use  = max(0.0, f_star * KELLY_FRACTION_MULTIPLIER)
        else:
            f_use = FIXED_FRACTION

        risk_amount = equity * f_use
        size = int(risk_amount / last_price)
        logger.info("Sizing [%s]: equity=%.2f price=%.4f f=%.4f → size=%d",
                    method, equity, last_price, f_use, size)
        return max(1, size)

    def _lookback_timedelta(self) -> timedelta:
        """Return ~100 bars lookback based on granularity."""
        unit = self.granularity[-1].upper()
        val  = int(self.granularity[:-1])
        mapping = {"M": "minutes", "H": "hours", "D": "days"}
        return timedelta(**{mapping[unit]: val * 100})

    def _initialize(self):
        """Seed strategy with historical bars and apply sizing."""
        df = self.dh.get_historical(
            self.instrument, self.granularity,
            start=datetime.utcnow() - self._lookback_timedelta(),
            end=datetime.utcnow()
        )
        if df.empty:
            raise RuntimeError("No historical data for initialization")

        last_price = df["close"].iloc[-1]
        if "size" in self.strategy_params:
            self.strategy_params["size"] = self._compute_position_size(last_price)

        self._cerebro = bt.Cerebro()
        self._cerebro.broker.setcash(self.cash)
        self._cerebro.broker.setcommission(commission=0.0002)
        self._cerebro.broker.set_slippage_perc(0.0001)
        self._cerebro.addstrategy(self.strategy_cls, **self.strategy_params)
        self._cerebro.adddata(bt.feeds.PandasData(dataname=df))
        self._strategy = self._cerebro.run()[0]
        logger.info("Executor initialized; strategy primed.")

    def start(self):
        """Start live trading loop in background."""
        try:
            self._initialize()
        except Exception as e:
            logger.error("Init failed: %s", e, exc_info=True)
            self._send_email("Executor Init Error", str(e))
            self._send_slack(f":warning: Init error: {e}")
            return

        Thread(target=self._loop, daemon=True).start()
        msg = f"{self.strategy_cls.__name__} on {self.instrument} started ({'paper' if self.paper else 'live'})"
        logger.info(msg)
        self._send_email("Executor Started", msg)
        self._send_slack(f":rocket: {msg}")

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                # Fetch latest bar
                df = self.dh.get_latest(self.instrument, self.granularity, count=1)
                bar = df.iloc[-1]

                # Feed into strategy
                dat = self._strategy.data
                dat.open[0], dat.high[0], dat.low[0], dat.close[0], dat.volume[0] = (
                    bar.open, bar.high, bar.low, bar.close, bar.volume
                )
                self._strategy.next()

                # Update equity metric
                equity_val = self._cerebro.broker.getvalue()
                PROM_EQUITY.set(equity_val)

                # Handle completed orders
                for order in list(self._strategy.broker.orders):
                    if order.status == order.Completed:
                        action = "BUY" if order.size > 0 else "SELL"
                        price  = order.executed.price
                        size   = abs(order.size)
                        text   = f"{action} {size}@{price:.5f} on {self.instrument}"
                        logger.info(text)
                        PROM_TRADES.inc()
                        self._send_email("Trade Executed", text)
                        self._send_slack(f":money_with_wings: {text}")

                # Drawdown alert
                hist = self.dh.get_historical(
                    self.instrument, self.granularity,
                    start=datetime.utcnow() - timedelta(days=1),
                    end=datetime.utcnow()
                )
                eq   = equity_curve(compute_returns(hist["close"].pct_change().fillna(0)), initial_capital=self.cash)
                draw = drawdown_series(eq).min()
                PROM_DRAWDOWN.set(draw)
                if draw <= -DRAW_ALERT_THRESHOLD:
                    alert = f"Drawdown alert: {draw:.2%} on {self.instrument}"
                    logger.warning(alert)
                    self._send_email("Drawdown Threshold Breached", alert)
                    self._send_slack(f":rotating_light: {alert}")

                time.sleep(self.poll_interval)

            except Exception as e:
                logger.error("Loop error: %s", e, exc_info=True)
                self._send_email("Executor Loop Error", str(e))
                self._send_slack(f":x: Loop error: {e}")
                time.sleep(5)

    def stop(self):
        """Stop the trading loop and send notifications."""
        self._stop_event.set()
        msg = f"{self.strategy_cls.__name__} on {self.instrument} stopped"
        logger.info(msg)
        self._send_email("Executor Stopped", msg)
        self._send_slack(f":stop_sign: {msg}")
