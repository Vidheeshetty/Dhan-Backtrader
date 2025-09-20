import backtrader as bt
import pandas as pd
import requests
from datetime import datetime, timedelta
from dhan_config import DHAN_CONFIG, DATA_CONFIG, TRADING_SYMBOLS, get_dhan_headers
from dhanhq import dhanhq

class DhanData(bt.feeds.PandasData):
    """
    Custom Backtrader Data Feed that gets data from Dhan API
    Supports both historical and live data
    """
    
    params = (
        ('symbol', ''),           # Trading symbol (e.g., 'RELIANCE')
        ('exchange', 'NSE'),      # Exchange 
        ('timeframe', '1minute'), # Timeframe
        ('historical_days', 30),  # Days of historical data
        ('live', False),          # Enable live data
    )
    
    def __init__(self):
        # Initialize Dhan client
        self.dhan = dhanhq(
            client_id=DHAN_CONFIG['client_id'],
            access_token=DHAN_CONFIG['access_token']
        )
        
        self.symbol_info = None
        self.data_loaded = False
        
        print(f"📊 DhanData initialized for {self.p.symbol}")
        print(f"   Exchange: {self.p.exchange}")
        print(f"   Timeframe: {self.p.timeframe}")
        print(f"   Historical Days: {self.p.historical_days}")
        print(f"   Live Data: {self.p.live}")
        
        # Get symbol information
        self._get_symbol_info()
        
        # Load historical data
        historical_data = self._fetch_historical_data()
        if historical_data is not None and not historical_data.empty:
            # Set the dataname for PandasData
            self.p.dataname = historical_data
            print(f"✅ Loaded {len(historical_data)} bars of historical data")
        else:
            print("❌ No historical data loaded - will create sample data")
            self.p.dataname = self._create_sample_data()
        
        super(DhanData, self).__init__()
    
    def _get_symbol_info(self):
        """Get symbol information from config"""
        if self.p.symbol in TRADING_SYMBOLS:
            self.symbol_info = TRADING_SYMBOLS[self.p.symbol]
            print(f"✅ Symbol info found: {self.symbol_info}")
        else:
            print(f"⚠️ Symbol {self.p.symbol} not in config, using defaults")
            self.symbol_info = {
                'symbol': self.p.symbol,
                'exchange': self.p.exchange,
                'instrument_token': '0',
                'lot_size': 1
            }
    
    def _fetch_historical_data(self):
        """Fetch historical data from Dhan API"""
        try:
            print(f"📈 Fetching historical data for {self.p.symbol}...")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.p.historical_days)
            
            # Format dates for Dhan API
            from_date = start_date.strftime('%Y-%m-%d')
            to_date = end_date.strftime('%Y-%m-%d')
            
            print(f"   Date range: {from_date} to {to_date}")
            
            # Map timeframe to Dhan format
            timeframe_map = {
                '1minute': '1',
                '5minute': '5', 
                '15minute': '15',
                '1hour': '60',
                '1day': 'D'
            }
            
            dhan_timeframe = timeframe_map.get(self.p.timeframe, '1')
            
            # Get instrument token
            instrument_token = self.symbol_info.get('instrument_token', '0')
            
            if instrument_token == '0':
                print("⚠️ No instrument token, creating sample data instead")
                return None
            
            # Fetch data using Dhan SDK
            response = self.dhan.historical_minute_charts(
                symbol=self.p.symbol,
                exchange_segment=self.p.exchange,
                instrument_type='EQUITY',
                expiry_code=0,
                from_date=from_date,
                to_date=to_date
            )
            
            if response['status'] == 'success' and 'data' in response:
                data = response['data']
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(data)
                
                # Rename columns to match Backtrader format
                column_mapping = {
                    'timestamp': 'datetime',
                    'open': 'open',
                    'high': 'high', 
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                }
                
                df = df.rename(columns=column_mapping)
                
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                
                # Sort by datetime
                df.sort_index(inplace=True)
                
                print(f"✅ Fetched {len(df)} bars from Dhan API")
                return df
                
            else:
                print(f"⚠️ Dhan API response: {response}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to fetch historical data: {e}")
            return None
    
    def _create_sample_data(self):
        """Create sample data when API data is not available"""
        print("📊 Creating sample data for testing...")
        
        # Generate sample data
        import numpy as np
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.p.historical_days)
        
        # Create minute-by-minute data for specified timeframe
        if self.p.timeframe == '1minute':
            freq = '1min'
            periods = self.p.historical_days * 6.5 * 60  # Trading hours per day
        elif self.p.timeframe == '5minute':
            freq = '5min'
            periods = self.p.historical_days * 6.5 * 12
        elif self.p.timeframe == '15minute':
            freq = '15min'
            periods = self.p.historical_days * 6.5 * 4
        elif self.p.timeframe == '1hour':
            freq = '1H'
            periods = self.p.historical_days * 6.5
        else:  # 1day
            freq = 'D'
            periods = self.p.historical_days
        
        # Generate date range
        dates = pd.date_range(start=start_date, periods=int(periods), freq=freq)
        
        # Filter to trading hours (9:15 AM to 3:30 PM)
        if freq != 'D':
            dates = dates[(dates.hour >= 9) & (dates.hour < 15) | 
                         ((dates.hour == 9) & (dates.minute >= 15)) |
                         ((dates.hour == 15) & (dates.minute <= 30))]
        
        # Generate realistic price data
        np.random.seed(42)
        
        # Base price based on symbol
        if self.p.symbol == 'RELIANCE':
            base_price = 2450
            volatility = 0.02
        elif self.p.symbol == 'TCS':
            base_price = 3200
            volatility = 0.015
        elif self.p.symbol == 'INFY':
            base_price = 1800
            volatility = 0.018
        else:
            base_price = 1500
            volatility = 0.025
        
        # Generate price series with random walk
        returns = np.random.normal(0, volatility/np.sqrt(252*78), len(dates))  # Adjust for intraday
        log_returns = np.cumsum(returns)
        prices = base_price * np.exp(log_returns)
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            open_price = close * (1 + np.random.normal(0, 0.002))
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
            volume = int(np.random.lognormal(11, 0.8))  # Realistic volume
            
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
        
        print(f"✅ Created {len(df)} bars of sample data")
        print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        
        return df
    
    def islive(self):
        """Return True if this is live data"""
        return self.p.live
    
    def haslivedata(self):
        """Return True if live data is available"""
        return self.p.live and self._is_market_open()
    
    def _is_market_open(self):
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check market hours (9:15 AM to 3:30 PM)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close

# Test the data feed
if __name__ == '__main__':
    print("🧪 Testing DhanData Feed")
    
    # Test with RELIANCE
    data_feed = DhanData(
        symbol='RELIANCE',
        exchange='NSE',
        timeframe='1minute',
        historical_days=5,
        live=False
    )
    
    print("✅ DhanData test completed")