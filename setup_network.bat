@echo off
setlocal EnableDelayedExpansion

echo ==========================================================
echo   Quota System - Network Setup Tool
echo ==========================================================
echo.

:: 1. Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Administrative privileges are required for network configuration.
    echo        Requesting elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [OK] Running as Administrator.
echo.

:: 2. Clean up legacy Hosts entries
set "HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts"
echo Checking hosts file for legacy 'giochuan' mappings...
findstr /i "giochuan" "%HOSTS_FILE%" >nul
if %errorlevel% equ 0 (
    echo [INFO] Legacy mappings found. Cleaning up hosts file...
    powershell -Command "(Get-Content '%HOSTS_FILE%') -replace '.*giochuan.*', '' | Set-Content '%HOSTS_FILE%'"
    echo [OK] Hosts file cleaned.
) else (
    echo [OK] No legacy hosts mappings found.
)

:: 3. Clean up legacy Port Proxy (Port 80)
echo.
echo Cleaning up legacy port proxy rule on port 80...
netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0 >nul 2>&1
echo [OK] Legacy port proxy removed.

:: 4. Configure Windows Firewall for Port 1111
echo.
echo Configuring Windows Firewall to allow inbound Port 1111...
:: Delete legacy port 80 rule if exists
netsh advfirewall firewall delete rule name="Quota App Port 80" >nul 2>&1
:: Delete existing port 1111 rule first to prevent duplicates
netsh advfirewall firewall delete rule name="Quota App Port 1111" >nul 2>&1
:: Add port 1111 rule
netsh advfirewall firewall add rule name="Quota App Port 1111" dir=in action=allow protocol=TCP localport=1111 >nul
if %errorlevel% equ 0 (
    echo [OK] Firewall rule for port 1111 added successfully.
) else (
    echo [ERROR] Failed to add firewall rule.
)

echo.
echo ==========================================================
echo   Network Setup Complete!
echo   Firewall is configured. Connect clients via Server IP on port 1111.
echo ==========================================================
echo.
pause
