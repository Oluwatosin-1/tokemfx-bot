#!/usr/bin/env python3
"""
Simple test script for Deriv API connection

Tests the single account configuration with your VRTC14195029 account.
Run from project root: python test_deriv_connection_simple.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.trading.execution.broker import DerivBroker

def test_connection():
    """Test basic Deriv API connection."""
    print("🚀 Testing Deriv API Connection")
    print("=" * 50)

    try:
        # Initialize broker (will connect and authenticate)
        print("🌐 Initializing broker...")
        broker = DerivBroker()
        assert broker is not None, "Broker initialization failed"

        # Test authentication and balance access
        print("\\n🔐 Testing Authentication and Balance Access...")
        balance = broker.get_account_balance()

        # Now check authentication status after attempting balance access
        auth_status = broker.get_auth_status()
        print(f"\\n✅ Authentication Status (after balance attempt):")
        print(f"   Authenticated: {auth_status['is_authenticated']}")
        print(f"   Account Type: {auth_status['account_type']}")
        print(f"   Auth Method: {auth_status['auth_method_used']}")
        print(f"   Account ID: {auth_status['account_id']}")

        if balance and not balance.get("error"):
            print("✅ Balance retrieved successfully!")
            print(f"   Balance data: {balance}")

            # Show account details if successful
            if "balance" in balance:
                balance_list = balance.get("balance", [])
                if balance_list and isinstance(balance_list[0], dict):
                    print("💰 Account Details:")
                    for key, value in balance_list[0].items():
                        print(f"   {key}: {value}")

        elif balance and balance.get("error"):
            error_msg = balance["error"]["message"]
            error_code = balance["error"].get("code", "Unknown")
            print(f"❌ Balance access failed: {error_msg}")
            print(f"   Error code: {error_code}")

            # Suggest next steps based on error
            if "oauth" in error_msg.lower() or "permission" in error_msg.lower():
                print("\\n💡 Recommendation:")
                print("   Your account appears to be REAL (not demo)")
                print("   For real accounts, you need OAuth tokens for balance access")
                print("   Run: python src/oauth_setup.py")
        else:
            print("❌ Balance request failed completely")

            # Check if we can at least get account status
            print("\\n🔍 Trying to get account status instead...")
            account_status = broker.get_account_status()
            if account_status and not account_status.get("error"):
                print("✅ Account status retrieved!")
                print(f"   Status: {account_status}")
            else:
                print("❌ All API calls are failing - check your API token and account details")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed with exception: {e}"

if __name__ == "__main__":
    success = test_connection()
    print("\\n" + "=" * 50)
    if success:
        print("🎉 Connection test completed!")
    else:
        print("❌ Connection test failed!")

    print("\\n📝 Next steps:")
    print("  1. Check your .env file has the correct values from Deriv dashboard")
    print("  2. If balance fails, your account might need OAuth configuration")
    print("  3. Run: python src/oauth_setup.py for OAuth token setup")
