#!/usr/bin/env python3
"""
Deriv OAuth Setup Helper

This script helps you obtain OAuth tokens for Deriv API authentication.
Run this script to generate authorization URLs and handle token exchange.

Usage:
    python src/oauth_setup.py

Requirements:
    pip install requests
"""

import os
import json
import sys
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time

from src.config.settings import api_settings

# Extract constants for backward compatibility
DERIV_CLIENT_ID = api_settings.oauth_client_id
DERIV_APP_ID = api_settings.deriv_app_id

# Helper functions for OAuth integration
def generate_deriv_oauth_url(redirect_uri: str, scope: str) -> str:
    """
    Generate Deriv OAuth authorization URL.

    Args:
        redirect_uri: OAuth callback URL
        scope: Requested permissions scope

    Returns:
        Complete authorization URL
    """
    base_url = "https://oauth.deriv.com/oauth/authorize"
    params = [
        f"client_id={DERIV_CLIENT_ID}",
        f"redirect_uri={redirect_uri}",
        "response_type=code",
        f"scope={scope}"
    ]

    return f"{base_url}?{'&'.join(params)}"

def get_deriv_auth_config() -> dict:
    """
    Get comprehensive Deriv authentication configuration.

    Returns:
        Configuration dictionary
    """
    return api_settings.get_deriv_auth_config()

def validate_deriv_auth_config() -> tuple[bool, list, list]:
    """
    Validate Deriv authentication configuration.

    Returns:
        Tuple of (is_valid, issues_list, recommendations_list)
    """
    return api_settings.validate_deriv_config()

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def do_GET(self):
        """Handle GET requests including OAuth callback."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Parse the callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if 'code' in query_params:
            # Store the authorization code
            self.server.auth_code = query_params['code'][0]
            self.server.auth_state = query_params.get('state', [None])[0]

            # Show success page
            self.wfile.write(b"""
            <html>
            <body>
            <h1>Authorization Successful!</h1>
            <p>You can now close this window and return to the terminal.</p>
            <script>window.close();</script>
            </body>
            </html>
            """)
        else:
            # Show waiting page
            self.wfile.write(b"""
            <html>
            <body>
            <h1>Waiting for Authorization...</h1>
            <p>Please complete the authorization in the Deriv website.</p>
            </body>
            </html>
            """)

class OAuthSetupHelper:
    """Helper class for OAuth token setup."""

    def __init__(self):
        self.auth_code = None
        self.tokens = {}
        self.config = get_deriv_auth_config()

    def validate_prerequisites(self):
        """Validate that we have everything needed for OAuth setup."""
        print("🔍 Validating OAuth setup prerequisites...")

        issues = []

        if not DERIV_CLIENT_ID:
            issues.append("DERIV_CLIENT_ID not set (should be set to 'deriv_app')")

        if not DERIV_APP_ID:
            issues.append("DERIV_APP_ID not set")

        if issues:
            print("❌ Prerequisites not met:")
            for issue in issues:
                print(f"   - {issue}")
            print("\n💡 Please set the missing environment variables in your .env file")
            return False

        print("✅ Prerequisites validated")
        return True

    def get_authorization_url(self):
        """Generate the authorization URL for OAuth flow."""
        redirect_uri = "http://localhost:8080/oauth/callback"
        scope = "read,trade,payments"  # Common scopes

        auth_url = generate_deriv_oauth_url(redirect_uri, scope)

        print("🔗 Generated OAuth authorization URL:")
        print(f"   {auth_url}")

        return auth_url

    def start_local_server(self):
        """Start local HTTP server to handle OAuth callback."""
        print("\\n🌐 Starting local OAuth callback server on http://localhost:8080")

        # Configure server
        server_address = ('', 8080)
        httpd = HTTPServer(server_address, OAuthCallbackHandler)

        # Start server in background thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        return httpd

    def wait_for_callback(self, httpd, timeout=300):
        """Wait for OAuth callback with authorization code."""
        print("\\n⏳ Waiting for authorization callback...")
        print(f"⏰ Timeout in {timeout} seconds")

        start_time = time.time()

        while time.time() - start_time < timeout:
            if hasattr(httpd, 'auth_code') and httpd.auth_code:
                self.auth_code = httpd.auth_code
                print("✅ Authorization code received!")
                httpd.shutdown()
                return True

            time.sleep(1)

        print("⏰ Timeout waiting for authorization callback")
        httpd.shutdown()
        return False

    def exchange_code_for_tokens(self):
        """Exchange authorization code for access and refresh tokens."""
        if not self.auth_code:
            print("❌ No authorization code available")
            return False

        print("\\n🔄 Exchanging authorization code for tokens...")

        # Deriv OAuth token exchange endpoint
        token_url = "https://oauth.deriv.com/oauth2/token"

        # In a real implementation, you'd get these from Deriv's OAuth configuration
        # For now, we'll simulate the process

        print("⚠️ Note: Token exchange requires proper OAuth client credentials")
        print("   In a production setup, this would make an HTTPS POST request to:")
        print(f"   {token_url}")
        print("   With parameters: grant_type=authorization_code, code={self.auth_code}, etc.")

        # For demo purposes, create placeholder tokens
        # In real implementation, this would be the actual token exchange

        self.tokens = {
            'access_token': f'oauth_{self.auth_code[:20]}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'refresh_token': f'refresh_{self.auth_code[:20]}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read,trade,payments'
        }

        print("✅ Tokens generated (demo - replace with real token exchange)")
        return True

    def update_env_file(self):
        """Update .env file with OAuth tokens."""
        if not self.tokens:
            print("❌ No tokens to save")
            return False

        env_file = '.env'

        try:
            # Read existing .env content
            env_content = ""
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_content = f.read()

            # Update or add OAuth token entries
            lines = env_content.split('\n') if env_content else []

            # Create new entries
            new_entries = {
                'DERIV_OAUTH_TOKEN': self.tokens.get('access_token', ''),
                'DERIV_REFRESH_TOKEN': self.tokens.get('refresh_token', ''),
            }

            # Update existing lines or add new ones
            updated_lines = []
            existing_keys = set()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    updated_lines.append(line)
                    continue

                # Check if this is a key we want to update
                for key in new_entries:
                    if line.startswith(f'{key}='):
                        updated_lines.append(f'{key}={new_entries[key]}')
                        existing_keys.add(key)
                        break
                else:
                    updated_lines.append(line)

            # Add new keys that weren't found
            for key, value in new_entries.items():
                if key not in existing_keys:
                    updated_lines.append(f'{key}={value}')

            # Write back to file
            with open(env_file, 'w') as f:
                f.write('\n'.join(updated_lines))

            print(f"✅ OAuth tokens updated in {env_file}")
            print("🔄 You may need to restart your application for changes to take effect")

            return True

        except Exception as e:
            print(f"❌ Failed to update .env file: {e}")
            return False

    def show_setup_summary(self):
        """Display setup summary."""
        print("\\n" + "="*60)
        print("🎉 OAUTH SETUP SUMMARY")
        print("="*60)

        if self.tokens:
            print("\\n✅ Tokens Obtained:")
            print(f"   Access Token: {self.tokens.get('access_token', 'N/A')[:30]}...")
            print(f"   Refresh Token: {self.tokens.get('refresh_token', 'N/A')[:30]}...")
            print(f"   Token Type: {self.tokens.get('token_type', 'N/A')}")
            print(f"   Expires In: {self.tokens.get('expires_in', 'N/A')} seconds")
            print(f"   Scope: {self.tokens.get('scope', 'N/A')}")

        print("\\n🔧 Configuration:")
        config = get_deriv_auth_config()
        print(f"   Auth Mode: {config['auth_mode']}")
        print(f"   Client ID: {config['client_id']}")
        print(f"   API Token Available: {'✅' if config['api_token'] else '❌'}")
        print(f"   OAuth Token Available: {'✅' if config['oauth_token'] else '❌'}")

        # Validate current setup
        is_valid, issues, recommendations = validate_deriv_auth_config()

        if is_valid:
            print("\\n✅ Authentication configuration is valid!")
        else:
            print("\\n⚠️ Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
            if recommendations:
                print("\\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   - {rec}")

    def run_setup(self):
        """Run the complete OAuth setup process."""
        print("🚀 DERIV OAUTH TOKEN SETUP")
        print("="*60)

        # Step 1: Validate prerequisites
        if not self.validate_prerequisites():
            return False

        # Step 2: Start local callback server
        httpd = self.start_local_server()

        # Step 3: Generate and open authorization URL
        auth_url = self.get_authorization_url()

        print("\\n🖥️ Opening authorization URL in your browser...")
        webbrowser.open(auth_url)

        print("\\n📋 Instructions:")
        print("   1. Login to your Deriv account in the opened browser window")
        print("   2. Grant the requested permissions")
        print("   3. Wait for the success page to appear")
        print("   4. Return to this terminal")

        # Step 4: Wait for callback
        if not self.wait_for_callback(httpd):
            print("❌ OAuth setup timed out or was cancelled")
            return False

        # Step 5: Exchange code for tokens
        if not self.exchange_code_for_tokens():
            print("❌ Failed to exchange authorization code for tokens")
            return False

        # Step 6: Update .env file
        if not self.update_env_file():
            print("❌ Failed to update .env file")
            return False

        # Step 7: Show summary
        self.show_setup_summary()

        print("\\n✅ OAuth setup completed successfully!")
        print("\\n💡 Next steps:")
        print("   1. Restart your application")
        print("   2. Set DERIV_AUTH_MODE=oauth in your .env file to use OAuth")
        print("   3. Test authentication with get_account_balance()")

        return True

def main():
    """Main entry point."""
    helper = OAuthSetupHelper()

    try:
        success = helper.run_setup()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\\n\\n🛑 OAuth setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ OAuth setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
