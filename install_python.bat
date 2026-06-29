@echo off
rem ============================================================================
rem  install_python.bat — Offline Python setup from vendor/ bundle
rem  Extracts embedded Python, bootstraps pip, installs all dependencies.
rem  Fully offline — never touches the network.
rem ============================================================================

echo.
echo ----------------------------------------------------------
echo   Setting up Python runtime from bundled package...
echo   This is a one-time operation (approx. 30 seconds).
echo ----------------------------------------------------------
echo.

rem --- Guard: check vendor/ exists ---
if not exist "vendor" (
    echo ERROR: vendor\ folder not found!
    echo Run prepare_bundle.bat on a machine with internet first.
    exit /b 1
)

rem --- Find the embedded zip ---
set "EMBED_ZIP="
for %%f in (vendor\python-*-embed-amd64.zip) do set "EMBED_ZIP=%%f"

if "%EMBED_ZIP%"=="" (
    echo ERROR: No python-*-embed-amd64.zip found in vendor\
    echo Run prepare_bundle.bat on a machine with internet first.
    exit /b 1
)

echo Found: %EMBED_ZIP%

rem --- Determine python version tag from zip name ---
rem Extract e.g. "313" from "python-3.13.13-embed-amd64.zip"
for /f "delims=" %%T in ('powershell -NoProfile -Command "$n='%EMBED_ZIP%'; if($n -match 'python-(\d+)\.(\d+)'){$matches[1]+$matches[2]}else{'UNKNOWN'}"') do set "PY_TAG=%%T"

echo Python tag: cp%PY_TAG%

rem --- Step 1: Extract embedded Python ---
if exist "runtime\python.exe" (
    echo [1/4] Python runtime already exists — skipping extraction.
) else (
    echo [1/4] Extracting embedded Python to runtime\ ...
    if exist "runtime" rmdir /s /q "runtime"
    powershell -NoProfile -Command "Expand-Archive -Path '%EMBED_ZIP%' -DestinationPath 'runtime' -Force"
    if not exist "runtime\python.exe" (
        echo ERROR: Extraction failed — runtime\python.exe not found.
        exit /b 1
    )
    echo   Extracted successfully.
)

rem --- Step 2: Patch ._pth file to enable pip ---
echo [2/4] Patching Python path configuration for pip support...
set "PTH_FILE="
for %%f in (runtime\python*._pth) do set "PTH_FILE=%%f"

if "%PTH_FILE%"=="" (
    echo WARNING: No ._pth file found. Pip may not work correctly.
) else (
    powershell -NoProfile -Command "(Get-Content '%PTH_FILE%') -replace '^#import site','import site' | Set-Content '%PTH_FILE%'"
    echo   Patched: %PTH_FILE%
)

rem --- Step 3: Bootstrap pip ---
if exist "runtime\Scripts\pip.exe" (
    echo [3/4] pip already installed — skipping bootstrap.
) else (
    echo [3/4] Bootstrapping pip...
    if not exist "vendor\get-pip.py" (
        echo ERROR: vendor\get-pip.py not found!
        exit /b 1
    )
    runtime\python.exe vendor\get-pip.py --no-index --find-links vendor\packages
    if %errorlevel% neq 0 (
        echo ERROR: pip bootstrap failed.
        exit /b 1
    )
    echo   pip installed successfully.
)

rem --- Step 4: Install all dependencies ---
echo [4/4] Installing dependencies from offline wheels...
runtime\python.exe -m pip install --no-index --find-links vendor\packages -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Dependency installation failed.
    echo Check that all required .whl files are in vendor\packages\
    exit /b 1
)

rem --- Verify ---
echo.
echo Verifying all imports...
runtime\python.exe -c "import streamlit, pandas, openpyxl, bcrypt, xlrd, deepdiff, st_aggrid, plotly, jinja2; print('All 9 packages verified OK')"
if %errorlevel% neq 0 (
    echo ERROR: Import verification failed.
    exit /b 1
)

echo.
echo ----------------------------------------------------------
echo   Python runtime setup complete!
echo   Location: runtime\python.exe
echo ----------------------------------------------------------
echo.
