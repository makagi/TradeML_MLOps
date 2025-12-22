# -*- coding: utf-8 -*-
"""分類メトリクス評価コンポーネント"""
from kfp import dsl
from src.utils.component_registry import register_component


@register_component('classification_metrics')
@dsl.component(
    base_image="python:3.11",
    packages_to_install=["pandas==2.2.3", "scikit-learn==1.5.2", "matplotlib==3.9.2", "seaborn==0.13.2", "gcsfs==2024.10.0", "joblib==1.4.2"]
)
def classification_metrics_component(
    models_dir: str,
    test_data_path: str,
    metrics: list,
    save_confusion_matrix: bool = True,
    output_report_path: str = "",
) -> dict:
    """分類モデルの評価メトリクスを計算するコンポーネント
    
    Args:
        models_dir: モデルファイルが格納されているディレクトリ (GCS or Local)
        test_data_path: テストデータのパス (CSV, GCS or Local)
        metrics: 計算するメトリクスのリスト (例: ["accuracy", "f1"])
        save_confusion_matrix: 混同行列を保存するか
        output_report_path: 評価レポートの保存パス (GCS or Local)
    
    Returns:
        評価メトリクス辞書
    """
    import pandas as pd
    import numpy as np
    import joblib
    import json
    import os
    import glob
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    from io import BytesIO
    import gcsfs

    print(f"Starting evaluation...")
    print(f"Models directory: {models_dir}")
    print(f"Test data: {test_data_path}")

    # GCSファイルシステムの準備
    fs = None
    if models_dir.startswith("gs://") or test_data_path.startswith("gs://"):
        fs = gcsfs.GCSFileSystem()

    # 1. データの読み込み
    print("Loading test data...")
    if test_data_path.startswith("gs://"):
        with fs.open(test_data_path, 'r') as f:
            df = pd.read_csv(f)
    else:
        df = pd.read_csv(test_data_path)
    
    if 'Target' not in df.columns:
        raise ValueError(f"Test data must contain 'Target' column. Columns found: {df.columns}")
    
    y_true = df['Target']
    # 特徴量はTarget以外と仮定（実際にはモデルの学習時の特徴量定義が必要だが、
    # ここではシンプルにするためTarget以外をすべて使用、またはモデルが特徴量を保持していることを期待）
    # 簡易実装として、データセットからTargetを除いたものを入力とする
    X_test = df.drop('Target', axis=1)
    
    print(f"Test data loaded: {len(df)} samples")

    # 2. モデルの探索と評価
    evaluation_results = {
        "status": "completed",
        "models_evaluated": 0,
        "results": {}
    }

    # モデルファイルのリスト取得
    model_files = []
    if models_dir.startswith("gs://"):
        # GCS上のファイルをリスト
        try:
            # fs.glob は gs:// を含まないパスを返すことがあるため調整
            files = fs.glob(os.path.join(models_dir, "*.pkl"))
            model_files = [f"gs://{f}" for f in files]
        except Exception as e:
            print(f"Error listing GCS files: {e}")
    else:
        # ローカルファイルをリスト
        model_files = glob.glob(os.path.join(models_dir, "*.pkl"))

    print(f"Found {len(model_files)} models")

    best_score = -1.0
    best_model_name = ""

    for model_path in model_files:
        model_name = os.path.basename(model_path)
        print(f"Evaluating model: {model_name}")
        
        try:
            # モデルロード
            model = None
            if model_path.startswith("gs://"):
                with fs.open(model_path, 'rb') as f:
                    model = joblib.load(f)
            else:
                model = joblib.load(model_path)
            
            # 推論（特徴量の整合性チェックはスキップするため、
            # モデルが学習した際の特徴量順序とX_testの列順序が一致している前提）
            # note: 厳密には学習時のfeature namesメタデータを参照すべき
            
            # モデルが feature_names_in_ を持っている場合、それに合わせてX_testをフィルタリング
            if hasattr(model, 'feature_names_in_'):
                features = model.feature_names_in_
                available_features = [f for f in features if f in X_test.columns]
                if len(available_features) != len(features):
                    print(f"Warning: Missing features for {model_name}. Skipping.")
                    continue
                X_input = X_test[features]
            else:
                X_input = X_test

            y_pred = model.predict(X_input)
            
            # メトリクス計算
            result = {}
            if "accuracy" in metrics:
                result["accuracy"] = float(accuracy_score(y_true, y_pred))
            if "precision" in metrics:
                result["precision"] = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
            if "recall" in metrics:
                result["recall"] = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
            if "f1" in metrics:
                result["f1"] = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
            
            evaluation_results["results"][model_name] = result
            evaluation_results["models_evaluated"] += 1
            
            # ベストモデル判定 (Accuracy優先)
            current_score = result.get("accuracy", 0)
            if current_score > best_score:
                best_score = current_score
                best_model_name = model_name

            # 混同行列の保存
            if save_confusion_matrix:
                cm = confusion_matrix(y_true, y_pred)
                plt.figure(figsize=(8, 6))
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
                plt.xlabel('Predicted')
                plt.ylabel('Actual')
                plt.title(f'Confusion Matrix - {model_name}')
                
                # 画像をバッファに保存
                buf = BytesIO()
                plt.savefig(buf, format='png')
                plt.close()
                buf.seek(0)
                
                # 保存先パス
                cm_filename = f"confusion_matrix_{model_name}.png"
                if output_report_path:
                    # report_pathがディレクトリパスならそこに保存
                    base_dir = os.path.dirname(output_report_path) if output_report_path.endswith('.json') else output_report_path
                    save_path = os.path.join(base_dir, cm_filename).replace("\\", "/") # GCS対策
                    
                    if save_path.startswith("gs://"):
                        with fs.open(save_path, 'wb') as f:
                            f.write(buf.getvalue())
                    else:
                        os.makedirs(base_dir, exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(buf.getvalue())
                    print(f"Saved confusion matrix to {save_path}")

        except Exception as e:
            print(f"Error evaluating {model_name}: {e}")
            import traceback
            traceback.print_exc()

    evaluation_results["best_model"] = best_model_name
    evaluation_results["best_accuracy"] = best_score
    
    # 結果の保存
    if output_report_path:
         # ディレクトリかファイルパスか判定
        if not output_report_path.endswith('.json'):
            report_file = os.path.join(output_report_path, "evaluation_report.json").replace("\\", "/")
        else:
            report_file = output_report_path

        json_str = json.dumps(evaluation_results, indent=2)
        
        if report_file.startswith("gs://"):
            with fs.open(report_file, 'w') as f:
                f.write(json_str)
        else:
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                f.write(json_str)
        print(f"Saved evaluation report to {report_file}")

    print(json.dumps(evaluation_results, indent=2))
    return evaluation_results
