# Deriv OAuth Configuration Guide

This guide explains how to set up OAuth tokens for Deriv API authentication to resolve balance access issues with real accounts.

## Problem

When using API tokens with real Deriv accounts, balance requests may fail with:
```
❌ API Error: {'code': 'PermissionDenied', 'message': 'Permission denied, balances of all accounts require oauth token'}
```

This occurs because Deriv requires OAuth tokens for accessing account information on real accounts.

## Solution Overview

The updated system supports both:
- **API Tokens**: For demo accounts and basic trading operations
- **OAuth Tokens**: For real accounts and enhanced permissions (balance, statements, etc.)

## Configuration

### 1. Environment Variables (.env file)

Add the following to your `.env` file:

```bash
# Basic Settings
DERIV_APP_ID=96454
DERIV_CLIENT_ID=deriv_app

# API Token Authentication (for demo accounts)
DERIV_API_TOKEN=RnmDtXN8thmn6j9  # Your existing token
DEMO_DERIV_ACCOUNT_ID=VRW478911     # Your demo account ID

# OAuth Token Authentication (for real accounts)
DERIV_OAUTH_TOKEN=your_oauth_token_here
DERIV_REFRESH_TOKEN=your_refresh_token_here

# Real Account
DERIV_ACCOUNT_ID=VRTC14195029        # Your real account ID

# Authentication Mode (auto, api, oauth)
DERIV_AUTH_MODE=auto
```

### 2. Authentication Modes

- **`auto`** *(recommended)*: Automatically chooses based on available tokens and account type
- **`api`**: Forces API token authentication (demo accounts only)
- **`oauth`**: Forces OAuth token authentication (real accounts)

## OAuth Token Setup

### Automatic Setup (Recommended)

Run the OAuth setup script:

```bash
python src/oauth_setup.py
```

This script will:
1. Validate your configuration
2. Generate OAuth authorization URL
3. Open your browser for Deriv login
4. Handle the authorization flow
5. Save tokens to your `.env` file

### Manual Setup

If you prefer to handle tokens manually:

1. **Generate Authorization URL:**
   ```python
   from src.tokemfx.config import generate_deriv_oauth_url
   url = generate_deriv_oauth_url('http://localhost:8080/callback')
   print(url)  # Visit this URL
   ```

2. **Obtain Tokens:**
   - Visit the generated URL
   - Login to Deriv
   - Grant permissions
   - Extract tokens from redirect URL

3. **Save to .env:**
   ```bash
   echo "DERIV_OAUTH_TOKEN=your_access_token_here" >> .env
   echo "DERIV_REFRESH_TOKEN=your_refresh_token_here" >> .env
   echo "DERIV_AUTH_MODE=oauth" >> .env
   ```

## Testing the Configuration

### 1. Validate Configuration

```python
from src.tokemfx.config import validate_deriv_auth_config
is_valid, issues, recommendations = validate_deriv_auth_config()

if is_valid:
    print("✅ Configuration is valid!")
else:
    print("❌ Issues found:")
    for issue in issues:
        print(f"   - {issue}")
    for rec in recommendations:
        print(f"   💡 {rec}")
```

### 2. Test Broker Connection

```python
from src.tokemfx.broker import DerivBroker

broker = DerivBroker()
status = broker.get_auth_status()
print(f"Authenticated: {status['is_authenticated']}")
print(f"Account Type: {status['account_type']}")
print(f"Auth Method: {status['auth_method_used']}")

# Test balance retrieval
balance = broker.get_account_balance()
print(f"Balance: {balance}")
```

### 3. Test Real Authentication

```bash
# Restart your app after configuration changes
streamlit run app.py

# Or run specific test
python -c "
from src.tokemfx.broker import DerivBroker
b = DerivBroker()
balance = b.get_account_balance()
print('Balance access result:', balance)
"
```

## Account Type Detection

The system automatically detects account types:

- **`DEMO`**: Demo account using API token
- **`REAL_OAUTH`**: Real account using OAuth token
- **`REAL_API`**: Real account using API token (may have permission limits)
- **`UNKNOWN`**: Cannot determine account type

## Troubleshooting

### Common Issues

1. **"balances of all accounts require oauth token"**
   - **Solution**: Switch to OAuth mode or get OAuth tokens

2. **Authentication succeeds but balance fails**
   - **Check**: Ensure you're using OAuth tokens for real accounts
   - **Fix**: Set `DERIV_AUTH_MODE=oauth` and provide OAuth tokens

3. **OAuth setup fails**
   - **Check**: Ensure DERIV_CLIENT_ID is set
   - **Check**: Ensure DERIV_APP_ID matches your registered app

4. **Tokens not saved**
   - **Check**: File permissions on `.env` file
   - **Fix**: Ensure the script can write to `.env`

### Token Management

- **Access tokens expire**: Use refresh tokens to get new access tokens
- **Store securely**: Never commit tokens to version control
- **Rotate regularly**: Generate new tokens periodically for security

## Security Best Practices

1. **Never commit tokens** to version control
2. **Use environment variables** for sensitive data
3. **Limit token scope** to required permissions only
4. **Rotate tokens** regularly
5. **Use HTTPS** for all API calls
6. **Monitor access** patterns

## Example .env Configuration

```bash
# Deriv API Configuration - Demo Account
DERIV_APP_ID=96454
DERIV_API_TOKEN=RnmDtXN8thmn6j9
DEMO_DERIV_ACCOUNT_ID=VRW478911
DERIV_AUTH_MODE=api

# Deriv API Configuration - Real Account with OAuth
# DERIV_OAUTH_TOKEN=oauth_abc123...
# DERIV_REFRESH_TOKEN=refresh_xyz789...
# DERIV_ACCOUNT_ID=VRTC14195029
# DERIV_AUTH_MODE=oauth
```

## Next Steps

1. **Configure your environment** with appropriate tokens
2. **Run the OAuth setup script** for automatic configuration
3. **Test authentication** with your preferred account type
4. **Monitor balance access** to ensure it's working correctly

The enhanced authentication system will now properly handle both demo and real accounts with appropriate permission levels.
