#!/usr/bin/env python3
"""
TRULY Fixed Demo - Corrects the commission setup issue
The problem was using 'fixed' parameter which doesn't exist in default broker
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
from pathlib import Path

# Load saved access token
def load_access_token():
    try:
        with open('zerodha_token.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Configuration (using your working setup)
ZERODHA_CONFIG = {
    'api_key': 'gs9ulgi4ipyq5tkf',
    'access_token': load_access_token()
}

TRADING_CONFIG = {
    'initial_cash': 500000.0,
    'commission': 20.0  # Fixed Rs 20 per order
}

class FixedCommissionInfo(bt.CommInfoBase):
    """
    Custom commission class for fixed Rs 20 per order
    This is the CORRECT way to set fixed commission in Backtrader
    """
    
    def __init__(self):
        super(FixedCommissionInfo, self).__init__()
        
    def _getcommission(self, size, price, pseudoexec):
        """Return fixed commission regardless of trade size or price"""
        return TRADING_CONFIG['commission']

class TradingLogger:
    """Simple logging for your existing setup"""
    
    def __init__(self):
        self.log_dir = Path("trading_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        today = datetime.now().strftime('%Y%m%d')
        self.trade_file = self.log_dir / f"trades_{today}.csv"
        self.portfolio_file = self.log_dir / f"portfolio_{today}.json"
        
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'trades': [],
            'portfolio_updates': []
        }
        
        print(f"📝 Logging enabled: {self.log_dir}")
    
    def log_trade(self, symbol, action, quantity, price, commission, pnl, portfolio_value, cash):
        """Log a trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'pnl': pnl,
            'portfolio_value': portfolio_value,
            'cash': cash
        }
        
        self.session_data['trades'].append(trade)
        
        # Write to CSV
        file_exists = self.trade_file.exists()
        with open(self.trade_file, 'a', newline='') as f:
            fieldnames = ['timestamp', 'symbol', 'action', 'quantity', 'price', 'commission', 'pnl', 'portfolio_value', 'cash']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(trade)
        
        print(f"📊 TRADE LOGGED: {action} {quantity} {symbol} @ Rs{price:.2f} | Commission: Rs{commission:.2f} | P&L: Rs{pnl:.2f}")
    
    def log_portfolio(self, total_value, cash, total_pnl):
        """Log portfolio status"""
        portfolio = {
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'cash': cash,
            'total_pnl': total_pnl
        }
        
        self.session_data['portfolio_updates'].append(portfolio)
        
        # Save to JSON
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)
    
    def generate_report(self):
        """Generate session report"""
        if not self.session_data['trades']:
            print("No trades to report")
            return
        
        trades_df = pd.DataFrame(self.session_data['trades'])
        
        print("\n" + "="*50)
        print("📊 TRADING SESSION REPORT")
        print("="*50)
        
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['action'] == 'BUY'])
        sell_trades = len(trades_df[trades_df['action'] == 'SELL'])
        total_pnl = trades_df['pnl'].sum()
        total_commission = trades_df['commission'].sum()
        
        print(f"Total Trades: {total_trades}")
        print(f"Buy Orders: {buy_trades}")
        print(f"Sell Orders: {sell_trades}")
        print(f"Total Commission Paid: Rs{total_commission:,.2f}")
        print(f"Total P&L: Rs{total_pnl:,.2f}")
        print(f"Net P&L (after commission): Rs{total_pnl - total_commission:,.2f}")
        
        if self.session_data['portfolio_updates']:
            final_portfolio = self.session_data['portfolio_updates'][-1]
            print(f"Final Portfolio Value: Rs{final_portfolio['total_value']:,.2f}")
            print(f"Total Return: Rs{final_portfolio['total_pnl']:,.2f}")
        
        print(f"\nFiles saved:")
        print(f"  📄 {self.trade_file}")
        print(f"  📄 {self.portfolio_file}")

class EnhancedStrategy(bt.Strategy):
    """Enhanced version of your working strategy with logging"""
    
    params = (
        ('fast_ma', 10),
        ('slow_ma', 30),
        ('position_size', 1),
    )
    
    def __init__(self):
        # Your existing indicators
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None
        self.trade_count = 0
        
        # Add logging
        self.logger = TradingLogger()
        
        print(f"📈 Enhanced Strategy initialized for {self.data._name}")
        print(f"   Fast MA: {self.params.fast_ma}, Slow MA: {self.params.slow_ma}")
        print(f"   Fixed Commission: Rs{TRADING_CONFIG['commission']:.2f} per order")
    
    def next(self):
        # Your existing trading logic
        if self.order:
            return
        
        if not self.position:
            if self.crossover[0] > 0:  # Fast MA crosses above slow MA
                print(f"🟢 BUY SIGNAL at Rs{self.data.close[0]:.2f}")
                self.order = self.buy(size=self.params.position_size)
        else:
            if self.crossover[0] < 0:  # Fast MA crosses below slow MA
                print(f"🔴 SELL SIGNAL at Rs{self.data.close[0]:.2f}")
                self.order = self.sell(size=self.params.position_size)
    
    def notify_order(self, order):
        """Enhanced order notification with logging"""
        if order.status in [order.Completed]:
            # Log the trade
            self.logger.log_trade(
                symbol=self.data._name,
                action='BUY' if order.isbuy() else 'SELL',
                quantity=order.executed.size,
                price=order.executed.price,
                commission=order.executed.comm,
                pnl=0.0,  # Will be updated in notify_trade
                portfolio_value=self.broker.getvalue(),
                cash=self.broker.getcash()
            )
            
            if order.isbuy():
                print(f"✅ BUY EXECUTED: {order.executed.size} @ Rs{order.executed.price:.2f} | Commission: Rs{order.executed.comm:.2f}")
            else:
                print(f"✅ SELL EXECUTED: {order.executed.size} @ Rs{order.executed.price:.2f} | Commission: Rs{order.executed.comm:.2f}")
        
        self.order = None
    
    def notify_trade(self, trade):
        """Enhanced trade notification with P&L logging"""
        if trade.isclosed:
            self.trade_count += 1
            profit = trade.pnl - trade.commission
            
            # Update trade log with actual P&L
            self.logger.log_trade(
                symbol=self.data._name,
                action='TRADE_CLOSED',
                quantity=abs(trade.size),
                price=trade.price,
                commission=trade.commission,
                pnl=profit,
                portfolio_value=self.broker.getvalue(),
                cash=self.broker.getcash()
            )
            
            print(f"💰 TRADE #{self.trade_count}: Gross P&L = Rs{trade.pnl:.2f} | Commission = Rs{trade.commission:.2f} | Net P&L = Rs{profit:.2f}")
            
            # Log portfolio update
            total_return = self.broker.getvalue() - TRADING_CONFIG['initial_cash']
            self.logger.log_portfolio(
                total_value=self.broker.getvalue(),
                cash=self.broker.getcash(),
                total_pnl=total_return
            )
    
    def stop(self):
        """Generate report when strategy stops"""
        print(f"\n🏁 Strategy completed")
        self.logger.generate_report()

def create_sample_data(symbol="RELIANCE", days=10):
    """Your existing sample data creation (unchanged)"""
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
    """Your existing API test (unchanged)"""
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

def run_truly_fixed_demo():
    """TRULY fixed version - correct commission setup"""
    print("TRULY Fixed Zerodha + Backtrader Demo")
    print("=" * 50)
    
    # Check token status (your existing code)
    if ZERODHA_CONFIG['access_token']:
        print(f"Access token loaded: {ZERODHA_CONFIG['access_token'][:20]}...")
        api_working = test_zerodha_api()
    else:
        print("No access token found")
        api_working = False
    
    print()
    
    # Create cerebro
    cerebro = bt.Cerebro()
    
    # CORRECT WAY: Set commission using custom commission info class
    cerebro.broker.setcash(TRADING_CONFIG['initial_cash'])
    
    # Set the custom commission info for fixed Rs 20 per order
    cerebro.broker.addcommissioninfo(FixedCommissionInfo())
    
    print(f"🏦 Correctly configured Backtrader broker")
    print(f"   Initial Cash: Rs{cerebro.broker.getcash():,.2f}")
    print(f"   Commission: Rs{TRADING_CONFIG['commission']:.2f} per order (FIXED - CORRECTLY SET)")
    print(f"   📝 Logging: Enabled")
    
    # Add sample data (your existing code)
    sample_data = create_sample_data("RELIANCE", 5)
    data_feed = bt.feeds.PandasData(dataname=sample_data)
    cerebro.adddata(data_feed, name="RELIANCE")
    
    # Add ENHANCED strategy with logging
    cerebro.addstrategy(EnhancedStrategy)
    
    print(f"\nStarting Portfolio: Rs{cerebro.broker.getvalue():,.2f}")
    print()
    print("Running TRULY fixed demo...")
    print("=" * 40)
    
    # Run backtest
    try:
        results = cerebro.run()
        
        print("=" * 40)
        print("📊 TRULY FIXED DEMO RESULTS")
        print("=" * 40)
        
        final_value = cerebro.broker.getvalue()
        total_return = final_value - TRADING_CONFIG['initial_cash']
        return_pct = (final_value / TRADING_CONFIG['initial_cash'] - 1) * 100
        
        print(f"Final Portfolio: Rs{final_value:,.2f}")
        print(f"Final Cash: Rs{cerebro.broker.getcash():,.2f}")
        print(f"Total Return: Rs{total_return:,.2f}")
        print(f"Return %: {return_pct:.2f}%")
        
        print()
        print("✅ TRULY fixed demo completed successfully!")
        print("🎯 What was ACTUALLY fixed:")
        print("   🔧 Used FixedCommissionInfo class instead of 'fixed' parameter")
        print("   📝 All trades logged with CORRECT commission calculation")
        print("   💰 Fixed Rs 20 commission per order (not percentage)")
        print("   📊 Portfolio tracking enabled")
        print("   📁 Session reports generated")
        
        if api_working:
            print("   🌐 Zerodha API connection working")
            print("   🚀 Ready for live data integration")
        else:
            print("   ⚠️ Zerodha API needs authentication")
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    run_truly_fixed_demo()