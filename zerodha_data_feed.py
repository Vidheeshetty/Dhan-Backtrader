import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from zerodha_config import ZERODHA_CONFIG, DATA_CONFIG, ZERODHA_INSTRUMENTS, TIMEFRAME_MAP

class ZerodhaData(bt.feeds.PandasData):
    """
    Custom Backtrader Data Feed that gets data from Zerodha KiteConnect API
    Supports both historical and live data
    """
    
    params = (
        ('symbol', ''),
        ('timeframe', DATA_CONFIG['timeframe']),
        ('historical_days', DATA_CONFIG['historical_days']),
        ('live', DATA_CONFIG['live_data']),
    )
    
    def __init__(self):
        self.kite = None
        self.instrument_info = None
        
        # Initialize KiteConnect if we have access token
        if ZERODHA_CONFIG['access_token']:
            try:
                self.kite = KiteConnect(api_key=ZERODHA_CONFIG['api_key'])
                self.kite.set_access_token(ZERODHA_CONFIG['access_token'])
                print(f"Data feed connected to Zerodha API")
            except Exception as e:
                print(f"Data feed API connection failed: {e}")
        
        print(f"ZerodhaData initialized for {self.p.symbol}")
        print(f"   Timeframe: {self.p.timeframe}")
        print(f"   Historical Days: {self.p.historical_days}")
        print(f"   Live Data: {self.p.live}")
        
        # Get instrument information
        self._get_instrument_info()
        
        # Fetch historical data
        historical_data = self._fetch_historical_data()
        if historical_data is not None and not historical_data.empty:
            self.p.dataname = historical_data
            print(f"Loaded {len(historical_data)} bars of historical data")
        else:
            print("No historical data loaded - creating sample data")
            self.p.dataname = self._create_sample_data()
        
        super(ZerodhaData, self).__init__()
    
    def _get_instrument_info(self):
        """Get instrument information from config"""
        if self.p.symbol in ZERODHA_INSTRUMENTS:
            self.instrument_info = ZERODHA_INSTRUMENTS[self.p.symbol]
            print(f"Instrument info found: {self.instrument_info}")
        else:
            print(f"Warning: Symbol {self.p.symbol} not in config")
            self.instrument_info = None
    
    def _fetch_historical_data(self):
        """Fetch historical data from Zerodha API"""
        if not self.kite or not self.instrument_info:
            print("Cannot fetch historical data: API not available or invalid symbol")
            return None
        
        try:
            print(f"Fetching historical data for {self.p.symbol}...")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.p.historical_days)
            
            print(f"   Date range: {start_date.date()} to {end_date.date()}")
            print(f"   Timeframe: {self.p.timeframe}")
            
            # Get Zerodha timeframe
            kite_timeframe = TIMEFRAME_MAP.get(self.p.timeframe, '5minute')
            
            # Fetch data
            historical_data = self.kite.historical_data(
                instrument_token=self.instrument_info['instrument_token'],
                from_date=start_date,
                to_date=end_date,
                interval=kite_timeframe
            )
            
            if not historical_data:
                print("No historical data returned from API")
                return None
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(historical_data)
            
            # Rename columns to match Backtrader format
            column_mapping = {
                'date': 'datetime',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure datetime column is datetime type
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            # Sort by datetime
            df.sort_index(inplace=True)
            
            # Remove any duplicate timestamps
            df = df[~df.index.duplicated(keep='first')]
            
            print(f"Successfully fetched {len(df)} bars from Zerodha API")
            print(f"   Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
            print(f"   Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"Failed to fetch historical data: {e}")
            return None
    
    def _create_sample_data(self):
        """Create sample data when API data is not available"""
        print(f"Creating sample data for {self.p.symbol}...")
        
        import numpy as np
        
        # Generate date range based on timeframe
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.p.historical_days)
        
        # Create appropriate frequency
        freq_map = {
            'minute': '1min',
            '5minute': '5min',
            '15minute': '15min',
            'hour': '1H',
            'day': 'D'
        }
        
        freq = freq_map.get(self.p.timeframe, '5min')
        
        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Filter to trading hours for intraday data
        if freq != 'D':
            dates = dates[(dates.hour >= 9) & (dates.hour < 16)]
            # Further filter to market hours (9:15 AM to 3:30 PM)
            dates = dates[
                ((dates.hour == 9) & (dates.minute >= 15)) |
                ((dates.hour > 9) & (dates.hour < 15)) |
                ((dates.hour == 15) & (dates.minute <= 30))
            ]
        
        # Limit number of bars
        dates = dates[-500:] if len(dates) > 500 else dates
        
        # Generate realistic price data based on symbol
        np.random.seed(42)
        
        base_prices = {
            'RELIANCE': 2450,
            'TCS': 3200, 
            'INFY': 1800,
            'HDFCBANK': 1650,
            'ICICIBANK': 950
        }
        
        base_price = base_prices.get(self.p.symbol, 1500)
        volatility = 0.02 if freq == 'D' else 0.005  # Lower volatility for intraday
        
        # Generate price series with random walk
        returns = np.random.normal(0, volatility/np.sqrt(252 if freq == 'D' else 252*78), len(dates))
        log_returns = np.cumsum(returns)
        prices = base_price * np.exp(log_returns)
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Generate realistic OHLC
            open_price = close * (1 + np.random.normal(0, 0.001))
            high_mult = 1 + abs(np.random.normal(0, 0.003))
            low_mult = 1 - abs(np.random.normal(0, 0.003))
            
            high = max(open_price, close) * high_mult
            low = min(open_price, close) * low_mult
            
            # Ensure OHLC consistency
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # Generate volume
            if freq == 'D':
                volume = int(np.random.lognormal(15, 0.5))  # Daily volume
            else:
                volume = int(np.random.lognormal(11, 0.8))  # Intraday volume
            
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
        
        print(f"Created {len(df)} bars of sample data")
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
        
        # Check market hours (9:15 AM to 3:30 PM IST)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def _get_live_data(self):
        """Get live data from Zerodha API (for live feeds)"""
        if not self.kite or not self.instrument_info:
            return None
        
        try:
            # Get latest quote
            quote = self.kite.quote([self.instrument_info['instrument_token']])
            
            if quote:
                instrument_token = str(self.instrument_info['instrument_token'])
                if instrument_token in quote:
                    data = quote[instrument_token]
                    return {
                        'open': data['ohlc']['open'],
                        'high': data['ohlc']['high'],
                        'low': data['ohlc']['low'],
                        'close': data['last_price'],
                        'volume': data['volume']
                    }
            
            return None
            
        except Exception as e:
            print(f"Failed to get live data: {e}")
            return None

# Test the data feed
if __name__ == '__main__':
    print("Testing ZerodhaData Feed")
    
    # Test with RELIANCE
    data_feed = ZerodhaData(
        symbol='RELIANCE',
        timeframe='5minute',
        historical_days=5,
        live=False
    )
    
    print("ZerodhaData test completed")