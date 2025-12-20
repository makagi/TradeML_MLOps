@echo off
REM セットアップスクリプト - 仮想環境の作成とパッケージインストール

echo ============================================
echo   TradeML MLOps - 環境セットアップ
echo ============================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0\.."

REM 仮想環境が既に存在するかチェック
if exist "venv\" (
    echo [INFO] 仮想環境は既に存在します。
    echo.
    choice /C YN /M "仮想環境を再作成しますか？（既存の環境は削除されます）"
    if errorlevel 2 goto :install_deps
    if errorlevel 1 goto :recreate_venv
) else (
    goto :create_venv
)

:recreate_venv
echo [INFO] 既存の仮想環境を削除中...
rmdir /s /q venv
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境の削除に失敗しました
    pause
    exit /b 1
)

:create_venv
echo [INFO] 仮想環境を作成中...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境の作成に失敗しました
    echo Pythonが正しくインストールされているか確認してください
    pause
    exit /b 1
)
echo [SUCCESS] 仮想環境が作成されました
echo.

:install_deps
echo [INFO] 仮想環境を有効化中...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

echo [INFO] Pythonバージョン確認:
python --version
echo.

echo [INFO] pipをアップグレード中...
python -m pip install --upgrade pip
echo.

echo [INFO] 依存関係をインストール中...
echo この処理には数分かかる場合があります...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依存関係のインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo ============================================
echo   セットアップ完了！
echo ============================================
echo.
echo 次のステップ:
echo   1. config/pipeline_config.yaml を編集してプロジェクトIDを設定
echo   2. 仮想環境を有効化: venv\Scripts\activate
echo   3. システムテスト実行: python test_system.py
echo   4. パイプライン実行: python run_pipeline.py
echo.
echo 注意: パイプライン実行時は必ず仮想環境を有効化してください！
echo.
pause
