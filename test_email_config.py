#!/usr/bin/env python3
"""
Test Email Configuration
========================
Test script to verify email alert configuration and connectivity.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    """Test email configuration."""
    print("📧 Testing Email Configuration")
    print("=" * 50)

    try:
        from src.monitoring.production.production_monitoring_system import test_email_configuration

        # Run the test
        result = test_email_configuration()

        print("\n" + "=" * 50)
        print("📊 FINAL TEST RESULTS")
        print("=" * 50)

        if result.get('test_passed', False):
            print("✅ EMAIL CONFIGURATION TEST PASSED")
            print("📧 Email alerts are properly configured and ready to send")
            print("🚨 Emergency alerts will work correctly")
        else:
            print("❌ EMAIL CONFIGURATION TEST FAILED")
            print("📧 Email alerts will not work - please fix configuration")

            if result.get('recommendations'):
                print("\n🔧 FIXES NEEDED:")
                for i, rec in enumerate(result['recommendations'], 1):
                    print(f"   {i}. {rec}")

        # Show environment variables that should be set
        print("\n📋 REQUIRED ENVIRONMENT VARIABLES:")
        print("   ALERT_SMTP_SERVER=your_smtp_server (e.g., smtp.gmail.com)")
        print("   ALERT_SMTP_PORT=your_smtp_port (e.g., 587)")
        print("   ALERT_EMAIL=your_sender_email@domain.com")
        print("   ALERT_EMAIL_PASSWORD=your_app_password")
        print("   ALERT_RECIPIENTS=email1@domain.com,email2@domain.com")
        print("   ALERT_USE_TLS=true")

        return result.get('test_passed', False)

    except Exception as e:
        print(f"❌ Error testing email configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
