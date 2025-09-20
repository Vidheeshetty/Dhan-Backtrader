#!/usr/bin/env python3
"""
Complete Zerodha + Backtrader Integration Demo
Shows backtesting and paper trading capabilities
"""

import backtrader as bt
import sys
from datetime import datetime
from zerodha_config import ZERODHA_CONFIG, TRADING_CONFIG, STRATEGY_CONFIG, print_config
from zerodha_broker import ZerodhaBroker
from zerodha_data_feed import ZerodhaData

class ZerodhaTradingStrategy(bt.Strategy):
    """
    Moving Average Crossover Strategy with RSI confirmation
    """
    
    params = (
        ('fast_ma', STRATEGY_CONFIG['fast_ma_period']),
        ('slow_ma', STRATEGY_CONFIG['slow_ma_period']),
        ('rsi_period', STRATEGY_CONFIG['rsi_period']),
        ('position_size', STRATEGY_CONFIG['position_size']),
        ('debug', STRATEGY_CONFIG['debug']),
    )
    
    def __init__(self):
        # Technical indicators
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma
        )
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.params.rsi_period
        )
        
        # Crossover signal
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # Order and trade tracking
        self.order = None
        self.trade_count = 0
        self.bar_count = 0
        
        if self.params.debug:
            print(f"Strategy initialized for {self.data._name}")
            print(f"   Fast MA: {self.params.fast_ma} periods")
            print(f"   Slow MA: {self.params.slow_ma} periods")
            print(f"   RSI: {self.params.rsi_period} periods")
            print(f"   Position Size: {self.params.position_size}")
    
    def next(self):
        self.bar_count += 1
        
        # Skip if we have a pending order
        if self.order:
            return
        
        # Print status every 50 bars
        if self.bar_count % 50 == 0 and self.params.debug:
            self.print_status()
        
        # Trading logic
        current_position = self.position.size
        
        # Entry signals
        if not current_position:  # No position
            # Buy signal: Fast MA crosses above Slow MA + RSI not overbought
            if (self.crossover[0] > 0 and 
                self.rsi[0] < 70 and 
                len(self.data) > self.params.slow_ma):
                
                self.log_signal("BUY", f"MA Cross + RSI={self.rsi[0]:.1f}")
                self.order = self.buy(size=self.params.position_size)
        
        else:  # Have position
            # Exit signals
            exit_condition = False
            exit_reason = ""
            
            # Exit on MA cross down
            if self.crossover[0] < 0:
                exit_condition = True
                exit_reason = "MA Cross Down"
            
            # Exit on RSI overbought
            elif self.rsi[0] > 80:
                exit_condition = True
                exit_reason = f"RSI Overbought ({self.rsi[0]:.1f})"
            
            if exit_condition:
                self.log_signal("SELL", exit_reason)
                self.order = self.sell(size=self.params.position_size)
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED")
                self.log(f"   Price: Rs{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: Rs{order.executed.comm:.2f}")
            else:
                self.log(f"SELL EXECUTED")
                self.log(f"   Price: Rs{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: Rs{order.executed.comm:.2f}")
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"ORDER {order.status}")
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            self.trade_count += 1
            profit = trade.pnl - trade.commission
            
            self.log(f"TRADE #{self.trade_count} CLOSED")
            self.log(f"   Gross P&L: Rs{trade.pnl:.2f}")
            self.log(f"   Commission: Rs{trade.commission:.2f}")
            self.log(f"   Net P&L: Rs{profit:.2f}")
            
            if trade.price > 0:
                roi = (profit / (trade.size * trade.price)) * 100
                self.log(f"   ROI: {roi:.2f}%")
    
    def log_signal(self, signal_type, reason):
        """Log trading signals"""
        self.log(f"{signal_type} SIGNAL")
        self.log(f"   Reason: {reason}")
        self.log(f"   Price: Rs{self.data.close[0]:.2f}")
        self.log(f"   Fast MA: Rs{self.fast_ma[0]:.2f}")
        self.log(f"   Slow MA: Rs{self.slow_ma[0]:.2f}")
        self.log(f"   RSI: {self.rsi[0]:.1f}")
    
    def print_status(self):
        """Print current status"""
        self.log(f"Status Update (Bar {self.bar_count})")
        self.log(f"   Date: {self.data.datetime.datetime(0)}")
        self.log(f"   Price: Rs{self.data.close[0]:.2f}")
        self.log(f"   Position: {self.position.size}")
        self.log(f"   Cash: Rs{self.broker.getcash():.2f}")
    
    def log(self, txt):
        """Logging function"""
        if self.params.debug:
            dt = self.data.datetime.datetime(0)
            print(f"[{dt.strftime('%Y-%m-%d %H:%M')}] {txt}")

def check_authentication():
    """Check if we have valid Zerodha authentication"""
    if not ZERODHA_CONFIG['access_token']:
        print("No access token found")
        print("Run: python zerodha_auth.py")
        return False
    
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=ZERODHA_CONFIG['api_key'])
        kite.set_access_token(ZERODHA_CONFIG['access_token'])
        profile = kite.profile()
        print(f"Authenticated as: {profile.get('user_name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Run: python zerodha_auth.py")
        return False

def run_zerodha_demo():
    """Run the complete Zerodha + Backtrader demo"""
    
    print("Zerodha + Backtrader Demo")
    print("=" * 50)
    
    # Print configuration
    print_config()
    print()
    
    # Check authentication
    auth_ok = check_authentication()
    
    # Create Cerebro
    cerebro = bt.Cerebro()
    
    # Add Zerodha broker
    print("Setting up Zerodha Broker...")
    zerodha_broker = ZerodhaBroker(paper_trading=True)  # Start with paper trading
    cerebro.setbroker(zerodha_broker)
    
    # Add data feeds
    symbols_to_trade = ['RELIANCE', 'TCS']  # Start with two symbols
    
    for symbol in symbols_to_trade:
        print(f"Adding data feed for {symbol}...")
        
        data_feed = ZerodhaData(
            symbol=symbol,
            timeframe='5minute',
            historical_days=10,
            live=False  # Use historical data for demo
        )
        
        cerebro.adddata(data_feed, name=symbol)
    
    # Add strategy
    print("Adding trading strategy...")
    cerebro.addstrategy(ZerodhaTradingStrategy,
                       fast_ma=10,
                       slow_ma=30,
                       rsi_period=14,
                       position_size=1,
                       debug=True)
    
    print(f"Initial Portfolio Value: Rs{cerebro.broker.getvalue():,.2f}")
    print(f"Initial Cash: Rs{cerebro.broker.getcash():,.2f}")
    
    print("Running trading simulation...")
    print("=" * 50)
    
    # Run the backtest
    try:
        results = cerebro.run()
        strategy = results[0]
        
        # Print results
        print("=" * 50)
        print("TRADING RESULTS")
        print("=" * 50)
        
        final_value = cerebro.broker.getvalue()
        initial_value = TRADING_CONFIG['initial_cash']
        total_return = final_value - initial_value
        return_pct = (final_value / initial_value - 1) * 100
        
        print(f"Final Portfolio Value: Rs{final_value:,.2f}")
        print(f"Final Cash: Rs{cerebro.broker.getcash():,.2f}")
        print(f"Total Return: Rs{total_return:,.2f}")
        print(f"Return Percentage: {return_pct:.2f}%")
        
        print("Demo completed successfully!")
        print("What this demonstrates:")
        print("   - Zerodha API integration with Backtrader")
        print("   - Historical data fetching from Zerodha")
        print("   - Custom broker for paper trading")
        print("   - Complete strategy execution")
        print("   - Portfolio tracking and P&L calculation")
        
        print("Ready for live trading:")
        print("   - During market hours: Enable live data")
        print("   - Switch paper_trading=False for real orders")
        print("   - Monitor positions in Zerodha app")
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    try:
        success = run_zerodha_demo()
        
        if success:
            print("Demo completed successfully!")
        else:
            print("Demo had issues - check error messages above")
            
    except KeyboardInterrupt:
        print("Demo interrupted by user")
    except Exception as e:
        print(f"Demo crashed: {e}")