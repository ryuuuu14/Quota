@echo off
rem ============================================================================
rem  prepare_bundle.bat — Run ONCE on dev machine (with internet)
rem  Downloads Python embeddable + all dependency wheels into vendor/
rem  so the entire app can be deployed offline via USB.
rem ============================================================================

echo ==========================================================
echo   Prepare Offline Bundle for Quota-main
echo   Run this on a machine WITH internet access.
echo ==========================================================

set "PYTHON_EXE="

rem --- Locate Python ---
if exist "D:\Python\python.exe" (
    set "PYTHON_EXE=D:\Python\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo ERROR: Python not found. Install Python 3.13 first.
        pause
        exit /b 1
    )
)

echo Found Python: %PYTHON_EXE%
%PYTHON_EXE% --version

rem --- Determine Python version for download ---
for /f "delims=" %%V in ('%PYTHON_EXE% -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}.{v.micro}')"') do set "PY_VER=%%V"
for /f "delims=" %%M in ('%PYTHON_EXE% -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}')"') do set "PY_MINOR=%%M"
for /f "delims=" %%T in ('%PYTHON_EXE% -c "import sys; v=sys.version_info; print(f'{v.major}{v.minor}')"') do set "PY_TAG=%%T"

echo Python version: %PY_VER% (tag: cp%PY_TAG%)

set "EMBED_ZIP=python-%PY_VER%-embed-amd64.zip"
set "EMBED_URL=https://www.python.org/ftp/python/%PY_VER%/%EMBED_ZIP%"
set "GETPIP_URL=https://bootstrap.pypa.io/get-pip.py"

rem --- Create vendor directories ---
if not exist "vendor" mkdir vendor
if not exist "vendor\packages" mkdir vendor\packages

rem --- Step 1: Download Python embeddable zip ---
echo.
echo [1/3] Downloading Python %PY_VER% embeddable (amd64)...
if exist "vendor\%EMBED_ZIP%" (
    echo   Already exists: vendor\%EMBED_ZIP% — skipping.
) else (
    curl -L -o "vendor\%EMBED_ZIP%" "%EMBED_URL%"
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download %EMBED_ZIP%
        echo URL: %EMBED_URL%
        pause
        exit /b 1
    )
    echo   Downloaded: vendor\%EMBED_ZIP%
)

rem --- Step 2: Download get-pip.py ---
echo.
echo [2/3] Downloading get-pip.py...
if exist "vendor\get-pip.py" (
    echo   Already exists: vendor\get-pip.py — skipping.
) else (
    curl -L -o "vendor\get-pip.py" "%GETPIP_URL%"
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download get-pip.py
        pause
        exit /b 1
    )
    echo   Downloaded: vendor\get-pip.py
)

rem --- Step 3: Download all dependency wheels ---
echo.
echo [3/3] Downloading dependency wheels for Windows amd64...
echo   Platform: win_amd64 ^| Python: %PY_MINOR% ^| Binary only
echo.

rem Download app dependencies
%PYTHON_EXE% -m pip download ^
    -r requirements.txt ^
    --dest vendor\packages ^
    --platform win_amd64 ^
    --python-version %PY_MINOR% ^
    --only-binary=:all:

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Some wheels failed to download.
    echo You may need to check requirements.txt for packages
    echo that don't publish pre-built Windows wheels.
    pause
    exit /b 1
)

rem Download pip/setuptools/wheel (needed for bootstrap)
%PYTHON_EXE% -m pip download pip setuptools wheel ^
    --dest vendor\packages ^
    --only-binary=:all:

echo.
echo ==========================================================
echo   Bundle Complete!
echo ==========================================================
echo.

rem --- Print manifest ---
echo Files in vendor\:
dir /b vendor\*.zip vendor\*.py 2>nul
echo.
echo Wheels in vendor\packages\:
set "WHEEL_COUNT=0"
for %%f in (vendor\packages\*.whl) do set /a WHEEL_COUNT+=1
echo   %WHEEL_COUNT% wheel files
echo.

rem Calculate total size
%PYTHON_EXE% -c "import os; total=sum(os.path.getsize(os.path.join(dp,f)) for dp,dn,fns in os.walk('vendor') for f in fns); print(f'  Total bundle size: {total/1024/1024:.1f} MB')"

echo.
echo Next steps:
echo   1. Copy the entire Quota-main folder to a USB drive
echo   2. On the target server, paste and double-click App.bat
echo.
pause
