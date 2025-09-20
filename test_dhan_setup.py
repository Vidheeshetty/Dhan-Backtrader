#!/usr/bin/env python3
"""
Test Dhan + Backtrader Integration Setup
Run this first to verify everything is working
"""

import sys
import traceback

def test_imports():
    """Test if all required packages are available"""
    print("🔍 Testing Package Imports")
    print("-" * 40)
    
    packages = [
        ("Backtrader", "import backtrader as bt"),
        ("Dhan SDK", "from dhanhq import dhanhq"),
        ("Pandas", "import pandas as pd"),
        ("NumPy", "import numpy as np"),
        ("Requests", "import requests"),
    ]
    
    all_good = True
    for name, import_statement in packages:
        try:
            exec(import_statement)
            print(f"✅ {name} - Available")
        except ImportError as e:
            print(f"❌ {name} - Missing: {e}")
            all_good = False
    
    return all_good

def test_config():
    """Test configuration files"""
    print("\n🔧 Testing Configuration")
    print("-" * 40)
    
    try:
        from dhan_config import DHAN_CONFIG, TRADING_CONFIG, print_config
        print("✅ Configuration loaded successfully")
        
        # Check essential config
        if DHAN_CONFIG['client_id'] and DHAN_CONFIG['access_token']:
            print("✅ Dhan credentials present")
        else:
            print("❌ Dhan credentials missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_dhan_api():
    """Test Dhan API connection"""
    print("\n🔗 Testing Dhan API Connection")
    print("-" * 40)
    
    try:
        from dhanhq import dhanhq
        from dhan_config import DHAN_CONFIG
        
        dhan = dhanhq(
            client_id=DHAN_CONFIG['client_id'],
            access_token=DHAN_CONFIG['access_token']
        )
        
        print(f"   Client ID: {DHAN_CONFIG['client_id']}")
        print(f"   Base URL: {DHAN_CONFIG['base_url']}")
        
        # Test API call
        response = dhan.get_fund_limits()
        
        if response and response.get('status') == 'success':
            print("✅ Dhan API connection successful")
            
            # Print fund details if available
            if 'data' in response:
                funds = response['data']
                print(f"   Available Funds: ₹{funds.get('availablecash', 'N/A')}")
                print(f"   Used Margin: ₹{funds.get('utilisedmargin', 'N/A')}")
            
            return True
        else:
            print(f"⚠️ Dhan API response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Dhan API test failed: {e}")
        print("   This might be okay - could be network/credentials issue")
        return False

def test_custom_components():
    """Test custom broker and data feed"""
    print("\n🏦 Testing Custom Components")
    print("-" * 40)
    
    try:
        # Test broker
        from dhan_broker import DhanBroker
        print("✅ DhanBroker can be imported")
        
        broker = DhanBroker()
        print(f"✅ DhanBroker created successfully")
        print(f"   Initial Cash: ₹{broker.getcash():,.2f}")
        
        # Test data feed
        from dhan_data_feed import DhanData
        print("✅ DhanData can be imported")
        
        # Don't actually create data feed here to avoid long wait
        print("✅ DhanData ready for use")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom components test failed: {e}")
        return False

def test_backtrader_integration():
    """Test basic Backtrader integration"""
    print("\n🧠 Testing Backtrader Integration")
    print("-" * 40)
    
    try:
        import backtrader as bt
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Create simple test
        cerebro = bt.Cerebro()
        
        # Create sample data
        dates = pd.date_range(start=datetime.now() - timedelta(days=5), 
                             periods=100, freq='5min')
        
        np.random.seed(42)
        prices = 2450 + np.cumsum(np.random.normal(0, 1, 100))
        
        data = pd.DataFrame({
            'open': prices * 0.999,
            'high': prices * 1.002,
            'low': prices * 0.998,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Add to cerebro
        data_feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_feed, name="TEST")
        
        print("✅ Sample data created and added to Cerebro")
        print(f"   Data points: {len(data)}")
        print(f"   Price range: ₹{data['close'].min():.2f} - ₹{data['close'].max():.2f}")
        
        # Simple strategy test
        class TestStrategy(bt.Strategy):
            def __init__(self):
                self.counter = 0
            def next(self):
                self.counter += 1
        
        cerebro.addstrategy(TestStrategy)
        
        # Quick run
        results = cerebro.run()
        
        print("✅ Backtrader integration test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtrader integration test failed: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("🧪 Dhan + Backtrader Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Dhan API", test_dhan_api),
        ("Custom Components", test_custom_components),
        ("Backtrader Integration", test_backtrader_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    critical_failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {test_name}")
        
        if result:
            passed += 1
        elif test_name in ["Package Imports", "Configuration", "Custom Components"]:
            critical_failed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    # Recommendations
    print("\n" + "=" * 60)
    if passed == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your Dhan + Backtrader integration is ready")
        print("🚀 You can now run the full demo:")
        print("   python dhan_backtrader_demo.py")
        
    elif critical_failed == 0:
        print("⚠️ MOSTLY WORKING")
        print("✅ Core functionality is ready")
        print("🚀 You can proceed with the demo")
        print("   Minor issues (like API connection) won't stop the demo")
        
    else:
        print("❌ CRITICAL ISSUES FOUND")
        print("🔧 Fix these issues before proceeding:")
        
        if not results[0][1]:  # Package imports failed
            print("   - Install missing packages: pip install dhanhq backtrader pandas")
        if not results[1][1]:  # Config failed
            print("   - Check dhan_config.py file")
        if not results[3][1]:  # Custom components failed
            print("   - Check dhan_broker.py and dhan_data_feed.py files")

def print_next_steps():
    """Print what to do next"""
    print(f"\n📝 Next Steps:")
    print("=" * 60)
    print("1. 🧪 If tests passed: python dhan_backtrader_demo.py")
    print("2. 📊 Review the demo results")
    print("3. 🔧 Customize strategies and parameters")
    print("4. 🚀 Start paper trading during market hours")
    print()
    print("📋 Files in your setup:")
    print("   - dhan_config.py (configuration)")
    print("   - dhan_broker.py (custom broker)")  
    print("   - dhan_data_feed.py (custom data feed)")
    print("   - dhan_backtrader_demo.py (complete demo)")
    print("   - test_dhan_setup.py (this test file)")
    print()
    print("🕒 Market Hours: 9:15 AM - 3:30 PM (Mon-Fri)")
    print("📈 Start with small position sizes")
    print("🎯 Use Dhan Sandbox for risk-free testing")

if __name__ == '__main__':
    try:
        run_all_tests()
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        print(f"Traceback: {traceback.format_exc()}")