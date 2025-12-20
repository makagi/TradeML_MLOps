# Vertex AI パイプライン実行ガイド

このガイドでは、Vertex AI上でMLパイプラインを初めて実行する手順を説明します。

## 前提条件

- [x] 仮想環境のセットアップ (`scripts\setup_venv.bat`)
- [x] Google Cloud認証の設定
- [x] GCSバケットの作成: `gs://trade-mlops-bucket`
- [x] 権限を持つサービスアカウント: `akamlops@helpful-girder-421422.iam.gserviceaccount.com`

---

## クイックスタート（自動化）

自動セットアップスクリプトを使用：

```cmd
scripts\prepare_vertex_ai.bat
```

このスクリプトは以下を実行します：
1. ✓ サンプル株価データの生成
2. ✓ GCSへのアップロード
3. ✓ パイプラインのコンパイル
4. Vertex AIへの提出確認

---

## 手動実行（ステップバイステップ）

### ステップ1: サンプルデータの生成

リアルなOHLCV株価データを作成：

```cmd
venv\Scripts\activate
python scripts\generate_sample_data.py 1000 data\stock.csv
```

**出力**: `data/stock.csv` (1000行、OHLCVとTarget列)

### ステップ2: GCSへのアップロード

```cmd
python scripts\upload_to_gcs.py
```

**確認**: `gs://trade-mlops-bucket/data/stock.csv`

### ステップ3: パイプライン設定の確認

必要に応じて [`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) を編集：

```yaml
# 以下の設定を確認
environment:
  project_id: "helpful-girder-421422"
  bucket: "gs://trade-mlops-bucket"

data:
  raw_data_path: "gs://trade-mlops-bucket/data/stock.csv"
```

### ステップ4: パイプラインのコンパイル

```cmd
python run_pipeline.py
```

**出力**: `trading_pipeline.json`

### ステップ5: Vertex AIへの提出

プロンプトが表示されたら `y` を入力：

```
[SUBMIT?] Submit to Vertex AI? [y/N]: y
```

またはプログラムから：

```python
from src.pipeline_builder import PipelineBuilder

builder = PipelineBuilder('config/pipeline_config.yaml')
builder.build_pipeline()
builder.compile('trading_pipeline.json')
builder.submit('trading_pipeline.json')
```

---

## 実行時の動作

### パイプラインフロー

```
1. 前処理 (standard_scaler)
   ↓
2. 特徴量エンジニアリング (technical_indicators)
   ↓ 
3. 並列学習 (4つの特徴量組み合わせ)
   ├─ ["Open", "Close"]
   ├─ ["Open", "Close", "Volume"]
   ├─ ["Open", "High", "Low", "Close", "Volume"]
   └─ ["RSI", "MACD", "SMA_20"]
   ↓
4. 実験結果集約
   └─ 精度によりベストモデルを選択
```

### 出力されるファイル

**GCS保存場所**:
- モデル: `gs://trade-mlops-bucket/models/model_*.pkl`
- メトリクス: `gs://trade-mlops-bucket/models/model_*_metrics.json`
- レポート: `gs://trade-mlops-bucket/reports/experiment_comparison.md`

### 実行時間

- **前処理**: 約1-2分
- **特徴量エンジニアリング**: 約2-3分
- **並列学習**: 約5-10分（4ジョブ並列）
- **結果集約**: 約1分

**合計**: 約10-15分

---

## 実行のモニタリング

### Vertex AI Console

1. [Vertex AI Pipelines Console](https://console.cloud.google.com/vertex-ai/pipelines) を開く
2. プロジェクト選択: `helpful-girder-421422`
3. パイプラインを探す: `trading-ml-pipeline`
4. クリックして実行グラフを表示

### ログの確認

```python
# Pythonで確認
from google.cloud import aiplatform

aiplatform.init(
    project="helpful-girder-421422",
    location="us-central1"
)

# 最近のパイプラインジョブをリスト
jobs = aiplatform.PipelineJob.list()
for job in jobs[:5]:
    print(f"{job.display_name}: {job.state}")
```

### 結果の確認

完了後、GCSバケットを確認：

```cmd
# gsutilを使用（インストール済みの場合）
gsutil ls gs://trade-mlops-bucket/models/
gsutil cat gs://trade-mlops-bucket/reports/experiment_comparison.md

# または
python scripts\list_gcs_files.py models/
```

---

## トラブルシューティング

### 認証エラー

```
Error: Could not authenticate
```

**解決方法**:
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=D:\work\GOOGLE_APPLICATION_CREDENTIALS\helpful-girder-421422-ee6bb27e5b9a.json
gcloud auth application-default login
```

### 権限エラー

```
Error: Permission denied on bucket
```

**解決方法**: サービスアカウントに以下のロールがあることを確認：
- `roles/storage.objectAdmin`
- `roles/aiplatform.user`

詳細は [`docs/gcs_permission_setup.md`](file:///d:/work/AI-Trade/TradeML_MLOps/docs/gcs_permission_setup.md) を参照。

### データが見つからない

```
Error: gs://trade-mlops-bucket/data/stock.csv not found
```

**解決方法**:
```cmd
python scripts\upload_to_gcs.py
```

### パイプライン実行中の失敗

Vertex AI Consoleでコンポーネントログを確認：
1. 失敗したコンポーネントをクリック
2. **ログ** タブを表示
3. エラーメッセージを確認

よくある問題：
- Pythonパッケージの不足 → コンポーネントの `packages_to_install` を確認
- データ形式の不一致 → CSV構造が期待される列と一致するか確認

---

## 初回実行後の次のステップ

### 1. 結果のレビュー

```cmd
# 実験レポートをダウンロード
gsutil cp gs://trade-mlops-bucket/reports/experiment_comparison.md reports/
```

### 2. 設定の調整

結果に基づいて [`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) を変更：

```yaml
# 異なる特徴量組み合わせを試す
experiments:
  feature_combinations:
    - ["RSI", "MACD"]
    - ["SMA_20", "SMA_50", "Volume"]

# モデルパラメータを調整
components:
  training:
    params:
      n_estimators: 200  # より多くの木
      max_depth: 15      # より深い木
```

### 3. パイプラインの再実行

```cmd
python run_pipeline.py
# 'y' で提出
```

### 4. 実験の比較

Vertex AI Experimentsで複数の実行を比較：
- Vertex AI → Experiments に移動
- 実行間のメトリクスを表示
- 各実験のベストモデルを比較

---

## コスト見積もり

1000サンプルの場合のおおよそのコスト（4並列ジョブ）：

- **コンピュート**: 約$0.50-1.00 / 回
- **ストレージ**: サンプルデータでは無視できる程度
- **パイプラインオーケストレーション**: Vertex AIに含まれる

本番環境で大規模データセットを使用する場合は、[Vertex AI料金](https://cloud.google.com/vertex-ai/pricing)を確認してください。

---

## 高度な使用: スケジュール実行

### Cloud Schedulerとの統合

```python
# スケジュール実行するパイプライン（例）
from google.cloud import aiplatform

pipeline = aiplatform.PipelineJob(
    display_name="daily-trading-pipeline",
    template_path="trading_pipeline.json",
    pipeline_root="gs://trade-mlops-bucket/pipeline_root",
    enable_caching=False
)

# スケジュール設定（Cloud Schedulerのセットアップが必要）
# 参照: https://cloud.google.com/vertex-ai/docs/pipelines/schedule-pipeline
```

---

## サポート

- **ドキュメント**: [README.md](file:///d:/work/AI-Trade/TradeML_MLOps/README.md) を参照
- **システムテスト**: `python test_system.py` を実行
- **コンポーネント詳細**: `src/components/` ディレクトリを確認
- **権限設定**: [docs/gcs_permission_setup.md](file:///d:/work/AI-Trade/TradeML_MLOps/docs/gcs_permission_setup.md)

---

**実行準備完了？** 実行: `scripts\prepare_vertex_ai.bat`
