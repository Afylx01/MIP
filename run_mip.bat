@echo off
rem ==============================================================================
rem run_mip.bat — Windows One-Click Quantitative Workstation Launcher
rem ==============================================================================
rem Supported: Windows 10, Windows 11 (x86_64 and ARM64)
rem Prerequisites: Python 3.10+ installed and added to Windows PATH
rem ==============================================================================

title Project MIP — Institutional Momentum Workstation
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in system PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python -c "import pandas, pyarrow, numpy, requests, dotenv" >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Quantitative libraries not found. Installing dependencies from requirements.txt...
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please verify your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully.
    echo.
)

python run_mip.py %*

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Workstation exited with status %errorlevel%.
    pause
)
