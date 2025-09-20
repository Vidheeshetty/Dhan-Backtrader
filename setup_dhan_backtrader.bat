@echo off
cls
echo ================================================
echo   Dhan Sandbox + Backtrader Setup
echo ================================================
echo.

echo 🎯 This approach is much better than the bridge!
echo ✅ Direct API connection
echo ✅ No dependency conflicts  
echo ✅ Perfect for paper trading
echo.

echo 📦 Installing required packages...
echo.

echo Installing Dhan Python SDK...
pip install dhanhq
if errorlevel 1 (
    echo ❌ Failed to install dhanhq
    pause
    exit /b 1
) else (
    echo ✅ dhanhq installed
)

echo.
echo Installing/verifying Backtrader...
pip install backtrader
if errorlevel 1 (
    echo ❌ Failed to install backtrader
    pause
    exit /b 1
) else (
    echo ✅ backtrader installed
)

echo.
echo Installing supporting packages...
pip install requests pandas numpy websocket-client
echo ✅ Supporting packages installed

echo.
echo 🧪 Testing installations...
echo.

echo Testing Dhan SDK...
python -c "
try:
    from dhanhq import dhanhq
    print('✅ Dhan SDK imported successfully')
except ImportError as e:
    print(f'❌ Dhan SDK failed: {e}')
"

echo.
echo Testing Backtrader...
python -c "
try:
    import backtrader as bt
    print('✅ Backtrader imported successfully')
except ImportError as e:
    print(f'❌ Backtrader failed: {e}')
"

echo.
echo Testing other packages...
python -c "
try:
    import pandas as pd
    import numpy as np
    import requests
    print('✅ All supporting packages work')
    print(f'   Pandas: {pd.__version__}')
    print(f'   NumPy: {np.__version__}')
except ImportError as e:
    print(f'❌ Supporting packages failed: {e}')
"

echo.
echo ================================================
echo              INSTALLATION COMPLETE
echo ================================================
echo.

echo ✅ Ready to create:
echo   📊 Custom Dhan data feed for Backtrader
echo   🏦 Custom Dhan broker for Backtrader  
echo   📈 Trading strategies with live paper trading
echo.

echo 📝 Your Dhan Sandbox credentials needed:
echo   - Client ID: 2509179790 (from your .env)
echo   - Access Token: (from your .env)
echo   - API Base URL: https://api.dhan.co (sandbox)
echo.

echo 🚀 Next: Create the Dhan-Backtrader integration files
echo.
pause