@echo off
echo Starting IMD GRD Reader...
echo.

echo [1/2] Starting Flask server...
cd /d "D:\PHD\grd reader\grd_reader_simple\grd_reader_project\backend"
start cmd /k "python app.py"

timeout /t 3 /nobreak

echo [2/2] Starting ngrok tunnel...
start cmd /k ""D:\PHD\exma material\chari\ngrok-v3-stable-windows-amd64\ngrok.exe" http 5000"

echo.
echo ✓ Both servers started!
echo ✓ Check the ngrok window for your public URL
echo.
pause