import backtrader as bt
import requests
import json
from datetime import datetime
from dhan_config import DHAN_CONFIG, TRADING_CONFIG, get_dhan_headers
from dhanhq import dhanhq

class DhanBroker(bt.BrokerBase):
    """
    Custom Backtrader Broker that integrates with Dhan Sandbox API
    Handles paper trading through Dhan Sandbox
    """
    
    def __init__(self):
        super(DhanBroker, self).__init__()
        
        # Initialize Dhan client
        self.dhan = dhanhq(
            client_id=DHAN_CONFIG['client_id'],
            access_token=DHAN_CONFIG['access_token']
        )
        
        # Portfolio tracking
        self.cash = TRADING_CONFIG['initial_cash']
        self.value = TRADING_CONFIG['initial_cash']
        self.positions = {}  # symbol -> position info
        self.orders = {}     # order_id -> order info
        self.order_counter = 1
        
        # Commission
        self.commission = TRADING_CONFIG['commission']
        
        print(f"🏦 DhanBroker initialized")
        print(f"   Initial Cash: ₹{self.cash:,.2f}")
        print(f"   Commission: {self.commission*100}%")
        print(f"   Client ID: {DHAN_CONFIG['client_id']}")
    
    def start(self):
        """Called when broker starts"""
        print("🚀 DhanBroker started")
        self.test_connection()
    
    def test_connection(self):
        """Test connection to Dhan API"""
        try:
            # Test with fund limits API
            response = self.dhan.get_fund_limits()
            if response['status'] == 'success':
                print("✅ Dhan API connection successful")
                return True
            else:
                print(f"⚠️ Dhan API response: {response}")
                return False
        except Exception as e:
            print(f"❌ Dhan API connection failed: {e}")
            return False
    
    def getcash(self):
        """Get available cash"""
        return self.cash
    
    def getvalue(self, datas=None):
        """Get total portfolio value"""
        total_value = self.cash
        
        # Add value of current positions
        for symbol, pos_info in self.positions.items():
            if pos_info['quantity'] != 0:
                # Get current price (in real implementation, you'd fetch from Dhan)
                # For now, use the last known price
                current_price = pos_info.get('last_price', pos_info['avg_price'])
                position_value = pos_info['quantity'] * current_price
                total_value += position_value
        
        self.value = total_value
        return total_value
    
    def getposition(self, data, clone=True):
        """Get position for a specific data/symbol"""
        symbol = data._name
        if symbol in self.positions:
            pos_info = self.positions[symbol]
            return self.DhanPosition(
                size=pos_info['quantity'],
                price=pos_info['avg_price']
            )
        else:
            return self.DhanPosition(size=0, price=0.0)
    
    class DhanPosition:
        """Position object compatible with Backtrader"""
        def __init__(self, size, price):
            self.size = size
            self.price = price
    
    def submit(self, order):
        """Submit order to Dhan"""
        try:
            symbol = order.data._name
            quantity = abs(order.created.size)
            side = 'BUY' if order.isbuy() else 'SELL'
            
            print(f"\n📝 Submitting order:")
            print(f"   Symbol: {symbol}")
            print(f"   Side: {side}")
            print(f"   Quantity: {quantity}")
            print(f"   Order Type: {TRADING_CONFIG['order_type']}")
            
            # For paper trading in sandbox, we'll simulate the order
            if TRADING_CONFIG.get('paper_trading', True):
                return self._simulate_order(order, symbol, side, quantity)
            else:
                return self._place_real_order(order, symbol, side, quantity)
                
        except Exception as e:
            print(f"❌ Order submission failed: {e}")
            order.reject()
            return order
    
    def _simulate_order(self, order, symbol, side, quantity):
        """Simulate order execution for paper trading"""
        try:
            # Get current price (simulate with order price or use last known price)
            if hasattr(order.created, 'price') and order.created.price:
                execution_price = order.created.price
            else:
                # Market order - use current market price (simulated)
                execution_price = order.data.close[0]  # Use current close price
            
            # Calculate commission
            trade_value = quantity * execution_price
            commission = trade_value * self.commission
            
            print(f"🔄 Simulating order execution:")
            print(f"   Execution Price: ₹{execution_price:.2f}")
            print(f"   Trade Value: ₹{trade_value:.2f}")
            print(f"   Commission: ₹{commission:.2f}")
            
            # Check if we have enough cash for buy orders
            if side == 'BUY':
                total_cost = trade_value + commission
                if total_cost > self.cash:
                    print(f"❌ Insufficient cash: Need ₹{total_cost:.2f}, Have ₹{self.cash:.2f}")
                    order.reject()
                    return order
                
                # Deduct cash
                self.cash -= total_cost
            else:  # SELL
                # Check if we have enough position to sell
                current_position = self.positions.get(symbol, {'quantity': 0})['quantity']
                if quantity > current_position:
                    print(f"❌ Insufficient position: Need {quantity}, Have {current_position}")
                    order.reject()
                    return order
                
                # Add cash from sale
                self.cash += (trade_value - commission)
            
            # Update position
            self._update_position(symbol, side, quantity, execution_price)
            
            # Mark order as completed
            order.completed()
            order.executed.dt = bt.date2num(datetime.now())
            order.executed.price = execution_price
            order.executed.size = quantity if side == 'BUY' else -quantity
            order.executed.comm = commission
            
            print(f"✅ Order executed successfully")
            print(f"   New Cash Balance: ₹{self.cash:.2f}")
            
            return order
            
        except Exception as e:
            print(f"❌ Order simulation failed: {e}")
            order.reject()
            return order
    
    def _place_real_order(self, order, symbol, side, quantity):
        """Place real order through Dhan API (for live trading)"""
        try:
            # This would be used for actual live trading
            order_data = {
                'dhan_client_id': DHAN_CONFIG['client_id'],
                'correlation_id': f"BT_{self.order_counter}",
                'exchange_segment': TRADING_CONFIG['exchange'],
                'transaction_type': side,
                'quantity': quantity,
                'order_type': TRADING_CONFIG['order_type'],
                'product_type': TRADING_CONFIG['product_type'],
                'price': 0,  # For market orders
                'trigger_price': 0,
                'validity': TRADING_CONFIG['validity'],
                'security_id': symbol  # You'd need to map symbol to Dhan security_id
            }
            
            response = self.dhan.place_order(**order_data)
            
            if response['status'] == 'success':
                print(f"✅ Real order placed: {response}")
                order.accept()
                # You'd track the order status and update when filled
            else:
                print(f"❌ Real order failed: {response}")
                order.reject()
            
            return order
            
        except Exception as e:
            print(f"❌ Real order placement failed: {e}")
            order.reject()
            return order
    
    def _update_position(self, symbol, side, quantity, price):
        """Update position tracking"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0.0,
                'last_price': price
            }
        
        pos = self.positions[symbol]
        
        if side == 'BUY':
            new_quantity = pos['quantity'] + quantity
            if new_quantity != 0:
                # Update average price
                total_value = (pos['quantity'] * pos['avg_price']) + (quantity * price)
                pos['avg_price'] = total_value / new_quantity
            pos['quantity'] = new_quantity
        else:  # SELL
            pos['quantity'] -= quantity
            if pos['quantity'] == 0:
                pos['avg_price'] = 0.0
        
        pos['last_price'] = price
        
        print(f"📊 Position updated for {symbol}:")
        print(f"   Quantity: {pos['quantity']}")
        print(f"   Avg Price: ₹{pos['avg_price']:.2f}")
    
    def cancel(self, order):
        """Cancel an order"""
        print(f"🚫 Cancelling order for {order.data._name}")
        order.cancel()
        return order
    
    def get_notification(self):
        """Get any pending notifications"""
        return None
    
    def next(self):
        """Called on each bar - update portfolio value"""
        self.getvalue()
    
    def stop(self):
        """Called when broker stops"""
        print("🛑 DhanBroker stopped")
        print(f"📊 Final Portfolio Summary:")
        print(f"   Cash: ₹{self.cash:.2f}")
        print(f"   Total Value: ₹{self.getvalue():.2f}")
        print(f"   Total Return: ₹{self.getvalue() - TRADING_CONFIG['initial_cash']:.2f}")
        
        if self.positions:
            print(f"   Open Positions:")
            for symbol, pos in self.positions.items():
                if pos['quantity'] != 0:
                    print(f"     {symbol}: {pos['quantity']} @ ₹{pos['avg_price']:.2f}")

# Test the broker
if __name__ == '__main__':
    print("🧪 Testing DhanBroker")
    broker = DhanBroker()
    broker.start()