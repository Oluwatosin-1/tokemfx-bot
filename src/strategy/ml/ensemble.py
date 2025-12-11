"""
Machine Learning Ensemble Strategies
====================================
ML-based trading strategies using ensemble methods.

This module contains:
- MLForestStrategy (Random Forest)
"""

import backtrader as bt
from sklearn.ensemble import RandomForestClassifier
from ..base.base_strategy import BaseStrategy


class MLForestStrategy(BaseStrategy):
    """
    Machine Learning Strategy using Random Forest.

    Uses technical indicators as features to predict price direction.
    Can adapt to market conditions through continuous learning.

    WARNING: ML strategies can overfit and require extensive backtesting.
    This implementation is for educational purposes.

    Parameters:
        lookback (int): Training window size (default: 30)
        forecast (int): Prediction horizon (default: 5)
        min_samples (int): Minimum samples for training (default: 50)
        threshold (float): Confidence threshold for signals (default: 0.6)
        size (int): Position size (default: 1000)
        instrument (str): Trading instrument symbol (optional)
    """

    params = (
        ("lookback", 30),
        ("forecast", 5),
        ("min_samples", 50),
        ("threshold", 0.6),
        ("size", 1000),
    )

    def __init__(self):
        """Initialize ML strategy with technical indicators."""
        super().__init__()

        # Technical indicators as ML features
        self.sma_short = bt.indicators.SMA(self.data.close, period=10)
        self.sma_long = bt.indicators.SMA(self.data.close, period=20)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        self.atr = bt.indicators.ATR(self.data, period=14)
        self.macd = bt.indicators.MACD(self.data.close)

        # ML model initialization
        self.model = None
        self.history = []
        self.predictions = []

        # Note: Model training happens in _train_model()
        pass

        self.logger.warning("🤖 ML Strategy: Requires extensive testing - may overfit!")
        self.logger.info("ML Forest initialized: lookback=%d, forecast=%d",
                        self.p.lookback, self.p.forecast)

    def _extract_features(self):
        """Extract technical indicators as ML features."""
        try:
            features = [
                float(self.sma_short[0]),
                float(self.sma_long[0]),
                float(self.rsi[0]),
                float(self.atr[0]),
                float(self.macd.macd[0]),
                float(self.macd.signal[0]),
                # Price momentum (avoid division by zero)
                (float(self.data.close[0]) - float(self.data.close[-1])) / max(float(self.data.close[-1]), 0.0001),
            ]
            return features
        except (IndexError, ZeroDivisionError):
            # Return zeros if indicators not ready
            return [0.0] * 7

    def _train_model(self):
        """Train Random Forest model on historical data."""
        if len(self.history) < self.p.min_samples:
            return

        try:
            # Prepare training data
            X = [row['features'] for row in self.history if len(row['features']) == 7]
            y = [1 if row['future_return'] > 0 else 0 for row in self.history
                 if len(row['features']) == 7]

            if len(X) < self.p.min_samples:
                return

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                min_samples_split=10
            )
            self.model.fit(X, y)

            self.logger.info("✅ ML Model trained on %d samples", len(X))

        except Exception as e:
            self.logger.error("❌ ML training failed: %s", str(e))

    def next(self):
        """Execute ML-based trading logic."""
        try:
            # Extract current features
            features = self._extract_features()

            # Update history for training
            if len(self.history) < self.p.lookback:
                # Build initial training set
                future_return = 0
                if len(self.data) > self.p.forecast:
                    current_price = float(self.data.close[0])
                    future_price = float(self.data.close[self.p.forecast])
                    future_return = future_price - current_price

                self.history.append({
                    'features': features,
                    'future_return': future_return
                })
                return

            # Train model if not trained
            if self.model is None:
                self._train_model()
                if self.model is None:
                    return  # Still not enough data

            # Make prediction
            confidence_scores = self.model.predict_proba([features])[0]
            prediction = self.model.predict([features])[0]

            confidence = float(confidence_scores[prediction])

            # Generate trading signal based on confidence
            if not self.position:
                if prediction == 1 and confidence > self.p.threshold:
                    # Bullish prediction with high confidence
                    self.buy(size=self.p.size)
                    self.logger.info("🎯 BUY signal: ML confidence=%.3f", confidence)

                elif prediction == 0 and confidence > self.p.threshold:
                    # Bearish prediction with high confidence
                    self.sell(size=self.p.size)
                    self.logger.info("🎯 SELL signal: ML confidence=%.3f", confidence)

            else:
                # Exit on opposite predictions with sufficient confidence
                if self.position.size > 0 and prediction == 0 and confidence > self.p.threshold:
                    self.close()
                    self.logger.info("🎯 EXIT LONG: ML reversed, confidence=%.3f", confidence)

                elif self.position.size < 0 and prediction == 1 and confidence > self.p.threshold:
                    self.close()
                    self.logger.info("🎯 EXIT SHORT: ML reversed, confidence=%.3f", confidence)

            # Update training data (sliding window)
            future_return = 0
            if len(self.data) > self.p.forecast:
                current_price = float(self.data.close[0])
                future_price = float(self.data.close[self.p.forecast])
                future_return = future_price - current_price

            self.history.append({
                'features': features,
                'future_return': future_return
            })

            if len(self.history) > self.p.lookback:
                self.history.pop(0)

        except Exception as e:
            self.logger.error("❌ ML strategy error: %s", str(e))

    def notify_order(self, order):
        """Handle order status updates."""
        super().notify_order(order)

    def notify_trade(self, trade):
        """Handle trade completion."""
        super().notify_trade(trade)
