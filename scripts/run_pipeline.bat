@echo off
cd /d %~dp0\..

if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run scripts\setup.bat first.
    pause
    exit /b
)

echo [INFO] Running Trading Pipeline...
call venv\Scripts\python pipelines\trading_pipeline.py

if %errorlevel% neq 0 (
    echo [ERROR] Pipeline execution failed.
) else (
    echo [SUCCESS] Pipeline execution completed.
)


