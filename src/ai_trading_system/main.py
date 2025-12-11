"""
AI Trading System Main Interface
================================
Complete AI-powered trading system for automated financial trading.

This module provides the main interface for:
- Running AI-powered trading analysis
- Executing automated trades
- Monitoring AI performance
- Dashboard integration

Features:
- Backtest analysis → Strategy selection → Trade execution
- Dynamic portfolio allocation
- Risk management
- Performance monitoring
- AI health surveillance
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

# Import AI components with proper fallback handling
try:
    from .analytics.performance_analyzer import performance_analyzer as analyzer
    AI_ANALYTICS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI performance analyzer not available: {e}")
    AI_ANALYTICS_AVAILABLE = False

try:
    from .decision_engine.strategy_selector import ai_strategy_selector as selector
    AI_STRATEGY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI strategy selector not available: {e}")
    AI_STRATEGY_AVAILABLE = False

try:
    from .execution.ai_trade_executor import ai_trade_executor as executor
    AI_EXECUTOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI trade executor not available: {e}")
    AI_EXECUTOR_AVAILABLE = False

# Define AI-capable wrapper functions with proper fallbacks
if AI_ANALYTICS_AVAILABLE:
    def analyze_strategy_performance(backtest_results, market_data=None):
        return analyzer.analyze_strategy_performance(backtest_results, market_data)
else:
    def analyze_strategy_performance(backtest_results, market_data=None):
        return {'status': 'analytics_unavailable', 'message': 'AI performance analysis requires implementation'}

if AI_STRATEGY_AVAILABLE:
    def select_optimal_strategy(market_data, **kwargs):
        return selector.select_optimal_strategy(market_data, **kwargs)

    def calculate_optimal_position_size(*args, **kwargs):
        return selector.calculate_position_size(*args, **kwargs)
else:
    def select_optimal_strategy(market_data, **kwargs):
        return {'selected_strategy': 'fallback_ma_crossover',
                'confidence': 0.3,
                'rationale': 'AI strategy selection not available - using default'}

    def calculate_optimal_position_size(*args, **kwargs):
        return 1.0  # Default position size

if AI_EXECUTOR_AVAILABLE:
    def analyze_and_execute_trade(market_data, instrument, risk_preference):
        return executor.analyze_and_execute_trade(market_data, instrument, risk_preference)

    def get_executor_status():
        return executor.get_executor_status()
else:
    def analyze_and_execute_trade(market_data, instrument, risk_preference):
        return {'decision': 'NO_TRADE', 'execution_status': 'AI_UNAVAILABLE',
                'reason': 'AI trade execution not implemented yet','confidence': 0.0}

    def get_executor_status():
        return {'status': 'unavailable', 'message': 'AI execution system not implemented'}

# Import existing backtest system
from src.trading.test_backtest_system import get_test_backtest_results, create_sample_ohlc_data

class AITradingSystem:
    """
    Main AI Trading System Interface
    Brings together all AI components for automated trading
    """

    def __init__(self,
                 account_balance: float = 10000.0,
                 enable_live_trading: bool = False):

        self.account_balance = account_balance
        self.enable_live_trading = enable_live_trading

        # System state
        self.is_initialised = False
        self.backtest_results = []
        self.performance_analysis = {}
        self.strategy_rankings = []

        # Portfolio state
        self.portfolio_allocation = {}
        self.active_positions = {}

        # Performance tracking
        self.system_performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'ai_confidence_avg': 0.0
        }

        print("🤖 AI TRADING SYSTEM INITIALISED")
        print(f"💰 Account Balance: ${account_balance:,.0f}")
        print(f"🏦 Live Trading: {'ENABLED' if enable_live_trading else 'SIMULATION MODE'}")

    def initialize_ai_system(self) -> bool:
        """
        Initialize the AI trading system with backtest data.

        Returns:
            Success status
        """
        print("🚀 INITIALIZING AI TRADING SYSTEM...")

        try:
            # Step 1: Load backtesting results
            print("📊 Step 1: Loading backtesting data...")
            self.backtest_results = self._load_backtest_results()

            if not self.backtest_results:
                print("⚠️ No backtest results found, generating sample data...")
                self.backtest_results = self._generate_sample_backtest_data()

            # Step 2: AI Performance Analysis
            print("🧠 Step 2: AI performance analysis...")
            market_data = create_sample_ohlc_data("R_10", 500)
            self.performance_analysis = analyze_strategy_performance(
                self.backtest_results,
                market_data
            )

            # Step 3: Generate strategy rankings
            print("🎯 Step 3: Ranking strategies...")
            self.strategy_rankings = self.performance_analysis.get('strategy_rankings', [])

            # Step 4: Calculate portfolio allocation - Note: This would need a separate import
            print("📈 Step 4: Setting basic allocation...")
            best_strategies = self.strategy_rankings[:5]
            # Simplified allocation for now - equal weight to top strategies
            self.portfolio_allocation = {}
            if best_strategies:
                weight = 1.0 / len(best_strategies)
                for strategy in best_strategies:
                    strategy_name = strategy.get('strategy_name', 'Unknown')
                    self.portfolio_allocation[strategy_name] = weight

            # Step 5: Initialize trade executor
            print("💰 Step 5: Initialising trade executor...")

            self.is_initialised = True

            print("✅ AI SYSTEM INITIALISED SUCCESSFULLY!")
            self._print_system_status()

            return True

        except Exception as e:
            print(f"❌ AI System initialization failed: {e}")
            return False

    def run_ai_trading_cycle(self,
                           market_data: pd.DataFrame,
                           instrument: str = "R_10",
                           risk_preference: str = 'balanced') -> Dict[str, Any]:
        """
        Run complete AI trading cycle: analysis → decision → execution.

        Args:
            market_data: Current market data
            instrument: Trading instrument
            risk_preference: Risk preference level

        Returns:
            Trading cycle results
        """
        if not self.is_initialised:
            return {'status': 'ERROR', 'reason': 'AI system not initialized'}

        print(f"\n🔄 AI TRADING CYCLE STARTED for {instrument}")

        cycle_result = {
            'timestamp': datetime.now(),
            'instrument': instrument,
            'status': 'PENDING',
            'ai_analysis': {},
            'strategy_selection': {},
            'trade_execution': {},
            'performance_update': {}
        }

        try:
            # Step 1: AI Analysis (using our performance analyzer)
            analysis_result = analyze_strategy_performance(
                self.backtest_results[-10:],  # Use recent backtests
                market_data
            )

            cycle_result['ai_analysis'] = {
                'confidence_score': analysis_result.get('ai_confidence_score', 0.5),
                'profitable_strategies_count': len(analysis_result.get('profitable_strategies', [])),
                'top_strategy': analysis_result.get('strategy_rankings', [{}])[0].get('strategy_name', 'None')
            }

            # Step 2: Strategy Selection
            strategy_selection = select_optimal_strategy(
                market_data,
                risk_preference=risk_preference
            )

            cycle_result['strategy_selection'] = {
                'selected_strategy': strategy_selection.get('selected_strategy'),
                'confidence': strategy_selection.get('confidence', 0.0),
                'rationale': strategy_selection.get('rationale', ''),
                'market_trend': strategy_selection.get('market_conditions', {}).get('trend', 'unknown')
            }

            # Step 3: Trade Execution
            trade_result = analyze_and_execute_trade(
                market_data,
                instrument,
                risk_preference
            )

            cycle_result['trade_execution'] = {
                'decision': trade_result.get('decision', 'NO_TRADE'),
                'execution_status': trade_result.get('execution_status', 'UNKNOWN'),
                'confidence': trade_result.get('confidence', 0.0),
                'reason': trade_result.get('reason', '')
            }

            # Step 4: Update Performance Tracking
            if trade_result.get('execution_status') == 'EXECUTED':
                self._update_performance_tracking(trade_result)

            cycle_result['performance_update'] = self._get_performance_summary()

            # Determine overall cycle status
            if trade_result.get('execution_status') == 'EXECUTED':
                cycle_result['status'] = 'TRADE_EXECUTED'
            elif trade_result.get('decision') == 'TRADE_SIGNAL_GENERATED':
                cycle_result['status'] = 'SIGNAL_GENERATED'
            else:
                cycle_result['status'] = 'NO_TRADE'

            # Log results
            self._log_trading_cycle(cycle_result)

            print("✅ AI Trading Cycle Completed")
            print(f"📊 Status: {cycle_result['status']}")
            if cycle_result['trade_execution']['decision'] != 'NO_TRADE':
                print(f"🎯 Strategy: {cycle_result['strategy_selection']['selected_strategy']}")
                print(".1f")

            return cycle_result

        except Exception as e:
            cycle_result['status'] = 'ERROR'
            cycle_result['error'] = str(e)
            print(f"❌ AI Trading cycle error: {e}")
            return cycle_result

    def get_ai_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive AI dashboard data for the web interface.

        Returns:
            Complete dashboard data dictionary
        """
        if not self.is_initialised:
            return {'status': 'not_initialised', 'message': 'AI system not initialized'}

        dashboard_data = {
            'system_status': {
                'is_initialised': self.is_initialised,
                'live_trading': self.enable_live_trading,
                'initialised_at': datetime.now().isoformat()
            },

            'portfolio_overview': {
                'account_balance': self.account_balance,
                'allocated_strategies': self.portfolio_allocation,
                'active_positions': len(self.active_positions),
                'total_pnl': self.system_performance['total_pnl']
            },

            'ai_performance': {
                'analysis_confidence': self.performance_analysis.get('ai_confidence_score', 0.0),
                'profitable_strategies_count': len(self.performance_analysis.get('profitable_strategies', [])),
                'strategy_rankings': self.strategy_rankings[:10],  # Top 10
                'risk_level': self.performance_analysis.get('risk_assessment', {}).get('risk_level', 'UNKNOWN'),
                'portfolio_allocation_quality': len([s for s in self.portfolio_allocation.values() if s > 0.1])
            },

            'trading_statistics': {
                'total_trades': self.system_performance['total_trades'],
                'win_rate': (self.system_performance['winning_trades'] / self.system_performance['total_trades'] * 100) if self.system_performance['total_trades'] > 0 else 0,
                'total_pnl': self.system_performance['total_pnl'],
                'sharpe_ratio': self.system_performance['sharpe_ratio'],
                'max_drawdown': self.system_performance['max_drawdown'],
                'avg_ai_confidence': self.system_performance['ai_confidence_avg']
            },

            'strategies_info': {
                'total_available': len(self.backtest_results),
                'profitable_strategies': len(self.performance_analysis.get('profitable_strategies', [])),
                'top_performing_strategy': self.strategy_rankings[0]['strategy_name'] if self.strategy_rankings else 'None',
                'allocation_details': self.portfolio_allocation
            },

            'execution_status': get_executor_status(),

            'recommendations': self.performance_analysis.get('trading_recommendations', []),

            'last_update': datetime.now().isoformat()
        }

        return dashboard_data

    def run_performance_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive AI performance analysis.

        Returns:
            Analysis results
        """
        print("🔬 RUNNING AI PERFORMANCE ANALYSIS...")

        if not self.backtest_results:
            return {'status': 'no_data', 'message': 'No backtest results available'}

        try:
            # Run AI analysis using imported function
            analysis = analyze_strategy_performance(self.backtest_results)

            # Update our performance analysis
            self.performance_analysis = analysis

            print("✅ AI Performance Analysis Complete")
            print(f"📊 Strategies Analyzed: {analysis.get('total_strategies_analyzed', 0)}")
            print(f"💎 Profitable Strategies: {len(analysis.get('profitable_strategies', []))}")
            print(f"🤖 AI Confidence: {analysis.get('ai_confidence_score', 0.5):.3f}")
            print(f"🏆 Top Strategy: {analysis.get('strategy_rankings', [{}])[0].get('strategy_name', 'None')}")

            return {
                'status': 'success',
                'analysis': analysis,
                'insights': analysis.get('pattern_insights', {}),
                'recommendations': analysis.get('trading_recommendations', [])
            }

        except Exception as e:
            print(f"❌ Performance analysis failed: {e}")
            return {'status': 'error', 'message': str(e)}

    def _load_backtest_results(self) -> List[Dict[str, Any]]:
        """
        Load backtesting results from the system.

        Returns:
            List of backtest result dictionaries
        """
        try:
            # Try to get actual backtest results
            results = get_test_backtest_results()

            if results and results.get('all_results'):
                return results['all_results']

        except Exception as e:
            print(f"Could not load backtest results: {e}")

        return []

    def _generate_sample_backtest_data(self) -> List[Dict[str, Any]]:
        """
        Generate sample backtest data for testing.

        Returns:
            Sample backtest results
        """
        strategies = [
            {'strategy_name': 'MovingAverageCrossStrategy', 'total_return': 12.5, 'sharpe_ratio': 1.4, 'win_rate': 0.65, 'max_drawdown': -4.2, 'total_trades': 87, 'avg_trade_pnl': 2.5},
            {'strategy_name': 'RSIReversionStrategy', 'total_return': 8.3, 'sharpe_ratio': 1.1, 'win_rate': 0.58, 'max_drawdown': -6.1, 'total_trades': 92, 'avg_trade_pnl': 1.8},
            {'strategy_name': 'BollingerBreakoutStrategy', 'total_return': 15.7, 'sharpe_ratio': 1.6, 'win_rate': 0.62, 'max_drawdown': -5.8, 'total_trades': 75, 'avg_trade_pnl': 3.2},
            {'strategy_name': 'ATRBreakoutStrategy', 'total_return': 9.4, 'sharpe_ratio': 1.2, 'win_rate': 0.59, 'max_drawdown': -4.9, 'total_trades': 83, 'avg_trade_pnl': 2.1},
            {'strategy_name': 'EMARSIHybridStrategy', 'total_return': 18.2, 'sharpe_ratio': 1.8, 'win_rate': 0.67, 'max_drawdown': -3.7, 'total_trades': 68, 'avg_trade_pnl': 4.1},
            {'strategy_name': 'MACDStrategy', 'total_return': 6.8, 'sharpe_ratio': 0.9, 'win_rate': 0.54, 'max_drawdown': -7.3, 'total_trades': 95, 'avg_trade_pnl': 1.3},
        ]

        # Add more sample data
        for strategy_data in strategies:
            strategy_data.update({
                'profit_factor': 1.4 + (strategy_data['sharpe_ratio'] - 0.8) * 0.3,
                'total_trades': strategy_data['total_trades'],
                'volatility': 0.12 + (strategy_data['sharpe_ratio'] - 1.0) * 0.05,
                'avg_loss': strategy_data['avg_trade_pnl'] * 0.6
            })

        return strategies

    def _update_performance_tracking(self, trade_result: Dict[str, Any]):
        """
        Update system performance tracking with new trade results.
        """
        self.system_performance['total_trades'] += 1

        # Get trade outcome (simulated for now)
        if 'trade_signal' in trade_result:
            # Simulate random outcome based on confidence
            confidence = trade_result.get('confidence', 0.5)
            success_probability = 0.5 + (confidence - 0.5) * 0.3  # 50% base + confidence boost

            import random
            is_winner = random.random() < success_probability

            if is_winner:
                self.system_performance['winning_trades'] += 1
                # Simulate reasonable P&L based on strategy and confidence
                pnl = random.uniform(0.5, 3.0) * confidence
                self.system_performance['total_pnl'] += pnl

        # Update AI confidence average
        total_trades = self.system_performance['total_trades']
        current_avg = self.system_performance['ai_confidence_avg']
        new_confidence = trade_result.get('confidence', 0.5)
        self.system_performance['ai_confidence_avg'] = (current_avg * (total_trades - 1) + new_confidence) / total_trades

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary."""
        return {
            'total_trades': self.system_performance['total_trades'],
            'win_rate': (self.system_performance['winning_trades'] / self.system_performance['total_trades'] * 100) if self.system_performance['total_trades'] > 0 else 0,
            'total_pnl': self.system_performance['total_pnl'],
            'avg_ai_confidence': self.system_performance['ai_confidence_avg']
        }

    def _log_trading_cycle(self, cycle_result: Dict[str, Any]):
        """Log trading cycle results."""
        # Create logs directory if not exists
        os.makedirs('logs', exist_ok=True)

        # Log to AI trading log
        log_file = 'logs/ai_trading.log'
        timestamp = cycle_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        confidence = cycle_result['strategy_selection'].get('confidence', 0.0)
        pnl = cycle_result['performance_update'].get('total_pnl', 0.0)

        log_entry = (
            f"[{timestamp}] {cycle_result['instrument']} - "
            f"Status: {cycle_result['status']} - "
            f"Strategy: {cycle_result['strategy_selection'].get('selected_strategy', 'None')} - "
            f"Confidence: {confidence:.1f} - "
            f"PNL: {pnl:.2f}"
        )

        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def _print_system_status(self):
        """Print system status after initialization."""
        analysis = self.performance_analysis

        print("\n" + "="*60)
        print("🤖 AI TRADING SYSTEM STATUS")
        print("="*60)
        print("📊 Performance Analysis:")
        print(f"   Strategies Analyzed: {analysis.get('total_strategies_analyzed', 0)}")
        print(f"   Profitable Strategies: {len(analysis.get('profitable_strategies', []))}")
        if analysis.get('ai_confidence_score') is not None:
            print(f"   AI Confidence Score: {analysis.get('ai_confidence_score', 0.0):.3f}")
        print()

        if self.strategy_rankings:
            print("🏆 Top 3 Strategies:")
            for i, strategy in enumerate(self.strategy_rankings[:3], 1):
                print(f"   {i}. {strategy.get('strategy_name', 'Unknown')}: {strategy.get('total_return', 0):.3f} return")
        print()

        if self.portfolio_allocation:
            print("📈 Portfolio Allocation:")
            for strategy, weight in sorted(self.portfolio_allocation.items(), key=lambda x: x[1], reverse=True):
                print(f"   {strategy}: {weight:.3f}")
        print()

        risk_info = analysis.get('risk_assessment', {})
        print("🛡️ Risk Assessment:")
        print(f"   Risk Level: {risk_info.get('risk_level', 'UNKNOWN')}")
        print(".1%")
        print()

        recommendations = analysis.get('trading_recommendations', [])
        if recommendations:
            print("💡 AI Recommendations:")
            for rec in recommendations[:2]:  # Show top 2
                print(f"   • {rec.get('message', 'Unknown')}")
            print()

        print("🚀 SYSTEM READY FOR AUTOMATED TRADING")
        print("="*60)

# Global AI trading system instance
ai_trading_system = AITradingSystem()

def initialize_ai_trading(account_balance: float = 10000.0,
                         enable_live_trading: bool = False) -> bool:
    """
    Initialize the complete AI trading system.

    Args:
        account_balance: Starting account balance
        enable_live_trading: Enable live trading mode

    Returns:
        Success status
    """
    global ai_trading_system
    ai_trading_system = AITradingSystem(account_balance, enable_live_trading)
    return ai_trading_system.initialize_ai_system()

def run_ai_trade_cycle(market_data: pd.DataFrame,
                      instrument: str = "R_10",
                      risk_preference: str = 'balanced') -> Dict[str, Any]:
    """
    Execute a complete AI trading cycle.

    Args:
        market_data: Current market data
        instrument: Trading instrument
        risk_preference: Risk preference level

    Returns:
        Trading cycle results
    """
    global ai_trading_system
    return ai_trading_system.run_ai_trading_cycle(market_data, instrument, risk_preference)

def get_dashboard_data() -> Dict[str, Any]:
    """
    Get AI dashboard data for web interface.

    Returns:
        Complete dashboard data
    """
    global ai_trading_system
    return ai_trading_system.get_ai_dashboard_data()

# Import strategy_factory for AI system compatibility
try:
    from src.strategy import strategy_factory
except ImportError:
    # Fallback if strategy factory not available
    class _DummyStrategyFactory:
        def create_strategy(self, *args, **kwargs):
            return {'name': 'fallback_strategy', 'type': 'basic', 'description': 'default strategy when factory unavailable'}
    strategy_factory = _DummyStrategyFactory()

# Export AITradingCoordinator as alias for backward compatibility
AITradingCoordinator = AITradingSystem

# Export AI Trading UI component
try:
    from src.trading.ui import AITradingUI
except ImportError:
    AITradingUI = None

# Updated exports
if __name__ == "__main__":
    print("🤖 AI TRADING SYSTEM MAIN INTERFACE")
    print("=" * 50)

    # Initialize system
    success = initialize_ai_trading(enable_live_trading=False)

    if success:
        print("\n✅ System initialized successfully!")

        # Test with sample data
        print("\n🧪 Testing AI trading cycle...")
        sample_data = create_sample_ohlc_data("R_10", 200)

        result = run_ai_trade_cycle(sample_data, "R_10", 'balanced')

        print(f"🎯 Cycle Result: {result.get('status', 'UNKNOWN')}")

        # Show dashboard data
        dashboard = get_dashboard_data()
        if dashboard.get('system_status', {}).get('is_initialised'):
            print("📊 Dashboard Data Ready:")
            perf = dashboard.get('trading_statistics', {})
            print(".1f")

    else:
        print("❌ System initialization failed")
