# fixed_zerodha_config.py
# Fixed configuration that properly loads saved tokens

# Zerodha API Configuration
ZERODHA_CONFIG = {
    'api_key': 'gs9ulgi4ipyq5tkf',
    'api_secret': 'kzbqml8arzr8y3mdzm9xlc8kgwkb8991',
    'redirect_url': 'http://127.0.0.1:5000/zerodha/callback',
    'access_token': None,  # Will be loaded from file
    'base_url': 'https://kite.zerodha.com'
}

# Trading Configuration
TRADING_CONFIG = {
    'exchange': 'NSE',
    'product': 'MIS',  # MIS for intraday, CNC for delivery
    'order_type': 'MARKET',
    'validity': 'DAY',
    'initial_cash': 500000.0,
    'commission': 20.0,  # Rs 20 per order
    'lot_size': 1,
}

# Data Configuration
DATA_CONFIG = {
    'timeframe': '5minute',
    'historical_days': 10,  # Reduced for faster testing
    'live_data': False,
}

# Zerodha Instrument Tokens
ZERODHA_INSTRUMENTS = {
    'RELIANCE': {
        'instrument_token': 738561,
        'trading_symbol': 'RELIANCE',
        'exchange': 'NSE',
        'lot_size': 1
    },
    'TCS': {
        'instrument_token': 2953217,
        'trading_symbol': 'TCS',
        'exchange': 'NSE', 
        'lot_size': 1
    },
    'INFY': {
        'instrument_token': 408065,
        'trading_symbol': 'INFY',
        'exchange': 'NSE',
        'lot_size': 1
    }
}

# Strategy Parameters
STRATEGY_CONFIG = {
    'fast_ma_period': 10,
    'slow_ma_period': 30,
    'rsi_period': 14,
    'position_size': 1,
    'max_positions': 3,
    'debug': True
}

def load_access_token():
    """Load access token from saved file"""
    try:
        with open('zerodha_token.txt', 'r') as f:
            token = f.read().strip()
        
        if token:
            ZERODHA_CONFIG['access_token'] = token
            print(f"✅ Access token loaded from file")
            return token
        else:
            print("⚠️ Empty token file")
            return None
            
    except FileNotFoundError:
        print("⚠️ No saved token file found")
        return None
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return None

def set_access_token(token):
    """Set access token"""
    ZERODHA_CONFIG['access_token'] = token

def print_config():
    """Print current configuration"""
    print("🔧 Zerodha-Backtrader Configuration")
    print("=" * 40)
    print(f"API Key: {ZERODHA_CONFIG['api_key']}")
    print(f"Exchange: {TRADING_CONFIG['exchange']}")
    print(f"Product: {TRADING_CONFIG['product']}")
    print(f"Initial Cash: ₹{TRADING_CONFIG['initial_cash']:,.2f}")
    print(f"Commission: ₹{TRADING_CONFIG['commission']:.2f} per order")
    print(f"Available Symbols: {list(ZERODHA_INSTRUMENTS.keys())}")
    print(f"Timeframe: {DATA_CONFIG['timeframe']}")
    print(f"Historical Days: {DATA_CONFIG['historical_days']}")
    print(f"Live Data: {DATA_CONFIG['live_data']}")
    
    if ZERODHA_CONFIG['access_token']:
        print(f"✅ Access Token: Loaded")
    else:
        print(f"❌ Access Token: Not loaded")

# Auto-load token when module is imported
load_access_token()

if __name__ == '__main__':
    print_config()