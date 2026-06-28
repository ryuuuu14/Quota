@echo off
rem Unified Deployment and Requirement Check Script for Windows Command Prompt
rem Ensures all dependencies, ports, and databases are healthy before launching.

echo ==========================================================
echo ⚡ Unlimited Void: Booting Quota-main App Offline LAN ⚡
echo ==========================================================

set "PYTHON_EXE="

rem 1. Locate Python Executable
if exist "D:\Python\python.exe" (
    set "PYTHON_EXE=D:\Python\python.exe"
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python3"
    ) else (
        where python >nul 2>&1
        if %errorlevel% equ 0 (
            set "PYTHON_EXE=python"
        ) else (
            where py >nul 2>&1
            if %errorlevel% equ 0 (
                set "PYTHON_EXE=py"
            )
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo ❌ ERROR: Python executable could not be found!
    echo Ensure D:\Python\python.exe or Python is installed in PATH.
    pause
    exit /b 1
)

echo Found Python: %PYTHON_EXE%

rem 2. Check Python Version
echo Checking Python version (3.8+)...
%PYTHON_EXE% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python 3.8+ is required.
    %PYTHON_EXE% --version
    pause
    exit /b 1
)

rem 3. Check Dependencies (Imports test)
echo Verifying Library Dependencies...
%PYTHON_EXE% -c "import sys; import importlib.util; deps=[('streamlit','streamlit'),('pandas','pandas'),('openpyxl','openpyxl'),('bcrypt','bcrypt'),('xlrd','xlrd'),('deepdiff','deepdiff'),('st_aggrid','streamlit-aggrid'),('plotly','plotly'),('jinja2','jinja2')]; status=[(n, importlib.util.find_spec(m) is not None) for m, n in deps]; [print('  [OK] ' + n) if ok else print('  [MISSING] ' + n) for n, ok in status]; sys.exit(1 if any(not ok for n, ok in status) else 0)"
if %errorlevel% neq 0 (
    echo ❌ ERROR: Missing or broken dependencies.
    echo Please run: %PYTHON_EXE% -m pip install -r requirements.txt
    pause
    exit /b 1
)
echo All dependencies verified!

rem 4. Check Database Seeding
set "DB_PATH=data\database.sqlite"
echo Verifying Database Status...
if not exist "%DB_PATH%" (
    echo Database file missing. Seeding database...
    %PYTHON_EXE% src\seed_full.py
    if %errorlevel% neq 0 (
        echo ❌ ERROR: Database seeding failed!
        pause
        exit /b 1
    )
    echo ✅ Database initialized and seeded successfully!
) else (
    echo Database exists: %DB_PATH%
)

rem 5. Check Port Availability (8501)
echo Checking Port 8501...
%PYTHON_EXE% -c "import socket; s = socket.socket(); s.bind(('127.0.0.1', 8501)); s.close()" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Port 8501 is already in use by another process!
    echo Ensure no other Streamlit instance is running.
    pause
    exit /b 1
)
echo Port 8501 is available!

echo ==========================================================
echo ✨ All Checks Passed! System is 100% Ready for Deployment. ✨
echo ==========================================================

echo 🚀 Launching Quota-main App...
%PYTHON_EXE% -m streamlit run src\app.py
