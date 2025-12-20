@echo off
REM Vertex AI パイプライン実行準備スクリプト

echo ============================================
echo   Vertex AI Pipeline - Setup and Execution
echo ============================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0\.."

REM 仮想環境の確認
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo Please run: scripts\setup_venv.bat
    pause
    exit /b 1
)

REM 仮想環境を有効化
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM ステップ1: サンプルデータ生成
echo ============================================
echo Step 1: Generate Sample Data
echo ============================================
echo.

if exist "data\stock.csv" (
    echo [INFO] data\stock.csv already exists
    choice /C YN /M "Regenerate sample data?"
    if errorlevel 2 goto :skip_generate
)

python scripts\generate_sample_data.py 1000 data\stock.csv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to generate sample data
    pause
    exit /b 1
)

:skip_generate
echo.

REM ステップ2: データをGCSにアップロード
echo ============================================
echo Step 2: Upload Data to GCS
echo ============================================
echo.

choice /C YN /M "Upload data to GCS?"
if errorlevel 2 goto :skip_upload

python scripts\upload_to_gcs.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upload to GCS
    pause
    exit /b 1
)

:skip_upload
echo.

REM ステップ3: パイプラインのコンパイル
echo ============================================
echo Step 3: Compile Pipeline
echo ============================================
echo.

python run_pipeline.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to compile pipeline
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Verify GCS bucket contains: data/stock.csv
echo   2. Review compiled pipeline: trading_pipeline.json
echo   3. Submit to Vertex AI: python run_pipeline.py (and answer 'y')
echo.
pause
