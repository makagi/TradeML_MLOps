@echo off
cd /d %~dp0\..

if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found.
    pause
    exit /b
)

echo [INFO] Running Local Tests...
call venv\Scripts\python -m unittest discover tests

if %errorlevel% neq 0 (
    echo [ERROR] Tests failed.
) else (
    echo [SUCCESS] All tests passed.
)


