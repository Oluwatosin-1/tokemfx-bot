#!/usr/bin/env python3
"""
Test Performance Analyzer with Real Data
========================================
Tests that the performance analyzer now uses real backtesting data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.ai_trading_system.analytics.performance_analyzer import performance_analyzer

def test_performance_analyzer():
    """Test that performance analyzer uses real data."""
    print("🧪 Testing Performance Analyzer with Real Data")
    print("=" * 60)

    try:
        # Get performance summary
        summary = performance_analyzer.get_performance_summary()

        print("📊 Performance Summary:")
        print(f"  Total Trades: {summary.get('total_trades', 0)}")
        print(f"  Win Rate: {summary.get('win_rate', 0):.1f}%")
        print(f"  Total P&L: ${summary.get('total_pnl', 0):.2f}")
        print(f"  Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
        print(f"  Data Source: {summary.get('data_source', 'unknown')}")

        # Check if it's using real data
        if summary.get('data_source') == 'aggregated_backtesting':
            print("✅ SUCCESS: Performance analyzer is using real backtesting data!")
            return True
        elif summary.get('data_source') == 'simulated_fallback':
            print("❌ FAILURE: Still using simulated fallback data")
            return False
        else:
            print(f"⚠️  UNKNOWN: Unexpected data source: {summary.get('data_source')}")
            return False

    except Exception as e:
        print(f"❌ Error testing performance analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_performance_analyzer()
    if success:
        print("\n🎉 Performance analyzer is now working with real data!")
    else:
        print("\n❌ Performance analyzer test failed")
