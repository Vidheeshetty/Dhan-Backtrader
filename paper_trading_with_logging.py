#!/usr/bin/env python3
"""
Enhanced Paper Trading System with Comprehensive Logging
"""

import backtrader as bt
import pandas as pd
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import threading
import time
import queue
import os

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
    'slippage_percent': 0.05,
    'historical_days': 5,
    'log_directory': 'trading_logs',
    'db_file': 'paper_trading.db'
}

class TradingLogger:
    """
    Comprehensive logging system for paper trading
    """
    
    def __init__(self):
        # Create logs directory
        os.makedirs(CONFIG['log_directory'], exist_ok=True)
        
        # Setup file logging
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(CONFIG['log_directory'], f'trading_{today}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Console output
            ]
        )
        
        self.logger = logging.getLogger('PaperTrading')
        
        # Setup database
        self.setup_database()
        
        # Portfolio tracking
        self.portfolio_history = []
        self.current_session_id = self.create_session()
        
        self.logger.info("Trading session started")
        self.logger.info(f"Initial cash: Rs{CONFIG['initial_cash']:,.2f}")
    
    def setup_database(self):
        """Setup SQLite database for trade tracking"""
        self.conn = sqlite3.connect(CONFIG['db_file'])
        cursor = self.conn.cursor()
        
        # Trading sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                initial_cash REAL,
                final_cash REAL,
                final_portfolio_value REAL,
                total_return REAL,
                return_percentage REAL,
                total_trades INTEGER
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP,
                symbol TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                commission REAL,
                pnl REAL,
                portfolio_value REAL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP,
                symbol TEXT,
                signal_type TEXT,
                reason TEXT,
                price REAL,
                fast_ma REAL,
                slow_ma REAL,
                rsi REAL,
                executed BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Portfolio snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP,
                cash REAL,
                portfolio_value REAL,
                positions TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_session(self):
        """Create new trading session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (start_time, initial_cash, total_trades)
            VALUES (?, ?, 0)
        ''', (datetime.now(), CONFIG['initial_cash']))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def log_signal(self, symbol, signal_type, reason, price, fast_ma, slow_ma, rsi, executed=False):
        """Log trading signal"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO signals (session_id, timestamp, symbol, signal_type, reason, 
                               price, fast_ma, slow_ma, rsi, executed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.current_session_id, datetime.now(), symbol, signal_type, reason,
              price, fast_ma, slow_ma, rsi, executed))
        
        self.conn.commit()
        
        self.logger.info(f"SIGNAL: {signal_type} {symbol} @ Rs{price:.2f} - {reason}")
    
    def log_trade(self, symbol, action, quantity, price, commission, pnl, portfolio_value):
        """Log completed trade"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades (session_id, timestamp, symbol, action, quantity, 
                              price, commission, pnl, portfolio_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.current_session_id, datetime.now(), symbol, action, quantity,
              price, commission, pnl, portfolio_value))
        
        self.conn.commit()
        
        self.logger.info(f"TRADE: {action} {quantity} {symbol} @ Rs{price:.2f}, PnL: Rs{pnl:.2f}")
    
    def log_portfolio_snapshot(self, cash, portfolio_value, positions):
        """Log portfolio snapshot"""
        cursor = self.conn.cursor()
        positions_json = json.dumps(positions)
        
        cursor.execute('''
            INSERT INTO portfolio_snapshots (session_id, timestamp, cash, 
                                           portfolio_value, positions)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.current_session_id, datetime.now(), cash, portfolio_value, positions_json))
        
        self.conn.commit()
        
        # Keep in-memory history for dashboard
        self.portfolio_history.append({
            'timestamp': datetime.now(),
            'cash': cash,
            'portfolio_value': portfolio_value,
            'positions': positions
        })
        
        # Keep only last 1000 snapshots in memory
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]
    
    def update_session_stats(self, final_cash, final_portfolio_value, total_trades):
        """Update session statistics"""
        total_return = final_portfolio_value - CONFIG['initial_cash']
        return_percentage = (final_portfolio_value / CONFIG['initial_cash'] - 1) * 100
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET end_time = ?, final_cash = ?, final_portfolio_value = ?,
                total_return = ?, return_percentage = ?, total_trades = ?
            WHERE session_id = ?
        ''', (datetime.now(), final_cash, final_portfolio_value, 
              total_return, return_percentage, total_trades, self.current_session_id))
        
        self.conn.commit()
    
    def get_session_summary(self):
        """Get current session summary"""
        cursor = self.conn.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (self.current_session_id,))
        session = cursor.fetchone()
        
        # Get trade count
        cursor.execute('SELECT COUNT(*) FROM trades WHERE session_id = ?', (self.current_session_id,))
        trade_count = cursor.fetchone()[0]
        
        # Get signal count
        cursor.execute('SELECT COUNT(*) FROM signals WHERE session_id = ?', (self.current_session_id,))
        signal_count = cursor.fetchone()[0]
        
        return {
            'session_id': self.current_session_id,
            'start_time': session[1] if session else None,
            'trade_count': trade_count,
            'signal_count': signal_count,
            'portfolio_history': self.portfolio_history[-50:]  # Last 50 snapshots
        }
    
    def close_session(self):
        """Close trading session"""
        self.logger.info("Trading session ended")
        self.conn.close()

class EnhancedTradingStrategy(bt.Strategy):
    """
    Enhanced trading strategy with comprehensive logging
    """
    
    params = (
        ('fast_ma', 10),
        ('slow_ma', 30),
        ('rsi_period', 14),
        ('position_size', 5),
        ('max_positions', 3),
        ('debug', True),
    )
    
    def __init__(self):
        # Initialize logger
        self.trading_logger = TradingLogger()
        
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
        self.last_portfolio_log = 0
        
        if self.params.debug:
            self.trading_logger.logger.info(f"Strategy initialized for {len(self.datas)} symbols")
    
    def next(self):
        self.bar_count += 1
        
        # Log portfolio status every 10 bars
        if self.bar_count - self.last_portfolio_log >= 10:
            self.log_portfolio_status()
            self.last_portfolio_log = self.bar_count
        
        # Check each symbol for trading opportunities
        for data in self.datas:
            symbol = data._name
            
            if symbol in self.orders:
                continue
            
            self.check_trading_signals(data, symbol)
    
    def check_trading_signals(self, data, symbol):
        """Check for trading signals with logging"""
        indicators = self.indicators[symbol]
        position = self.getposition(data)
        
        # Entry signals
        if not position:
            if (indicators['crossover'][0] > 0 and 
                indicators['rsi'][0] < 70 and 
                len(data) > self.params.slow_ma):
                
                active_positions = sum(1 for d in self.datas if self.getposition(d))
                
                if active_positions < self.params.max_positions:
                    reason = f"MA Cross + RSI={indicators['rsi'][0]:.1f}"
                    
                    # Log signal
                    self.trading_logger.log_signal(
                        symbol, "BUY", reason, data.close[0],
                        indicators['fast_ma'][0], indicators['slow_ma'][0],
                        indicators['rsi'][0], executed=True
                    )
                    
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
                # Log signal
                self.trading_logger.log_signal(
                    symbol, "SELL", exit_reason, data.close[0],
                    indicators['fast_ma'][0], indicators['slow_ma'][0],
                    indicators['rsi'][0], executed=True
                )
                
                self.orders[symbol] = self.sell(data=data, size=self.params.position_size)
    
    def notify_order(self, order):
        """Handle order notifications with logging"""
        symbol = order.data._name
        
        if order.status in [order.Completed]:
            action = "BUY" if order.isbuy() else "SELL"
            
            # Log trade
            self.trading_logger.log_trade(
                symbol, action, order.executed.size, order.executed.price,
                order.executed.comm, 0, self.broker.getvalue()
            )
        
        # Clear order tracking
        if symbol in self.orders:
            del self.orders[symbol]
    
    def notify_trade(self, trade):
        """Handle trade notifications with logging"""
        if trade.isclosed:
            self.trade_count += 1
            symbol = trade.data._name
            profit = trade.pnl - trade.commission
            
            # Update trade log with P&L
            self.trading_logger.log_trade(
                symbol, "CLOSE", trade.size, trade.price,
                trade.commission, profit, self.broker.getvalue()
            )
    
    def log_portfolio_status(self):
        """Log current portfolio status"""
        positions = {}
        for data in self.datas:
            position = self.getposition(data)
            if position.size != 0:
                positions[data._name] = {
                    'size': position.size,
                    'price': position.price,
                    'value': position.size * data.close[0]
                }
        
        self.trading_logger.log_portfolio_snapshot(
            self.broker.getcash(),
            self.broker.getvalue(),
            positions
        )
    
    def stop(self):
        """Called when strategy stops"""
        # Final portfolio log
        self.log_portfolio_status()
        
        # Update session stats
        self.trading_logger.update_session_stats(
            self.broker.getcash(),
            self.broker.getvalue(),
            self.trade_count
        )
        
        # Print session summary
        summary = self.trading_logger.get_session_summary()
        self.trading_logger.logger.info("SESSION SUMMARY:")
        self.trading_logger.logger.info(f"  Session ID: {summary['session_id']}")
        self.trading_logger.logger.info(f"  Total Trades: {summary['trade_count']}")
        self.trading_logger.logger.info(f"  Total Signals: {summary['signal_count']}")
        self.trading_logger.logger.info(f"  Final Portfolio: Rs{self.broker.getvalue():,.2f}")
        
        # Close logger
        self.trading_logger.close_session()

# Previous LiveDataFeed and PaperTradingBroker classes remain the same
class LiveDataFeed(bt.feeds.PandasData):
    """Live data feed (same as before)"""
    # ... (same implementation as previous version)
    pass

class PaperTradingBroker(bt.brokers.BackBroker):
    """Enhanced paper trading broker (same as before)"""
    # ... (same implementation as previous version)
    pass

def run_enhanced_paper_trading():
    """Run enhanced paper trading with logging"""
    print("Enhanced Paper Trading System with Logging")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Logs directory: {CONFIG['log_directory']}")
    print(f"Database: {CONFIG['db_file']}")
    print()
    
    # Setup Zerodha connection
    kite = None
    if CONFIG['access_token']:
        try:
            kite = KiteConnect(api_key=CONFIG['api_key'])
            kite.set_access_token(CONFIG['access_token'])
            profile = kite.profile()
            print(f"Connected to Zerodha as: {profile.get('user_name', 'Unknown')}")
        except Exception as e:
            print(f"Zerodha connection failed: {e}")
    
    # Create Cerebro with enhanced components
    cerebro = bt.Cerebro()
    
    # Setup broker
    broker = PaperTradingBroker()
    cerebro.setbroker(broker)
    
    # Add data feeds
    symbols_to_trade = ['RELIANCE', 'TCS']
    
    for symbol in symbols_to_trade:
        print(f"Setting up data feed for {symbol}...")
        # Use sample data for demo (replace with LiveDataFeed for live trading)
        import numpy as np
        
        # Create sample data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        dates = pd.date_range(start=start_date, end=end_date, freq='5min')
        dates = dates[(dates.hour >= 9) & (dates.hour < 16)][:100]
        
        np.random.seed(42)
        base_price = 2450 if symbol == "RELIANCE" else 3200
        returns = np.random.normal(0, 0.001, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            open_price = close * (1 + np.random.normal(0, 0.002))
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
            volume = int(np.random.lognormal(11, 0.8))
            
            data.append({
                'datetime': date, 'open': round(open_price, 2),
                'high': round(high, 2), 'low': round(low, 2),
                'close': round(close, 2), 'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)
        
        data_feed = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data_feed, name=symbol)
    
    # Add enhanced strategy
    cerebro.addstrategy(EnhancedTradingStrategy,
                       fast_ma=10, slow_ma=30, position_size=5, debug=True)
    
    print(f"Starting Portfolio: Rs{cerebro.broker.getvalue():,.2f}")
    print("Running enhanced paper trading with logging...")
    print("=" * 60)
    
    try:
        results = cerebro.run()
        
        print("\n" + "=" * 60)
        print("ENHANCED PAPER TRADING COMPLETE")
        print("=" * 60)
        print(f"Check logs in: {CONFIG['log_directory']}")
        print(f"Database saved to: {CONFIG['db_file']}")
        print("Run dashboard: python trading_dashboard.py")
        
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
    run_enhanced_paper_trading()