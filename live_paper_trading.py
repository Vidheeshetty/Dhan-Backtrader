#!/usr/bin/env python3
"""
Complete Live Paper Trading System using Zerodha + Backtrader
Uses real-time market data with simulated order execution
"""

import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import threading
import time
import queue

# Load your access token
def load_access_token():
    try:
        with open('zerodha_token.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Configuration
CONFIG = {
    'api_key': 'gs9ulgi4ipyq5tkf',
    'access_token': load_access_token(),
    'symbols': {
        'RELIANCE': 738561,
        'TCS': 2953217,
        'INFY': 408065,
        'HDFCBANK': 341249,
        'ICICIBANK': 1270529
    },
    'initial_cash': 500000.0,
    'commission_per_order': 20.0,
    'slippage_percent': 0.05,  # 0.05% slippage
    'historical_days': 5
}

class LiveDataFeed(bt.feeds.PandasData):
    """
    Live data feed that gets real-time data from Zerodha
    """
    
    def __init__(self, symbol, kite):
        self.symbol = symbol
        self.kite = kite
        self.instrument_token = CONFIG['symbols'][symbol]
        self.live_data_queue = queue.Queue()
        self.is_live = False
        
        # Get initial historical data
        historical_data = self._get_historical_data()
        
        if historical_data is not None:
            super(LiveDataFeed, self).__init__(dataname=historical_data)
            print(f"Loaded {len(historical_data)} historical bars for {symbol}")
        else:
            # Fallback to sample data
            sample_data = self._create_sample_data()
            super(LiveDataFeed, self).__init__(dataname=sample_data)
            print(f"Using sample data for {symbol}")
    
    def _get_historical_data(self):
        """Fetch historical data from Zerodha"""
        if not self.kite:
            return None
            
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=CONFIG['historical_days'])
            
            data = self.kite.historical_data(
                instrument_token=self.instrument_token,
                from_date=start_date,
                to_date=end_date,
                interval="5minute"
            )
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['date'])
            df.set_index('datetime', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {self.symbol}: {e}")
            return None
    
    def _create_sample_data(self):
        """Create sample data as fallback"""
        import numpy as np
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=CONFIG['historical_days'])
        dates = pd.date_range(start=start_date, end=end_date, freq='5min')
        
        # Filter to trading hours
        dates = dates[(dates.hour >= 9) & (dates.hour < 16)]
        dates = dates[:100]  # Limit for demo
        
        np.random.seed(42)
        base_prices = {'RELIANCE': 2450, 'TCS': 3200, 'INFY': 1800, 'HDFCBANK': 1650, 'ICICIBANK': 950}
        base_price = base_prices.get(self.symbol, 1500)
        
        returns = np.random.normal(0, 0.001, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
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
        return df
    
    def start_live_feed(self):
        """Start live data feed in separate thread"""
        if not self.kite or not self._is_market_open():
            print(f"Market closed or no API - using historical data for {self.symbol}")
            return
        
        print(f"Starting live data feed for {self.symbol}")
        self.is_live = True
        thread = threading.Thread(target=self._live_data_worker)
        thread.daemon = True
        thread.start()
    
    def _live_data_worker(self):
        """Worker thread for live data"""
        while self.is_live:
            try:
                # Get latest quote
                quote = self.kite.quote([self.instrument_token])
                
                if quote and str(self.instrument_token) in quote:
                    data = quote[str(self.instrument_token)]
                    
                    live_bar = {
                        'datetime': datetime.now(),
                        'open': data['ohlc']['open'],
                        'high': data['ohlc']['high'],
                        'low': data['ohlc']['low'],
                        'close': data['last_price'],
                        'volume': data['volume']
                    }
                    
                    self.live_data_queue.put(live_bar)
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Error in live data feed for {self.symbol}: {e}")
                time.sleep(5)
    
    def _is_market_open(self):
        """Check if market is open"""
        now = datetime.now()
        
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close

class PaperTradingBroker(bt.brokers.BackBroker):
    """
    Enhanced paper trading broker with realistic fills
    """
    
    def __init__(self):
        super(PaperTradingBroker, self).__init__()
        
        # Set commission (fixed amount per order)
        self.setcommission(commission=0.0, stocklike=True, fixed=CONFIG['commission_per_order'])
        
        # Set initial cash
        self.setcash(CONFIG['initial_cash'])
        
        print(f"Paper Trading Broker initialized")
        print(f"   Initial Cash: Rs{self.getcash():,.2f}")
        print(f"   Commission: Rs{CONFIG['commission_per_order']:.2f} per order")
        print(f"   Slippage: {CONFIG['slippage_percent']}%")
    
    def _fill_price(self, order, price):
        """Apply realistic slippage to fills"""
        if order.isbuy():
            # Buy orders get slight slippage upward
            slippage = price * (CONFIG['slippage_percent'] / 100)
            return price + slippage
        else:
            # Sell orders get slight slippage downward
            slippage = price * (CONFIG['slippage_percent'] / 100)
            return price - slippage
    
    def submit(self, order):
        """Submit order with realistic fill simulation"""
        # Apply slippage to market orders
        if hasattr(order.created, 'price') and order.created.price is None:
            # Market order - use current price with slippage
            current_price = order.data.close[0]
            fill_price = self._fill_price(order, current_price)
            order.created.price = fill_price
        
        return super(PaperTradingBroker, self).submit(order)

class TradingStrategy(bt.Strategy):
    """
    Enhanced trading strategy for live paper trading
    """
    
    params = (
        ('fast_ma', 10),
        ('slow_ma', 30),
        ('rsi_period', 14),
        ('position_size', 5),  # Number of shares
        ('max_positions', 3),  # Max concurrent positions
        ('debug', True),
    )
    
    def __init__(self):
        # Technical indicators
        self.indicators = {}
        
        for data in self.datas:
            symbol = data._name
            
            self.indicators[symbol] = {
                'fast_ma': bt.indicators.SimpleMovingAverage(
                    data.close, period=self.params.fast_ma
                ),
                'slow_ma': bt.indicators.SimpleMovingAverage(
                    data.close, period=self.params.slow_ma
                ),
                'rsi': bt.indicators.RSI(
                    data.close, period=self.params.rsi_period
                ),
                'crossover': None
            }
            
            self.indicators[symbol]['crossover'] = bt.indicators.CrossOver(
                self.indicators[symbol]['fast_ma'],
                self.indicators[symbol]['slow_ma']
            )
        
        self.orders = {}
        self.trade_count = 0
        self.bar_count = 0
        
        if self.params.debug:
            print(f"Strategy initialized for {len(self.datas)} symbols")
            print(f"   Fast MA: {self.params.fast_ma}, Slow MA: {self.params.slow_ma}")
            print(f"   RSI: {self.params.rsi_period}, Position Size: {self.params.position_size}")
    
    def next(self):
        self.bar_count += 1
        
        # Print status every 20 bars
        if self.bar_count % 20 == 0 and self.params.debug:
            self.print_portfolio_status()
        
        # Check each symbol for trading opportunities
        for data in self.datas:
            symbol = data._name
            
            # Skip if we have pending order for this symbol
            if symbol in self.orders:
                continue
            
            self.check_trading_signals(data, symbol)
    
    def check_trading_signals(self, data, symbol):
        """Check for trading signals on a specific symbol"""
        indicators = self.indicators[symbol]
        position = self.getposition(data)
        
        # Entry signals
        if not position:
            # Buy signal: Fast MA crosses above Slow MA + RSI not overbought
            if (indicators['crossover'][0] > 0 and 
                indicators['rsi'][0] < 70 and 
                len(data) > self.params.slow_ma):
                
                # Check if we can take more positions
                active_positions = sum(1 for d in self.datas if self.getposition(d))
                
                if active_positions < self.params.max_positions:
                    self.log_signal(symbol, "BUY", f"MA Cross + RSI={indicators['rsi'][0]:.1f}")
                    self.orders[symbol] = self.buy(data=data, size=self.params.position_size)
        
        else:
            # Exit signals
            exit_condition = False
            exit_reason = ""
            
            if indicators['crossover'][0] < 0:
                exit_condition = True
                exit_reason = "MA Cross Down"
            elif indicators['rsi'][0] > 80:
                exit_condition = True
                exit_reason = f"RSI Overbought ({indicators['rsi'][0]:.1f})"
            
            if exit_condition:
                self.log_signal(symbol, "SELL", exit_reason)
                self.orders[symbol] = self.sell(data=data, size=self.params.position_size)
    
    def notify_order(self, order):
        """Handle order notifications"""
        symbol = order.data._name
        
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED - {symbol}")
                self.log(f"   Price: Rs{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: Rs{order.executed.comm:.2f}")
            else:
                self.log(f"SELL EXECUTED - {symbol}")
                self.log(f"   Price: Rs{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: Rs{order.executed.comm:.2f}")
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"ORDER {order.status} - {symbol}")
        
        # Clear order tracking
        if symbol in self.orders:
            del self.orders[symbol]
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            self.trade_count += 1
            symbol = trade.data._name
            profit = trade.pnl - trade.commission
            
            self.log(f"TRADE #{self.trade_count} CLOSED - {symbol}")
            self.log(f"   Gross P&L: Rs{trade.pnl:.2f}")
            self.log(f"   Commission: Rs{trade.commission:.2f}")
            self.log(f"   Net P&L: Rs{profit:.2f}")
            
            if trade.price > 0:
                roi = (profit / (abs(trade.size) * trade.price)) * 100
                self.log(f"   ROI: {roi:.2f}%")
    
    def log_signal(self, symbol, signal_type, reason):
        """Log trading signals"""
        data = None
        for d in self.datas:
            if d._name == symbol:
                data = d
                break
        
        if data:
            indicators = self.indicators[symbol]
            self.log(f"{signal_type} SIGNAL - {symbol}")
            self.log(f"   Reason: {reason}")
            self.log(f"   Price: Rs{data.close[0]:.2f}")
            self.log(f"   Fast MA: Rs{indicators['fast_ma'][0]:.2f}")
            self.log(f"   Slow MA: Rs{indicators['slow_ma'][0]:.2f}")
    
    def print_portfolio_status(self):
        """Print current portfolio status"""
        self.log(f"Portfolio Status (Bar {self.bar_count})")
        self.log(f"   Cash: Rs{self.broker.getcash():,.2f}")
        self.log(f"   Portfolio Value: Rs{self.broker.getvalue():,.2f}")
        
        positions = []
        for data in self.datas:
            position = self.getposition(data)
            if position.size != 0:
                positions.append(f"{data._name}: {position.size}@{position.price:.2f}")
        
        if positions:
            self.log(f"   Positions: {', '.join(positions)}")
    
    def log(self, txt):
        """Logging function"""
        if self.params.debug:
            dt = datetime.now()
            print(f"[{dt.strftime('%H:%M:%S')}] {txt}")

def setup_kite_connection():
    """Setup Zerodha KiteConnect"""
    if not CONFIG['access_token']:
        print("No access token found. Run: python zerodha_auth.py")
        return None
    
    try:
        kite = KiteConnect(api_key=CONFIG['api_key'])
        kite.set_access_token(CONFIG['access_token'])
        
        # Test connection
        profile = kite.profile()
        print(f"Connected to Zerodha as: {profile.get('user_name', 'Unknown')}")
        return kite
        
    except Exception as e:
        print(f"Zerodha connection failed: {e}")
        return None

def run_live_paper_trading():
    """Run the complete live paper trading system"""
    print("Live Paper Trading System")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Setup Zerodha connection
    kite = setup_kite_connection()
    
    # Create Cerebro
    cerebro = bt.Cerebro()
    
    # Setup paper trading broker
    broker = PaperTradingBroker()
    cerebro.setbroker(broker)
    
    # Add data feeds for multiple symbols
    symbols_to_trade = ['RELIANCE', 'TCS']  # Start with 2 symbols
    
    for symbol in symbols_to_trade:
        print(f"Setting up data feed for {symbol}...")
        data_feed = LiveDataFeed(symbol, kite)
        cerebro.adddata(data_feed, name=symbol)
        
        # Start live feed if market is open
        data_feed.start_live_feed()
    
    # Add strategy
    cerebro.addstrategy(TradingStrategy,
                       fast_ma=10,
                       slow_ma=30,
                       position_size=5,
                       debug=True)
    
    print(f"\nStarting Portfolio: Rs{cerebro.broker.getvalue():,.2f}")
    print("Running live paper trading...")
    print("=" * 50)
    
    try:
        results = cerebro.run()
        
        print("\n" + "=" * 50)
        print("PAPER TRADING SESSION COMPLETE")
        print("=" * 50)
        
        final_value = cerebro.broker.getvalue()
        total_return = final_value - CONFIG['initial_cash']
        return_pct = (final_value / CONFIG['initial_cash'] - 1) * 100
        
        print(f"Final Portfolio: Rs{final_value:,.2f}")
        print(f"Final Cash: Rs{cerebro.broker.getcash():,.2f}")
        print(f"Total Return: Rs{total_return:,.2f}")
        print(f"Return %: {return_pct:.2f}%")
        
        return True
        
    except KeyboardInterrupt:
        print("\nPaper trading stopped by user")
        return True
    except Exception as e:
        print(f"\nPaper trading failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    run_live_paper_trading()