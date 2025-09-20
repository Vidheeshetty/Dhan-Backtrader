#!/usr/bin/env python3
"""
Complete Dhan + Backtrader Integration Demo
This demonstrates paper trading using Dhan Sandbox API with Backtrader
"""

import backtrader as bt
import sys
from datetime import datetime
from dhan_config import DHAN_CONFIG, TRADING_CONFIG, STRATEGY_CONFIG, print_config
from dhan_broker import DhanBroker
from dhan_data_feed import DhanData

class DhanTradingStrategy(bt.Strategy):
    """
    Moving Average Crossover Strategy with RSI confirmation
    Designed for paper trading with Dhan Sandbox
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
            print(f"\n📊 Strategy initialized for {self.data._name}")
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
                len(self.data) > self.params.slow_ma):  # Ensure we have enough data
                
                self.log_signal("BUY", 
                              f"MA Cross + RSI={self.rsi[0]:.1f}")
                self.order = self.buy(size=self.params.position_size)
        
        else:  # Have position
            # Exit signals
            exit_condition = False
            exit_reason = ""
            
            # Exit on MA cross down
            if self.crossover[0] < 0:
                exit_condition = True
                exit_reason = f"MA Cross Down"
            
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
            return  # Order acknowledged
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"✅ BUY EXECUTED")
                self.log(f"   Price: ₹{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: ₹{order.executed.comm:.2f}")
                self.log(f"   Cash: ₹{self.broker.getcash():.2f}")
            else:
                self.log(f"✅ SELL EXECUTED")
                self.log(f"   Price: ₹{order.executed.price:.2f}")
                self.log(f"   Size: {order.executed.size}")
                self.log(f"   Commission: ₹{order.executed.comm:.2f}")
                self.log(f"   Cash: ₹{self.broker.getcash():.2f}")
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"❌ ORDER {order.status}")
        
        self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            self.trade_count += 1
            profit = trade.pnl - trade.commission
            
            self.log(f"💰 TRADE #{self.trade_count} CLOSED")
            self.log(f"   Gross P&L: ₹{trade.pnl:.2f}")
            self.log(f"   Commission: ₹{trade.commission:.2f}")
            self.log(f"   Net P&L: ₹{profit:.2f}")
            
            if trade.price > 0:
                roi = (profit / (trade.size * trade.price)) * 100
                self.log(f"   ROI: {roi:.2f}%")
    
    def log_signal(self, signal_type, reason):
        """Log trading signals"""
        self.log(f"\n🚨 {signal_type} SIGNAL")
        self.log(f"   Reason: {reason}")
        self.log(f"   Price: ₹{self.data.close[0]:.2f}")
        self.log(f"   Fast MA: ₹{self.fast_ma[0]:.2f}")
        self.log(f"   Slow MA: ₹{self.slow_ma[0]:.2f}")
        self.log(f"   RSI: {self.rsi[0]:.1f}")
        self.log(f"   Portfolio: ₹{self.broker.getvalue():.2f}")
    
    def print_status(self):
        """Print current status"""
        self.log(f"\n📊 Status Update (Bar {self.bar_count})")
        self.log(f"   Date: {self.data.datetime.datetime(0)}")
        self.log(f"   Price: ₹{self.data.close[0]:.2f}")
        self.log(f"   Position: {self.position.size}")
        self.log(f"   Cash: ₹{self.broker.getcash():.2f}")
        self.log(f"   Portfolio: ₹{self.broker.getvalue():.2f}")
    
    def log(self, txt):
        """Logging function"""
        if self.params.debug:
            dt = self.data.datetime.datetime(0)
            print(f"[{dt.strftime('%Y-%m-%d %H:%M')}] {txt}")

def run_dhan_backtrader_demo():
    """Run the complete Dhan + Backtrader demo"""
    
    print("🚀 Dhan + Backtrader Paper Trading Demo")
    print("=" * 60)
    
    # Print configuration
    print_config()
    print()
    
    # Create Cerebro
    cerebro = bt.Cerebro()
    
    # Add custom Dhan broker
    print("🏦 Setting up Dhan Broker...")
    dhan_broker = DhanBroker()
    cerebro.setbroker(dhan_broker)
    
    # Add data feeds for multiple symbols
    symbols_to_trade = ['RELIANCE']  # Start with one symbol
    
    for symbol in symbols_to_trade:
        print(f"\n📊 Adding data feed for {symbol}...")
        
        data_feed = DhanData(
            symbol=symbol,
            exchange='NSE',
            timeframe='5minute',  # Use 5-minute for faster demo
            historical_days=10,   # 10 days of data
            live=False           # Historical data for demo
        )
        
        cerebro.adddata(data_feed, name=symbol)
    
    # Add strategy
    print(f"\n📈 Adding trading strategy...")
    cerebro.addstrategy(DhanTradingStrategy,
                       fast_ma=10,
                       slow_ma=20,  # Shorter periods for demo
                       rsi_period=14,
                       position_size=5,  # Trade 5 shares at a time
                       debug=True)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    print(f"\n💰 Initial Portfolio Value: ₹{cerebro.broker.getvalue():,.2f}")
    print(f"💵 Initial Cash: ₹{cerebro.broker.getcash():,.2f}")
    
    print(f"\n🔄 Running paper trading simulation...")
    print("=" * 60)
    
    # Run the backtest
    try:
        results = cerebro.run()
        strategy = results[0]
        
        # Print results
        print("\n" + "=" * 60)
        print("📈 PAPER TRADING RESULTS")
        print("=" * 60)
        
        final_value = cerebro.broker.getvalue()
        initial_value = TRADING_CONFIG['initial_cash']
        total_return = final_value - initial_value
        return_pct = (final_value / initial_value - 1) * 100
        
        print(f"💰 Final Portfolio Value: ₹{final_value:,.2f}")
        print(f"💵 Final Cash: ₹{cerebro.broker.getcash():,.2f}")
        print(f"📊 Total Return: ₹{total_return:,.2f}")
        print(f"📈 Return Percentage: {return_pct:.2f}%")
        
        # Analyzer results
        print(f"\n📊 Performance Metrics:")
        
        try:
            trades_analysis = strategy.analyzers.trades.get_analysis()
            total_trades = trades_analysis.get('total', {}).get('total', 0)
            won_trades = trades_analysis.get('won', {}).get('total', 0)
            lost_trades = trades_analysis.get('lost', {}).get('total', 0)
            
            print(f"🔄 Total Trades: {total_trades}")
            print(f"✅ Winning Trades: {won_trades}")
            print(f"❌ Losing Trades: {lost_trades}")
            
            if total_trades > 0:
                win_rate = (won_trades / total_trades) * 100
                print(f"🎯 Win Rate: {win_rate:.1f}%")
        except:
            print("🔄 Trade analysis not available")
        
        try:
            drawdown = strategy.analyzers.drawdown.get_analysis()
            print(f"📉 Max Drawdown: {drawdown['max']['drawdown']:.2f}%")
        except:
            print("📉 Drawdown analysis not available")
        
        print(f"\n" + "=" * 60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print(f"\n✅ What this demo showed:")
        print(f"   ✅ Direct Dhan Sandbox integration with Backtrader")
        print(f"   ✅ Custom broker handling paper trading orders")
        print(f"   ✅ Custom data feed providing market data")
        print(f"   ✅ Complete strategy execution and tracking")
        print(f"   ✅ Portfolio management and P&L calculation")
        
        print(f"\n🚀 Ready for live paper trading:")
        print(f"   📊 During market hours: Use live data feeds")
        print(f"   🔄 Real-time order execution via Dhan Sandbox")
        print(f"   📈 Multiple strategies and symbols")
        print(f"   🎯 Risk management and position sizing")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_dhan_connection():
    """Test Dhan API connection before running demo"""
    print("🔍 Testing Dhan API Connection...")
    
    try:
        from dhanhq import dhanhq
        
        dhan = dhanhq(
            client_id=DHAN_CONFIG['client_id'],
            access_token=DHAN_CONFIG['access_token']
        )
        
        response = dhan.get_fund_limits()
        
        if response['status'] == 'success':
            print("✅ Dhan API connection successful")
            return True
        else:
            print(f"⚠️ Dhan API response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Dhan API connection failed: {e}")
        print("   This is okay for demo - we'll use sample data")
        return False

if __name__ == '__main__':
    try:
        # Test connection first
        api_working = test_dhan_connection()
        
        if api_working:
            print("🎯 Using live Dhan API for demo")
        else:
            print("🎯 Using sample data for demo")
        
        print()
        
        # Run the demo
        success = run_dhan_backtrader_demo()
        
        if success:
            print(f"\n🎉 Demo completed successfully!")
            print(f"📝 You now have a working Dhan + Backtrader setup!")
        else:
            print(f"\n⚠️ Demo had issues - check the error messages above")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo crashed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")