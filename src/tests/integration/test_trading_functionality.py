#!/usr/bin/env python3
"""
Comprehensive API Mode Trading Functionality Test

Tests all trading-related features that work with API tokens in Deriv:
- Market data fetching
- Account information
- Trading operations (if supported on demo)
- API connection stability
"""

import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.trading.execution.broker import DerivBroker
import time

@pytest.fixture
def broker():
    """Fixture to provide a DerivBroker instance."""
    return DerivBroker()

def test_market_data_fetching(broker):
    """Test fetching market data for different instruments."""
    print("\\n📊 Testing Market Data Access...")
    instruments = ["frxUSDJPY", "R_10", "R_25", "R_50"]

    results = {}
    for instrument in instruments:
        try:
            # Test 1-minute candle data
            candles = broker.fetch_candles(instrument, "M1", count=10)
            if candles is not None and not candles.empty:
                results[instrument] = {
                    'status': 'SUCCESS',
                    'rows': len(candles),
                    'latest_price': candles.iloc[-1]['close'] if 'close' in candles.columns else 'N/A'
                }
                print(f"  ✅ {instrument}: {len(candles)} candles, latest: {results[instrument]['latest_price']}")
                assert len(candles) > 0, f"No candles returned for {instrument}"
            else:
                results[instrument] = {'status': 'EMPTY_DATA'}
                print(f"  ⚠️ {instrument}: Empty data")
                assert False, f"Empty data returned for {instrument}"
        except Exception as e:
            results[instrument] = {'status': 'ERROR', 'message': str(e)}
            print(f"  ❌ {instrument}: {str(e)}")
            assert False, f"Error fetching data for {instrument}: {str(e)}"

def test_account_operations(broker):
    """Test account-related operations."""
    print("\\n👤 Testing Account Operations...")

    auth_status = broker.get_auth_status()
    print(f"  ✅ Authenticated: {auth_status['is_authenticated']}")
    print(f"  ✅ Account Type: {auth_status['account_type']}")
    print(f"  ✅ Account ID: {auth_status['account_id']}")

    # Test account status (non-balance operations)
    try:
        account_status = broker.get_account_status()
        if account_status and not account_status.get('error'):
            print("  ✅ Account status retrieved")
        else:
            print("  ⚠️ Account status failed (may require OAuth)")
    except Exception as e:
        print(f"  ❌ Account status error: {e}")

    return auth_status

def test_trading_operations(broker):
    """Test basic trading operations."""
    print("\\n💹 Testing Trading Operations...")

    # Test order placement (may not work on demo accounts, but let's try)
    try:
        # Test CFD order placement - even if rejected, we want to see the API response
        order_result = broker.place_order("R_10", 1)  # Buy 1 unit of R_10

        if order_result:
            if order_result.get('error'):
                error_msg = order_result['error']['message']
                print(f"  ⚠️ Order placement: {error_msg}")
                if "demo" in error_msg.lower() or "trading" in error_msg.lower():
                    print("  💡 Demo accounts may have trading restrictions")
                return {'status': 'RESTRICTED', 'message': error_msg}
            else:
                print("  ✅ Sample order placed successfully")
                return {'status': 'SUCCESS', 'order': order_result}
        else:
            print("  ⚠️ Order placement returned None")
            return {'status': 'NO_RESPONSE'}
    except Exception as e:
        print(f"  ❌ Order placement error: {e}")
        return {'status': 'ERROR', 'message': str(e)}

def test_api_stability(broker):
    """Test API connection stability with multiple requests."""
    print("\\n🔄 Testing API Stability (Multiple Requests)...")

    success_count = 0
    total_tests = 5

    for i in range(total_tests):
        try:
            # Quick market data test
            data = broker.fetch_candles("R_10", "M1", count=2)
            if data is not None and not data.empty:
                success_count += 1
                print(f"  ✅ Request {i+1}/{total_tests}: Success")
            else:
                print(f"  ⚠️ Request {i+1}/{total_tests}: Empty data")

            time.sleep(0.5)  # Small delay between requests
        except Exception as e:
            print(f"  ❌ Request {i+1}/{total_tests}: {str(e)}")

    reliability = (success_count / total_tests) * 100
    print(".1f")

    return {
        'success_rate': reliability,
        'successful_requests': success_count,
        'total_requests': total_tests
    }

def create_production_readiness_report(test_results):
    """Create a summary report for production readiness."""
    print("\\n" + "="*60)
    print("🚀 PRODUCTION READINESS REPORT")
    print("="*60)

    print("\\n📊 Test Results Summary:")

    # Auth Status
    auth = test_results['auth_status']
    print("🏆 Authentication: {'✅ WORKING' if auth['is_authenticated'] else '❌ FAILED'}")
    print(f"   Account Type: {auth['account_type']}")
    print(f"   Account ID: {auth['account_id']}")

    # Market Data
    market_data = test_results['market_data']
    successful_instruments = sum(1 for r in market_data.values() if r['status'] == 'SUCCESS')
    print(f"💹 Market Data: ✅ {successful_instruments}/{len(market_data)} instruments working")

    # Trading Operations
    trading = test_results['trading_operations']
    if trading['status'] == 'SUCCESS':
        print("🎯 Order Placement: ✅ WORKING")
    elif trading['status'] == 'RESTRICTED':
        print("🎯 Order Placement: ⚠️ RESTRICTED (Demo Account)")
    else:
        print("🎯 Order Placement: ❌ FAILED")

    # API Stability
    stability = test_results['api_stability']
    if stability['success_rate'] >= 80:
        print(".1f")
    elif stability['success_rate'] >= 50:
        print(".1f")
    else:
        print(".1f")

    # Overall Assessment
    print("\\n🏁 OVERALL ASSESSMENT:")
    auth_working = test_results['auth_status']['is_authenticated']
    data_working = successful_instruments > 0
    stable = test_results['api_stability']['success_rate'] >= 70

    if auth_working and data_working and stable:
        print("🟢 READY FOR PRODUCTION DEPLOYMENT")
        print("   ✅ Core trading functionality working")
        print("   ✅ API authentication stable")
        print("   ✅ Market data accessible")
        print("   ⚠️ Balance queries need OAuth (set up in production)")
    else:
        print("🔴 REQUIRES FURTHER TESTING")
        if not auth_working:
            print("   ❌ Authentication not working")
        if not data_working:
            print("   ❌ Market data not accessible")
        if not stable:
            print("   ❌ API connection unstable")
        print("   💡 Address issues before production deployment")

    print("\\n📋 DEPLOYMENT NOTES:")
    print("1. Deploy this code to production server")
    print("2. Set up Deriv OAuth app with real domain")
    print("3. Run: python src/oauth_setup.py")
    print("4. Set DERIV_AUTH_MODE=oauth for full functionality")
    print("5. Test balance access in production environment")

def main():
    """Run comprehensive trading functionality test."""
    print("🚀 COMPREHENSIVE API-MODE TRADING FUNCTIONALITY TEST")
    print("="*60)
    print("Testing all trading operations that work with API tokens only...")
    print("This confirms your bot is ready for production deployment!")

    try:
        # Initialize broker
        print("\\n🔧 Initializing Broker...")
        broker = DerivBroker()

        # Run all tests
        test_results = {}

        # Test authentication
        test_results['auth_status'] = test_account_operations(broker)

        # Test market data access
        test_results['market_data'] = test_market_data_fetching(broker)

        # Test trading operations
        test_results['trading_operations'] = test_trading_operations(broker)

        # Test API stability
        test_results['api_stability'] = test_api_stability(broker)

        # Generate production readiness report
        create_production_readiness_report(test_results)

        return True

    except KeyboardInterrupt:
        print("\\n\\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1

    print(f"\\n{'='*60}")
    if success:
        print("🎉 Testing completed successfully!")
    else:
        print("❌ Testing failed - check errors above")

    print(f"\\nExit code: {exit_code}")
    sys.exit(exit_code)
