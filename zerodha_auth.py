#!/usr/bin/env python3
"""
Zerodha Authentication Handler
Handles the OAuth flow to get access tokens
"""

import hashlib
from kiteconnect import KiteConnect
from zerodha_config import ZERODHA_CONFIG, set_access_token

def authenticate_zerodha():
    """
    Complete Zerodha authentication flow
    """
    print("🔐 Zerodha Authentication")
    print("=" * 40)
    
    # Initialize KiteConnect
    kite = KiteConnect(api_key=ZERODHA_CONFIG['api_key'])
    
    # Step 1: Generate login URL
    login_url = kite.login_url()
    print(f"\n📋 Step 1: Login to Zerodha")
    print(f"Visit this URL and login:")
    print(f"{login_url}")
    print()
    
    # Step 2: Get request token from user
    print(f"📋 Step 2: Get Request Token")
    print(f"After login, you'll be redirected to:")
    print(f"{ZERODHA_CONFIG['redirect_url']}")
    print(f"Copy the 'request_token' from the URL")
    print()
    
    request_token = input("Enter request_token: ").strip()
    
    if not request_token:
        print("❌ No request token provided")
        return None
    
    try:
        # Step 3: Generate session
        print(f"\n📋 Step 3: Generating session...")
        
        data = kite.generate_session(
            request_token=request_token,
            api_secret=ZERODHA_CONFIG['api_secret']
        )
        
        access_token = data['access_token']
        user_id = data['user_id']
        
        print(f"✅ Authentication successful!")
        print(f"   User ID: {user_id}")
        print(f"   Access Token: {access_token[:20]}...")
        
        # Set access token in config
        set_access_token(access_token)
        
        # Test the connection
        kite.set_access_token(access_token)
        profile = kite.profile()
        
        print(f"\n📊 Profile Information:")
        print(f"   Name: {profile.get('user_name', 'N/A')}")
        print(f"   Email: {profile.get('email', 'N/A')}")
        print(f"   Broker: {profile.get('broker', 'N/A')}")
        
        # Save token to file for reuse
        with open('zerodha_token.txt', 'w') as f:
            f.write(access_token)
        
        print(f"\n💾 Access token saved to zerodha_token.txt")
        print(f"⚠️ Note: Zerodha tokens expire daily at 6 AM")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def load_saved_token():
    """Load previously saved access token"""
    try:
        with open('zerodha_token.txt', 'r') as f:
            token = f.read().strip()
        
        if token:
            set_access_token(token)
            print(f"✅ Loaded saved access token")
            return token
        else:
            print("⚠️ No saved token found")
            return None
            
    except FileNotFoundError:
        print("⚠️ No saved token file found")
        return None

def test_connection():
    """Test Zerodha API connection"""
    try:
        if not ZERODHA_CONFIG['access_token']:
            print("❌ No access token available")
            return False
        
        kite = KiteConnect(api_key=ZERODHA_CONFIG['api_key'])
        kite.set_access_token(ZERODHA_CONFIG['access_token'])
        
        # Test API call
        profile = kite.profile()
        print(f"✅ Connection test successful")
        print(f"   User: {profile.get('user_name', 'N/A')}")
        
        # Test historical data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        historical_data = kite.historical_data(
            instrument_token=738561,  # RELIANCE
            from_date=start_date,
            to_date=end_date,
            interval="5minute"
        )
        
        print(f"✅ Historical data test successful")
        print(f"   Fetched {len(historical_data)} bars for RELIANCE")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main authentication flow"""
    print("🚀 Zerodha Authentication Setup")
    print("=" * 50)
    
    # Try to load saved token first
    saved_token = load_saved_token()
    
    if saved_token:
        print("\n🧪 Testing saved token...")
        if test_connection():
            print("\n🎉 Ready to trade with saved token!")
            return
        else:
            print("\n⚠️ Saved token invalid/expired, need fresh authentication")
    
    # Perform fresh authentication
    print("\n🔐 Starting fresh authentication...")
    token = authenticate_zerodha()
    
    if token:
        print("\n🎉 Authentication complete!")
        print("📝 Next steps:")
        print("   1. Run: python zerodha_backtrader_demo.py")
        print("   2. Start backtesting and live trading")
        print("\n⚠️ Remember:")
        print("   - Tokens expire daily at 6 AM IST")
        print("   - Re-run this script if you get auth errors")
    else:
        print("\n❌ Authentication failed")
        print("🔧 Troubleshooting:")
        print("   1. Check your API credentials")
        print("   2. Ensure you copied the correct request_token")
        print("   3. Try the process again")

if __name__ == '__main__':
    main()