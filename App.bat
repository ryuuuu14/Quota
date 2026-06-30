@echo off
rem ============================================================================
rem  App.bat — 1-Click Launcher for Quota-main (Offline LAN Deployment)
rem  Automatically sets up Python from bundled package if needed,
rem  installs dependencies, seeds database, and launches Streamlit.
rem ============================================================================

echo ==========================================================
echo   Unlimited Void: Booting Quota-main App Offline LAN
echo ==========================================================

set "PYTHON_EXE="

rem ── 1. Locate Python Executable ─────────────────────────────
rem Priority: runtime (bundled) > D:\Python > system PATH

if exist "runtime\python.exe" (
    set "PYTHON_EXE=runtime\python.exe"
    goto :found_python
)

if exist "D:\Python\python.exe" (
    set "PYTHON_EXE=D:\Python\python.exe"
    goto :found_python
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python3"
    goto :found_python
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    rem Skip the Microsoft Store stub that returns errorlevel 0
    python -c "import sys" >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
        goto :found_python
    )
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto :found_python
)

rem ── Python not found — attempt auto-install from vendor/ ────
if exist "vendor\get-pip.py" (
    echo.
    echo   Python not found on this machine.
    echo   Setting up from bundled package (one-time, ~30 seconds)...
    echo.
    call install_python.bat
    if exist "runtime\python.exe" (
        set "PYTHON_EXE=runtime\python.exe"
        goto :found_python
    )
)

echo.
echo   ERROR: Python could not be found or installed!
echo   Ensure the vendor\ folder is present with the bundled Python package.
echo   Or install Python 3.8+ manually from https://www.python.org
echo.
pause
exit /b 1

:found_python
echo Found Python: %PYTHON_EXE%

rem ── 2. Check Python Version ─────────────────────────────────
echo Checking Python version (3.8+)...
%PYTHON_EXE% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorlevel% neq 0 (
    echo   ERROR: Python 3.8+ is required.
    %PYTHON_EXE% --version
    pause
    exit /b 1
)

rem ── 3. Check Dependencies ───────────────────────────────────
echo Verifying Library Dependencies...
%PYTHON_EXE% -c "import sys; import importlib.util; deps=[('streamlit','streamlit'),('pandas','pandas'),('openpyxl','openpyxl'),('bcrypt','bcrypt'),('xlrd','xlrd'),('deepdiff','deepdiff'),('st_aggrid','streamlit-aggrid'),('plotly','plotly'),('jinja2','jinja2')]; status=[(n, importlib.util.find_spec(m) is not None) for m, n in deps]; [print('  [OK] ' + n) if ok else print('  [MISSING] ' + n) for n, ok in status]; sys.exit(1 if any(not ok for n, ok in status) else 0)"
if %errorlevel% neq 0 (
    echo.
    echo   Some dependencies are missing. Attempting auto-install...
    if exist "vendor\packages" (
        %PYTHON_EXE% -m pip install --no-index --find-links vendor\packages -r requirements.txt
    ) else (
        %PYTHON_EXE% -m pip install -r requirements.txt
    )
    rem Re-verify after install
    %PYTHON_EXE% -c "import sys; import importlib.util; deps=[('streamlit','streamlit'),('pandas','pandas'),('openpyxl','openpyxl'),('bcrypt','bcrypt'),('xlrd','xlrd'),('deepdiff','deepdiff'),('st_aggrid','streamlit-aggrid'),('plotly','plotly'),('jinja2','jinja2')]; status=[(n, importlib.util.find_spec(m) is not None) for m, n in deps]; sys.exit(1 if any(not ok for n, ok in status) else 0)"
    if %errorlevel% neq 0 (
        echo.
        echo   ERROR: Dependency installation failed.
        echo   Please check requirements.txt and vendor\packages\ contents.
        pause
        exit /b 1
    )
    echo   Dependencies installed successfully!
)
echo All dependencies verified!

rem ── 4. Check Database Seeding ───────────────────────────────
set "DB_PATH=data\database.sqlite"
echo Verifying Database Status...
if not exist "data" mkdir data
if not exist "%DB_PATH%" (
    echo Database file missing. Seeding database...
    %PYTHON_EXE% src\seed_full.py
    if %errorlevel% neq 0 (
        echo   ERROR: Database seeding failed!
        pause
        exit /b 1
    )
    echo   Database initialized and seeded successfully!
) else (
    echo Database exists: %DB_PATH%
)

rem ── 5. Setup Network Redirection ─────────────────────────────
echo Setting up Network Redirection (Firewall Port 1111)...
powershell -Command "Start-Process '%PYTHON_EXE%' -ArgumentList 'src\setup_network.py' -Verb RunAs -Wait"
if %errorlevel% neq 0 (
    echo   WARNING: Failed to apply network configuration automatically.
    echo   Please make sure to accept the UAC administrator prompt.
)

rem ── 6. Check Port Availability (1111) ───────────────────────
echo Checking Port 1111...
%PYTHON_EXE% -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', 1111)); s.close()" >nul 2>&1
if %errorlevel% neq 0 (
    echo   WARNING: Port 1111 may already be in use.
    echo   If another instance is running, close it first.
    echo   Attempting to launch anyway...
)
echo Port 1111 is available!

echo ==========================================================
echo   All Checks Passed! System is 100%% Ready for Deployment.
echo ==========================================================

:: Resolve LAN IP using Python
set "LAN_IP=127.0.0.1"
for /f "tokens=*" %%g in ('%PYTHON_EXE% -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect((\"10.255.255.255\",1)); print(s.getsockname()[0]); s.close()" 2^>nul') do (
    set "LAN_IP=%%g"
)

echo.
echo   Launching Quota-main App...
echo   Unified Server URL: http://%LAN_IP%:1111
echo.
%PYTHON_EXE% -m streamlit run src\app.py --server.port 1111 --server.address 0.0.0.0

rem ── 7. Cleanup and Teardown on Exit ─────────────────────────
echo.
echo   Application closed. Cleaning up network routing...
powershell -Command "Start-Process '%PYTHON_EXE%' -ArgumentList 'src\setup_network.py --teardown' -Verb RunAs -Wait"
echo   Teardown complete. Restored original configuration.
