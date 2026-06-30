@echo off
rem ============================================================================
rem  diagnose_network.bat — Offline Network Diagnostics Dashboard Launcher
rem ============================================================================

set "PYTHON_EXE="

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

echo ERROR: Python executable not found. Please install Python or run App.bat first.
pause
exit /b 1

:found_python
%PYTHON_EXE% src\diagnose_network.py
pause
