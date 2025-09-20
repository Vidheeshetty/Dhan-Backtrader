#!/usr/bin/env python3
"""
Simple Trading Dashboard - Reads your existing log files
Works seamlessly with your enhanced_fixed_demo.py
"""

from flask import Flask, render_template_string, jsonify
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import threading
import time

app = Flask(__name__)

def get_latest_data():
    """Read latest trading data from your log files"""
    log_dir = Path("trading_logs")
    today = datetime.now().strftime('%Y%m%d')
    
    trade_file = log_dir / f"trades_{today}.csv"
    portfolio_file = log_dir / f"portfolio_{today}.json"
    
    data = {
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'trades': [],
        'portfolio': {},
        'summary': {}
    }
    
    # Read trades
    if trade_file.exists():
        try:
            trades_df = pd.read_csv(trade_file)
            data['trades'] = trades_df.tail(10).to_dict('records')  # Last 10 trades
            
            # Calculate summary stats
            total_trades = len(trades_df)
            buy_trades = len(trades_df[trades_df['action'] == 'BUY'])
            sell_trades = len(trades_df[trades_df['action'] == 'SELL'])
            total_pnl = trades_df['pnl'].sum()
            
            data['summary'] = {
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'total_pnl': total_pnl
            }
        except Exception as e:
            print(f"Error reading trades: {e}")
    
    # Read portfolio
    if portfolio_file.exists():
        try:
            with open(portfolio_file, 'r') as f:
                portfolio_data = json.load(f)
            
            if portfolio_data['portfolio_updates']:
                latest_portfolio = portfolio_data['portfolio_updates'][-1]
                data['portfolio'] = latest_portfolio
        except Exception as e:
            print(f"Error reading portfolio: {e}")
    
    return data

# Simple HTML template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-label { color: #666; }
        .metric-value { font-weight: bold; }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .trade-item { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #007bff; }
        .trade-item.buy { border-left-color: #28a745; }
        .trade-item.sell { border-left-color: #dc3545; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status.running { background: #28a745; color: white; }
        .status.stopped { background: #6c757d; color: white; }
        .refresh-info { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Trading Dashboard</h1>
            <p>Real-time monitoring for your Zerodha paper trading</p>
            <span id="status" class="status stopped">System Status</span>
            <span style="float: right;">Last updated: <span id="last-updated">Never</span></span>
        </div>
        
        <div class="cards">
            <!-- Portfolio Summary -->
            <div class="card">
                <h3>💰 Portfolio</h3>
                <div class="metric">
                    <span class="metric-label">Total Value:</span>
                    <span class="metric-value" id="total-value">₹0.00</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Cash:</span>
                    <span class="metric-value" id="cash">₹0.00</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total P&L:</span>
                    <span class="metric-value" id="total-pnl">₹0.00</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Updated:</span>
                    <span class="metric-value" id="portfolio-time">--</span>
                </div>
            </div>
            
            <!-- Trading Summary -->
            <div class="card">
                <h3>📈 Trading Summary</h3>
                <div class="metric">
                    <span class="metric-label">Total Trades:</span>
                    <span class="metric-value" id="total-trades">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Buy Orders:</span>
                    <span class="metric-value" id="buy-trades">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Sell Orders:</span>
                    <span class="metric-value" id="sell-trades">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Session P&L:</span>
                    <span class="metric-value" id="session-pnl">₹0.00</span>
                </div>
            </div>
            
            <!-- System Info -->
            <div class="card">
                <h3>⚙️ System Info</h3>
                <div class="metric">
                    <span class="metric-label">Current Time:</span>
                    <span class="metric-value" id="current-time">--:--:--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Market Hours:</span>
                    <span class="metric-value">9:15 AM - 3:30 PM</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Mode:</span>
                    <span class="metric-value">Paper Trading</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Logs:</span>
                    <span class="metric-value">trading_logs/</span>
                </div>
            </div>
        </div>
        
        <!-- Recent Trades -->
        <div class="card">
            <h3>💼 Recent Trades</h3>
            <div id="recent-trades">
                <div style="text-align: center; color: #666; padding: 20px;">
                    No trades yet - run enhanced_fixed_demo.py to start trading
                </div>
            </div>
        </div>
        
        <div class="refresh-info">
            Dashboard auto-refreshes every 5 seconds | Paper Trading Mode
        </div>
    </div>
    
    <script>
        function updateDashboard() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // Update portfolio
                    if (data.portfolio.total_value) {
                        document.getElementById('total-value').textContent = '₹' + data.portfolio.total_value.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        document.getElementById('cash').textContent = '₹' + data.portfolio.cash.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        
                        const totalPnl = data.portfolio.total_pnl || 0;
                        const pnlElement = document.getElementById('total-pnl');
                        pnlElement.textContent = '₹' + totalPnl.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        pnlElement.className = 'metric-value ' + (totalPnl > 0 ? 'positive' : totalPnl < 0 ? 'negative' : '');
                        
                        const portfolioTime = new Date(data.portfolio.timestamp).toLocaleTimeString();
                        document.getElementById('portfolio-time').textContent = portfolioTime;
                    }
                    
                    // Update trading summary
                    if (data.summary.total_trades !== undefined) {
                        document.getElementById('total-trades').textContent = data.summary.total_trades;
                        document.getElementById('buy-trades').textContent = data.summary.buy_trades;
                        document.getElementById('sell-trades').textContent = data.summary.sell_trades;
                        
                        const sessionPnl = data.summary.total_pnl || 0;
                        const sessionPnlElement = document.getElementById('session-pnl');
                        sessionPnlElement.textContent = '₹' + sessionPnl.toLocaleString('en-IN', {minimumFractionDigits: 2});
                        sessionPnlElement.className = 'metric-value ' + (sessionPnl > 0 ? 'positive' : sessionPnl < 0 ? 'negative' : '');
                    }
                    
                    // Update system info
                    document.getElementById('current-time').textContent = data.current_time;
                    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                    
                    // Update recent trades
                    updateRecentTrades(data.trades);
                    
                    // Update status
                    const statusElement = document.getElementById('status');
                    if (data.trades.length > 0) {
                        statusElement.textContent = 'Trading Active';
                        statusElement.className = 'status running';
                    } else {
                        statusElement.textContent = 'Waiting for Trades';
                        statusElement.className = 'status stopped';
                    }
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                    document.getElementById('status').textContent = 'Connection Error';
                    document.getElementById('status').className = 'status stopped';
                });
        }
        
        function updateRecentTrades(trades) {
            const container = document.getElementById('recent-trades');
            
            if (!trades || trades.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No trades yet - run enhanced_fixed_demo.py to start trading</div>';
                return;
            }
            
            container.innerHTML = trades.reverse().map(trade => {
                const timestamp = new Date(trade.timestamp).toLocaleTimeString();
                const action = trade.action.toLowerCase();
                const pnl = trade.pnl || 0;
                const pnlClass = pnl > 0 ? 'positive' : pnl < 0 ? 'negative' : '';
                
                return `
                    <div class="trade-item ${action}">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <strong>${trade.action} ${trade.quantity} ${trade.symbol}</strong><br>
                                <small>@ ₹${(trade.price || 0).toFixed(2)} | ${timestamp}</small>
                            </div>
                            <div style="text-align: right;">
                                <div class="${pnlClass}">₹${pnl.toFixed(2)}</div>
                                <small>Comm: ₹${(trade.commission || 0).toFixed(2)}</small>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // Initialize and auto-refresh
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify(get_latest_data())

def run_dashboard_server():
    """Run the dashboard server"""
    print("🌐 Starting Trading Dashboard...")
    print("📊 Dashboard URL: http://127.0.0.1:5000")
    print("🔄 Auto-refresh: Every 5 seconds")
    print("📁 Reading logs from: trading_logs/")
    
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    run_dashboard_server()