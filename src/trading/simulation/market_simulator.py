"""
Market Simulator Class
=======================

Provides realistic market simulation capabilities for testing trading strategies.
Simulates market conditions, volatility, and price movements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketSimulator:
    """
    Realistic market simulation engine for trading strategy testing.

    Simulates various market conditions including:
    - Price movements (trends, reversals, volatility)
    - Volume patterns
    - Market microstructure effects
    - Holiday/weekend gaps
    - News event impacts
    """

    def __init__(self, start_price: float = 100.0,
                 volatility: float = 0.02,
                 drift: float = 0.0001,
                 trading_days: int = 252,
                 trading_hours: Tuple[int, int] = (9, 16)):
        """
        Initialize market simulator

        Args:
            start_price: Starting price for simulation
            volatility: Daily volatility (annualized)
            drift: Daily drift (annualized)
            trading_days: Number of trading days per year
            trading_hours: Trading hours as (start_hour, end_hour)
        """
        self.start_price = start_price
        self.volatility = volatility
        self.drift = drift
        self.trading_days = trading_days
        self.trading_hours = trading_hours

        # Simulation parameters
        self.current_price = start_price
        self.current_time = None

        # Market state
        self.is_open = False
        self.market_regime = 'NORMAL'  # NORMAL, HIGH_VOL, LOW_VOL, TREND_UP, TREND_DOWN

        # Historical data storage
        self.price_history = []
        self.volume_history = []
        self.time_stamps = []

        logger.info(f"✅ MarketSimulator initialized: Start Price ${start_price}, Volatility {volatility:.2%}")

    def simulate_market_period(self, days: int = 30,
                              num_bars_per_day: int = 390,
                              include_weekends: bool = False,
                              market_events: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        Simulate market data for a specified period

        Args:
            days: Number of days to simulate
            num_bars_per_day: Number of price bars per trading day
            include_weekends: Whether to include weekend data
            market_events: List of market events to simulate

        Returns:
            DataFrame with OHLCV price data
        """
        if market_events is None:
            market_events = []

        logger.info(f"🏭 Starting market simulation for {days} days")
        logger.info(f"📊 {num_bars_per_day} bars per day, volatility: {self.volatility:.2%}")

        try:
            # Reset simulation state
            self._reset_simulation()

            # Generate datetime index
            dates = self._generate_trading_dates(days, include_weekends)
            time_index = self._generate_intraday_times(dates, num_bars_per_day)

            # Simulate price movements
            price_data = []
            current_price = self.start_price

            for i, timestamp in enumerate(time_index):
                # Check for market hours
                is_market_open = self._is_market_open(timestamp)

                # Apply market events if any
                event_impact = self._apply_market_events(timestamp, market_events)

                # Generate next price bar
                ohlc = self._generate_price_bar(current_price, is_market_open, event_impact)

                # Create data row
                row = {
                    'timestamp': timestamp,
                    'open': ohlc['open'],
                    'high': ohlc['high'],
                    'low': ohlc['low'],
                    'close': ohlc['close'],
                    'volume': ohlc['volume'],
                    'market_open': is_market_open,
                    'market_regime': self.market_regime
                }

                price_data.append(row)
                current_price = ohlc['close']

                self.current_price = current_price
                self.current_time = timestamp

            # Convert to DataFrame
            df = pd.DataFrame(price_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Add technical indicators
            df = self._add_technical_indicators(df)

            logger.info(f"✅ Simulation completed: {len(df)} price bars generated")
            logger.info(f"🏁 Final price: ${current_price:.2f} ({((current_price/self.start_price)-1)*100:.1f}% change)")

            return df

        except Exception as e:
            logger.error(f"❌ Market simulation failed: {e}")
            return pd.DataFrame()

    def simulate_with_strategy(self, strategy_function,
                              days: int = 30,
                              initial_balance: float = 10000.0) -> Dict[str, Any]:
        """
        Simulate market with a trading strategy applied

        Args:
            strategy_function: Trading strategy function
            days: Number of days to simulate
            initial_balance: Starting portfolio balance

        Returns:
            Simulation results with strategy performance
        """
        logger.info("🎯 Running strategy simulation")

        try:
            # Generate market data
            market_data = self.simulate_market_period(days)

            if market_data.empty:
                return {'error': 'Failed to generate market data'}

            # Generate trading signals
            signals = self._generate_strategy_signals(strategy_function, market_data)

            # Simulate execution
            portfolio_history = self._simulate_portfolio(signals, market_data, initial_balance)

            # Calculate strategy performance
            performance = self._calculate_strategy_performance(portfolio_history, market_data)

            results = {
                'market_data': market_data,
                'signals': signals,
                'portfolio_history': portfolio_history,
                'performance': performance,
                'simulation_params': {
                    'days': days,
                    'initial_balance': initial_balance,
                    'volatility': self.volatility,
                    'drift': self.drift
                }
            }

            logger.info("✅ Strategy simulation completed")
            return results

        except Exception as e:
            logger.error(f"❌ Strategy simulation failed: {e}")
            return {'error': str(e)}

    def _generate_price_bar(self, prev_close: float,
                           market_open: bool,
                           event_impact: float = 0.0) -> Dict[str, float]:
        """
        Generate a single OHLC price bar

        Args:
            prev_close: Previous closing price
            market_open: Whether market is open
            event_impact: External event impact on price

        Returns:
            OHLCV price bar
        """
        # Base price movement parameters
        daily_vol = self.volatility / np.sqrt(self.trading_days)  # Convert to daily
        daily_drift = self.drift / self.trading_days

        # Adjust for market regime
        regime_multiplier = self._get_regime_multiplier()

        # Add randomness and event impact
        base_return = np.random.normal(daily_drift, daily_vol * regime_multiplier)
        total_return = base_return + event_impact

        # Generate OHLC from return
        if market_open:
            # Realistic OHLC generation
            close = prev_close * (1 + total_return)
            volatility_factor = abs(total_return) * 2 + daily_vol * regime_multiplier

            # High/low based on close movement
            if total_return >= 0:
                high = close * (1 + abs(np.random.normal(0, volatility_factor/2)))
                low = prev_close * (1 - abs(np.random.normal(0, volatility_factor/4)))
            else:
                high = prev_close * (1 + abs(np.random.normal(0, volatility_factor/4)))
                low = close * (1 - abs(np.random.normal(0, volatility_factor/2)))

            # Ensure OHLC relationships
            open_price = prev_close
            high = max(high, max(open_price, close))
            low = min(low, min(open_price, close))
        else:
            # Market closed - gap
            close = high = low = open_price = prev_close * (1 + total_return)

        # Generate volume
        volume = self._generate_volume(open_price, close)

        return {
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }

    def _get_regime_multiplier(self) -> float:
        """Get volatility multiplier based on current market regime"""
        regime_multipliers = {
            'NORMAL': 1.0,
            'HIGH_VOL': 2.5,
            'LOW_VOL': 0.5,
            'TREND_UP': 1.2,
            'TREND_DOWN': 1.3
        }

        # Randomly change regime (small probability)
        if np.random.random() < 0.02:  # 2% chance per bar
            self.market_regime = np.random.choice(list(regime_multipliers.keys()))

        return regime_multipliers.get(self.market_regime, 1.0)

    def _generate_volume(self, open_price: float, close_price: float) -> int:
        """Generate realistic volume based on price movement"""
        # Base volume
        base_volume = np.random.lognormal(10, 1)  # Mean around 22,000 shares

        # Volatility multiplier
        price_range = abs(close_price - open_price) / open_price
        volatility_multiplier = 1 + price_range * 10

        # Trend days have higher volume
        if self.market_regime in ['TREND_UP', 'TREND_DOWN']:
            volatility_multiplier *= 1.5

        return int(base_volume * volatility_multiplier)

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add common technical indicators to the price data"""
        try:
            # Simple Moving Averages
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            df['MACD'] = ema_12 - ema_26
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_hist'] = df['MACD'] - df['MACD_signal']

            # Bollinger Bands
            sma_20 = df['close'].rolling(window=20).mean()
            std_20 = df['close'].rolling(window=20).std()
            df['BB_upper'] = sma_20 + (std_20 * 2)
            df['BB_lower'] = sma_20 - (std_20 * 2)
            df['BB_middle'] = sma_20

        except Exception as e:
            logger.warning(f"Failed to add technical indicators: {e}")

        return df

    def _generate_trading_dates(self, days: int, include_weekends: bool) -> List[datetime]:
        """Generate list of trading dates"""
        dates = []
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        while len(dates) < days:
            if not include_weekends:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday-Friday
                    dates.append(current_date)
            else:
                dates.append(current_date)
            current_date += timedelta(days=1)

        return dates

    def _generate_intraday_times(self, dates: List[datetime], bars_per_day: int) -> List[datetime]:
        """Generate intraday timestamps for price bars"""
        timestamps = []

        for date in dates:
            # Generate timestamps within trading hours
            start_time = date.replace(hour=self.trading_hours[0], minute=0)
            end_time = date.replace(hour=self.trading_hours[1], minute=0)

            # Divide trading day into bars
            time_per_bar = (end_time - start_time) / bars_per_day

            for i in range(bars_per_day):
                bar_time = start_time + (time_per_bar * i)
                timestamps.append(bar_time)

        return timestamps

    def _is_market_open(self, timestamp: datetime) -> bool:
        """Check if market is open at given timestamp"""
        hour = timestamp.hour
        return self.trading_hours[0] <= hour < self.trading_hours[1]

    def _apply_market_events(self, timestamp: datetime,
                           events: List[Dict[str, Any]]) -> float:
        """Apply market events to price movement"""
        for event in events:
            event_time = pd.to_datetime(event.get('timestamp', ''))
            if abs((timestamp - event_time).total_seconds()) < 300:  # Within 5 minutes
                return event.get('impact', 0.0)

        return 0.0

    def _reset_simulation(self):
        """Reset simulation state"""
        self.current_price = self.start_price
        self.current_time = None
        self.market_regime = 'NORMAL'
        self.price_history = []
        self.volume_history = []
        self.time_stamps = []

    def _generate_strategy_signals(self, strategy_function, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate trading signals using strategy function"""
        try:
            return strategy_function(market_data, {})
        except Exception as e:
            logger.error(f"Strategy signal generation failed: {e}")
            return []

    def _simulate_portfolio(self, signals: List[Dict[str, Any]],
                           market_data: pd.DataFrame,
                           initial_balance: float) -> List[Dict[str, Any]]:
        """Simulate portfolio changes based on strategy signals"""
        balance = initial_balance
        positions = {}
        portfolio_history = []

        # Simplified portfolio simulation
        for signal in signals:
            try:
                timestamp = signal.get('timestamp')
                current_price = market_data.loc[timestamp, 'close'] if timestamp in market_data.index else self.current_price

                # Apply simple buy/sell logic
                if signal.get('action') == 'BUY' and balance > current_price:
                    shares = int(balance * 0.1 / current_price)  # Use 10% of balance
                    if shares > 0:
                        cost = shares * current_price
                        balance -= cost
                        positions[timestamp] = positions.get(timestamp, 0) + shares

                portfolio_history.append({
                    'timestamp': timestamp,
                    'balance': balance,
                    'positions': positions.copy(),
                    'total_value': balance + sum(positions.values()) * current_price if positions else balance
                })

            except Exception as e:
                logger.warning(f"Portfolio simulation error: {e}")
                continue

        return portfolio_history

    def _calculate_strategy_performance(self, portfolio_history: List[Dict[str, Any]],
                                       market_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate strategy performance metrics"""
        if not portfolio_history:
            return {'error': 'No portfolio history'}

        try:
            initial_value = portfolio_history[0]['total_value']
            final_value = portfolio_history[-1]['total_value']
            total_return = (final_value - initial_value) / initial_value

            # Compare to buy-and-hold
            market_return = (market_data['close'].iloc[-1] - market_data['close'].iloc[0]) / market_data['close'].iloc[0]

            return {
                'total_return': total_return,
                'market_return': market_return,
                'alpha': total_return - market_return,
                'final_balance': final_value
            }

        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            return {'error': str(e)}

    def get_market_summary(self) -> Dict[str, Any]:
        """Get summary of simulated market conditions"""
        return {
            'current_price': self.current_price,
            'volatility': self.volatility,
            'drift': self.drift,
            'market_regime': self.market_regime,
            'trading_days': self.trading_days,
            'total_bars_simulated': len(self.price_history)
        }
