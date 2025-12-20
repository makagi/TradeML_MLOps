@echo off
cd /d %~dp0\..

echoString ========================================================
echo Vertex AI MLOps Environment Setup for Windows
echo ========================================================

REM 1. Pythonの確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

REM 2. 仮想環境(venv)の作成
if not exist "venv" (
    echo [INFO] Creating virtual environment (venv)...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists.
)

REM 3. 仮想環境の有効化とライブラリインストール
echo [INFO] Activating venv and installing requirements...
call venv\Scripts\activate

python -m pip install --upgrade pip
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [INFO] Dependencies installed.
) else (
    echo [WARNING] requirements.txt not found. Skipping installation.
)

REM 4. Google Cloud認証チェック (gcloud CLIが必要)
echo ========================================================
echo Checking Google Cloud Authentication...
call gcloud auth application-default print-access-token >nul 2>&1
if %errorlevel% neq 0 (
    echo [ACTION REQUIRED] Please login to Google Cloud.
    echo Opening browser for authentication...
    call gcloud auth application-default login
) else (
    echo [OK] Google Cloud credentials found.
)

echo ========================================================
echo Setup Complete! The virtual environment is active.
echo You can now run: python pipelines/trading_pipeline.py
echo ========================================================


