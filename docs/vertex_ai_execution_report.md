# Vertex AI パイプライン実行レポート

## 実行概要

- **実行日時**: 2025-12-21 01:31:31
- **ジョブID**: `trading-ml-pipeline-20251221013131`
- **ステータス**: 提出成功（実行中）

---

## パイプライン構成

### 実行されるコンポーネント

1. **前処理** (`standard_scaler`)
   - 欠損値処理
   - 重複削除
   - 標準化

2. **特徴量エンジニアリング** (`technical_indicators`)
   - RSI計算
   - MACD計算
   - 移動平均（SMA）計算

3. **並列学習** (`random_forest`) - 4ジ ョブ並列実行
   - ジョブ1: `["Open", "Close"]`
   - ジョブ2: `["Open", "Close", "Volume"]`
   - ジョブ3: `["Open", "High", "Low", "Close", "Volume"]`
   - ジョブ4: `["RSI", "MACD", "SMA_20"]`

4. **実験結果集約** (`experiment_aggregator`)
   - 4モデルの比較
   - ベストモデル選択（accuracy基準）

---

## 実行URL

**Vertex AI Console**:
```
https://console.cloud.google.com/vertex-ai/locations/us-central1/pipelines/runs/trading-ml-pipeline-20251221013131?project=245533195318
```

**パイプライン一覧**:
```
https://console.cloud.google.com/vertex-ai/pipelines?project=helpful-girder-421422
```

---

## 実行パラメータ

### データソース
- **入力**: `gs://trade-mlops-bucket/data/stock.csv` (93.85 KB)
- **サンプル数**: 1000行
- **列**: Date, Open, High, Low, Close, Volume, Target

### モデルパラメータ
```yaml
n_estimators: 100
max_depth: 10
random_state: 42
class_weight: balanced
```

---

## 期待される出力

### GCS保存先

1. **処理済みデータ**
   - `gs://trade-mlops-bucket/processed/stock_processed.csv`

2. **特徴量データ**
   - `gs://trade-mlops-bucket/features/stock_features.csv`

3. **モデル** (4ファイル)
   - `gs://trade-mlops-bucket/models/model_Open,Close.pkl`
   - `gs://trade-mlops-bucket/models/model_Open,Close,Volume.pkl`
   - `gs://trade-mlops-bucket/models/model_Open,High,Low,Close,Volume.pkl`
   - `gs://trade-mlops-bucket/models/model_RSI,MACD,SMA_20.pkl`

4. **メトリクス** (4ファイル)
   - `gs://trade-mlops-bucket/models/model_*_metrics.json`

5. **実験レポート**
   - `gs://trade-mlops-bucket/reports/experiment_comparison.md`

---

## モニタリング方法

### 方法1: Vertex AI Console（推奨）

1. 上記のURLにアクセス
2. パイプラインのDAG（有向非巡回グラフ）を確認
3. 各コンポーネントの状態を確認:
   - ✅ 成功
   - ⏳ 実行中
   - ❌ 失敗

### 方法2: Pythonコード

```python
from google.cloud import aiplatform

aiplatform.init(project="helpful-girder-421422", location="us-central1")

# ジョブを取得
job = aiplatform.PipelineJob.get(
    'projects/245533195318/locations/us-central1/pipelineJobs/trading-ml-pipeline-20251221013131'
)

# ステータス確認
print(f"State: {job.state}")
print(f"Error: {job.error}")
```

### 方法3: GCSファイル確認

```cmd
# 完了後、結果を確認
venv\Scripts\activate
python scripts\list_gcs_files.py models/
python scripts\list_gcs_files.py reports/
```

---

## 予想実行時間

- **前処理**: 約1-2分
- **特徴量エンジニアリング**: 約2-3分
- **並列学習** (4ジョブ): 約5-10分
- **実験集約**: 約1分

**合計**: 約10-15分

---

## ローカル実行との比較

### ローカル実行結果

```
Testing features: ['Open', 'Close', 'Volume']
Accuracy: 0.4650
Model saved locally: models\local_test_model.pkl
実行時間: 約30秒
```

### Vertex AI実行（期待値）

```
4つの特徴量組み合わせで並列実行:
- Model 1: ['Open', 'Close']
- Model 2: ['Open', 'Close', 'Volume'] ← ローカルと同じ
- Model 3: ['Open', 'High', 'Low', 'Close', 'Volume']
- Model 4: ['RSI', 'MACD', 'SMA_20']

期待される精度: 0.45-0.55の範囲
ベストモデル: 自動選択

実行時間: 約10-15分（並列実行のため）
```

---

## 結果確認手順

### 1. 実行完了の確認

```cmd
# Vertex AI Consoleで確認
# または
python -c "from google.cloud import aiplatform; aiplatform.init(project='helpful-girder-421422', location='us-central1'); job = aiplatform.PipelineJob.get('projects/245533195318/locations/us-central1/pipelineJobs/trading-ml-pipeline-20251221013131'); print(job.state)"
```

### 2. 出力ファイルの確認

```cmd
# モデルファイル
python scripts\list_gcs_files.py models/

# レポート
python scripts\list_gcs_files.py reports/
```

### 3. 実験レポートのダウンロード

```cmd
# デフォルトのgsutilがある場合
gsutil cp gs://trade-mlops-bucket/reports/experiment_comparison.md reports/

# または、Pythonスクリプトで
python -c "from google.cloud import storage; fs = storage.Client(); bucket = fs.bucket('trade-mlops-bucket'); blob = bucket.blob('reports/experiment_comparison.md'); content = blob.download_as_text(); print(content)"
```

### 4. ベストモデルの確認

`experiment_comparison.md`に以下の情報が含まれます:
- 全モデルのメトリクス比較
- ベストモデルの詳細
- Top 5ランキング

---

## トラブルシューティング

### ジョブが失敗した場合

1. **Vertex AI Consoleで確認**
   - 失敗したコンポーネントをクリック
   - ログタブでエラーメッセージを確認

2. **よくあるエラー**

**データが見つからない**:
```
Error: gs://trade-mlops-bucket/data/stock.csv not found
```
解決方法:
```cmd
python scripts\upload_to_gcs.py
```

**権限エラー**:
```
Error: Permission denied
```
解決方法: `docs/gcs_permission_setup.md` 参照

**メモリ不足**:
```
Error: Out of memory
```
解決方法: `pipeline_config.yaml`でサンプル数を減らす

---

## 次のステップ

1. ✅ **実行完了を待つ** (約10-15分)

2. ✅ **結果を確認**
   ```cmd
   python scripts\list_gcs_files.py reports/
   ```

3. ✅ **ローカル結果と比較**
   - ローカル: Accuracy 0.4650
   - Vertex AI: 4モデルの中で最良の精度を確認

4. ✅ **レポート分析**
   - どの特徴量組み合わせが最良か
   - 精度の改善余地はあるか

5. ✅ **次の実験**
   - 設定を調整して再実行
   - 異なるハイパーパラメータを試す

---

## まとめ

### 実行内容
- ✅ パイプラインをVertex AIに提出
- ✅ 4つの特徴量組み合わせで並列実行
- ✅ 自動的にベストモデルを選択

### 期待される成果
- ローカル実行と同等以上の精度
- 複数モデルの比較レポート
- 本番環境への展開準備完了

**ステータス**: 実行中 → Vertex AI Consoleで進捗確認
