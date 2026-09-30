@echo off
echo Stopping OliveSoft services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5678') do taskkill /F /PID %%a >nul 2>&1
echo All services stopped successfully.
pause
