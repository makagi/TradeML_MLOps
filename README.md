# トレーディング用 Vertex AI パイプライン

このプロジェクトは、BigQuery からデータを読み込み、PyTorch モデルをトレーニングし、結果を保存する Vertex AI パイプラインを実装します。MLOps ワークフローのテンプレートとして設計されています。

## 前提条件

*   Windows OS
*   Python 3.9 以上
*   Google Cloud SDK (`gcloud` CLI) がインストールされ、認証されていること。

## プロジェクト構成

*   `pipelines/`: パイプライン定義とコンポーネントロジックが含まれています。
    *   `trading_pipeline.py`: メインのパイプラインコード。
    *   `submit_pipeline.py`: パイプラインを Vertex AI に送信するためのスクリプト。
*   `scripts/`: セットアップと実行のためのヘルパースクリプト。
    *   `setup.bat`: 仮想環境 (`venv`) をセットアップします。
    *   `run_pipeline.bat`: パイプラインを JSON にコンパイルします。
    *   `submit_job.bat`: ジョブを Vertex AI に送信します。
    *   `test_local.bat`: ローカル単体テストを実行します。
*   `tests/`: 単体テスト。

## セットアップ

1.  プロジェクトのルートでターミナルを開きます。
2.  セットアップスクリプトを実行します:
    ```cmd
    scripts\setup.bat
    ```
    これにより `venv` が作成され、必要なパッケージがインストールされます。

## 使用方法

### 1. パイプラインのコンパイル
パイプラインコードを `trading_pipeline.json` にコンパイルするには:
```cmd
scripts\run_pipeline.bat
```

### 2. ローカルテストの実行
コンポーネントとコンパイルをローカルで検証するには:
```cmd
scripts\test_local.bat
```

### 3. Vertex AI への送信
パイプラインジョブを Vertex AI に送信するには:
```cmd
scripts\submit_job.bat
```
*注意: `pipelines/submit_pipeline.py` のバケット URL を正しく更新していることを確認してください。*

## 設定

*   **Project ID**: `pipelines/trading_pipeline.py` と `pipelines/submit_pipeline.py` で設定されています。
*   **Credentials**: `scripts/setup.bat` が `gcloud` のログイン状態を確認します。
