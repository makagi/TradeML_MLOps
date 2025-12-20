@echo off
cd /d %~dp0\..

echo [INFO] Activating virtual environment...
if exist "venv" (
    call venv\Scripts\activate
) else (
    echo [ERROR] Virtual environment 'venv' not found.
    pause
    exit /b
)

echo [INFO] Running local training...
python src/train.py ^
    --data_path "data/stock.csv" ^
    --features "Open,Close,Volume" ^
    --model_output_path "models/model_local.pkl" ^
    --n_estimators 10

if %errorlevel% neq 0 (
    echo [ERROR] Training failed.
) else (
    echo [SUCCESS] Training completed. Model saved to models/model_local.pkl
)

pause
