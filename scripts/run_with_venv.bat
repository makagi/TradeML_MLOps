@echo off
REM Helper script to run Python scripts with venv automatically activated

REM Move to project root
cd /d "%~dp0\.."

REM Check argument
if "%~1"=="" (
    echo Usage: run_with_venv.bat ^<script.py^> [args...]
    echo Example: run_with_venv.bat test_system.py
    echo Example: run_with_venv.bat run_pipeline.py config/pipeline_config.yaml
    pause
    exit /b 1
)

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo Please run: scripts\setup_venv.bat
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [INFO] Virtual environment activated
echo [INFO] Python: 
python --version
echo.

REM Run script with all arguments
echo [INFO] Executing: python %*
echo.
python %*

REM Capture exit code
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE%==0 (
    echo [SUCCESS] Script completed successfully
) else (
    echo [ERROR] Script exited with error code %EXIT_CODE%
)

REM venv automatically deactivates, no need for deactivate
exit /b %EXIT_CODE%
