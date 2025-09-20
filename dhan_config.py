# dhan_config.py
# Configuration for Dhan Sandbox + Backtrader Integration

# Dhan Sandbox Configuration (from your .env file)
DHAN_CONFIG = {
    'client_id': '2509179790',
    'access_token': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA5MTc5NzkwIiwid2ViaG9va1VybCI6IiIsImlzcyI6ImRoYW4iLCJleHAiOjE3NTgzNDMwMjB9.__nkz5GImpMsYgxdI3YT31gR46vWVL7s1R4Ujr8gm0IEEw02AOEP6j7mDh9StBLGLjKubOGuw8cZeGhAYKyZtQ',
    'base_url': 'https://api.dhan.co',  # Sandbox URL
    'api_version': 'v2'
}

# Trading Configuration
TRADING_CONFIG = {
    'exchange': 'NSE',
    'product_type': 'MIS',  # MIS for intraday, CNC for delivery
    'order_type': 'MARKET',  # MARKET, LIMIT, SL, SL-M
    'validity': 'DAY',
    'initial_cash': 500000.0,  # ₹5 lakh for paper trading
    'commission': 0.001,  # 0.1% commission
}

# Data Configuration
DATA_CONFIG = {
    'timeframe': '1minute',  # 1minute, 5minute, 15minute, 1hour, 1day
    'historical_days': 30,   # Days of historical data to fetch
    'live_data': False,      # Set to True during market hours
}

# Symbols for Trading (Dhan format)
TRADING_SYMBOLS = {
    'RELIANCE': {
        'symbol': 'RELIANCE',
        'exchange': 'NSE',
        'instrument_token': '2885',  # Dhan instrument token for RELIANCE
        'lot_size': 1
    },
    'TCS': {
        'symbol': 'TCS', 
        'exchange': 'NSE',
        'instrument_token': '11536',  # Dhan instrument token for TCS
        'lot_size': 1
    },
    'INFY': {
        'symbol': 'INFY',
        'exchange': 'NSE', 
        'instrument_token': '1594',   # Dhan instrument token for INFY
        'lot_size': 1
    }
}

# Strategy Parameters
STRATEGY_CONFIG = {
    'fast_ma_period': 10,
    'slow_ma_period': 30,
    'rsi_period': 14,
    'position_size': 1,  # Number of shares per trade
    'max_positions': 3,  # Maximum number of concurrent positions
    'debug': True
}

# API Endpoints (Dhan Sandbox)
DHAN_ENDPOINTS = {
    'base_url': DHAN_CONFIG['base_url'],
    'orders': f"{DHAN_CONFIG['base_url']}/orders",
    'positions': f"{DHAN_CONFIG['base_url']}/positions", 
    'holdings': f"{DHAN_CONFIG['base_url']}/holdings",
    'funds': f"{DHAN_CONFIG['base_url']}/fundlimit",
    'historical_data': f"{DHAN_CONFIG['base_url']}/charts/historical",
    'live_feeds': f"{DHAN_CONFIG['base_url']}/marketfeed/ltp"
}

def get_dhan_headers():
    """Get headers for Dhan API requests"""
    return {
        'access-token': DHAN_CONFIG['access_token'],
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def print_config():
    """Print current configuration"""
    print("🔧 Dhan-Backtrader Configuration")
    print("=" * 40)
    print(f"Client ID: {DHAN_CONFIG['client_id']}")
    print(f"Base URL: {DHAN_CONFIG['base_url']}")
    print(f"Exchange: {TRADING_CONFIG['exchange']}")
    print(f"Product: {TRADING_CONFIG['product_type']}")
    print(f"Initial Cash: ₹{TRADING_CONFIG['initial_cash']:,.2f}")
    print(f"Commission: {TRADING_CONFIG['commission']*100}%")
    print(f"Trading Symbols: {list(TRADING_SYMBOLS.keys())}")
    print(f"Timeframe: {DATA_CONFIG['timeframe']}")
    print(f"Live Data: {DATA_CONFIG['live_data']}")

if __name__ == '__main__':
    print_config()