@echo off
:: run_sync.bat

:: Navigate to script directory
cd /d "%~dp0"

:: Run the Python script
python main.py

:: Pause if there's an error
if errorlevel 1 pause