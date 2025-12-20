@echo off
REM 仮想環境を有効化してスクリプトを実行するヘルパー

REM プロジェクトルートに移動
cd /d "%~dp0\.."

REM 引数チェック
if "%~1"=="" (
    echo 使い方: run_with_venv.bat ^<script.py^> [args...]
    echo 例: run_with_venv.bat test_system.py
    echo 例: run_with_venv.bat run_pipeline.py config/pipeline_config.yaml
    pause
    exit /b 1
)

REM 仮想環境の存在確認
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 仮想環境が見つかりません
    echo 先に scripts\setup_venv.bat を実行してください
    pause
    exit /b 1
)

REM 仮想環境を有効化
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

echo [INFO] 仮想環境が有効化されました
echo [INFO] Python: 
python --version
echo.

REM スクリプトを実行（すべての引数を渡す）
echo [INFO] 実行中: python %*
echo.
python %*

REM 終了コードを保持
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE%==0 (
    echo [SUCCESS] スクリプトが正常に完了しました
) else (
    echo [ERROR] スクリプトがエラーコード %EXIT_CODE% で終了しました
)

REM 仮想環境は自動的に非アクティブになるため、deactivateは不要
exit /b %EXIT_CODE%
