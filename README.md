# Hybrid MLOps Trading System with YAML Configuration

このプロジェクトは、YAML設定ベースのモジュラーMLパイプラインアーキテクチャを実装しています。

## 🎯 特徴

- **YAML設定管理**: パイプラインの構成を宣言的に定義
- **モジュラーコンポーネント**: 層ごとに分離された再利用可能なコンポーネント
- **KFP統合**: Kubeflow Pipelines (KFP) の機能を最大限活用
- **並列実験**: 複数の特徴量組み合わせやハイパーパラメータを並列実行
- **ハイブリッド実行**: ローカル開発とクラウド実行の両方をサポート

## 📁 プロジェクト構造

```
TradeML_MLOps/
├── config/
│   └── pipeline_config.yaml          # パイプライン設定（メイン）
├── src/                              # コアロジック
│   ├── components/                   # パイプラインコンポーネント
│   ├── utils/                        # ユーティリティ（Config, Registry等）
│   ├── pipeline_builder.py           # パイプライン構築エンジン
│   └── train.py                      # ローカル学習スクリプト
├── scripts/                          # ユーザーインターフェース (UI)
│   ├── run_pipeline.bat              # パイプライン実行
│   ├── prepare_vertex_ai.bat         # 初期セットアップ
│   └── verify_run.py                 # クラウド実行結果の確認
├── tests/                            # 内部検証・パリティ確認
│   ├── test_system.py                # システム構成テスト
│   ├── test_parity.py                # ローカル/クラウド精度一致確認
│   └── test_components.py            # コンポーネント単体テスト
├── README.md
└── requirements.txt                  # 依存関係 (Python 3.11/安定版)
```

| フォルダ | 役割 |
| :--- | :--- |
| `scripts/` | 開発者がパイプラインを操作し、データを管理するためのツール群。 |
| `tests/` | システムの整合性、精度の再現性、および各機能の正しさを検証するための内部ツール。 |

## 🚀 セットアップ

### クイックスタート（推奨）

自動セットアップスクリプトを使用：

```cmd
scripts\setup_venv.bat
```

このスクリプトが以下を自動実行します：
- 仮想環境の作成
- pipのアップグレード
- 依存関係のインストール

### 1. Python環境のセットアップ（手動）

> [!IMPORTANT]
> **仮想環境を必ず使用してください！** システム全体のPython環境を汚染せず、依存関係を分離します。

```cmd
# 仮想環境作成（初回のみ）
python -m venv venv

# 仮想環境有効化（毎回必須）
venv\Scripts\activate

# プロンプトが (venv) で始まることを確認
# 例: (venv) D:\work\AI-Trade\TradeML_MLOps>

# 依存関係インストール
pip install -r requirements.txt
```

**重要**: パイプラインを実行する前に、**必ず仮想環境を有効化**してください。有効化されていない場合、`ModuleNotFoundError`が発生します。

### 2. Google Cloud認証設定

認証情報は以下の優先順位で使用されます：

**方法1: 環境変数（推奨）**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=D:\work\GOOGLE_APPLICATION_CREDENTIALS\helpful-girder-421422-ee6bb27e5b9a.json
```

**方法2: 設定ファイル**

[`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) に記載：
```yaml
environment:
  credentials_path: "D:\\work\\GOOGLE_APPLICATION_CREDENTIALS\\helpful-girder-421422-ee6bb27e5b9a.json"
```

**方法3: デフォルト認証**
```cmd
gcloud auth application-default login
```

> [!NOTE]
> 環境変数が設定されている場合は、それが優先されます。設定ファイルのパスは環境変数が未設定の場合のフォールバックとして使用されます。

### 3. 設定ファイルの確認

[`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) を編集して、プロジェクトIDやバケット名を設定します。

## 📝 使い方

> [!WARNING]
> すべてのコマンドを実行する前に、**仮想環境を有効化**してください: `venv\Scripts\activate`

### システムテスト

設定とコンポーネントが正しく登録されているか確認：

```cmd
# 仮想環境を有効化
venv\Scripts\activate

# テスト実行
python test_system.py
```

または、ヘルパースクリプトを使用（自動的にvenvを有効化）：

```cmd
scripts\run_with_venv.bat test_system.py
```

### 🚀 Vertex AI実行準備

初回実行の準備を自動化：

```cmd
scripts\prepare_vertex_ai.bat
```

このスクリプトは以下を実行：
1. サンプルデータ生成（1000行のOHLCV株価データ）
2. GCSへのアップロード
3. パイプラインのコンパイル

**手動実行**:

```cmd
# 1. サンプルデータ生成
venv\Scripts\activate
python scripts\generate_sample_data.py 1000 data\stock.csv

# 2. GCSアップロード
python scripts\upload_to_gcs.py

# 3. パイプライン実行
python run_pipeline.py
```

詳細は [`docs/vertex_ai_execution_guide.md`](file:///d:/work/AI-Trade/TradeML_MLOps/docs/vertex_ai_execution_guide.md) を参照。

### パイプライン実行

#### オプション1: 対話的実行

```cmd
# 仮想環境を有効化
venv\Scripts\activate

# パイプライン実行
python run_pipeline.py
```

または：

```cmd
scripts\run_with_venv.bat run_pipeline.py
```

このスクリプトは：
1. YAML設定を読み込み
2. パイプラインをビルド
3. KFP JSONにコンパイル
4. Vertex AIへの提出を確認

#### オプション2: Pythonスクリプトから

```python
from src.pipeline_builder import PipelineBuilder

# パイプラインビルダー作成
builder = PipelineBuilder('config/pipeline_config.yaml')

# パイプライン構築とコンパイル
builder.build_pipeline()
builder.compile('trading_pipeline.json')

# Vertex AIに提出
builder.submit('trading_pipeline.json')
```

## ⚙️ 設定のカスタマイズ

### コンポーネントの選択

[`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) で各層のコンポーネントを選択：

```yaml
components:
  preprocessing:
    type: "standard_scaler"  # 前処理タイプを選択
    enabled: true
    params:
      fillna_strategy: "forward_fill"
  
  feature_engineering:
    type: "technical_indicators"  # 特徴量エンジニアリング選択
    enabled: true
    params:
      indicators:
        - name: "RSI"
          period: 14
```

### 実験設定（並列実行）

複数の特徴量組み合わせを並列実行：

```yaml
experiments:
  mode: "grid_search"
  feature_combinations:
    - ["Open", "Close"]
    - ["Open", "Close", "Volume"]
    - ["Open", "High", "Low", "Close", "Volume"]
    - ["RSI", "MACD", "SMA_20"]
```

## 🧩 新しいコンポーネントの追加

### 1. コンポーネント実装

```python
# src/components/training/xgboost.py
from kfp import dsl
from src.utils.component_registry import register_component

@register_component('xgboost')  # レジストリに登録
@dsl.component(
    base_image="python:3.9",
    packages_to_install=["pandas", "xgboost", "scikit-learn"]
)
def xgboost_component(
    data_path: str,
    features: str,
    model_output_path: str,
    # ... その他のパラメータ
):
    """XGBoostモデル学習コンポーネント"""
    # 実装...
    pass
```

### 2. コンポーネントをインポート

```python
# src/components/__init__.py に追加
from src.components.training.xgboost import xgboost_component
```

### 3. YAML設定で使用

```yaml
components:
  training:
    type: "xgboost"  # 新しいコンポーネントを選択
    enabled: true
    params:
      max_depth: 6
      learning_rate: 0.1
```

## 🔧 アーキテクチャ

### YAML設定 → KFPパイプライン変換フロー

```
config/pipeline_config.yaml
    ↓
ConfigLoader (設定読み込み・検証)
    ↓
PipelineBuilder (パイプライン構築)
    ↓
ComponentRegistry (コンポーネント取得)
    ↓
KFP Pipeline (dsl.pipeline)
    ↓
Compiler (JSON生成)
    ↓
Vertex AI PipelineJob (実行)
```

### コンポーネント層

1. **前処理層** (`preprocessing/`)
   - データクリーニング
   - 欠損値処理
   - 正規化・標準化

2. **特徴量エンジニアリング層** (`feature_engineering/`)
   - テクニカル指標計算
   - カスタム特徴量生成

3. **モデル学習層** (`training/`)
   - RandomForest
   - XGBoost
   - LightGBM
   - LSTM（将来）

4. **評価層** (`evaluation/`)
   - メトリクス計算
   - モデル比較
   - ベストモデル選択

## 📊 Vertex AI実験トラッキング

パイプライン実行時、メトリクスは自動的にVertex AI Experimentsにログされます：

- モデル精度
- 使用した特徴量
- ハイパーパラメータ

## 🐛 トラブルシューティング

### ❌ ModuleNotFoundError: No module named 'kfp'

**原因**: 仮想環境が有効化されていない、または依存関係がインストールされていない

**解決方法**:
```cmd
# 1. 仮想環境を有効化
venv\Scripts\activate

# 2. プロンプトが (venv) で始まることを確認
# 正しい例: (venv) D:\work\AI-Trade\TradeML_MLOps>
# 誤った例: D:\work\AI-Trade\TradeML_MLOps>

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. インストール確認
pip list | findstr kfp
```

### 仮想環境の確認方法

現在の環境を確認：
```cmd
# Pythonの場所を確認
where python

# 正しい例（venv内）: D:\work\AI-Trade\TradeML_MLOps\venv\Scripts\python.exe
# 誤った例（システム）: C:\Users\...\Python39\python.exe
```

### Google Cloud認証エラー

```cmd
# 認証情報のパスを確認
echo %GOOGLE_APPLICATION_CREDENTIALS%

# gcloud認証
gcloud auth application-default login
```

### コンポーネントが見つからない

`test_system.py`を実行してコンポーネント登録を確認：

```cmd
# 仮想環境を有効化してから実行
venv\Scripts\activate
python test_system.py
```

## 📚 参考資料

- [Kubeflow Pipelines Documentation](https://www.kubeflow.org/docs/components/pipelines/)
- [Vertex AI Pipelines Guide](https://cloud.google.com/vertex-ai/docs/pipelines)
- [設計ドキュメント](file:///C:/Users/masak/.gemini/antigravity/brain/a7be8cd8-fa41-4b68-af45-b9da0e1eb1ce/revised_approach.md)
- [Gitブランチ戦略とAI連携](file:///d:/work/AI-Trade/TradeML_MLOps/docs/git_branch_strategy.md)

