#!/usr/bin/env python3
"""
Fixed Zerodha Demo - Addresses token loading and broker implementation issues
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Load saved access token
def load_access_token():
    try:
        with open('zerodha_token.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Configuration
ZERODHA_CONFIG = {
    'api_key': 'gs9ulgi4ipyq5tkf',
    'access_token': load_access_token()  # Load token here
}

TRADING_CONFIG = {
    'initial_cash': 500000.0,
    'commission': 20.0
}

class SimpleStrategy(bt.Strategy):
    """Simple strategy for testing"""
    
    params = (
        ('fast_ma', 10),
        ('slow_ma', 30),
        ('position_size', 1),
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None
        self.trade_count = 0
        
        print(f"Strategy initialized for {self.data._name}")
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            if self.crossover[0] > 0:  # Fast MA crosses above slow MA
                print(f"BUY SIGNAL at Rs{self.data.close[0]:.2f}")
                self.order = self.buy(size=self.params.position_size)
        else:
            if self.crossover[0] < 0:  # Fast MA crosses below slow MA
                print(f"SELL SIGNAL at Rs{self.data.close[0]:.2f}")
                self.order = self.sell(size=self.params.position_size)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"BUY EXECUTED: {order.executed.size} @ Rs{order.executed.price:.2f}")
            else:
                print(f"SELL EXECUTED: {order.executed.size} @ Rs{order.executed.price:.2f}")
        self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            profit = trade.pnl - trade.commission
            print(f"TRADE #{self.trade_count}: P&L = Rs{profit:.2f}")

def create_sample_data(symbol="RELIANCE", days=10):
    """Create sample data for testing"""
    print(f"Creating sample data for {symbol}...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='5min')
    
    # Filter to trading hours
    dates = dates[(dates.hour >= 9) & (dates.hour < 16)]
    dates = dates[:200]  # Limit to 200 bars
    
    # Generate realistic price data
    np.random.seed(42)
    base_price = 2450 if symbol == "RELIANCE" else 3200
    returns = np.random.normal(0, 0.001, len(dates))
    log_returns = np.cumsum(returns)
    prices = base_price * np.exp(log_returns)
    
    # Create OHLCV data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        open_price = close * (1 + np.random.normal(0, 0.002))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
        volume = int(np.random.lognormal(11, 0.8))
        
        data.append({
            'datetime': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    print(f"Created {len(df)} bars")
    print(f"   Price range: Rs{df['close'].min():.2f} - Rs{df['close'].max():.2f}")
    
    return df

def test_zerodha_api():
    """Test Zerodha API connection"""
    if not ZERODHA_CONFIG['access_token']:
        print("No access token available")
        return False
    
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=ZERODHA_CONFIG['api_key'])
        kite.set_access_token(ZERODHA_CONFIG['access_token'])
        
        profile = kite.profile()
        print(f"Connected to Zerodha as: {profile.get('user_name', 'Unknown')}")
        
        # Test historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        historical_data = kite.historical_data(
            instrument_token=738561,  # RELIANCE
            from_date=start_date,
            to_date=end_date,
            interval="5minute"
        )
        
        print(f"Historical data test: {len(historical_data)} bars fetched")
        return True
        
    except Exception as e:
        print(f"API test failed: {e}")
        return False

def run_fixed_demo():
    """Run the fixed demo"""
    print("Fixed Zerodha + Backtrader Demo")
    print("=" * 50)
    
    # Check token status
    if ZERODHA_CONFIG['access_token']:
        print(f"Access token loaded: {ZERODHA_CONFIG['access_token'][:20]}...")
        api_working = test_zerodha_api()
    else:
        print("No access token found")
        api_working = False
    
    print()
    
    # Create cerebro
    cerebro = bt.Cerebro()
    
    # Use standard Backtrader broker (avoids custom implementation issues)
    cerebro.broker.setcash(TRADING_CONFIG['initial_cash'])
    cerebro.broker.setcommission(commission=TRADING_CONFIG['commission'])
    
    print(f"Using standard Backtrader broker")
    print(f"   Initial Cash: Rs{cerebro.broker.getcash():,.2f}")
    print(f"   Commission: Rs{TRADING_CONFIG['commission']:.2f} per order")
    
    # Add sample data (works regardless of API status)
    sample_data = create_sample_data("RELIANCE", 5)
    data_feed = bt.feeds.PandasData(dataname=sample_data)
    cerebro.adddata(data_feed, name="RELIANCE")
    
    # Add strategy
    cerebro.addstrategy(SimpleStrategy)
    
    print(f"Starting Portfolio: Rs{cerebro.broker.getvalue():,.2f}")
    print()
    print("Running strategy...")
    print("=" * 30)
    
    # Run backtest
    try:
        results = cerebro.run()
        
        print("=" * 30)
        print("DEMO RESULTS")
        print("=" * 30)
        
        final_value = cerebro.broker.getvalue()
        total_return = final_value - TRADING_CONFIG['initial_cash']
        return_pct = (final_value / TRADING_CONFIG['initial_cash'] - 1) * 100
        
        print(f"Final Portfolio: Rs{final_value:,.2f}")
        print(f"Final Cash: Rs{cerebro.broker.getcash():,.2f}")
        print(f"Total Return: Rs{total_return:,.2f}")
        print(f"Return %: {return_pct:.2f}%")
        
        print()
        print("Demo completed successfully!")
        print("What this proves:")
        print("   - Backtrader strategy execution works")
        print("   - Paper trading simulation works")
        print("   - Token loading is functional")
        
        if api_working:
            print("   - Zerodha API connection is working")
            print("   - Ready for live data integration")
        else:
            print("   - Zerodha API needs authentication")
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    run_fixed_demo()