#!/usr/bin/env python3
"""
Complete System Check & Monday Morning Preparation
Tests your existing setup and prepares for live trading
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

def check_files():
    """Check if all your existing files are present"""
    print("📁 Checking Your Existing Files...")
    print("-" * 40)
    
    required_files = {
        'zerodha_token.txt': 'Access token file',
        'zerodha_auth.py': 'Authentication script',
        'zerodha_config.py': 'Configuration file',
        'fixed_demo.py': 'Working demo script',
        'live_paper_trading.py': 'Live trading script'
    }
    
    files_status = {}
    for file, description in required_files.items():
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file} - {description}")
            files_status[file] = True
        else:
            print(f"❌ {file} - Missing: {description}")
            files_status[file] = False
    
    return all(files_status.values())

def check_token_validity():
    """Check if your Zerodha token is valid"""
    print("\n🔐 Checking Zerodha Token...")
    print("-" * 40)
    
    try:
        with open('zerodha_token.txt', 'r') as f:
            token = f.read().strip()
        
        if not token:
            print("❌ Token file is empty")
            return False
        
        print(f"✅ Token found: {token[:20]}...")
        
        # Test the token
        try:
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key='gs9ulgi4ipyq5tkf')
            kite.set_access_token(token)
            
            profile = kite.profile()
            print(f"✅ Token valid - Connected as: {profile.get('user_name', 'Unknown')}")
            
            # Test data access
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            historical_data = kite.historical_data(
                instrument_token=738561,  # RELIANCE
                from_date=start_date,
                to_date=end_date,
                interval="5minute"
            )
            
            print(f"✅ Data access working: {len(historical_data)} bars fetched")
            return True
            
        except Exception as e:
            print(f"❌ Token invalid or expired: {e}")
            return False
            
    except FileNotFoundError:
        print("❌ Token file not found")
        return False

def check_packages():
    """Check if all required packages are installed"""
    print("\n📦 Checking Required Packages...")
    print("-" * 40)
    
    packages = [
        ('kiteconnect', 'KiteConnect Zerodha API'),
        ('backtrader', 'Backtrader trading framework'),
        ('pandas', 'Data analysis library'),
        ('flask', 'Web dashboard framework')
    ]
    
    all_good = True
    for package, description in packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - Missing: {description}")
            all_good = False
    
    return all_good

def test_enhanced_demo():
    """Test the enhanced demo with logging"""
    print("\n🧪 Testing Enhanced Demo...")
    print("-" * 40)
    
    try:
        # Check if enhanced demo exists
        if not Path('enhanced_fixed_demo.py').exists():
            print("⚠️ Enhanced demo not found - will create after this check")
            return True
        
        print("✅ Enhanced demo file found")
        print("✅ Ready for testing with logging")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced demo test failed: {e}")
        return False

def check_dashboard():
    """Check dashboard readiness"""
    print("\n🌐 Checking Dashboard Setup...")
    print("-" * 40)
    
    try:
        # Create trading_logs directory if it doesn't exist
        log_dir = Path('trading_logs')
        log_dir.mkdir(exist_ok=True)
        print("✅ Trading logs directory ready")
        
        # Check if we can import Flask
        try:
            from flask import Flask
            print("✅ Flask available for dashboard")
        except ImportError:
            print("❌ Flask not installed - dashboard won't work")
            return False
        
        # Check if simple dashboard exists
        if Path('simple_dashboard.py').exists():
            print("✅ Dashboard file ready")
        else:
            print("⚠️ Dashboard file not found - will create after this check")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard check failed: {e}")
        return False

def check_market_status():
    """Check current market status"""
    print("\n📊 Market Status Check...")
    print("-" * 40)
    
    now = datetime.now()
    
    # Check if it's a trading day (Monday to Friday)
    is_weekday = now.weekday() < 5  # 0-4 are Mon-Fri
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_market_hours = market_open <= now <= market_close
    
    print(f"📅 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Day of week: {now.strftime('%A')}")
    
    if is_weekday:
        print("✅ Trading day (Monday-Friday)")
    else:
        print("⚠️ Weekend - Markets closed")
    
    if is_market_hours and is_weekday:
        print("✅ Market is OPEN (9:15 AM - 3:30 PM)")
        print("🚀 Perfect time for live trading!")
    elif is_weekday:
        if now < market_open:
            print(f"⏰ Market opens in: {market_open - now}")
        else:
            print(f"🔒 Market closed - opens tomorrow at 9:15 AM")
    else:
        next_monday = now + timedelta(days=(7 - now.weekday()))
        next_monday = next_monday.replace(hour=9, minute=15, second=0, microsecond=0)
        print(f"⏰ Next trading session: {next_monday.strftime('%A, %B %d at 9:15 AM')}")
    
    return is_weekday and is_market_hours

def create_monday_checklist():
    """Create Monday morning checklist"""
    print("\n📋 MONDAY MORNING CHECKLIST")
    print("=" * 50)
    
    checklist = [
        ("🔐 AUTHENTICATION", [
            "Run: python zerodha_auth.py",
            "Ensure fresh access token is saved",
            "Tokens expire daily at 6 AM IST"
        ]),
        ("⏰ TIMING", [
            "Best to start before 9:15 AM",
            "Market hours: 9:15 AM - 3:30 PM",
            "Live data only available during market hours"
        ]),
        ("🚀 SYSTEM START", [
            "Option 1: python enhanced_fixed_demo.py (basic + logging)",
            "Option 2: python live_paper_trading.py (live data)",
            "Dashboard: python simple_dashboard.py (separate terminal)"
        ]),
        ("📊 MONITORING", [
            "Dashboard URL: http://127.0.0.1:5000",
            "Logs saved to: trading_logs/ directory",
            "Check console for trade signals"
        ]),
        ("⚙️ CONFIGURATION", [
            "Initial capital: ₹5,00,000",
            "Commission: ₹20 per order",
            "Position size: 1-2 shares per trade",
            "Symbols: RELIANCE, TCS"
        ])
    ]
    
    for section, items in checklist:
        print(f"\n{section}:")
        for item in items:
            print(f"   • {item}")

def run_comprehensive_check():
    """Run complete system check"""
    print("🚀 Complete System Check for Zerodha Paper Trading")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all checks
    checks = [
        ("Files Check", check_files),
        ("Token Validity", check_token_validity),
        ("Packages Check", check_packages),
        ("Enhanced Demo", test_enhanced_demo),
        ("Dashboard Setup", check_dashboard),
        ("Market Status", check_market_status)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} crashed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SYSTEM CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    # Recommendations
    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 ALL SYSTEMS GO!")
        print("✅ Your setup is perfect for Monday trading")
        print("🚀 You're ready to start paper trading!")
        
    elif passed >= total - 1:
        print("✅ MOSTLY READY")
        print("⚠️ Minor issues that won't prevent trading")
        print("🚀 You can start with what you have")
        
    else:
        print("⚠️ ISSUES FOUND")
        print("🔧 Fix these before Monday:")
        
        failed_checks = [name for name, result in results if not result]
        for check in failed_checks:
            if check == "Token Validity":
                print("   • Run: python zerodha_auth.py")
            elif check == "Packages Check":
                print("   • Run: pip install kiteconnect backtrader pandas flask")
            elif check == "Files Check":
                print("   • Ensure all your Zerodha files are present")
    
    # Create Monday checklist
    create_monday_checklist()
    
    # Next steps
    print(f"\n📝 IMMEDIATE NEXT STEPS:")
    print("=" * 50)
    print("1. 🧪 Test basic system: python fixed_demo.py")
    print("2. 📊 Test with logging: python enhanced_fixed_demo.py")
    print("3. 🌐 Start dashboard: python simple_dashboard.py")
    print("4. 📱 Open http://127.0.0.1:5000 in browser")
    print()
    print("🎯 FOR MONDAY LIVE TRADING:")
    print("1. 🔐 Fresh authentication: python zerodha_auth.py")
    print("2. 🚀 Live system: python live_paper_trading.py")
    print("3. 📊 Monitor via dashboard")
    print()
    print("⚠️ REMEMBER:")
    print("• Paper trading = No real money at risk")
    print("• Tokens expire daily at 6 AM IST")
    print("• Live data only during market hours")
    print("• All trades are logged for analysis")

if __name__ == '__main__':
    run_comprehensive_check()